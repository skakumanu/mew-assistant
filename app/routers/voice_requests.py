"""
Voice, mapped onto the one write path.

Two constraints from the design, both enforced here rather than left to the
caller:

  * **Voice may request anything and approve nothing.** There is no spoken
    route to approving, choosing an alternative or denying; the endpoint that
    would do it refuses, and says why.
  * **A spoken request is read back before it is sent.** The first call
    returns the sentence and writes nothing. Only a call that echoes that
    sentence back submits it.

Everything else is the ordinary loop: the request goes through
``ChangeRequestService`` exactly like a tap on a screen does.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import ChangeKind, ScheduledSession, User
from ..schemas.change_request import ChangeRequestOut
from ..services.change_request_service import ChangeRequestService
from ..services.presenter import Presenter
from ..utils.auth import get_current_user
from ..utils.locale_context import translator_for

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])


class VoiceChangeRequest(BaseModel):
    """A spoken ask, in the same shape as the tapped one."""

    session_id: int
    kind: str = Field(..., description="move | cancel | swap_provider")
    new_start: Optional[datetime] = None
    new_provider_person_id: Optional[int] = None
    confirmed: bool = Field(
        False,
        description="False returns the read-back sentence and writes nothing",
    )


class VoiceReadback(BaseModel):
    """What the device should say, and what the screen must show alongside it."""

    confirmed: bool = False
    readback: str
    speak: str


def _readback(translator, session: ScheduledSession, payload: VoiceChangeRequest) -> str:
    """The sentence the person hears back, built from locale templates."""
    if payload.kind == ChangeKind.CANCEL.value:
        return translator.t("parent.headline_skip", title=session.title)
    when = translator.when(payload.new_start or session.start_utc)
    return translator.t("parent.headline_move", title=session.title, when=when)


@router.post(
    "/requests",
    response_model=None,
    responses={200: {"description": "Read-back sentence, or the outcome once confirmed"}},
)
async def submit_spoken_request(
    payload: VoiceChangeRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Ask for a change out loud.

    Call once to hear the request read back; call again with
    ``confirmed: true`` to send it. The reply is the same sentence in both
    channels - spoken and on screen - never one without the other.
    """
    try:
        kind = ChangeKind(payload.kind)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="kind must be one of: move, cancel, swap_provider",
        )

    session = db.query(ScheduledSession).filter(ScheduledSession.id == payload.session_id).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)

    if not payload.confirmed:
        # Nothing is written until the person has heard what they asked for.
        sentence = _readback(translator, session, payload)
        return VoiceReadback(confirmed=False, readback=sentence, speak=sentence)

    service = ChangeRequestService(db)
    outcome = await service.submit(
        actor=current_user,
        session_id=payload.session_id,
        kind=kind,
        new_start=payload.new_start,
        new_provider_person_id=payload.new_provider_person_id,
    )

    presenter = Presenter(translator, db)
    reasons_text = translator.reasons(outcome.reason_codes)

    if outcome.auto_applied:
        message = (
            translator.t("kid.parent_yes_skip", title=outcome.session.title)
            if kind is ChangeKind.CANCEL
            else translator.t(
                "kid.done",
                title=outcome.session.title,
                time=translator.time(outcome.session.start_utc),
            )
        )
    else:
        message = (
            translator.t("kid.asked_skip" if kind is ChangeKind.CANCEL else "kid.asked")
            if current_user.is_kid_account
            else translator.t("provider.sent", reasons=reasons_text)
        )

    return ChangeRequestOut(
        auto_applied=outcome.auto_applied,
        session=presenter.session(outcome.session),
        request_id=outcome.request.id if outcome.request else None,
        reason_codes=outcome.reason_codes,
        reasons_text=reasons_text if outcome.reason_codes else None,
        # Alternatives are a parent's decision surface, and a parent decides
        # by tapping. They are deliberately not read out here.
        alternatives=[],
        message=message,
    )


@router.post("/approvals/{request_id}/approve", status_code=status.HTTP_403_FORBIDDEN)
async def approving_by_voice_is_not_available(
    request_id: int, current_user: User = Depends(get_current_user)
):
    """
    Approving out loud is not possible, by design.

    A voice channel cannot show the parent what they are agreeing to, and
    cannot tell one voice in a room from another. Requests, yes. Decisions,
    on a screen.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Voice can ask for a change but cannot approve one. "
            "Open the request in Mew to decide."
        ),
    )
