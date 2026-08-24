"""
Parent's rules.

Six toggles, set once. Every request from every persona is checked against
them before it can reach the parent, so this is the only screen a parent has
to keep up to date.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import RuleSet, User
from ..schemas.change_request import (
    ProtectedBlockOut,
    RuleSetOut,
    RuleSetUpdate,
    WeeklyCapOut,
)
from ..services.ruleset_service import RuleSetService
from ..utils.auth import get_current_user, verify_parent_account

router = APIRouter(prefix="/rules", tags=["Rules"])


def _serialise(ruleset: RuleSet) -> RuleSetOut:
    return RuleSetOut(
        id=ruleset.id,
        child_id=ruleset.child_id,
        timezone=ruleset.timezone,
        min_notice_hours=ruleset.min_notice_hours,
        earliest_start=ruleset.earliest_start,
        latest_end=ruleset.latest_end,
        require_same_provider_person=bool(ruleset.require_same_provider_person),
        buffer_minutes=ruleset.buffer_minutes,
        cancellation_needs_approval=bool(ruleset.cancellation_needs_approval),
        allowed_weekdays=ruleset.allowed_weekdays,
        notify_on_auto_approve=bool(ruleset.notify_on_auto_approve),
        protected_blocks=[
            ProtectedBlockOut(
                id=block.id,
                start=block.start_time,
                end=block.end_time,
                weekdays=block.weekdays,
                label_key=block.label_key,
            )
            for block in sorted(ruleset.protected_blocks, key=lambda b: b.start_time)
        ],
        weekly_caps=[
            WeeklyCapOut(id=cap.id, activity_type=cap.activity_type, max_sessions=cap.max_sessions)
            for cap in ruleset.weekly_caps
        ],
    )


@router.get("", response_model=RuleSetOut)
async def get_rules(
    child_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    The parent's rule set, protected blocks and weekly caps.

    Created with the design's defaults on first read, and seeded from any
    older ``ApprovalRule`` rows the family already had.
    """
    verify_parent_account(current_user)
    ruleset = RuleSetService(db).get_or_create(current_user.id, child_id)
    return _serialise(ruleset)


@router.put("", response_model=RuleSetOut)
async def update_rules(
    payload: RuleSetUpdate,
    request: Request,
    child_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Upsert the parent's rules.

    Only fields present in the body are touched, so a single toggle is one
    field. Sending ``null`` for an optional field turns that rule off.
    """
    verify_parent_account(current_user)
    service = RuleSetService(db)
    ruleset = service.get_or_create(current_user.id, child_id)

    body = payload.model_dump(exclude_unset=True)
    if "protected_blocks" in body and body["protected_blocks"] is not None:
        body["protected_blocks"] = [
            {
                "start": block["start"],
                "end": block["end"],
                "weekdays": block.get("weekdays"),
                "label_key": block.get("label_key", "block.custom"),
            }
            for block in body["protected_blocks"]
        ]

    ruleset = service.update(ruleset, body)
    return _serialise(ruleset)
