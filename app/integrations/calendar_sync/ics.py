"""
ICS feed reader.

Every calendar worth naming publishes ICS: Apple, Calendly, most school and
clinic booking tools, and Google and Outlook as a fallback. It is read-only,
which is exactly right for a provider who wants Mew to see their schedule
without handing over write access to their calendar.

Parsed here rather than through a dependency because the subset that matters
is small and well specified, and because a scheduling assistant should not
inherit a parser's CVEs for the sake of four fields.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

from .base import CalendarAdapter, CalendarEvent, CalendarSyncError

logger = logging.getLogger(__name__)

# RFC 5545 folds long lines by starting the continuation with a space or tab.
_FOLD = re.compile(r"\r?\n[ \t]")
_DEFAULT_DURATION_MINUTES = 60
# A feed is somebody else's file. Cap what we are willing to read.
MAX_FEED_BYTES = 5 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 20


class IcsFeedAdapter(CalendarAdapter):
    """A published ICS URL. Read-only by nature."""

    name = "ics"
    writable = False

    def __init__(self, url: str, client: Optional[httpx.AsyncClient] = None):
        self.url = url
        self._client = client

    async def list_events(self, start: datetime, end: datetime) -> List[CalendarEvent]:
        text = await self._fetch()
        return [
            event
            for event in parse_ics(text)
            if start <= event.start_utc < end and not event.cancelled
        ]

    async def _fetch(self) -> str:
        client = self._client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
        try:
            response = await client.get(self.url)
            response.raise_for_status()
            if len(response.content) > MAX_FEED_BYTES:
                raise CalendarSyncError(f"ICS feed larger than {MAX_FEED_BYTES} bytes")
            return response.text
        except httpx.HTTPError as exc:
            raise CalendarSyncError(f"Could not read ICS feed: {exc}") from exc
        finally:
            if self._client is None:
                await client.aclose()


def parse_ics(text: str) -> List[CalendarEvent]:
    """Pull VEVENTs out of an ICS document. Unparseable events are skipped."""
    events: List[CalendarEvent] = []
    unfolded = _FOLD.sub("", text or "")

    for block in unfolded.split("BEGIN:VEVENT")[1:]:
        block = block.split("END:VEVENT")[0]
        fields = _fields(block)

        uid = fields.get("UID")
        start = _parse_datetime(fields.get("DTSTART"))
        if not uid or start is None:
            continue  # an event we cannot identify or place is not an event

        end = _parse_datetime(fields.get("DTEND"))
        if end is not None and end > start:
            duration = int((end - start).total_seconds() // 60)
        else:
            duration = _parse_duration(fields.get("DURATION")) or _DEFAULT_DURATION_MINUTES

        events.append(
            CalendarEvent(
                external_id=uid,
                title=_unescape(fields.get("SUMMARY") or "Untitled"),
                start_utc=start,
                duration_minutes=duration,
                location=_unescape(fields.get("LOCATION")) or None,
                description=_unescape(fields.get("DESCRIPTION")) or None,
                cancelled=(fields.get("STATUS") or "").upper() == "CANCELLED",
            )
        )

    events.sort(key=lambda event: event.start_utc)
    return events


def _fields(block: str) -> Dict[str, str]:
    """
    Map property name to value.

    Property parameters (``DTSTART;TZID=...``) are dropped: the name before
    the first semicolon is what we key on, and the value is everything after
    the first colon.
    """
    out: Dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        head, _, value = line.partition(":")
        name = head.split(";")[0].strip().upper()
        if name:
            out[name] = value.strip()
    return out


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """
    Accept the three forms an ICS DTSTART actually takes.

    Anything carrying a zone other than UTC is read as-is: without a tz
    database per feed, guessing an offset would silently move a session,
    which is worse than treating the wall time as given.
    """
    if not value:
        return None
    raw = value.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _parse_duration(value: Optional[str]) -> Optional[int]:
    """ISO 8601 duration, the subset ICS uses: PT1H30M, P1D, PT45M."""
    if not value:
        return None
    match = re.fullmatch(
        r"[+-]?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?",
        value.strip().upper(),
    )
    if not match:
        return None
    weeks, days, hours, minutes, seconds = (int(g or 0) for g in match.groups())
    total = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return int(total.total_seconds() // 60) or None


def _unescape(value: Optional[str]) -> str:
    """RFC 5545 escapes commas, semicolons and newlines in text values."""
    if not value:
        return ""
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )
