"""
Mobile Schemas
Pydantic models for mobile device integration
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DeviceRegistrationRequest(BaseModel):
    """Request model for registering a mobile device"""

    platform: str = Field(..., description="Mobile platform (ios or android)")
    device_token: str = Field(
        ..., min_length=10, description="Device push notification token"
    )
    device_info: Optional[Dict[str, Any]] = Field(
        None, description="Additional device information"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "ios",
                "device_token": "abc123def456...",
                "device_info": {
                    "model": "iPhone 14 Pro",
                    "os_version": "17.1",
                    "app_version": "1.0.0",
                },
            }
        }


class DeviceRegistrationResponse(BaseModel):
    """Response model for device registration"""

    success: bool
    platform: str
    message: str


class PushNotificationRequest(BaseModel):
    """Request model for sending a push notification"""

    platform: str = Field(..., description="Mobile platform")
    device_token: str = Field(..., description="Device push notification token")
    title: str = Field(
        ..., min_length=1, max_length=100, description="Notification title"
    )
    body: str = Field(
        ..., min_length=1, max_length=500, description="Notification body"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")
    badge: Optional[int] = Field(None, ge=0, description="Badge count (iOS only)")
    sound: str = Field("default", description="Notification sound")

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "ios",
                "device_token": "abc123def456...",
                "title": "Upcoming Therapy Session",
                "body": "Your therapy session with Dr. Smith starts in 30 minutes",
                "data": {"session_id": "12345", "type": "reminder"},
                "badge": 1,
                "sound": "default",
            }
        }


class PushNotificationResponse(BaseModel):
    """Response model for push notification"""

    success: bool
    message: str


class BatchNotificationRequest(BaseModel):
    """Request model for sending batch notifications"""

    platform: str = Field(..., description="Mobile platform")
    device_tokens: List[str] = Field(
        ..., min_items=1, description="List of device tokens"
    )
    title: str = Field(
        ..., min_length=1, max_length=100, description="Notification title"
    )
    body: str = Field(
        ..., min_length=1, max_length=500, description="Notification body"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "android",
                "device_tokens": ["token1", "token2", "token3"],
                "title": "System Update",
                "body": "New features are now available",
                "data": {"update_version": "2.0.0"},
            }
        }


class BatchNotificationResponse(BaseModel):
    """Response model for batch notifications"""

    success: bool
    total_sent: int
    failed: int
    message: str


class DeepLinkRequest(BaseModel):
    """Request model for generating deep links"""

    screen: str = Field(..., description="Target screen/route in the app")
    params: Optional[Dict[str, str]] = Field(None, description="Query parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "screen": "session/details",
                "params": {"session_id": "12345", "user_id": "67890"},
            }
        }


class DeepLinkResponse(BaseModel):
    """Response model for deep link generation"""

    ios_link: str
    android_link: str
    universal_link: str
    success: bool


class ScheduledReminderRequest(BaseModel):
    """Request model for scheduling a reminder"""

    platform: str = Field(..., description="Mobile platform")
    device_token: str = Field(..., description="Device push notification token")
    title: str = Field(
        ..., min_length=1, max_length=100, description="Notification title"
    )
    body: str = Field(
        ..., min_length=1, max_length=500, description="Notification body"
    )
    scheduled_time: str = Field(
        ..., description="ISO format datetime string for scheduled delivery"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "ios",
                "device_token": "abc123def456...",
                "title": "Daily Medication Reminder",
                "body": "Time to take your morning medication",
                "scheduled_time": "2024-01-15T08:00:00Z",
                "data": {"medication_id": "med_123"},
            }
        }


class ScheduledReminderResponse(BaseModel):
    """Response model for scheduled reminder"""

    success: bool
    scheduled_time: str
    message: str


class MobilePlatform(str, Enum):
    IOS = "ios"
    ANDROID = "android"


class NotificationType(str, Enum):
    REMINDER = "reminder"
    APPROVAL_REQUEST = "approval_request"
    EMERGENCY = "emergency"
    SYSTEM = "system"
    MESSAGE = "message"


class MobileDeviceRegister(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    platform: MobilePlatform
    push_token: str = Field(..., description="FCM or APNS token")
    device_name: Optional[str] = None
    app_version: str
    os_version: str
    timezone: str = "UTC"


class MobileDeviceResponse(BaseModel):
    device_id: str
    registered_at: datetime
    last_sync: Optional[datetime]
    push_enabled: bool

    class Config:
        from_attributes = True


class AppConfigResponse(BaseModel):
    api_version: str
    features: Dict[str, bool]
    sync_interval_seconds: int
    min_app_version: str
    update_required: bool
    endpoints: Dict[str, str]


class OfflineAction(BaseModel):
    action_id: str
    action_type: str  # "schedule", "message", "voice_command"
    timestamp: datetime
    data: Dict[str, Any]


class OfflineSyncRequest(BaseModel):
    device_id: str
    last_sync: Optional[datetime]
    actions: List[OfflineAction]


class OfflineSyncResponse(BaseModel):
    synced_count: int
    conflicts: List[Dict[str, Any]]
    server_timestamp: datetime
    next_sync_recommended: datetime


class MobileSessionSync(BaseModel):
    session_id: str
    last_modified: datetime
    data: Dict[str, Any]
