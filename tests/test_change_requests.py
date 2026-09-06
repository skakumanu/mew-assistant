"""
Tests for the three-persona loop.

One write path: a kid or a provider asks, the rule engine decides, and the
change is either applied immediately or parked for the parent with reason
codes and three compliant alternatives attached.
"""

from datetime import datetime, timedelta

from fastapi import status

from app.database.models import (
    ApprovalRequest,
    ApprovalStatus,
    ChangeLogEntry,
    ProviderOrg,
    ScheduledSession,
    User,
)
from app.utils.auth import get_password_hash
from app.utils.locale import DEFAULT_TIMEZONE, Translator, from_local, to_local

from .conftest import _auth


def _soon_today(hours=2):
    """
    A moment `hours` from now, clamped to stay on today's date in the
    family's own timezone - the `rules` fixture never sets one explicitly,
    so it's whatever a fresh RuleSet defaults to (DEFAULT_TIMEZONE).

    Plain `datetime.utcnow() + timedelta(hours=hours)` rolls into tomorrow
    whenever the suite happens to run within `hours` of that timezone's own
    midnight - /kid/today filters strictly to that family's own
    [midnight, midnight+1) - so a session "in 2 hours" would silently fall
    outside "today" and the test would fail for no reason connected to the
    code under test.
    """
    now_local = to_local(datetime.utcnow().replace(microsecond=0), DEFAULT_TIMEZONE)
    start_local = now_local + timedelta(hours=hours)
    if start_local.date() != now_local.date():
        start_local = now_local.replace(hour=23, minute=59, second=0)
    return from_local(start_local, DEFAULT_TIMEZONE)


class TestAutoApply:
    """A request inside the rules never waits on anybody."""

    def test_compliant_move_is_applied_immediately(
        self, client, db_session, family, rules, session_row
    ):
        new_start = session_row.start_utc.replace(hour=16, minute=0)

        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": new_start.isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["auto_applied"] is True
        assert body["reason_codes"] == []

        db_session.refresh(session_row)
        assert session_row.start_utc == new_start
        assert session_row.last_changed_at is not None

    def test_auto_applied_change_is_written_to_the_quiet_log(
        self, client, db_session, family, rules, session_row
    ):
        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        entry = db_session.query(ChangeLogEntry).one()
        assert entry.tone == "auto"
        assert entry.text_key == "parent.log_moved"
        # A key and parameters, never a rendered sentence.
        assert entry.params["title"] == "ABA session"
        assert entry.meta_key == "parent.meta_auto"

    def test_auto_applied_change_is_still_audited(
        self, client, db_session, family, rules, session_row
    ):
        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        request = (
            db_session.query(ApprovalRequest)
            .filter(ApprovalRequest.id == response.json()["request_id"])
            .one()
        )
        assert request.auto_applied is True
        assert request.status == ApprovalStatus.APPROVED
        assert request.requested_by == "kid"

    def test_the_kid_is_told_it_happened_not_why(
        self, client, db_session, family, rules, session_row
    ):
        # A morning session, so "Later, please" still lands inside the day.
        session_row.start_utc = session_row.start_utc.replace(hour=10, minute=0)
        db_session.commit()

        response = client.post(
            "/kid/ask",
            json={"session_id": session_row.id, "ask": "later"},
            headers=_auth(family["kid"]),
        )

        body = response.json()
        assert body["auto_applied"] is True
        assert body["message"].startswith("Done.")
        # The kid never sees a rule, not even the ones that passed.
        assert body["reason_codes"] == []


