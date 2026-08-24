"""
Tests for the deterministic rule engine.

The engine is pure, so these tests need no database and no client. They lock
the reason codes: a rule failure is identified by a stable code, never by a
sentence, and the UI resolves codes through the locale files.
"""

from datetime import datetime, time, timedelta

from app.services.rule_engine import (
    ChangeRequest,
    ProtectedBlock,
    ReasonCode,
    RequestKind,
    RuleEngine,
    RuleSet,
    Session,
)

# A Wednesday, so a five-day horizon stays inside one working week.
NOW = datetime(2026, 9, 9, 8, 0)


def a_session(**overrides) -> Session:
    defaults = dict(
        id="s1",
        start=datetime(2026, 9, 10, 15, 30),
        duration_minutes=90,
        activity_type="aba",
        provider_org_id="org1",
        provider_person_id="dana",
    )
    defaults.update(overrides)
    return Session(**defaults)


def a_ruleset(**overrides) -> RuleSet:
    defaults = dict(
        min_notice_hours=24,
        earliest_start=time(8, 0),
        latest_end=time(18, 0),
        protected_blocks=[ProtectedBlock(time(12, 0), time(13, 0), "block.midday")],
        require_same_provider_person=True,
        buffer_minutes=45,
        cancellation_needs_approval=True,
    )
    defaults.update(overrides)
    return RuleSet(**defaults)


def move(session, start, person=None, by="kid") -> ChangeRequest:
    return ChangeRequest(
        kind=RequestKind.MOVE,
        session_id=session.id,
        requested_by=by,
        new_start=start,
        new_provider_person_id=person,
    )


class TestCompliantRequests:
    """A request that satisfies every active rule must never wait."""

    def test_move_inside_every_rule_passes(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)

        result = engine.evaluate(move(session, datetime(2026, 9, 10, 16, 0)), session, [])

        assert result.passed is True
        assert result.auto_approve is True
        assert result.reasons == []

    def test_an_unset_rule_is_an_inactive_rule(self):
        """Every optional field off means the engine has nothing to object to."""
        session = a_session()
        permissive = RuleSet(
            min_notice_hours=None,
            earliest_start=None,
            latest_end=None,
            protected_blocks=[],
            require_same_provider_person=False,
            buffer_minutes=None,
            max_sessions_per_week=None,
            cancellation_needs_approval=False,
        )
        engine = RuleEngine(permissive, now=NOW)

        # Ten minutes' notice, 11pm, a different therapist: still fine.
        request = move(session, NOW + timedelta(minutes=10), person="marcus")
        assert engine.evaluate(request, session, []).passed is True


class TestReasonCodes:
    """Each rule fails with its own stable code."""

    def test_min_notice(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)

        result = engine.evaluate(move(session, NOW + timedelta(hours=2)), session, [])

        assert result.passed is False
        assert ReasonCode.MIN_NOTICE in result.reasons

    def test_runs_past_the_latest_end(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)

        # 17:00 + 90 minutes ends at 18:30, past the 18:00 limit.
        result = engine.evaluate(move(session, datetime(2026, 9, 10, 17, 0)), session, [])

        assert result.reasons == [ReasonCode.LATEST_END]

    def test_starts_before_the_earliest_start(self):
        """One code covers the whole allowed-hours window, and only once."""
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)

        # Friday, so the 24-hour notice rule is satisfied and only the
        # allowed-hours window is at issue.
        result = engine.evaluate(move(session, datetime(2026, 9, 11, 7, 0)), session, [])

        assert result.reasons == [ReasonCode.LATEST_END]

    def test_protected_block(self):
        session = a_session(duration_minutes=60)
        engine = RuleEngine(a_ruleset(), now=NOW)

        result = engine.evaluate(move(session, datetime(2026, 9, 10, 12, 30)), session, [])

        assert ReasonCode.PROTECTED_BLOCK in result.reasons

    def test_protected_block_only_on_its_own_weekdays(self):
        monday_only = a_ruleset(
            protected_blocks=[ProtectedBlock(time(12, 0), time(13, 0), "block.midday", (0,))]
        )
        session = a_session(duration_minutes=60)
        engine = RuleEngine(monday_only, now=NOW)

        # 10 Sep 2026 is a Thursday, so the Monday block does not apply.
        result = engine.evaluate(move(session, datetime(2026, 9, 10, 12, 30)), session, [])

        assert ReasonCode.PROTECTED_BLOCK not in result.reasons

    def test_different_therapist(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)

        result = engine.evaluate(
            move(session, datetime(2026, 9, 10, 16, 0), person="jordan"), session, []
        )

        assert result.reasons == [ReasonCode.SAME_PROVIDER]

    def test_buffer_between_sessions(self):
        session = a_session()
        neighbour = a_session(id="s2", start=datetime(2026, 9, 10, 14, 0), duration_minutes=45)
        engine = RuleEngine(a_ruleset(), now=NOW)

        # 15:00 starts 15 minutes after the neighbour ends, inside the 45 pad.
        result = engine.evaluate(
            move(session, datetime(2026, 9, 10, 15, 0)), session, [session, neighbour]
        )

        assert ReasonCode.BUFFER in result.reasons

    def test_a_session_never_conflicts_with_itself(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)

        result = engine.evaluate(move(session, datetime(2026, 9, 10, 16, 0)), session, [session])

        assert result.passed is True

    def test_weekly_cap(self):
        session = a_session()
        rules = a_ruleset(max_sessions_per_week={"aba": 2}, buffer_minutes=None)
        engine = RuleEngine(rules, now=NOW)
        week = [
            session,
            a_session(id="s2", start=datetime(2026, 9, 8, 9, 0)),
            a_session(id="s3", start=datetime(2026, 9, 11, 9, 0)),
        ]

        result = engine.evaluate(move(session, datetime(2026, 9, 10, 16, 0)), session, week)

        assert ReasonCode.MAX_PER_WEEK in result.reasons

    def test_outside_allowed_days(self):
        session = a_session()
        rules = a_ruleset(allowed_weekdays=(0, 1, 2))  # Mon-Wed only
        engine = RuleEngine(rules, now=NOW)

        result = engine.evaluate(move(session, datetime(2026, 9, 10, 16, 0)), session, [])

        assert ReasonCode.OUTSIDE_ALLOWED_DAYS in result.reasons

    def test_several_broken_rules_report_several_codes(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)

        # Two hours' notice AND a different therapist.
        result = engine.evaluate(
            move(session, NOW + timedelta(hours=2), person="jordan"), session, []
        )

        assert ReasonCode.MIN_NOTICE in result.reasons
        assert ReasonCode.SAME_PROVIDER in result.reasons

    def test_codes_are_strings_not_sentences(self):
        """Nothing user-facing ever leaks out of the engine."""
        assert ReasonCode.MIN_NOTICE.value == "min_notice"
        assert {code.value for code in ReasonCode} == {
            "min_notice",
            "latest_end",
            "protected_block",
            "same_provider",
            "buffer",
            "max_per_week",
            "cancel_needs_approval",
            "outside_allowed_days",
        }


