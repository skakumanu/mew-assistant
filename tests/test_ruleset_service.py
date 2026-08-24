"""
Tests for RuleSet persistence, engine translation and the backfill.

Nobody re-enters rules they already declared: whatever a family expressed
through the older free-form ``ApprovalRule`` rows is folded into their new
RuleSet the first time it is read.
"""

from datetime import time

import pytest

from app.database.models import ApprovalRule, Family, RuleSet, User, WeeklyCap
from app.services.ruleset_service import RuleSetService
from app.utils.auth import get_password_hash


@pytest.fixture
def parent(db_session):
    user = User(
        email="parent-rules@example.com",
        username="parent-rules",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=False,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def family(db_session, parent):
    row = Family(name="Kumar", primary_contact_id=parent.id)
    db_session.add(row)
    db_session.commit()
    return row


class TestDefaults:
    def test_first_read_creates_the_designs_defaults(self, db_session, parent):
        ruleset = RuleSetService(db_session).get_or_create(parent.id)

        assert ruleset.min_notice_hours == 24
        assert ruleset.earliest_start == time(8, 0)
        assert ruleset.latest_end == time(18, 0)
        assert ruleset.buffer_minutes == 45
        assert ruleset.require_same_provider_person is True
        assert ruleset.cancellation_needs_approval is True
        assert [block.label_key for block in ruleset.protected_blocks] == ["block.midday"]

    def test_reading_twice_does_not_create_twice(self, db_session, parent):
        service = RuleSetService(db_session)
        first = service.get_or_create(parent.id)
        second = service.get_or_create(parent.id)

        assert first.id == second.id
        assert db_session.query(RuleSet).count() == 1


class TestEngineTranslation:
    def test_stored_rules_become_engine_rules(self, db_session, parent):
        service = RuleSetService(db_session)
        ruleset = service.get_or_create(parent.id)
        db_session.add(WeeklyCap(ruleset_id=ruleset.id, activity_type="aba", max_sessions=3))
        db_session.commit()
        db_session.refresh(ruleset)

        engine_rules = service.to_engine_rules(ruleset)

        assert engine_rules.min_notice_hours == 24
        assert engine_rules.max_sessions_per_week == {"aba": 3}
        assert engine_rules.protected_blocks[0].start == time(12, 0)
        assert engine_rules.protected_blocks[0].label_key == "block.midday"

    def test_an_off_toggle_becomes_an_unset_field(self, db_session, parent):
        service = RuleSetService(db_session)
        ruleset = service.get_or_create(parent.id)

        service.update(ruleset, {"min_notice_hours": None, "protected_blocks": []})
        engine_rules = service.to_engine_rules(ruleset)

        assert engine_rules.min_notice_hours is None
        assert engine_rules.protected_blocks == []

    def test_updating_only_touches_what_was_sent(self, db_session, parent):
        service = RuleSetService(db_session)
        ruleset = service.get_or_create(parent.id)

        service.update(ruleset, {"buffer_minutes": 15})

        assert ruleset.buffer_minutes == 15
        assert ruleset.min_notice_hours == 24  # untouched
        assert len(ruleset.protected_blocks) == 1


class TestBackfill:
    def test_a_time_range_rule_seeds_the_allowed_hours(self, db_session, parent, family):
        db_session.add(
            ApprovalRule(
                family_id=family.id,
                rule_name="hours",
                rule_type="time_range",
                conditions='{"earliest_start": "09:00", "latest_end": "17:00"}',
                is_active=True,
                created_by=parent.id,
            )
        )
        db_session.commit()

        ruleset = RuleSetService(db_session).get_or_create(parent.id)

        assert ruleset.earliest_start == time(9, 0)
        assert ruleset.latest_end == time(17, 0)

    def test_a_duration_rule_seeds_the_buffer(self, db_session, parent, family):
        db_session.add(
            ApprovalRule(
                family_id=family.id,
                rule_name="travel",
                rule_type="duration",
                conditions='{"buffer_minutes": 30}',
                is_active=True,
                created_by=parent.id,
            )
        )
        db_session.commit()

        ruleset = RuleSetService(db_session).get_or_create(parent.id)

        assert ruleset.buffer_minutes == 30

    def test_an_activity_rule_seeds_a_weekly_cap(self, db_session, parent, family):
        db_session.add(
            ApprovalRule(
                family_id=family.id,
                rule_name="cap",
                rule_type="activity_type",
                conditions='{"activity_type": "aba", "max_per_week": 3}',
                is_active=True,
                created_by=parent.id,
            )
        )
        db_session.commit()

        ruleset = RuleSetService(db_session).get_or_create(parent.id)

        assert [(cap.activity_type, cap.max_sessions) for cap in ruleset.weekly_caps] == [
            ("aba", 3)
        ]

    def test_an_inactive_rule_is_ignored(self, db_session, parent, family):
        db_session.add(
            ApprovalRule(
                family_id=family.id,
                rule_name="hours",
                rule_type="time_range",
                conditions='{"latest_end": "20:00"}',
                is_active=False,
                created_by=parent.id,
            )
        )
        db_session.commit()

        ruleset = RuleSetService(db_session).get_or_create(parent.id)

        assert ruleset.latest_end == time(18, 0)

    def test_unparseable_conditions_do_not_break_the_migration(self, db_session, parent, family):
        db_session.add(
            ApprovalRule(
                family_id=family.id,
                rule_name="broken",
                rule_type="time_range",
                conditions="not json at all",
                is_active=True,
                created_by=parent.id,
            )
        )
        db_session.commit()

        ruleset = RuleSetService(db_session).get_or_create(parent.id)

        assert ruleset.latest_end == time(18, 0)
