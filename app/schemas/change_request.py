"""Pydantic schemas for the three-persona scheduling loop."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..database.models import CAREGIVER_TERMS, DEFAULT_CAREGIVER_TERM

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


class ProtectedBlockIn(BaseModel):
    """A daily window nothing may overlap."""

    start: time
    end: time
    weekdays: Optional[List[int]] = Field(None, description="Mon=0. Omit for every day.")
    label_key: str = Field("block.custom", description="Locale key, never a sentence")


class WeeklyCapIn(BaseModel):
    activity_type: str
    max_sessions: int = Field(..., ge=0)


class RuleSetUpdate(BaseModel):
    """
    The six toggles in the parent's Rules tab.

    Sending ``null`` for an optional field turns that rule off - an inactive
    rule is exactly what the engine treats an unset field as.
    """

    timezone: Optional[str] = None
    min_notice_hours: Optional[int] = Field(None, ge=0, le=720)
    earliest_start: Optional[time] = None
    latest_end: Optional[time] = None
    require_same_provider_person: Optional[bool] = None
    buffer_minutes: Optional[int] = Field(None, ge=0, le=480)
    cancellation_needs_approval: Optional[bool] = None
    allowed_weekdays: Optional[List[int]] = None
    notify_on_auto_approve: Optional[bool] = None
    caregiver_term: Optional[str] = Field(
        None,
        description=(
            'Which word this family reads: "parent" or "guardian". '
            "The two are interchangeable - only the label changes."
        ),
    )
    protected_blocks: Optional[List[ProtectedBlockIn]] = None
    weekly_caps: Optional[List[WeeklyCapIn]] = None

    @field_validator("caregiver_term")
    @classmethod
    def _known_term(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalised = value.strip().lower()
        if normalised not in CAREGIVER_TERMS:
            raise ValueError('caregiver_term must be "parent" or "guardian"')
        return normalised


class ProtectedBlockOut(BaseModel):
    id: int
    start: time
    end: time
    weekdays: Optional[List[int]] = None
    label_key: str


class WeeklyCapOut(BaseModel):
    id: int
    activity_type: str
    max_sessions: int


class RuleSetOut(BaseModel):
    id: int
    child_id: Optional[int] = None
    timezone: str
    min_notice_hours: Optional[int] = None
    earliest_start: Optional[time] = None
    latest_end: Optional[time] = None
    require_same_provider_person: bool
    buffer_minutes: Optional[int] = None
    cancellation_needs_approval: bool
    allowed_weekdays: Optional[List[int]] = None
    notify_on_auto_approve: bool
    caregiver_term: str = DEFAULT_CAREGIVER_TERM
    caregiver_label: str = Field("", description="That word rendered in the reader's language")
    protected_blocks: List[ProtectedBlockOut] = Field(default_factory=list)
    weekly_caps: List[WeeklyCapOut] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class ChangeRequestIn(BaseModel):
    """The only write path for a kid or a provider."""

    session_id: int
    kind: str = Field(..., description="move | cancel | swap_provider")
    new_start: Optional[datetime] = None
    new_provider_person_id: Optional[int] = None


class SessionOut(BaseModel):
    id: int
    title: str
    activity_type: str
    start_utc: datetime
    duration_minutes: int
    location: Optional[str] = None
    provider_org_id: Optional[int] = None
    provider_org_name: Optional[str] = None
    provider_person_id: Optional[int] = None
    provider_person_name: Optional[str] = None
    is_cancelled: bool = False
    changed: bool = False


class AlternativeOut(BaseModel):
    """One compliant slot, rendered in the reader's locale."""

    index: int
    start: datetime
    label: str
    note: str = Field(..., description="'closest' for the first, 'also fits' after")


class ChangeRequestOut(BaseModel):
    """
    Two shapes, one status code.

    ``auto_applied: true`` means the schedule already moved. ``false`` means
    the parent has one card waiting, with reasons and alternatives attached.
    """

    auto_applied: bool
    session: SessionOut
    request_id: Optional[int] = None
    reason_codes: List[str] = Field(default_factory=list)
    reasons_text: Optional[str] = None
    alternatives: List[AlternativeOut] = Field(default_factory=list)
    message: str = Field("", description="The sentence to show the requester")


# ---------------------------------------------------------------------------
# Parent inbox and log
# ---------------------------------------------------------------------------


class PendingRequestOut(BaseModel):
    id: int
    source_label: str
    requested_by: str
    headline: str
    detail: str
    reason_codes: List[str] = Field(default_factory=list)
    reasons_text: str = ""
    alternatives: List[AlternativeOut] = Field(default_factory=list)
    kind: str
    session_id: Optional[int] = None
    created_at: datetime


class ChooseAlternativeIn(BaseModel):
    alternative_index: int = Field(..., ge=0)


class LogEntryOut(BaseModel):
    id: int
    text: str
    meta: str
    tone: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Kid and provider views
# ---------------------------------------------------------------------------


class KidCardOut(BaseModel):
    session_id: int
    title: str
    time_label: str
    person: str
    initial: str
    tile_index: int
    can_ask: bool
    status_text: Optional[str] = None
    symbols: List[Dict[str, Any]] = Field(default_factory=list)


class KidTodayOut(BaseModel):
    greeting: str
    day_label: str
    count_label: str
    streak_label: str
    cards: List[KidCardOut] = Field(default_factory=list)
    note: str
    locale: str
    dir: str


class ProviderSessionOut(BaseModel):
    session: SessionOut
    when_label: str
    waiting_on_parent: bool
    people: List[Dict[str, Any]] = Field(default_factory=list)
