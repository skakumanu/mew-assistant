"""
Golden outcomes: change an assertion here only alongside a deliberate,
reviewed decision to change what auto-applies vs. what needs a parent -
never to make a failing test pass.

`tests/test_rule_engine.py` already locks the pure engine's `Evaluation`
for every `ReasonCode`. This module locks the layer above it -
`ChangeRequestService.submit()`'s own approve/park decision - by calling
`submit()` directly (bypassing the HTTP client, the same way
`test_rule_engine.py` calls the engine directly) and asserting the
*orchestration* outcome: `ChangeOutcome.auto_applied`, the resulting
`ApprovalRequest.status`, and `applied_to_calendar`. One case per
`ReasonCode`, plus both cancellation branches, plus a compliant baseline.

A regression here is not cosmetic: it is a family's change silently
auto-applied when it should have waited for a parent, or vice versa.
"""

from datetime import datetime

import pytest

from app.database.models import (
    ApprovalStatus,
    ChangeKind,
    ProtectedBlock,
    ScheduledSession,
    WeeklyCap,
)
from app.services.change_request_service import ChangeRequestService

# A fixed reference clock, entirely decoupled from wall-clock time: every
# case below passes this explicitly as `now=`, so nothing here can ever
# flake based on when the suite happens to run.
NOW = datetime(2026, 9, 9, 8, 0)  # Wednesday

# The session's own declared time, also fixed - matches
# tests/test_rule_engine.py's own default session for the same reason.
BASE_START = datetime(2026, 9, 10, 15, 30)  # Thursday, 90 minutes -> ends 17:00


def _reset_session_start(db_session, session_row, start=BASE_START, duration=90):
    session_row.start_utc = start
    session_row.duration_minutes = duration
    db_session.commit()
    db_session.refresh(session_row)


