"""
Calendar Schemas
Pydantic models for calendar integration
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.integrations.calendar_integration import CalendarProvider


class CalendarConnectionRequest(BaseModel):
    """Request model for connecting to a calendar provider"""
    credentials: Dict[str, Any] = Field(
        ...,
        description="Provider-specific credentials",
        example={
            "google": {"token": "oauth2_token"},
            "apple": {"username": "user@icloud.com", "app_specific_password": "xxxx-xxxx-xxxx-xxxx", "server": "https://caldav.icloud.com"},
            "outlook": {"client_id": "xxx", "tenant_id": "xxx", "client_secret": "xxx"}
        }
    )


class CalendarConnectionResponse(BaseModel):
    """Response model for calendar connection"""
    success: bool
    provider: CalendarProvider
    message: str


class CalendarEventCreate(BaseModel):
    """Request model for creating a calendar event"""
    provider: CalendarProvider = Field(..., description="Calendar provider")
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    start_time: datetime = Field(..., description="Event start time (UTC)")
    end_time: datetime = Field(..., description="Event end time (UTC)")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    location: Optional[str] = Field(None, max_length=200, description="Event location")
    attendees: Optional[List[str]] = Field(None, description="List of attendee email addresses")
    reminder_minutes: int = Field(30, ge=0, le=10080, description="Reminder time before event (minutes)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "google",
                "title": "Therapy Session with Emma",
                "start_time": "2024-01-15T14:00:00Z",
                "end_time": "2024-01-15T15:00:00Z",
                "description": "Weekly therapy session",
                "location": "123 Main St, Suite 200",
                "attendees": ["therapist@example.com", "parent@example.com"],
                "reminder_minutes": 30
            }
        }


class CalendarEventResponse(BaseModel):
    """Response model for calendar event creation"""
    event_id: str
    provider: CalendarProvider
    title: str
    start_time: datetime
    end_time: datetime
    success: bool
    message: str


class UpcomingEventsRequest(BaseModel):
    """Request model for retrieving upcoming events"""
    provider: CalendarProvider = Field(..., description="Calendar provider")
    days_ahead: int = Field(7, ge=1, le=365, description="Number of days to look ahead")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "google",
                "days_ahead": 7
            }
        }


class CalendarEvent(BaseModel):
    """Model for a calendar event"""
    id: str
    title: str
    start: Optional[str]
    end: Optional[str]
    description: Optional[str]
    location: Optional[str]


class UpcomingEventsResponse(BaseModel):
    """Response model for upcoming events"""
    provider: CalendarProvider
    events: List[CalendarEvent]
    count: int
    days_ahead: int
