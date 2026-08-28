"""
Google Calendar, through the token the user already granted.

Talks to the v3 REST API over httpx rather than the google-api-python-client,
because the existing CalendarIntegration is service-account based and this
needs the *person's* calendar, not the app's. The tokens are the ones
app/routers/calendar_oauth.py stores on OAuthProvider.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from .base import CalendarAdapter, CalendarEvent, CalendarSyncError

logger = logging.getLogger(__name__)

API_ROOT = "https://www.googleapis.com/calendar/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REQUEST_TIMEOUT_SECONDS = 20
PAGE_SIZE = 250
# Refresh a little early rather than racing the expiry on a slow request.
EXPIRY_SKEW_SECONDS = 120


class GoogleCalendarAdapter(CalendarAdapter):
    """One person's Google calendar."""

    name = "google"
    writable = True

    def __init__(
        self,
        access_token: str,
        calendar_id: str = "primary",
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        on_token_refreshed=None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.access_token = access_token
        self.calendar_id = calendar_id or "primary"
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        # Called with (access_token, expires_at) so the caller can persist a
        # refreshed token; this class does not touch the database.
        self.on_token_refreshed = on_token_refreshed
        self._client = client

    # -- reading ----------------------------------------------------------

    async def list_events(self, start: datetime, end: datetime) -> List[CalendarEvent]:
        params = {
            "timeMin": _rfc3339(start),
            "timeMax": _rfc3339(end),
            "singleEvents": "true",  # expand recurrence into real occurrences
            "orderBy": "startTime",
            "maxResults": str(PAGE_SIZE),
            "showDeleted": "true",  # so a cancellation reaches us as one
        }

        events: List[CalendarEvent] = []
        page_token: Optional[str] = None
        while True:
            if page_token:
                params["pageToken"] = page_token
            payload = await self._request(
                "GET", f"/calendars/{_quote(self.calendar_id)}/events", params=params
            )
            for item in payload.get("items", []):
                event = _to_event(item)
                if event is not None:
                    events.append(event)
            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        events.sort(key=lambda event: event.start_utc)
        return events

    # -- writing ----------------------------------------------------------

    async def update_event(
        self,
        external_id: str,
        start_utc: datetime,
        duration_minutes: int,
        location: Optional[str] = None,
    ) -> bool:
        body: Dict[str, Any] = {
            "start": {"dateTime": _rfc3339(start_utc), "timeZone": "UTC"},
            "end": {
                "dateTime": _rfc3339(start_utc + timedelta(minutes=duration_minutes)),
                "timeZone": "UTC",
            },
        }
        if location is not None:
            body["location"] = location

        await self._request(
            "PATCH",
            f"/calendars/{_quote(self.calendar_id)}/events/{_quote(external_id)}",
            json=body,
            # Everyone on the invite hears about it - that is the point.
            params={"sendUpdates": "all"},
        )
        return True

    async def cancel_event(self, external_id: str) -> bool:
        await self._request(
            "DELETE",
            f"/calendars/{_quote(self.calendar_id)}/events/{_quote(external_id)}",
            params={"sendUpdates": "all"},
            expect_json=False,
        )
        return True

    # -- transport --------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        expect_json: bool = True,
        _retried: bool = False,
    ) -> Dict[str, Any]:
        client = self._client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
        try:
            if self._token_is_stale() and not _retried:
                await self._refresh(client)

            response = await client.request(
                method,
                API_ROOT + path,
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            # An access token can be revoked between refreshes; one retry.
            if response.status_code == 401 and self.refresh_token and not _retried:
                await self._refresh(client)
                return await self._request(method, path, params, json, expect_json, _retried=True)

            if response.status_code >= 400:
                raise CalendarSyncError(
                    f"Google Calendar {method} {path} failed: "
                    f"{response.status_code} {response.text[:200]}"
                )
            if not expect_json or not response.content:
                return {}
            return response.json()
        except httpx.HTTPError as exc:
            raise CalendarSyncError(f"Google Calendar unreachable: {exc}") from exc
        finally:
            if self._client is None:
                await client.aclose()

    def _token_is_stale(self) -> bool:
        if not self.refresh_token or self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at - timedelta(seconds=EXPIRY_SKEW_SECONDS)

    async def _refresh(self, client: httpx.AsyncClient) -> None:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not (self.refresh_token and client_id and client_secret):
            return  # nothing to refresh with; the call will fail loudly instead

        response = await client.post(
            TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if response.status_code >= 400:
            raise CalendarSyncError(f"Could not refresh Google token: {response.status_code}")

        payload = response.json()
        self.access_token = payload.get("access_token") or self.access_token
        expires_in = payload.get("expires_in")
        if expires_in:
            self.expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
        if self.on_token_refreshed:
            self.on_token_refreshed(self.access_token, self.expires_at)


def _to_event(item: Dict[str, Any]) -> Optional[CalendarEvent]:
    """
    One Google event, normalised.

    All-day events are skipped: a therapy session has a time, and treating a
    date-only entry as midnight would put a made-up slot on a child's day.
    """
    external_id = item.get("id")
    start = _parse(item.get("start", {}))
    if not external_id or start is None:
        return None

    end = _parse(item.get("end", {}))
    duration = int((end - start).total_seconds() // 60) if end and end > start else 60

    return CalendarEvent(
        external_id=external_id,
        title=item.get("summary") or "Untitled",
        start_utc=start,
        duration_minutes=duration,
        location=item.get("location"),
        description=item.get("description"),
        cancelled=item.get("status") == "cancelled",
        raw=item,
    )


def _parse(node: Dict[str, Any]) -> Optional[datetime]:
    value = node.get("dateTime")
    if not value:
        return None  # date-only: an all-day event, deliberately ignored
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _rfc3339(moment: datetime) -> str:
    return moment.replace(microsecond=0).isoformat() + "Z"


def _quote(value: str) -> str:
    from urllib.parse import quote

    return quote(str(value), safe="")
