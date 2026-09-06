"""
POST /requests - the only write path for kid and provider.

A caller says what they want. The rule engine decides. Either the schedule
already moved by the time the response is written, or the parent has one
card waiting with three compliant alternatives attached. No client ever
decides whether something is allowed.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import ChangeKind, User
from ..schemas.change_request import ChangeRequestIn, ChangeRequestOut
from ..services.change_request_service import ChangeRequestService
from ..services.presenter import Presenter
from ..services.ruleset_service import RuleSetService
from ..utils.auth import get_current_user
from ..utils.locale import to_local
from ..utils.locale_context import translator_for

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Change Requests"])


@router.post("/requests", response_model=ChangeRequestOut)
async def submit_change_request(
    payload: ChangeRequestIn,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Ask for a change to one session.

    Returns ``auto_applied: true`` with the updated session when the request
    satisfied every active rule, or ``auto_applied: false`` with reason codes
    and up to three compliant alternatives when it did not.
    """
    try:
        kind = ChangeKind(payload.kind)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="kind must be one of: move, cancel, swap_provider",
        )

    service = ChangeRequestService(db)
    outcome = await service.submit(
        actor=current_user,
        session_id=payload.session_id,
        kind=kind,
        new_start=payload.new_start,
        new_provider_person_id=payload.new_provider_person_id,
    )

    translator = translator_for(request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)
    session_out = presenter.session(outcome.session)

    if outcome.auto_applied:
        tz_name = RuleSetService(db).timezone_for_child(outcome.session.child_id)
        message = _applied_message(translator, outcome, kind, current_user, tz_name)
        return ChangeRequestOut(
            auto_applied=True,
            session=session_out,
            request_id=outcome.request.id if outcome.request else None,
            message=message,
        )

    reasons_text = translator.reasons(outcome.reason_codes)
    message = (
        translator.t("kid.asked_skip" if kind is ChangeKind.CANCEL else "kid.asked")
        if current_user.is_kid_account
        else translator.t("provider.sent", reasons=reasons_text)
    )

    return ChangeRequestOut(
        auto_applied=False,
        session=session_out,
        request_id=outcome.request.id if outcome.request else None,
        reason_codes=outcome.reason_codes,
        reasons_text=reasons_text,
        alternatives=presenter.alternatives(outcome.alternatives),
        message=message,
    )


def _applied_message(
    translator, outcome, kind: ChangeKind, actor: User, tz_name: str
) -> str:
    """
    The confirmation the requester reads.

    A kid is told what happened, never which rule allowed it. A provider is
    told plainly that both calendars are already updated.
    """
    session = outcome.session
    local_start = to_local(session.start_utc, tz_name)
    if actor.is_kid_account:
        if kind is ChangeKind.CANCEL:
            return translator.t("kid.parent_yes_skip", title=session.title)
        return translator.t("kid.done", title=session.title, time=translator.time(local_start))
    return translator.t("provider.confirmed", when=translator.when(local_start))
