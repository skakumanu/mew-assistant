"""
Tests for calendar ingest and write-back.

Nothing in Mew invents a therapy appointment: sessions exist because a
calendar says so. These cover the parsing, the mirroring and the push, with
no network - the adapters take an injected client.
"""

from datetime import datetime

import httpx
import pytest

from app.database.models import (
    ChangeKind,
    OAuthProvider,
    ProviderOrg,
    ProviderPerson,
    ScheduledSession,
    User,
)
from app.integrations.calendar_sync import CalendarSyncError, parse_ics
from app.integrations.calendar_sync.google import GoogleCalendarAdapter
from app.integrations.calendar_sync.ics import IcsFeedAdapter
from app.services.calendar_sync_service import CalendarSyncService
from app.utils.auth import get_password_hash

ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:aba-001
SUMMARY:ABA session
DTSTART:20260910T153000Z
DTEND:20260910T170000Z
LOCATION:Bright Steps\\, Room 2
END:VEVENT
BEGIN:VEVENT
UID:speech-002
SUMMARY:Speech
DTSTART;TZID=America/Chicago:20260911T100000
DURATION:PT45M
END:VEVENT
BEGIN:VEVENT
UID:gone-003
SUMMARY:Cancelled thing
DTSTART:20260912T090000Z
DTEND:20260912T100000Z
STATUS:CANCELLED
END:VEVENT
END:VCALENDAR
"""


class TestIcsParsing:
    def test_events_are_pulled_out_with_their_times(self):
        events = parse_ics(ICS)

        assert [e.external_id for e in events] == ["aba-001", "speech-002", "gone-003"]
        first = events[0]
        assert first.title == "ABA session"
        assert first.start_utc == datetime(2026, 9, 10, 15, 30)
        assert first.duration_minutes == 90

    def test_escaped_text_is_unescaped(self):
        assert parse_ics(ICS)[0].location == "Bright Steps, Room 2"

    def test_a_duration_is_read_when_there_is_no_end(self):
        speech = parse_ics(ICS)[1]

        assert speech.duration_minutes == 45
        assert speech.start_utc == datetime(2026, 9, 11, 10, 0)

    def test_a_cancelled_event_is_marked_not_dropped(self):
        """The sync needs to see it to cancel the session it mirrors."""
        assert parse_ics(ICS)[2].cancelled is True

    def test_events_come_back_in_time_order(self):
        events = parse_ics(ICS)
        assert [e.start_utc for e in events] == sorted(e.start_utc for e in events)

    def test_an_event_with_no_uid_or_no_start_is_skipped(self):
        broken = (
            "BEGIN:VEVENT\nSUMMARY:No uid\nDTSTART:20260910T150000Z\nEND:VEVENT\n"
            "BEGIN:VEVENT\nUID:no-start\nSUMMARY:No start\nEND:VEVENT\n"
        )
        assert parse_ics(broken) == []

    def test_folded_lines_are_joined(self):
        folded = (
            "BEGIN:VEVENT\nUID:x\nSUMMARY:A very long titl\n e that was folded\n"
            "DTSTART:20260910T150000Z\nEND:VEVENT\n"
        )
        assert parse_ics(folded)[0].title == "A very long title that was folded"

    def test_junk_does_not_raise(self):
        assert parse_ics("not a calendar at all") == []
        assert parse_ics("") == []


class TestIcsAdapter:
    @pytest.mark.asyncio
    async def test_the_window_is_honoured(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text=ICS))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = IcsFeedAdapter("https://example.test/feed.ics", client=client)
            events = await adapter.list_events(datetime(2026, 9, 10), datetime(2026, 9, 11))

        assert [e.external_id for e in events] == ["aba-001"]

    @pytest.mark.asyncio
    async def test_cancelled_events_are_not_returned_as_sessions(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text=ICS))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = IcsFeedAdapter("https://example.test/feed.ics", client=client)
            events = await adapter.list_events(datetime(2026, 9, 1), datetime(2026, 10, 1))

        assert "gone-003" not in [e.external_id for e in events]

    @pytest.mark.asyncio
    async def test_an_unreachable_feed_raises_a_sync_error(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(503))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = IcsFeedAdapter("https://example.test/feed.ics", client=client)
            with pytest.raises(CalendarSyncError):
                await adapter.list_events(datetime(2026, 9, 1), datetime(2026, 10, 1))

    @pytest.mark.asyncio
    async def test_a_feed_is_read_only_and_says_so(self):
        adapter = IcsFeedAdapter("https://example.test/feed.ics")

        assert adapter.writable is False
        assert await adapter.update_event("x", datetime(2026, 9, 10, 16, 0), 60) is False
        assert await adapter.cancel_event("x") is False


class TestGoogleAdapter:
    @pytest.mark.asyncio
    async def test_events_are_normalised(self):
        payload = {
            "items": [
                {
                    "id": "evt1",
                    "summary": "ABA session",
                    "status": "confirmed",
                    "start": {"dateTime": "2026-09-10T15:30:00Z"},
                    "end": {"dateTime": "2026-09-10T17:00:00Z"},
                    "location": "Room 2",
                },
                {  # all-day: deliberately ignored, it has no real time
                    "id": "evt2",
                    "summary": "Holiday",
                    "start": {"date": "2026-09-11"},
                    "end": {"date": "2026-09-12"},
                },
            ]
        }
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = GoogleCalendarAdapter("token", client=client)
            events = await adapter.list_events(datetime(2026, 9, 1), datetime(2026, 10, 1))

        assert [e.external_id for e in events] == ["evt1"]
        assert events[0].duration_minutes == 90
        assert events[0].start_utc == datetime(2026, 9, 10, 15, 30)

    @pytest.mark.asyncio
    async def test_a_zoned_time_is_converted_to_utc(self):
        payload = {
            "items": [
                {
                    "id": "evt1",
                    "summary": "Speech",
                    "start": {"dateTime": "2026-09-10T10:30:00-05:00"},
                    "end": {"dateTime": "2026-09-10T11:15:00-05:00"},
                }
            ]
        }
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = GoogleCalendarAdapter("token", client=client)
            events = await adapter.list_events(datetime(2026, 9, 1), datetime(2026, 10, 1))

        assert events[0].start_utc == datetime(2026, 9, 10, 15, 30)
        assert events[0].duration_minutes == 45

    @pytest.mark.asyncio
    async def test_pages_are_followed(self):
        pages = [
            {"items": [_event("a", "2026-09-10T09:00:00Z")], "nextPageToken": "p2"},
            {"items": [_event("b", "2026-09-11T09:00:00Z")]},
        ]
        calls = {"n": 0}

        def handler(request):
            page = pages[calls["n"]]
            calls["n"] += 1
            return httpx.Response(200, json=page)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = GoogleCalendarAdapter("token", client=client)
            events = await adapter.list_events(datetime(2026, 9, 1), datetime(2026, 10, 1))

        assert [e.external_id for e in events] == ["a", "b"]

    @pytest.mark.asyncio
    async def test_moving_an_event_sends_the_new_window_and_tells_attendees(self):
        seen = {}

        def handler(request):
            seen["method"] = request.method
            seen["url"] = str(request.url)
            seen["body"] = request.read().decode()
            return httpx.Response(200, json={})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = GoogleCalendarAdapter("token", client=client)
            ok = await adapter.update_event("evt1", datetime(2026, 9, 10, 16, 30), 90)

        assert ok is True
        assert seen["method"] == "PATCH"
        assert "sendUpdates=all" in seen["url"]
        assert "2026-09-10T16:30:00Z" in seen["body"]
        assert "2026-09-10T18:00:00Z" in seen["body"]

    @pytest.mark.asyncio
    async def test_an_api_error_becomes_a_sync_error(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(500, text="boom"))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = GoogleCalendarAdapter("token", client=client)
            with pytest.raises(CalendarSyncError):
                await adapter.list_events(datetime(2026, 9, 1), datetime(2026, 10, 1))


def _event(uid, start):
    return {
        "id": uid,
        "summary": uid,
        "start": {"dateTime": start},
        "end": {"dateTime": start},
    }


@pytest.fixture
def synced_org(db_session):
    """A child whose provider publishes an ICS feed."""
    parent = User(
        email="sync-parent@example.com",
        username="sync-parent",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=False,
    )
    db_session.add(parent)
    db_session.commit()

    kid = User(
        email="sync-kid@example.com",
        username="sync-kid",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=True,
        parent_id=parent.id,
    )
    org = ProviderOrg(
        name="Bright Steps ABA",
        kind="aba",
        calendar_provider="ics",
        calendar_account_id="https://example.test/feed.ics",
    )
    db_session.add_all([kid, org])
    db_session.commit()
    return {"parent": parent, "kid": kid, "org": org}


class TestPull:
    @pytest.mark.asyncio
    async def test_a_pull_creates_sessions(self, db_session, synced_org, monkeypatch):
        _serve(monkeypatch, ICS)
        service = CalendarSyncService(db_session)

        result = await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )

        assert result.ok and result.created == 2  # the cancelled one is skipped
        rows = db_session.query(ScheduledSession).all()
        assert {row.title for row in rows} == {"ABA session", "Speech"}
        assert all(row.source == "calendar" for row in rows)
        assert all(row.external_event_id for row in rows)

    @pytest.mark.asyncio
    async def test_pulling_twice_changes_nothing(self, db_session, synced_org, monkeypatch):
        _serve(monkeypatch, ICS)
        service = CalendarSyncService(db_session)

        await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )
        second = await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )

        assert second.created == 0 and second.updated == 0
        assert db_session.query(ScheduledSession).count() == 2

    @pytest.mark.asyncio
    async def test_a_moved_event_updates_the_session(self, db_session, synced_org, monkeypatch):
        _serve(monkeypatch, ICS)
        service = CalendarSyncService(db_session)
        await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )

        moved = ICS.replace("DTSTART:20260910T153000Z", "DTSTART:20260910T163000Z")
        _serve(monkeypatch, moved)
        result = await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )

        assert result.updated == 1
        row = (
            db_session.query(ScheduledSession)
            .filter(ScheduledSession.external_event_id == "aba-001")
            .one()
        )
        assert row.start_utc == datetime(2026, 9, 10, 16, 30)
        # The provider edited their own calendar - that is not "your rules
        # handled a request", so the week must not show an `updated` pill.
        assert row.last_changed_at is None

    @pytest.mark.asyncio
    async def test_an_event_that_vanished_is_cancelled(self, db_session, synced_org, monkeypatch):
        _serve(monkeypatch, ICS)
        service = CalendarSyncService(db_session)
        await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )

        without_speech = ICS.replace("UID:speech-002", "UID:speech-002-renamed")
        _serve(monkeypatch, without_speech)
        await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )

        gone = (
            db_session.query(ScheduledSession)
            .filter(ScheduledSession.external_event_id == "speech-002")
            .one()
        )
        assert gone.is_cancelled is True

    @pytest.mark.asyncio
    async def test_a_disconnected_calendar_reports_rather_than_raising(
        self, db_session, synced_org
    ):
        synced_org["org"].calendar_provider = None
        db_session.commit()

        result = await CalendarSyncService(db_session).pull_org(
            synced_org["org"], child_id=synced_org["kid"].id
        )

        assert result.ok is False
        assert result.error == "no calendar connected"

    @pytest.mark.asyncio
    async def test_an_unreachable_feed_reports_rather_than_raising(
        self, db_session, synced_org, monkeypatch
    ):
        _serve(monkeypatch, "", status=502)

        result = await CalendarSyncService(db_session).pull_org(
            synced_org["org"], child_id=synced_org["kid"].id
        )

        assert result.ok is False and result.error
        assert db_session.query(ScheduledSession).count() == 0


class TestPush:
    @pytest.mark.asyncio
    async def test_a_read_only_feed_reports_false_not_an_error(
        self, db_session, synced_org, monkeypatch
    ):
        _serve(monkeypatch, ICS)
        service = CalendarSyncService(db_session)
        await service.pull_org(
            synced_org["org"], child_id=synced_org["kid"].id, now=datetime(2026, 9, 1)
        )
        row = db_session.query(ScheduledSession).first()

        assert await service.push(row, ChangeKind.MOVE) is False

    @pytest.mark.asyncio
    async def test_a_manual_session_is_never_pushed(self, db_session, synced_org):
        row = ScheduledSession(
            child_id=synced_org["kid"].id,
            provider_org_id=synced_org["org"].id,
            title="Typed in by hand",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 15, 30),
            duration_minutes=60,
            source="manual",
        )
        db_session.add(row)
        db_session.commit()

        assert await CalendarSyncService(db_session).push(row, ChangeKind.MOVE) is False

    @pytest.mark.asyncio
    async def test_a_writable_calendar_receives_the_change(
        self, db_session, synced_org, monkeypatch
    ):
        """A Google-backed org gets a real PATCH when a change is applied."""
        org = synced_org["org"]
        org.calendar_provider = "google"
        org.calendar_account_id = "primary"
        login = User(
            email="therapist@example.com",
            username="therapist",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(login)
        db_session.commit()
        db_session.add(ProviderPerson(org_id=org.id, display_name="Dana R.", user_id=login.id))
        db_session.add(
            OAuthProvider(
                user_id=login.id,
                provider="google",
                provider_user_id="g-1",
                access_token="token",
            )
        )
        row = ScheduledSession(
            child_id=synced_org["kid"].id,
            provider_org_id=org.id,
            title="ABA session",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 16, 30),
            duration_minutes=90,
            source="calendar",
            external_event_id="evt1",
        )
        db_session.add(row)
        db_session.commit()

        seen = {}

        def handler(request):
            seen["method"] = request.method
            seen["body"] = request.read().decode()
            return httpx.Response(200, json={})

        import app.services.calendar_sync_service as module

        real = module.GoogleCalendarAdapter

        def patched(*args, **kwargs):
            kwargs["client"] = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            return real(*args, **kwargs)

        monkeypatch.setattr(module, "GoogleCalendarAdapter", patched)

        assert await CalendarSyncService(db_session).push(row, ChangeKind.MOVE) is True
        assert seen["method"] == "PATCH"
        assert "2026-09-10T16:30:00Z" in seen["body"]


def _serve(monkeypatch, body: str, status: int = 200):
    """Point the ICS adapter at a canned response instead of the network."""
    import app.integrations.calendar_sync.ics as ics_module

    real = ics_module.IcsFeedAdapter

    def patched(url, client=None):
        transport = httpx.MockTransport(lambda request: httpx.Response(status, text=body))
        return real(url, client=httpx.AsyncClient(transport=transport))

    monkeypatch.setattr("app.services.calendar_sync_service.IcsFeedAdapter", patched)
