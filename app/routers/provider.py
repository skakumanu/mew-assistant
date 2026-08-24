"""
Service provider endpoints.

Providers keep working in the calendar they already use; this is the thin
surface they need to propose a change. The answer comes back into their own
calendar, and most changes clear themselves.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import ProviderPerson, ScheduledSession, User
from ..schemas.change_request import ProviderSessionOut
from ..services.change_request_service import ChangeRequestService
from ..services.presenter import Presenter
from ..utils.auth import get_current_user
from ..utils.locale_context import translator_for

router = APIRouter(prefix="/provider", tags=["Service Provider"])

DEFAULT_HORIZON_DAYS = 14


def _provider_person(db: DbSession, user: User) -> ProviderPerson:
    person = (
        db.query(ProviderPerson)
        .filter(ProviderPerson.user_id == user.id, ProviderPerson.is_active.is_(True))
        .first()
    )
    if person is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for service provider accounts",
        )
    return person


@router.get("/sessions", response_model=List[ProviderSessionOut])
async def get_provider_sessions(
    request: Request,
    child_id: Optional[int] = None,
    days: int = DEFAULT_HORIZON_DAYS,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    This organisation's sessions, from the calendar it already syncs.

    Only sessions belonging to the caller's own organisation are returned,
    and only for the child they are asked about.
    """
    person = _provider_person(db, current_user)
    service = ChangeRequestService(db)
    translator = translator_for(request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)

    now = datetime.utcnow()
    query = (
        db.query(ScheduledSession)
        .filter(
            ScheduledSession.provider_org_id == person.org_id,
            ScheduledSession.is_cancelled.is_(False),
            ScheduledSession.start_utc >= now - timedelta(days=1),
            ScheduledSession.start_utc < now + timedelta(days=days),
        )
        .order_by(ScheduledSession.start_utc.asc())
    )
    if child_id is not None:
        query = query.filter(ScheduledSession.child_id == child_id)

    # Everyone in the org, so a swap can be proposed without a second call.
    people = (
        db.query(ProviderPerson)
        .filter(ProviderPerson.org_id == person.org_id, ProviderPerson.is_active.is_(True))
        .order_by(ProviderPerson.display_name.asc())
        .all()
    )
    roster = [{"id": p.id, "display_name": p.display_name} for p in people]

    out: List[ProviderSessionOut] = []
    for row in query.all():
        out.append(
            ProviderSessionOut(
                session=presenter.session(row),
                when_label=translator.when(row.start_utc),
                waiting_on_parent=service.pending_for_session(row.id) is not None,
                people=roster,
            )
        )
    return out