class TestCancellations:
    def test_cancelling_reaches_the_parent_when_they_asked_for_that(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)
        request = ChangeRequest(RequestKind.CANCEL, session.id, "kid")

        result = engine.evaluate(request, session, [])

        assert result.passed is False
        assert result.reasons == [ReasonCode.CANCEL_NEEDS_APPROVAL]

    def test_cancelling_is_allowed_when_the_rule_is_off(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(cancellation_needs_approval=False), now=NOW)
        request = ChangeRequest(RequestKind.CANCEL, session.id, "kid")

        assert engine.evaluate(request, session, []).passed is True

    def test_no_alternatives_are_offered_for_a_cancellation(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)
        request = ChangeRequest(RequestKind.CANCEL, session.id, "kid")

        assert engine.alternatives(request, session, []) == []


class TestAlternatives:
    """Three compliant slots, closest first, one per day."""

    def test_three_alternatives_are_offered(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)
        request = move(session, datetime(2026, 9, 10, 17, 0))

        options = engine.alternatives(request, session, [session])

        assert len(options) == 3

    def test_every_alternative_actually_passes(self):
        session = a_session()
        rules = a_ruleset()
        engine = RuleEngine(rules, now=NOW)
        request = move(session, datetime(2026, 9, 10, 17, 0))

        for option in engine.alternatives(request, session, [session]):
            probe = move(session, option.start)
            assert engine.evaluate(probe, session, [session]).passed is True, option.start

    def test_alternatives_are_one_per_day_and_closest_first(self):
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)
        target = datetime(2026, 9, 10, 17, 0)

        options = engine.alternatives(move(session, target), session, [session])

        days = [option.start.date() for option in options]
        assert len(set(days)) == len(days)
        assert [option.reason_rank for option in options] == [0, 1, 2]

        distances = [abs((option.start - target).total_seconds()) for option in options]
        assert distances == sorted(distances)

    def test_alternatives_keep_the_assigned_therapist(self):
        """Swapping is what failed; the fix must not smuggle the swap through."""
        session = a_session()
        engine = RuleEngine(a_ruleset(), now=NOW)
        request = move(session, datetime(2026, 9, 10, 16, 0), person="jordan")

        options = engine.alternatives(request, session, [session])

        assert options, "a same-therapist slot exists"
        for option in options:
            probe = move(session, option.start)
            assert engine.evaluate(probe, session, [session]).passed is True

    def test_no_alternatives_when_nothing_can_comply(self):
        session = a_session(duration_minutes=90)
        impossible = a_ruleset(earliest_start=None, latest_end=None, allowed_weekdays=())
        engine = RuleEngine(impossible, now=NOW)

        options = engine.alternatives(move(session, datetime(2026, 9, 10, 16, 0)), session, [])

        assert options == []
