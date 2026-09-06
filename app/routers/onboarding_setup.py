"""
Setting Mew up: one person, once.

The design's promise is fifteen minutes and nobody installing anything they
do not already have. That means a caregiver describes their family and the
services already in their week, and everything else - the rule set, the
provider records, the first calendar pull - falls out of that one call
rather than a wizard with six screens.

Idempotent by name: running it again with the same child and the same
organisations updates them instead of creating duplicates, because setup is
something people do halfway and come back to.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import ProviderOrg, ProviderPerson, User
from ..routers.calendar_sync import _upsert_connection
from ..schemas.change_request import RuleSetUpdate
from ..services.calendar_sync_service import CalendarSyncService
from ..services.ruleset_service import RuleSetService
from ..utils.auth import get_current_user, get_password_hash, verify_parent_account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


class ChildIn(BaseModel):
    """The child whose week this is."""

    display_name: str = Field(..., max_length=100)
    email: Optional[str] = Field(
        None, description="Only if they sign in themselves; a tablet often does not"
    )
    age: Optional[int] = Field(None, ge=0, le=25)


class ProviderPersonIn(BaseModel):
    display_name: str = Field(..., max_length=200)


class ProviderOrgIn(BaseModel):
    """A service already in the family's week."""

    name: str = Field(..., max_length=200)
    kind: str = Field("other", description="aba | speech | ot | school | transport | other")
    calendar_provider: Optional[str] = Field(None, description="google | ics")
    calendar_account_id: Optional[str] = Field(
        None, description="A Google calendar id, or an ICS feed URL"
    )
    people: List[ProviderPersonIn] = Field(default_factory=list)


class SetupIn(BaseModel):
    child: ChildIn
    providers: List[ProviderOrgIn] = Field(default_factory=list)
    rules: Optional[RuleSetUpdate] = None
    pull_calendars: bool = True


class SetupOrgOut(BaseModel):
    id: int
    name: str
    people: List[dict] = Field(default_factory=list)
    calendar_connected: bool = False
    sessions_imported: int = 0
    calendar_error: Optional[str] = None


class SetupOut(BaseModel):
    child_id: int
    ruleset_id: int
    providers: List[SetupOrgOut] = Field(default_factory=list)
    kid_screen: str = "/app/kid"
    caregiver_screen: str = "/app/parent"