class TestParkedForParent:
    """A request outside the rules arrives with a fix already attached."""

    def test_late_end_is_parked_with_a_reason_code(
        self, client, db_session, family, rules, session_row
    ):
        # 17:00 + 90 minutes runs past the 18:00 limit.
        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17, minute=0).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        )

        body = response.json()
        assert body["auto_applied"] is False
        assert body["reason_codes"] == ["latest_end"]
        assert body["reasons_text"] == "outside the allowed hours"

        db_session.refresh(session_row)
        assert session_row.start_utc.hour == 15  # nothing moved

    def test_three_alternatives_come_with_the_card(self, client, family, rules, session_row):
        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        )

        alternatives = response.json()["alternatives"]
        assert len(alternatives) == 3
        assert alternatives[0]["note"] == "closest"
        assert alternatives[1]["note"] == "also fits"

    def test_a_cancellation_still_reaches_the_parent(
        self, client, db_session, family, rules, session_row
    ):
        response = client.post(
            "/kid/ask",
            json={"session_id": session_row.id, "ask": "skip"},
            headers=_auth(family["kid"]),
        )

        body = response.json()
        assert body["auto_applied"] is False
        assert body["message"] == "I asked about skipping. An answer is coming."

        db_session.refresh(session_row)
        assert session_row.is_cancelled is False

    def test_a_swap_to_another_therapist_is_parked(self, client, family, rules, session_row):
        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "swap_provider",
                "new_start": session_row.start_utc.isoformat(),
                "new_provider_person_id": family["jordan"].id,
            },
            headers=_auth(family["provider_login"]),
        )

        assert response.json()["reason_codes"] == ["same_provider"]

    def test_the_provider_is_told_which_of_the_two_things_happened(
        self, client, family, rules, session_row
    ):
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()
        assert parked["message"] == "Sent for approval: outside the allowed hours."

        applied = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=14).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()
        assert applied["message"].startswith("Confirmed for ")
        assert "no approval needed" in applied["message"]


