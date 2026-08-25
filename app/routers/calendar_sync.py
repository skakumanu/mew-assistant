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
from ..database.models import ProviderOrg, ProviderOrgConnection, User
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


def _resolve_child_ids(
    db: DbSession, current_user: User, child_id: Optional[int]
) -> List[int]:
    """
    Which of this parent's children a calendar action applies to.

    Nothing client-side currently knows a child's id - the setup wizard
    creates one child per family in the common case, and the rest of the
    parent-facing app already treats "no child_id given" as "every child
    this parent has" (see parent_approval.py's week view), so calendar
    sync follows the same convention rather than requiring a picker.
    """
    if child_id is not None:
        child = db.query(User).filter(User.id == child_id).first()
        if child is None or child.parent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your child's schedule",
            )
        return [child_id]

    return [kid.id for kid in db.query(User).filter(User.parent_id == current_user.id).all()]


@router.post("/pull", response_model=List[SyncReport])
async def pull_calendars(
    child_id: Optional[int] = None,
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
    child_ids = _resolve_child_ids(db, current_user, child_id)

    query = db.query(ProviderOrg).filter(ProviderOrg.is_active.is_(True))
    if provider_org_id is not None:
        query = query.filter(ProviderOrg.id == provider_org_id)

    service = CalendarSyncService(db)
    reports: List[SyncReport] = []

    for org in query.all():
        for cid in child_ids:
            result = await service.pull_org(org, child_id=cid, days_ahead=days_ahead)
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
    child_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Connect an organisation's calendar, then pull straight away so the
    person who did it can see whether it actually worked.
    """
    verify_parent_account(current_user)
    child_ids = _resolve_child_ids(db, current_user, child_id)

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
    _upsert_connection(db, org_id=org.id, parent_id=current_user.id)
    db.commit()

    created = updated = cancelled = skipped = 0
    error: Optional[str] = None
    for cid in child_ids:
        result = await CalendarSyncService(db).pull_org(org, child_id=cid)
        created += result.created
        updated += result.updated
        cancelled += result.cancelled
        skipped += result.skipped
        error = error or result.error

    return SyncReport(
        provider_org_id=org.id,
        provider_org_name=org.name,
        ok=error is None,
        created=created,
        updated=updated,
        cancelled=cancelled,
        skipped=skipped,
        error=error,
    )


def _upsert_connection(
    db: DbSession, org_id: int, parent_id: int, connected_by_user_id: Optional[int] = None
) -> ProviderOrgConnection:
    """
    Record (or refresh) that this family cares about this org.

    ``ProviderOrg`` is global, so this row is the only thing that scopes it
    to a family - the source both the "your providers" list and the Google
    token lookup read from.
    """
    connection = (
        db.query(ProviderOrgConnection)
        .filter(
            ProviderOrgConnection.org_id == org_id,
            ProviderOrgConnection.parent_id == parent_id,
        )
        .first()
    )
    if connection is None:
        connection = ProviderOrgConnection(org_id=org_id, parent_id=parent_id)
        db.add(connection)
    if connected_by_user_id is not None:
        connection.connected_by_user_id = connected_by_user_id
    return connection


class ProviderOrgOut(BaseModel):
    """One of this family's providers, as the Providers tab shows it."""

    id: int
    name: str
    kind: str
    calendar_provider: Optional[str] = None
    calendar_connected: bool = False


@router.get("/orgs", response_model=List[ProviderOrgOut])
async def list_my_orgs(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    The providers this family has actually connected - never another
    family's, even when both reference an org with the same name.
    """
    verify_parent_account(current_user)

    rows = (
        db.query(ProviderOrg)
        .join(ProviderOrgConnection, ProviderOrgConnection.org_id == ProviderOrg.id)
        .filter(ProviderOrgConnection.parent_id == current_user.id, ProviderOrg.is_active.is_(True))
        .all()
    )
    return [
        ProviderOrgOut(
            id=org.id,
            name=org.name,
            kind=org.kind,
            calendar_provider=org.calendar_provider,
            calendar_connected=bool(org.calendar_provider and org.calendar_account_id),
        )
        for org in rows
    ]
