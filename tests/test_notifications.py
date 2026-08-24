"""
Notifications that say something, and keep saying it.

The design is explicit on two points, and both are load-bearing here:
nothing is announced in a single channel, and an outcome must survive the
session moving off today.
"""

from datetime import datetime, timedelta

from fastapi import status

from app.database.models import Notification, NotificationKind
from app.services.notification_delivery import NotificationDelivery

from .conftest import _auth


class TestTheLoopNotifies:
    def test_an_auto_applied_change_tells_the_caregiver_what_happened(
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

        rows = (
            db_session.query(Notification)
            .filter(Notification.recipient_id == family["parent"].id)
            .all()
        )
        assert [r.kind for r in rows] == [NotificationKind.AUTO_APPLIED.value]
        # A key and parameters, never a rendered sentence.
        assert rows[0].text_key == "parent.log_moved"
        assert rows[0].params["title"] == "ABA session"

    def test_the_caregiver_can_turn_auto_approve_notices_off(
        self, client, db_session, family, rules, session_row
    ):
        client.put(
            "/rules", json={"notify_on_auto_approve": False}, headers=_auth(family["parent"])
        )

        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        assert (
            db_session.query(Notification)
            .filter(Notification.recipient_id == family["parent"].id)
            .count()
            == 0
        )

    def test_a_parked_request_tells_the_caregiver_it_is_waiting(
        self, client, db_session, family, rules, session_row
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

        row = (
            db_session.query(Notification)
            .filter(Notification.recipient_id == family["parent"].id)
            .one()
        )
        assert row.kind == NotificationKind.NEEDS_YOU.value

    def test_the_answer_reaches_whoever_asked(self, client, db_session, family, rules, session_row):
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
            json={"alternative_index": 0},
            headers=_auth(family["parent"]),
        )

        outcome = (
            db_session.query(Notification)
            .filter(
                Notification.recipient_id == family["kid"].id,
                Notification.kind == NotificationKind.OUTCOME.value,
            )
            .one()
        )
        assert outcome.text_key == "kid.parent_yes"

    def test_a_denial_is_an_outcome_too(self, client, db_session, family, rules, session_row):
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
            f"/parent/approvals/{parked['request_id']}/deny",
            json={"approved": False, "parent_note": "Too late in the day."},
            headers=_auth(family["parent"]),
        )

        outcome = (
            db_session.query(Notification)
            .filter(
                Notification.recipient_id == family["kid"].id,
                Notification.kind == NotificationKind.OUTCOME.value,
            )
            .one()
        )
        assert outcome.text_key == "kid.parent_no"


class TestItSurvives:
    def test_an_outcome_is_still_there_after_the_session_moves_off_today(
        self, client, db_session, family, rules, session_row
    ):
        """The whole point: a child who was not looking still finds it."""
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
            json={"alternative_index": 0},
            headers=_auth(family["parent"]),
        )

        # The session is pushed well into the future; today's cards are empty.
        session_row.start_utc = datetime.utcnow() + timedelta(days=20)
        db_session.commit()
        assert client.get("/kid/today", headers=_auth(family["kid"])).json()["cards"] == []

        notifications = client.get("/notifications", headers=_auth(family["kid"])).json()

        assert notifications
        assert notifications[0]["text"].startswith("Yes. ABA session is ")

    def test_the_sentence_is_rendered_in_the_readers_language(
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

        from app.utils.locale_context import set_user_locale

        english = client.get("/notifications", headers=_auth(family["parent"])).json()[0]
        set_user_locale(db_session, family["parent"], "es")
        spanish = client.get("/notifications", headers=_auth(family["parent"])).json()[0]

        assert english["text"].startswith("ABA session moved to ")
        assert spanish["text"].startswith("ABA session movido al ")
        assert english["id"] == spanish["id"]  # one row, two readings


class TestReading:
    def test_notifications_can_be_marked_read(self, client, db_session, family, rules, session_row):
        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )
        first = client.get("/notifications", headers=_auth(family["parent"])).json()[0]
        assert first["read"] is False

        client.post(f"/notifications/{first['id']}/read", headers=_auth(family["parent"]))

        after = client.get("/notifications", headers=_auth(family["parent"])).json()[0]
        assert after["read"] is True
        assert (
            client.get("/notifications?unread_only=true", headers=_auth(family["parent"])).json()
            == []
        )

    def test_you_cannot_read_somebody_elses_notification(
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
        theirs = client.get("/notifications", headers=_auth(family["parent"])).json()[0]

        response = client.post(f"/notifications/{theirs['id']}/read", headers=_auth(family["kid"]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_you_only_see_your_own(self, client, db_session, family, rules, session_row):
        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        kid_view = client.get("/notifications", headers=_auth(family["kid"])).json()

        assert kid_view == []  # the auto-apply notice was the caregiver's


class TestChannels:
    def test_the_stored_row_is_always_a_delivery(self, db_session, family, monkeypatch):
        """If every outbound channel fails, the sentence is still readable."""
        monkeypatch.setattr(NotificationDelivery, "_try_email", lambda self, a, s: False)
        monkeypatch.setattr(NotificationDelivery, "_try_sms", lambda self, n, s: False)

        notification = NotificationDelivery(db_session).notify(
            recipient=family["parent"],
            kind=NotificationKind.OUTCOME,
            text_key="kid.parent_yes_skip",
            params={"title": "ABA session"},
        )

        assert notification.delivered_channels == ["in_app"]
        # And it is readable regardless of what any channel did.
        assert (
            NotificationDelivery(db_session).render(notification, family["parent"])
            == "Yes. No ABA session today."
        )

    def test_a_broken_channel_never_breaks_the_loop(
        self, client, db_session, family, rules, session_row, monkeypatch
    ):
        monkeypatch.setattr(
            NotificationDelivery,
            "_fan_out",
            lambda self, recipient, sentence: (_ for _ in ()).throw(RuntimeError("smtp")),
        )

        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=16).isoformat(),
            },
            headers=_auth(family["kid"]),
        )

        assert response.json()["auto_applied"] is True
        db_session.refresh(session_row)
        assert session_row.start_utc.hour == 16  # the change still happened
