"""
Pull the schedule in from the calendars people already keep.

Nothing in Mew invents a therapy appointment. Sessions exist because a
provider's calendar says so, and this is what mirrors them across.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import ProviderOrg, User
from ..services.calendar_sync_service import CalendarSyncService
from ..utils.auth import get_current_user, verify_parent_account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar-sync", tags=["Calendar Sync"])


class SyncReport(BaseModel):
    """What one organisation's pull actually did."""

    provider_org_id: int
    provider_org_name: str
    ok: bool
    created: int = 0
    updated: int = 0
    cancelled: int = 0
    skipped: int = 0
    error: Optional[str] = None


@router.post("/pull", response_model=List[SyncReport])
async def pull_calendars(
    child_id: int,
    provider_org_id: Optional[int] = None,
    days_ahead: int = 30,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Mirror connected calendars into this child's schedule.

    Idempotent, so it is safe to call on a timer or on demand. Every
    organisation is reported on individually: one clinic's expired token must
    not hide another clinic's successful sync.
    """
    verify_parent_account(current_user)

    child = db.query(User).filter(User.id == child_id).first()
    if child is None or child.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your child's schedule",
        )

    query = db.query(ProviderOrg).filter(ProviderOrg.is_active.is_(True))
    if provider_org_id is not None:
        query = query.filter(ProviderOrg.id == provider_org_id)

    service = CalendarSyncService(db)
    reports: List[SyncReport] = []

    for org in query.all():
        result = await service.pull_org(org, child_id=child_id, days_ahead=days_ahead)
        reports.append(
            SyncReport(
                provider_org_id=org.id,
                provider_org_name=org.name,
                ok=result.ok,
                created=result.created,
                updated=result.updated,
                cancelled=result.cancelled,
                skipped=result.skipped,
                error=result.error,
            )
        )

    return reports


class ConnectCalendar(BaseModel):
    """Point an organisation at the calendar it already keeps."""

    calendar_provider: str  # google | ics
    calendar_account_id: str  # a Google calendar id, or an ICS feed URL


@router.put("/orgs/{org_id}/calendar", response_model=SyncReport)
async def connect_org_calendar(
    org_id: int,
    payload: ConnectCalendar,
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Connect an organisation's calendar, then pull straight away so the
    person who did it can see whether it actually worked.
    """
    verify_parent_account(current_user)

    provider = payload.calendar_provider.strip().lower()
    if provider not in ("google", "ics"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="calendar_provider must be 'google' or 'ics'",
        )

    org = db.query(ProviderOrg).filter(ProviderOrg.id == org_id).first()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider organisation not found"
        )

    org.calendar_provider = provider
    org.calendar_account_id = payload.calendar_account_id.strip()
    db.commit()

    result = await CalendarSyncService(db).pull_org(org, child_id=child_id)
    return SyncReport(
        provider_org_id=org.id,
        provider_org_name=org.name,
        ok=result.ok,
        created=result.created,
        updated=result.updated,
        cancelled=result.cancelled,
        skipped=result.skipped,
        error=result.error,
    )
