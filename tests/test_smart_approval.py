"""
Smart approval is the second opinion, never the decision.

The deterministic engine decides. These tests pin that boundary: a request
that satisfies the declared rules is applied without consulting this module
at all, and a request that breaks one stays parked no matter what history
says about it.
"""

import json
from datetime import datetime, timedelta

import pytest

from app.database.models import (
    ApprovalRequest,
    ApprovalRule,
    ApprovalStatus,
    Family,
    RequestType,
    ScheduledSession,
)
from app.services.smart_approval_service import MIN_HISTORY, SmartApprovalService

from .conftest import _auth


@pytest.fixture
def advisor(db_session):
    return SmartApprovalService(db_session)


def _decided(db_session, family, status, activity="aba", days_ago=1):
    """A request the caregiver actually decided, not one auto-applied."""
    session = ScheduledSession(
        child_id=family["kid"].id,
        provider_org_id=family["org"].id,
        title="ABA session",
        activity_type=activity,
        start_utc=datetime.utcnow() + timedelta(days=3),
        duration_minutes=90,
    )
    db_session.add(session)
    db_session.commit()

    request = ApprovalRequest(
        kid_id=family["kid"].id,
        parent_id=family["parent"].id,
        request_type=RequestType.TIME_CHANGE,
        status=status,
        change_kind="move",
        scheduled_session_id=session.id,
        auto_applied=False,
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)
    return request


class TestItNeverDecides:
    def test_a_compliant_request_is_applied_without_any_advice(
        self, client, db_session, family, rules, session_row, monkeypatch
    ):
        """The engine passes it, so the advisor is never even consulted."""
        called = {"n": 0}

        def tripwire(self, request):
            called["n"] += 1
            raise AssertionError("advisor consulted on the auto-apply path")

        monkeypatch.setattr(SmartApprovalService, "advise", tripwire)

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
        assert called["n"] == 0

    def test_history_cannot_rescue_a_request_the_rules_reject(
        self, client, db_session, family, rules, session_row
    ):
        """Even with a perfect approval record, a broken rule still parks."""
        for _ in range(10):
            _decided(db_session, family, ApprovalStatus.APPROVED)

        response = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        )

        body = response.json()
        assert body["auto_applied"] is False
        assert body["reason_codes"] == ["latest_end"]
        db_session.refresh(session_row)
        assert session_row.start_utc.hour == 15


class TestAdvice:
    def test_no_advice_without_enough_history(self, db_session, family, advisor):
        request = _decided(db_session, family, ApprovalStatus.PENDING)

        assert advisor.advise(request) is None

    def test_advice_counts_past_decisions(self, db_session, family, advisor):
        for _ in range(MIN_HISTORY + 1):
            _decided(db_session, family, ApprovalStatus.APPROVED)
        _decided(db_session, family, ApprovalStatus.DENIED)
        request = _decided(db_session, family, ApprovalStatus.PENDING)

        advisory = advisor.advise(request)

        assert advisory is not None
        assert advisory.approved == MIN_HISTORY + 1
        assert advisory.denied == 1
        assert 0 < advisory.approval_rate < 1

    def test_auto_applied_requests_are_not_counted_as_agreement(self, db_session, family, advisor):
        """A caregiver never saw those, so they are not evidence they agreed."""
        for _ in range(6):
            auto = _decided(db_session, family, ApprovalStatus.APPROVED)
            auto.auto_applied = True
        db_session.commit()
        request = _decided(db_session, family, ApprovalStatus.PENDING)

        assert advisor.advise(request) is None

    def test_advice_only_compares_like_with_like(self, db_session, family, advisor):
        for _ in range(6):
            _decided(db_session, family, ApprovalStatus.APPROVED, activity="speech")
        request = _decided(db_session, family, ApprovalStatus.PENDING, activity="aba")

        assert advisor.advise(request) is None

    def test_the_card_carries_the_advisory(self, client, db_session, family, rules, session_row):
        for _ in range(MIN_HISTORY + 1):
            _decided(db_session, family, ApprovalStatus.APPROVED)

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

        assert card["advisory"]["approved"] == MIN_HISTORY + 1
        assert card["advisory"]["denied"] == 0

    def test_a_broken_advisor_does_not_break_the_card(
        self, client, db_session, family, rules, session_row, monkeypatch
    ):
        monkeypatch.setattr(
            SmartApprovalService,
            "advise",
            lambda self, request: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        )

        response = client.get("/parent/approvals/inbox", headers=_auth(family["parent"]))

        assert response.status_code == 200
        assert response.json()[0]["advisory"] is None


