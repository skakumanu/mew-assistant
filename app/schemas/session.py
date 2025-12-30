"""
Pydantic schemas for session management.
Validates request/response data for session endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SessionType(str, Enum):
    """Available session types for Mew Assistant."""

    TUTORING = "tutoring"
    SCHEDULING = "scheduling"
    CAREGIVER_SUMMARY = "caregiver_summary"


class SessionStatus(str, Enum):
    """Session status values."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    """Priority levels for scheduling."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SessionCreate(BaseModel):
    """Request schema for creating a new session."""

    user_id: str = Field(..., description="User identifier")
    session_type: SessionType = Field(..., description="Type of session to create")
    title: Optional[str] = Field(None, max_length=255, description="Session title")
    description: Optional[str] = Field(None, description="Session description")
    priority: PriorityLevel = Field(
        default=PriorityLevel.NORMAL, description="Session priority"
    )
    scheduled_at: Optional[datetime] = Field(
        None, description="Scheduled time (ISO format)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_12345",
                "session_type": "tutoring",
                "title": "Math tutoring session",
                "description": "Algebra homework help",
                "priority": "normal",
                "scheduled_at": "2025-11-15T14:00:00Z",
            }
        }
    )


class SessionConfirm(BaseModel):
    """Request schema for confirming a session."""

    session_id: int = Field(..., description="Session ID to confirm")
    notes: Optional[str] = Field(None, description="Additional notes")
    override_cooldown: bool = Field(
        default=False, description="Override cooldown period for urgent sessions"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": 42,
                "notes": "Confirmed via phone call",
                "override_cooldown": False,
            }
        }
    )


class SessionUpdate(BaseModel):
    """Request schema for updating session details."""

    status: Optional[SessionStatus] = None
    priority: Optional[PriorityLevel] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    notes: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class SessionResponse(BaseModel):
    """Response schema for session data."""

    id: int
    user_id: str
    session_type: str
    status: str
    priority: str
    title: Optional[str]
    description: Optional[str]
    notes: Optional[str]
    created_at: datetime
    confirmed_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    cooldown_until: Optional[datetime]
    in_cooldown: bool = Field(
        default=False, description="Whether session is in cooldown period"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 42,
                "user_id": "user_12345",
                "session_type": "tutoring",
                "status": "confirmed",
                "priority": "normal",
                "title": "Math tutoring session",
                "description": "Algebra homework help",
                "notes": "Student needs extra help with quadratics",
                "created_at": "2025-11-13T10:00:00Z",
                "confirmed_at": "2025-11-13T10:05:00Z",
                "scheduled_at": "2025-11-15T14:00:00Z",
                "completed_at": None,
                "cooldown_until": None,
                "in_cooldown": False,
            }
        },
    )
