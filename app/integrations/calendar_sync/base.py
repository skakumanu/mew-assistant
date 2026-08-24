"""
The shape every calendar looks like once it reaches Mew.

Providers differ wildly - Google speaks JSON over REST, an ICS feed is a
text file, Graph uses its own field names - but the scheduling loop only
ever needs four things from an event and only ever does three things to one.
Keeping that contract this narrow is what lets a family bring whichever
calendar they already use.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CalendarEvent:
    """One event, normalised. Times are always naive UTC, as the DB stores them."""

    external_id: str
    title: str
    start_utc: datetime
    duration_minutes: int
    location: Optional[str] = None
    description: Optional[str] = None
    cancelled: bool = False
    # Anything provider-specific a caller might want, never interpreted here.
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def end_utc(self) -> datetime:
        from datetime import timedelta

        return self.start_utc + timedelta(minutes=self.duration_minutes)


class CalendarSyncError(RuntimeError):
    """A calendar could not be reached or answered with something unusable."""


class CalendarAdapter(ABC):
    """
    One calendar, two directions.

    Read is how sessions get into Mew at all; write is how an approved change
    reaches the people who work from the calendar rather than from Mew.
    """

    #: Value stored in ``ProviderOrg.calendar_provider``.
    name: str = "base"

    #: False for feeds that are inherently read-only, such as a published ICS
    #: URL. The loop still works: the change is authoritative in Mew and the
    #: log says the calendar could not be written to.
    writable: bool = True

    @abstractmethod
    async def list_events(
        self, start: datetime, end: datetime
    ) -> List[CalendarEvent]:  # pragma: no cover - interface
        """Every event in the window, oldest first."""

    async def update_event(
        self,
        external_id: str,
        start_utc: datetime,
        duration_minutes: int,
        location: Optional[str] = None,
    ) -> bool:
        """Move an event. Returns False when this calendar cannot be written to."""
        return False

    async def cancel_event(self, external_id: str) -> bool:
        """Cancel an event. Returns False when this calendar cannot be written to."""
        return False