class TestGoldenOutcomes:
    """One case per `ReasonCode`, plus both cancellation branches."""

    @pytest.mark.asyncio
    async def test_a_fully_compliant_move_is_auto_applied(
        self, db_session, family, rules, session_row
    ):
        """Baseline: nothing failed, so the change never waits."""
        _reset_session_start(db_session, session_row)
        service = ChangeRequestService(db_session)

        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.MOVE,
            new_start=datetime(2026, 9, 10, 16, 0),
            now=NOW,
        )

        assert outcome.auto_applied is True
        assert outcome.reason_codes == []
        assert outcome.request.status == ApprovalStatus.APPROVED
        assert outcome.request.applied_to_calendar is True

    @pytest.mark.asyncio
    async def test_min_notice_is_parked(self, db_session, family, rules, session_row):
        _reset_session_start(db_session, session_row)
        service = ChangeRequestService(db_session)

        # Two hours' notice against a 24-hour rule.
        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.MOVE,
            new_start=datetime(2026, 9, 9, 10, 0),
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["min_notice"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False

    @pytest.mark.asyncio
    async def test_outside_allowed_hours_is_parked(self, db_session, family, rules, session_row):
        _reset_session_start(db_session, session_row)
        service = ChangeRequestService(db_session)

        # Ends at 19:00, past the 18:00 latest_end.
        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.MOVE,
            new_start=datetime(2026, 9, 10, 17, 30),
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["latest_end"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False

    @pytest.mark.asyncio
    async def test_a_protected_block_is_parked(self, db_session, family, rules, session_row):
        _reset_session_start(db_session, session_row)
        db_session.add(
            ProtectedBlock(
                ruleset_id=rules.id,
                start_time=datetime(2026, 9, 10, 12, 0).time(),
                end_time=datetime(2026, 9, 10, 13, 0).time(),
                label_key="block.midday",
            )
        )
        db_session.commit()
        service = ChangeRequestService(db_session)

        # 12:15-13:45 overlaps the 12:00-13:00 protected block.
        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.MOVE,
            new_start=datetime(2026, 9, 10, 12, 15),
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["protected_block"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False

    @pytest.mark.asyncio
    async def test_a_swap_to_a_different_therapist_is_parked(
        self, db_session, family, rules, session_row
    ):
        _reset_session_start(db_session, session_row)
        service = ChangeRequestService(db_session)

        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.SWAP_PROVIDER,
            new_provider_person_id=family["jordan"].id,
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["same_provider"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False

    @pytest.mark.asyncio
    async def test_a_buffer_conflict_is_parked(self, db_session, family, rules, session_row):
        _reset_session_start(db_session, session_row)
        # 20 minutes after this session's 17:00 end - inside the 45-minute buffer.
        db_session.add(
            ScheduledSession(
                child_id=family["kid"].id,
                provider_org_id=family["org"].id,
                provider_person_id=family["dana"].id,
                title="Another ABA session",
                activity_type="aba",
                start_utc=datetime(2026, 9, 10, 17, 20),
                duration_minutes=60,
                source="calendar",
            )
        )
        db_session.commit()
        service = ChangeRequestService(db_session)

        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.MOVE,
            new_start=BASE_START,
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["buffer"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False

    @pytest.mark.asyncio
    async def test_exceeding_the_weekly_cap_is_parked(
        self, db_session, family, rules, session_row
    ):
        _reset_session_start(db_session, session_row)
        db_session.add(WeeklyCap(ruleset_id=rules.id, activity_type="aba", max_sessions=1))
        # A second "aba" session the same ISO week (Mon 9/7 - Sun 9/13).
        db_session.add(
            ScheduledSession(
                child_id=family["kid"].id,
                provider_org_id=family["org"].id,
                provider_person_id=family["dana"].id,
                title="Tuesday ABA session",
                activity_type="aba",
                start_utc=datetime(2026, 9, 8, 10, 0),
                duration_minutes=60,
                source="calendar",
            )
        )
        db_session.commit()
        service = ChangeRequestService(db_session)

        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.MOVE,
            new_start=datetime(2026, 9, 10, 16, 0),
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["max_per_week"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False

    @pytest.mark.asyncio
    async def test_outside_allowed_days_is_parked(self, db_session, family, rules, session_row):
        _reset_session_start(db_session, session_row)
        rules.allowed_weekdays = [0, 1, 2, 3]  # Mon-Thu only
        db_session.commit()
        service = ChangeRequestService(db_session)

        # Saturday.
        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.MOVE,
            new_start=datetime(2026, 9, 12, 10, 0),
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["outside_allowed_days"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False

    @pytest.mark.asyncio
    async def test_a_cancellation_needing_approval_is_parked(
        self, db_session, family, rules, session_row
    ):
        """Cancellation branch 1 of 2: `cancellation_needs_approval` is on."""
        _reset_session_start(db_session, session_row)
        assert rules.cancellation_needs_approval is True
        service = ChangeRequestService(db_session)

        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.CANCEL,
            now=NOW,
        )

        assert outcome.auto_applied is False
        assert outcome.reason_codes == ["cancel_needs_approval"]
        assert outcome.request.status == ApprovalStatus.PENDING
        assert outcome.request.applied_to_calendar is False
        db_session.refresh(session_row)
        assert session_row.is_cancelled is False

    @pytest.mark.asyncio
    async def test_a_cancellation_not_needing_approval_is_auto_applied(
        self, db_session, family, rules, session_row
    ):
        """Cancellation branch 2 of 2: the parent turned that rule off."""
        _reset_session_start(db_session, session_row)
        rules.cancellation_needs_approval = False
        db_session.commit()
        service = ChangeRequestService(db_session)

        outcome = await service.submit(
            actor=family["kid"],
            session_id=session_row.id,
            kind=ChangeKind.CANCEL,
            now=NOW,
        )

        assert outcome.auto_applied is True
        assert outcome.reason_codes == []
        assert outcome.request.status == ApprovalStatus.APPROVED
        assert outcome.request.applied_to_calendar is True
        db_session.refresh(session_row)
        assert session_row.is_cancelled is True
