"""
Calendar Router
Endpoints for calendar integration and event management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.integrations.calendar_integration import CalendarIntegration
from app.schemas.auth import UserResponse
from app.schemas.calendar import (
    CalendarConnectionRequest,
    CalendarConnectionResponse,
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarProvider,
    UpcomingEventsRequest,
    UpcomingEventsResponse,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["Calendar"])
calendar_integration = CalendarIntegration()


@router.post("/connect/{provider}", response_model=CalendarConnectionResponse)
async def connect_calendar(
    provider: CalendarProvider,
    connection_data: CalendarConnectionRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Connect to a calendar provider (Google, Apple iCloud, or Outlook)

    **Required credentials by provider:**
    - **Google**: OAuth2 credentials
    - **Apple**: CalDAV server, username, app-specific password
    - **Outlook**: Microsoft Graph OAuth2 credentials (client_id, tenant_id, client_secret)
    """
    try:
        success = False

        if provider == CalendarProvider.GOOGLE:
            success = await calendar_integration.connect_google_calendar(connection_data.credentials)
        elif provider == CalendarProvider.APPLE:
            success = await calendar_integration.connect_apple_calendar(connection_data.credentials)
        elif provider == CalendarProvider.OUTLOOK:
            success = await calendar_integration.connect_outlook_calendar(connection_data.credentials)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to {provider} calendar",
            )

        return CalendarConnectionResponse(
            success=True,
            provider=provider,
            message=f"Successfully connected to {provider} calendar",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calendar connection error: {str(e)}",
        )


@router.post("/events", response_model=CalendarEventResponse)
async def create_calendar_event(
    event_data: CalendarEventCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a calendar event

    Supports creating events in Google Calendar, Apple iCloud, or Outlook Calendar
    """
    try:
        event_id = await calendar_integration.create_event(
            provider=event_data.provider,
            title=event_data.title,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            description=event_data.description,
            location=event_data.location,
            attendees=event_data.attendees,
            reminder_minutes=event_data.reminder_minutes,
        )

        if not event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create calendar event",
            )

        return CalendarEventResponse(
            event_id=event_id,
            provider=event_data.provider,
            title=event_data.title,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            success=True,
            message="Calendar event created successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}",
        )


@router.post("/events/upcoming", response_model=UpcomingEventsResponse)
async def get_upcoming_events(
    request_data: UpcomingEventsRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve upcoming calendar events

    Get events from the next N days across all connected calendars
    """
    try:
        events = await calendar_integration.get_upcoming_events(
            provider=request_data.provider, days_ahead=request_data.days_ahead
        )

        return UpcomingEventsResponse(
            provider=request_data.provider,
            events=events,
            count=len(events),
            days_ahead=request_data.days_ahead,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(e)}",
        )