class TestParentDecides:
    def test_choosing_an_alternative_moves_the_session(
        self, client, db_session, family, rules, session_row
    ):
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()

        response = client.post(
            f"/parent/approvals/{parked['request_id']}/choose",
            json={"alternative_index": 0},
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK
        chosen = datetime.fromisoformat(parked["alternatives"][0]["start"])
        db_session.refresh(session_row)
        assert session_row.start_utc == chosen

    def test_choosing_records_a_parent_decided_log_row(
        self, client, db_session, family, rules, session_row
    ):
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()
        client.post(
            f"/parent/approvals/{parked['request_id']}/choose",
            json={"alternative_index": 1},
            headers=_auth(family["parent"]),
        )

        entry = db_session.query(ChangeLogEntry).one()
        assert entry.tone == "manual"
        assert entry.meta_key == "parent.meta_picked"

    def test_an_out_of_range_alternative_is_refused(self, client, family, rules, session_row):
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()

        response = client.post(
            f"/parent/approvals/{parked['request_id']}/choose",
            json={"alternative_index": 9},
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_allowing_their_time_anyway_applies_what_was_asked(
        self, client, db_session, family, rules, session_row
    ):
        asked_for = session_row.start_utc.replace(hour=17, minute=0)
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": asked_for.isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()

        client.post(
            f"/parent/approvals/{parked['request_id']}/approve",
            json={"approved": True},
            headers=_auth(family["parent"]),
        )

        db_session.refresh(session_row)
        assert session_row.start_utc == asked_for

    def test_saying_no_leaves_the_schedule_alone_but_logs_it(
        self, client, db_session, family, rules, session_row
    ):
        original = session_row.start_utc
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": original.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()

        client.post(
            f"/parent/approvals/{parked['request_id']}/deny",
            json={"approved": False, "parent_note": "Too late in the day."},
            headers=_auth(family["parent"]),
        )

        db_session.refresh(session_row)
        assert session_row.start_utc == original
        entry = db_session.query(ChangeLogEntry).one()
        assert entry.text_key == "parent.log_stays"
        assert entry.meta_key == "parent.meta_declined"


class TestParentViews:
    def test_the_inbox_card_carries_everything_needed_to_decide(
        self, client, family, rules, session_row
    ):
        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        )

        card = client.get("/parent/approvals/inbox", headers=_auth(family["parent"])).json()[0]

        assert card["source_label"] == "Bright Steps ABA"
        assert card["headline"].startswith("ABA session to ")
        assert card["detail"].startswith("Now ")
        assert "Dana R." in card["detail"]
        assert card["reasons_text"] == "Does not fit your rules: outside the allowed hours"
        assert len(card["alternatives"]) == 3

    def test_the_log_renders_in_the_readers_language(self, client, family, rules, session_row):
        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        headers = _auth(family["parent"])
        english = client.get("/parent/log", headers=headers).json()[0]
        headers["Accept-Language"] = "es-MX,es;q=0.9"
        spanish = client.get("/parent/log", headers=headers).json()[0]

        assert english["text"].startswith("ABA session moved to ")
        assert spanish["text"].startswith("ABA session movido al ")
        # Same stored row, two readers, no translation at write time.
        assert english["id"] == spanish["id"]

    def test_the_week_marks_what_changed(self, client, family, rules, session_row):
        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        week = client.get("/parent/week", headers=_auth(family["parent"])).json()
        moved = [
            session
            for day in week
            for session in day["sessions"]
            if session["id"] == session_row.id
        ]

        assert moved and moved[0]["changed"] is True

    def test_the_week_groups_an_evening_class_by_the_familys_own_day(
        self, client, db_session, family, rules
    ):
        """
        A class stored just after midnight UTC is still evening-of-the-day-
        before for a family in Pacific time. Grouping by the UTC calendar
        date - the bug this guards against - would silently put it a day
        too late in the Week tab.
        """
        rules.timezone = "America/Los_Angeles"
        db_session.commit()

        # A few days out, at 1am UTC: always the previous evening in
        # Pacific time regardless of DST, and far enough out that the test
        # doesn't depend on what day it happens to run.
        start_utc = (datetime.utcnow() + timedelta(days=3)).replace(
            hour=1, minute=0, second=0, microsecond=0
        )
        local_date = to_local(start_utc, "America/Los_Angeles").date()
        assert local_date != start_utc.date()  # the fixture only proves anything if these differ

        row = ScheduledSession(
            child_id=family["kid"].id,
            provider_org_id=family["org"].id,
            title="ENGL-1000 Hybrid",
            activity_type="school",
            start_utc=start_utc,
            duration_minutes=120,
        )
        db_session.add(row)
        db_session.commit()

        week = client.get(
            "/parent/week", params={"days": 10}, headers=_auth(family["parent"])
        ).json()

        correct_day = next(d for d in week if d["date"] == local_date.isoformat())
        wrong_day = next((d for d in week if d["date"] == start_utc.date().isoformat()), None)

        assert "ENGL-1000 Hybrid" in [s["title"] for s in correct_day["sessions"]]
        if wrong_day is not None:
            assert "ENGL-1000 Hybrid" not in [s["title"] for s in wrong_day["sessions"]]

        matched = next(s for s in correct_day["sessions"] if s["title"] == "ENGL-1000 Hybrid")
        expected_time_label = Translator("en").time(to_local(start_utc, "America/Los_Angeles"))
        assert matched["time_label"] == expected_time_label


class TestAuthorisation:
    """No client decides whether something is allowed - and neither does a
    stranger decide whose schedule they are touching."""

    def test_another_familys_kid_cannot_touch_this_session(
        self, client, db_session, family, rules, session_row
    ):
        outsider = User(
            email="someone@example.com",
            username="someone",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_kid_account=True,
            parent_id=family["parent"].id,
            display_name="Outsider",
        )
        db_session.add(outsider)
        db_session.commit()

        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(outsider),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_a_move_without_a_new_time_is_refused(self, client, family, rules, session_row):
        response = client.post(
            "/requests",
            json={"session_id": session_row.id, "kind": "move"},
            headers=_auth(family["kid"]),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_an_unknown_kind_is_refused(self, client, family, rules, session_row):
        response = client.post(
            "/requests",
            json={"session_id": session_row.id, "kind": "delete_everything"},
            headers=_auth(family["kid"]),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestKidToday:
    def test_today_lists_the_days_cards(self, client, db_session, family, rules):
        start = _soon_today()
        row = ScheduledSession(
            child_id=family["kid"].id,
            provider_org_id=family["org"].id,
            provider_person_id=family["dana"].id,
            title="Speech",
            activity_type="speech",
            start_utc=start,
            duration_minutes=45,
        )
        db_session.add(row)
        db_session.commit()

        today = client.get("/kid/today", headers=_auth(family["kid"])).json()

        titles = [card["title"] for card in today["cards"]]
        assert "Speech" in titles
        assert today["count_label"].endswith("today")
        # No emoji anywhere in what the kid reads.
        assert all(ord(ch) < 0x2190 for ch in today["greeting"] + today["note"])

    def test_a_card_with_an_open_request_shows_a_status_instead_of_buttons(
        self, client, db_session, family, rules
    ):
        start = _soon_today()
        row = ScheduledSession(
            child_id=family["kid"].id,
            provider_org_id=family["org"].id,
            provider_person_id=family["dana"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=start,
            duration_minutes=60,
        )
        db_session.add(row)
        db_session.commit()
        db_session.refresh(row)

        # Two hours' notice, so this one is parked.
        client.post(
            "/kid/ask",
            json={"session_id": row.id, "ask": "later"},
            headers=_auth(family["kid"]),
        )

        card = [
            c
            for c in client.get("/kid/today", headers=_auth(family["kid"])).json()["cards"]
            if c["session_id"] == row.id
        ][0]

        assert card["can_ask"] is False
        assert card["status_text"] == "I asked. You will get an answer soon."


class TestProviderView:
    def test_a_provider_sees_only_their_own_organisations_sessions(
        self, client, db_session, family, rules, session_row
    ):
        other_org = ProviderOrg(name="Willow Speech", kind="speech")
        db_session.add(other_org)
        db_session.commit()
        db_session.add(
            ScheduledSession(
                child_id=family["kid"].id,
                provider_org_id=other_org.id,
                title="Speech",
                activity_type="speech",
                start_utc=datetime.utcnow() + timedelta(days=2),
                duration_minutes=45,
            )
        )
        db_session.commit()

        rows = client.get("/provider/sessions", headers=_auth(family["provider_login"])).json()

        assert [row["session"]["title"] for row in rows] == ["ABA session"]

    def test_a_parent_is_not_a_provider(self, client, family, rules):
        response = client.get("/provider/sessions", headers=_auth(family["parent"]))
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRulesApi:
    def test_rules_are_created_with_the_designs_defaults(self, client, family):
        rules = client.get("/rules", headers=_auth(family["parent"])).json()

        assert rules["min_notice_hours"] == 24
        assert rules["latest_end"] == "18:00:00"
        assert rules["buffer_minutes"] == 45
        assert rules["require_same_provider_person"] is True
        assert rules["cancellation_needs_approval"] is True
        assert [block["label_key"] for block in rules["protected_blocks"]] == ["block.midday"]

    def test_turning_a_rule_off_stops_it_asking(
        self, client, db_session, family, rules, session_row
    ):
        # With cancellation approval on, skipping is parked.
        first = client.post(
            "/kid/ask",
            json={"session_id": session_row.id, "ask": "skip"},
            headers=_auth(family["kid"]),
        ).json()
        assert first["auto_applied"] is False

        client.put(
            "/rules",
            json={"cancellation_needs_approval": False},
            headers=_auth(family["parent"]),
        )

        second = client.post(
            "/kid/ask",
            json={"session_id": session_row.id, "ask": "skip"},
            headers=_auth(family["kid"]),
        ).json()

        assert second["auto_applied"] is True
        db_session.refresh(session_row)
        assert session_row.is_cancelled is True

    def test_a_kid_cannot_read_the_rules(self, client, family):
        response = client.get("/rules", headers=_auth(family["kid"]))
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestVoice:
    """Voice may request anything and approve nothing."""

    def test_a_spoken_request_is_read_back_before_it_is_sent(
        self, client, db_session, family, rules, session_row
    ):
        original = session_row.start_utc

        response = client.post(
            "/voice/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": original.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        body = response.json()
        assert body["confirmed"] is False
        assert body["readback"].startswith("ABA session to ")
        # The spoken line and the on-screen line are the same sentence.
        assert body["speak"] == body["readback"]

        db_session.refresh(session_row)
        assert session_row.start_utc == original  # nothing was written

    def test_a_confirmed_request_goes_through_the_same_loop(
        self, client, db_session, family, rules, session_row
    ):
        new_start = session_row.start_utc.replace(hour=16, minute=0)

        response = client.post(
            "/voice/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": new_start.isoformat(),
                "confirmed": True,
            },
            headers=_auth(family["kid"]),
        )

        assert response.json()["auto_applied"] is True
        db_session.refresh(session_row)
        assert session_row.start_utc == new_start

    def test_a_spoken_request_outside_the_rules_still_parks(
        self, client, family, rules, session_row
    ):
        response = client.post(
            "/voice/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
                "confirmed": True,
            },
            headers=_auth(family["provider_login"]),
        )

        body = response.json()
        assert body["auto_applied"] is False
        assert body["reason_codes"] == ["latest_end"]
        # A decision surface is not read out loud.
        assert body["alternatives"] == []

    def test_approving_by_voice_is_refused(self, client, family, rules, session_row):
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()

        response = client.post(
            f"/voice/approvals/{parked['request_id']}/approve",
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "cannot approve" in response.json()["detail"]