class TestFreeFormRules:
    def test_conditions_are_read_from_json_not_from_columns(self, db_session, family, advisor):
        db_session.add(Family(name="Kumar"))
        db_session.commit()
        db_session.add(
            ApprovalRule(
                family_id=1,
                rule_name="Weekday ABA",
                rule_type="activity_type",
                conditions=json.dumps({"allowed_activities": ["aba"], "max_duration_minutes": 120}),
                is_active=True,
                created_by=family["parent"].id,
            )
        )
        db_session.commit()
        request = _decided(db_session, family, ApprovalStatus.PENDING)

        rule = advisor.matching_rule(request)

        assert rule is not None and rule.rule_name == "Weekday ABA"

    def test_a_rule_with_no_usable_conditions_matches_nothing(self, db_session, family, advisor):
        db_session.add(
            ApprovalRule(
                family_id=1,
                rule_name="Empty",
                rule_type="activity_type",
                conditions="{}",
                is_active=True,
                created_by=family["parent"].id,
            )
        )
        db_session.commit()
        request = _decided(db_session, family, ApprovalStatus.PENDING)

        assert advisor.matching_rule(request) is None

    def test_unparseable_conditions_do_not_raise(self, db_session, family, advisor):
        db_session.add(
            ApprovalRule(
                family_id=1,
                rule_name="Broken",
                rule_type="activity_type",
                conditions="not json",
                is_active=True,
                created_by=family["parent"].id,
            )
        )
        db_session.commit()
        request = _decided(db_session, family, ApprovalStatus.PENDING)

        assert advisor.matching_rule(request) is None


class TestBatching:
    def test_a_short_queue_is_one_batch(self, db_session, family, advisor):
        _decided(db_session, family, ApprovalStatus.PENDING)

        batches = advisor.batch_pending(family["parent"])

        assert len(batches) == 1 and batches[0]["batch_id"] == "single"

    def test_time_sensitive_requests_are_separated_out(self, db_session, family, advisor):
        for _ in range(3):
            _decided(db_session, family, ApprovalStatus.PENDING)
        soon = _decided(db_session, family, ApprovalStatus.PENDING)
        soon.new_start_utc = datetime.utcnow() + timedelta(minutes=30)
        db_session.commit()

        batches = {b["batch_id"]: b for b in advisor.batch_pending(family["parent"])}

        assert soon.id in batches["time_sensitive"]["request_ids"]
        assert soon.id not in batches["everything_else"]["request_ids"]


class TestSuggestions:
    def test_a_suggestion_is_never_an_applied_rule(self, db_session, family, advisor):
        for _ in range(6):
            _decided(db_session, family, ApprovalStatus.APPROVED)
        for _ in range(5):
            _decided(db_session, family, ApprovalStatus.APPROVED, activity="speech")

        suggestions = advisor.suggest_rules_from_history(family["parent"])

        assert {s["activity_type"] for s in suggestions} == {"aba", "speech"}
        assert all(s["suggestion"] == "always_allow" for s in suggestions)
        # Nothing was written: it is a suggestion, not a rule.
        assert db_session.query(ApprovalRule).count() == 0

    def test_an_activity_ever_denied_is_not_suggested(self, db_session, family, advisor):
        for _ in range(9):
            _decided(db_session, family, ApprovalStatus.APPROVED)
        _decided(db_session, family, ApprovalStatus.DENIED)

        assert advisor.suggest_rules_from_history(family["parent"]) == []