@router.post("/setup", response_model=SetupOut)
async def set_up_family(
    payload: SetupIn,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Create the child, the rules and the providers, and pull their calendars.

    Everything a family needs before the loop can run, in one call. Safe to
    repeat: the child is matched by display name and the organisations by
    name, so a half-finished setup can simply be sent again.
    """
    verify_parent_account(current_user)

    child = _upsert_child(db, current_user, payload.child)

    rules_service = RuleSetService(db)
    ruleset = rules_service.get_or_create(current_user.id, child.id)
    if payload.rules is not None:
        rules_service.update(ruleset, payload.rules.model_dump(exclude_unset=True))

    sync = CalendarSyncService(db)
    orgs: List[SetupOrgOut] = []

    for spec in payload.providers:
        org = _upsert_org(db, spec)
        _upsert_connection(db, org_id=org.id, parent_id=current_user.id)
        db.commit()
        people = _upsert_people(db, org, spec.people)

        report = SetupOrgOut(
            id=org.id,
            name=org.name,
            people=[{"id": p.id, "display_name": p.display_name} for p in people],
            calendar_connected=bool(org.calendar_provider and org.calendar_account_id),
        )

        if payload.pull_calendars and report.calendar_connected:
            result = await sync.pull_org(org, child_id=child.id)
            report.sessions_imported = result.created
            report.calendar_error = result.error

        orgs.append(report)

    return SetupOut(child_id=child.id, ruleset_id=ruleset.id, providers=orgs)


class AddProviderIn(BaseModel):
    """A provider added any time after setup, from the Providers tab."""

    name: str = Field(..., max_length=200)
    kind: str = Field("other", description="aba | speech | ot | school | transport | other")


class AddProviderOut(BaseModel):
    id: int
    name: str
    kind: str


@router.post("/providers", response_model=AddProviderOut)
async def add_provider(
    payload: AddProviderIn,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Add one more provider to this family - the setup wizard is only ever
    seen once, but a family's roster of providers grows over time. Same
    idempotent-by-name upsert setup itself uses, so adding a name twice
    just reconnects it rather than duplicating it.
    """
    verify_parent_account(current_user)
    org = _upsert_org(db, ProviderOrgIn(name=payload.name, kind=payload.kind))
    _upsert_connection(db, org_id=org.id, parent_id=current_user.id)
    db.commit()
    return AddProviderOut(id=org.id, name=org.name, kind=org.kind)


class AddKidIn(BaseModel):
    """A child added any time after setup, from the Providers tab."""

    display_name: str = Field(..., max_length=100)
    age: Optional[int] = Field(None, ge=0, le=25)


class AddKidOut(BaseModel):
    id: int
    name: str


@router.post("/kids", response_model=AddKidOut)
async def add_kid(
    payload: AddKidIn,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Add another child to this family - most families with more than one
    kid on Mew add the second one well after their own first setup."""
    verify_parent_account(current_user)
    child = _upsert_child(db, current_user, ChildIn(display_name=payload.display_name, age=payload.age))
    RuleSetService(db).get_or_create(current_user.id, child.id)
    return AddKidOut(id=child.id, name=child.display_name)


def _upsert_child(db: DbSession, caregiver: User, spec: ChildIn) -> User:
    """
    Find or create the child.

    A kid account with no email is normal: plenty of children use a tablet
    that is simply already signed in, and inventing an address for them would
    be a lie in the audit trail.
    """
    existing = (
        db.query(User)
        .filter(
            User.parent_id == caregiver.id,
            User.is_kid_account.is_(True),
            User.display_name == spec.display_name,
        )
        .first()
    )
    if existing is not None:
        if spec.age is not None:
            existing.age = spec.age
        db.commit()
        return existing

    email = spec.email or _derived_email(caregiver, spec.display_name)
    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email is already in use",
        )

    child = User(
        email=email,
        username=None,
        display_name=spec.display_name,
        age=spec.age,
        # No password is set: this account cannot be signed into until
        # somebody deliberately gives it credentials.
        hashed_password=get_password_hash(_unusable_secret()),
        is_active=True,
        is_kid_account=True,
        parent_id=caregiver.id,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


def _upsert_org(db: DbSession, spec: ProviderOrgIn) -> ProviderOrg:
    org = db.query(ProviderOrg).filter(ProviderOrg.name == spec.name).first()
    if org is None:
        org = ProviderOrg(name=spec.name)
        db.add(org)

    org.kind = spec.kind
    org.is_active = True
    if spec.calendar_provider:
        provider = spec.calendar_provider.strip().lower()
        if provider not in ("google", "ics"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="calendar_provider must be 'google' or 'ics'",
            )
        org.calendar_provider = provider
        org.calendar_account_id = (spec.calendar_account_id or "").strip() or None

    db.commit()
    db.refresh(org)
    return org


def _upsert_people(
    db: DbSession, org: ProviderOrg, specs: List[ProviderPersonIn]
) -> List[ProviderPerson]:
    people: List[ProviderPerson] = []
    for spec in specs:
        person = (
            db.query(ProviderPerson)
            .filter(
                ProviderPerson.org_id == org.id,
                ProviderPerson.display_name == spec.display_name,
            )
            .first()
        )
        if person is None:
            person = ProviderPerson(org_id=org.id, display_name=spec.display_name)
            db.add(person)
        person.is_active = True
        people.append(person)
    db.commit()
    for person in people:
        db.refresh(person)
    return people


def _derived_email(caregiver: User, display_name: str) -> str:
    """A stable internal address for a child who does not have one."""
    slug = "".join(ch for ch in display_name.lower() if ch.isalnum()) or "child"
    return f"{slug}+{caregiver.id}@kid.mew.local"


def _unusable_secret() -> str:
    import secrets

    return secrets.token_urlsafe(32)
