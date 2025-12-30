"""
Tests for Calendar Integration
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from app.integrations.calendar_integration import CalendarIntegration, CalendarProvider


@pytest.fixture
def calendar_integration():
    """Create calendar integration instance"""
    return CalendarIntegration()


@pytest.mark.asyncio
async def test_connect_google_calendar(calendar_integration):
    """Test Google Calendar connection"""
    credentials = {
        "token": "[REDACTED]",
        "refresh_token": "[REDACTED]",
        "client_id": "[REDACTED]",
        "client_secret": "[REDACTED]",
    }

    with (
        patch("app.integrations.calendar_integration.Credentials") as mock_creds,
        patch("app.integrations.calendar_integration.build") as mock_build,
    ):
        mock_creds.from_authorized_user_info.return_value = Mock()
        mock_build.return_value = Mock()

        result = await calendar_integration.connect_google_calendar(credentials)

        assert result is True
        assert calendar_integration.google_client is not None


@pytest.mark.asyncio
async def test_create_event(calendar_integration):
    """Test creating a calendar event"""
    calendar_integration.google_client = Mock()
    mock_events = Mock()
    mock_events.insert.return_value.execute.return_value = {"id": "event_123"}
    calendar_integration.google_client.events.return_value = mock_events

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)

    event_id = await calendar_integration.create_event(
        provider=CalendarProvider.GOOGLE,
        title="Test Event",
        start_time=start_time,
        end_time=end_time,
        description="Test description",
        location="Test location",
        attendees=["test@example.com"],
        reminder_minutes=30,
    )

    assert event_id == "event_123"


@pytest.mark.asyncio
async def test_get_upcoming_events(calendar_integration):
    """Test retrieving upcoming events"""
    calendar_integration.google_client = Mock()
    mock_events = Mock()
    mock_events.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "event_1",
                "summary": "Event 1",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "description": "Test event 1",
                "location": "Location 1",
            },
            {
                "id": "event_2",
                "summary": "Event 2",
                "start": {"dateTime": "2024-01-16T14:00:00Z"},
                "end": {"dateTime": "2024-01-16T15:00:00Z"},
                "description": "Test event 2",
                "location": "Location 2",
            },
        ]
    }
    calendar_integration.google_client.events.return_value = mock_events

    events = await calendar_integration.get_upcoming_events(
        provider=CalendarProvider.GOOGLE, days_ahead=7
    )

    assert len(events) == 2
    assert events[0]["id"] == "event_1"
    assert events[0]["title"] == "Event 1"
    assert events[1]["id"] == "event_2"
    assert events[1]["title"] == "Event 2"


@pytest.mark.asyncio
async def test_connect_apple_calendar(calendar_integration):
    """Test Apple Calendar connection"""
    credentials = {
        "username": "test@icloud.com",
        "app_specific_password": "xxxx-xxxx-xxxx-xxxx",
        "server": "https://caldav.icloud.com",
    }

    with patch("app.integrations.calendar_integration.caldav") as mock_caldav:
        mock_client = Mock()
        mock_principal = Mock()
        mock_principal.calendars.return_value = [Mock()]
        mock_client.principal.return_value = mock_principal
        mock_caldav.DAVClient.return_value = mock_client

        result = await calendar_integration.connect_apple_calendar(credentials)

        assert result is True
        assert calendar_integration.apple_client is not None


@pytest.mark.asyncio
async def test_connect_outlook_calendar(calendar_integration):
    """Test Outlook Calendar connection"""
    credentials = {
        "client_id": "[REDACTED]",
        "tenant_id": "[REDACTED]",
        "client_secret": "[REDACTED]",
    }

    with patch("app.integrations.calendar_integration.msal") as mock_msal:
        mock_app = Mock()
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "test_access_token"
        }
        mock_msal.ConfidentialClientApplication.return_value = mock_app

        result = await calendar_integration.connect_outlook_calendar(credentials)

        assert result is True
        assert calendar_integration.outlook_client is not None


@pytest.mark.asyncio
async def test_create_event_invalid_provider(calendar_integration):
    """Test creating event with invalid provider"""
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)

    with pytest.raises(Exception):
        await calendar_integration.create_event(
            provider="invalid_provider",
            title="Test Event",
            start_time=start_time,
            end_time=end_time,
        )


@pytest.mark.asyncio
async def test_get_events_without_connection(calendar_integration):
    """Test getting events without established connection"""
    events = await calendar_integration.get_upcoming_events(
        provider=CalendarProvider.GOOGLE, days_ahead=7
    )

    assert events == []
