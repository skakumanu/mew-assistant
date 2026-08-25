"""
Calendar in, calendar out.

Two jobs, and the direction matters:

  **Pull** is how sessions exist at all. Nothing in Mew invents a therapy
  appointment; they come from the calendar a provider or a family already
  keeps, and are mirrored into ``ScheduledSession`` so the rule engine has
  something to evaluate.

  **Push** is how an approved change reaches the people who work from the
  calendar rather than from Mew.

Mew stays authoritative on a conflict. A calendar that cannot be written to
is a normal state - a published ICS feed is read-only by design - and never
a reason to undo a change the rules allowed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session as DbSession

from ..database.models import (
    ChangeKind,
    OAuthProvider,
    ProviderOrg,
    ProviderOrgConnection,
    ScheduledSession,
    SessionSource,
)
from ..integrations.calendar_sync import (
    CalendarAdapter,
    CalendarEvent,
    CalendarSyncError,
    GoogleCalendarAdapter,
    IcsFeedAdapter,
)

logger = logging.getLogger(__name__)

DEFAULT_PULL_DAYS_BACK = 1
DEFAULT_PULL_DAYS_AHEAD = 30


@dataclass
class SyncResult:
    """What one pull actually did. Reported, never inferred from silence."""

    created: int = 0
    updated: int = 0
    cancelled: int = 0
    skipped: int = 0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def total(self) -> int:
        return self.created + self.updated + self.cancelled


class CalendarSyncService:
    """Mirrors a provider organisation's calendar into the schedule."""

    def __init__(self, db: DbSession):
        self.db = db

    # ------------------------------------------------------------------
    # adapters
    # ------------------------------------------------------------------

    def adapter_for(self, org: ProviderOrg) -> Optional[CalendarAdapter]:
        """
        Build the adapter this organisation's calendar needs.

        Returns None when the org has not connected one - a perfectly normal
        state for a family entering sessions by hand.
        """
        provider = (org.calendar_provider or "").strip().lower()
        account = org.calendar_account_id

        if not provider or not account:
            return None

        if provider == "ics":
            return IcsFeedAdapter(url=account)

        if provider == "google":
            return self._google_adapter(org, account)

        logger.warning("Provider org %s has an unsupported calendar provider %r", org.id, provider)
        return None

    def _google_adapter(
        self, org: ProviderOrg, calendar_id: str
    ) -> Optional[GoogleCalendarAdapter]:
        """
        Google needs a person's token - specifically, whoever granted Mew
        access to read this calendar. That is recorded on
        ``ProviderOrgConnection.connected_by_user_id`` when a family
        connects Google Calendar for this org; it is deliberately NOT
        ``ProviderPerson.user_id``, which means something else entirely (a
        real clinic staff member's own login) and is trusted elsewhere
        (provider.py, change_request_service.py) to grant that org's whole
        roster and session list - a parent's own connection must never
        satisfy that check.
        """
        user_ids = [
            row.connected_by_user_id
            for row in self.db.query(ProviderOrgConnection)
            .filter(
                ProviderOrgConnection.org_id == org.id,
                ProviderOrgConnection.connected_by_user_id.isnot(None),
            )
            .all()
        ]
        if not user_ids:
            logger.info("Provider org %s has nobody with a linked account", org.id)
            return None

        link = (
            self.db.query(OAuthProvider)
            .filter(
                OAuthProvider.provider == "google",
                OAuthProvider.user_id.in_(user_ids),
                OAuthProvider.access_token.isnot(None),
            )
            .first()
        )
        if link is None:
            logger.info("Provider org %s has no usable Google token", org.id)
            return None

        def persist(access_token: str, expires_at: Optional[datetime]) -> None:
            """A refreshed token is worth keeping, or we refresh every call."""
            link.access_token = access_token
            link.token_expires_at = expires_at
            self.db.commit()

        return GoogleCalendarAdapter(
            access_token=link.access_token,
            calendar_id=calendar_id,
            refresh_token=link.refresh_token,
            expires_at=link.token_expires_at,
            on_token_refreshed=persist,
        )

    # ------------------------------------------------------------------
    # pull
    # ------------------------------------------------------------------

    async def pull_org(
        self,
        org: ProviderOrg,
        child_id: int,
        days_back: int = DEFAULT_PULL_DAYS_BACK,
        days_ahead: int = DEFAULT_PULL_DAYS_AHEAD,
        now: Optional[datetime] = None,
    ) -> SyncResult:
        """
        Mirror one organisation's calendar into this child's schedule.

        Idempotent: events are matched on ``external_event_id``, so running it
        twice changes nothing the second time.
        """
        adapter = self.adapter_for(org)
        if adapter is None:
            return SyncResult(error="no calendar connected")

        now = now or datetime.utcnow()
        window_start = now - timedelta(days=days_back)
        window_end = now + timedelta(days=days_ahead)

        try:
            events = await adapter.list_events(window_start, window_end)
        except CalendarSyncError as exc:
            logger.warning("Calendar pull failed for org %s: %s", org.id, exc)
            return SyncResult(error=str(exc))

        result = SyncResult()
        seen: List[str] = []

        for event in events:
            seen.append(event.external_id)
            self._upsert(event, org, child_id, result)

        # An event that vanished from the feed was cancelled at the source.
        self._cancel_missing(org, child_id, window_start, window_end, seen, result)

        self.db.commit()
        return result

    def _upsert(
        self,
        event: CalendarEvent,
        org: ProviderOrg,
        child_id: int,
        result: SyncResult,
    ) -> None:
        existing = (
            self.db.query(ScheduledSession)
            .filter(
                ScheduledSession.child_id == child_id,
                ScheduledSession.provider_org_id == org.id,
                ScheduledSession.external_event_id == event.external_id,
            )
            .first()
        )

        if existing is None:
            if event.cancelled:
                result.skipped += 1
                return
            self.db.add(
                ScheduledSession(
                    child_id=child_id,
                    provider_org_id=org.id,
                    title=event.title,
                    activity_type=_activity_for(org),
                    start_utc=event.start_utc,
                    duration_minutes=event.duration_minutes,
                    location=event.location,
                    source=SessionSource.CALENDAR.value,
                    external_event_id=event.external_id,
                )
            )
            result.created += 1
            return

        if event.cancelled:
            if not existing.is_cancelled:
                existing.is_cancelled = True
                result.cancelled += 1
            else:
                result.skipped += 1
            return

        changed = (
            existing.start_utc != event.start_utc
            or existing.duration_minutes != event.duration_minutes
            or existing.title != event.title
            or existing.location != event.location
        )
        if not changed:
            result.skipped += 1
            return

        existing.start_utc = event.start_utc
        existing.duration_minutes = event.duration_minutes
        existing.title = event.title
        existing.location = event.location
        existing.is_cancelled = False
        # Deliberately NOT last_changed_at: that pill means "your rules
        # handled a request", not "the provider edited their own calendar".
        result.updated += 1

    def _cancel_missing(
        self,
        org: ProviderOrg,
        child_id: int,
        window_start: datetime,
        window_end: datetime,
        seen: List[str],
        result: SyncResult,
    ) -> None:
        rows = (
            self.db.query(ScheduledSession)
            .filter(
                ScheduledSession.child_id == child_id,
                ScheduledSession.provider_org_id == org.id,
                ScheduledSession.source == SessionSource.CALENDAR.value,
                ScheduledSession.is_cancelled.is_(False),
                ScheduledSession.start_utc >= window_start,
                ScheduledSession.start_utc < window_end,
                ScheduledSession.external_event_id.isnot(None),
            )
            .all()
        )
        for row in rows:
            if row.external_event_id not in seen:
                row.is_cancelled = True
                result.cancelled += 1

    # ------------------------------------------------------------------
    # push
    # ------------------------------------------------------------------

    async def push(self, session: ScheduledSession, kind: ChangeKind) -> bool:
        """
        Write an applied change back out.

        Returns True only when a calendar actually accepted it. False covers
        every ordinary reason it could not happen - no calendar connected, a
        read-only feed, a manually entered session - and is not an error.
        """
        if not session.external_event_id or not session.provider_org_id:
            return False

        org = self.db.query(ProviderOrg).filter(ProviderOrg.id == session.provider_org_id).first()
        if org is None:
            return False

        adapter = self.adapter_for(org)
        if adapter is None or not adapter.writable:
            return False

        try:
            if kind is ChangeKind.CANCEL:
                return await adapter.cancel_event(session.external_event_id)
            return await adapter.update_event(
                external_id=session.external_event_id,
                start_utc=session.start_utc,
                duration_minutes=session.duration_minutes,
                location=session.location,
            )
        except CalendarSyncError as exc:
            # Mew is already authoritative; a calendar hiccup never undoes a
            # change the rules allowed.
            logger.warning("Calendar write-back failed for session %s: %s", session.id, exc)
            return False


def _activity_for(org: ProviderOrg) -> str:
    """An org's kind is the best available guess at what it schedules."""
    return (org.kind or "other").lower()
