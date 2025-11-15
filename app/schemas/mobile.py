"""
Mobile Schemas
Pydantic models for mobile device integration
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.integrations.mobile_integration import MobilePlatform


class DeviceRegistrationRequest(BaseModel):
    """Request model for registering a mobile device"""
    platform: MobilePlatform = Field(..., description="Mobile platform (ios or android)")
    device_token: str = Field(..., min_length=10, description="Device push notification token")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Additional device information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "ios",
                "device_token": "abc123def456...",
                "device_info": {
                    "model": "iPhone 14 Pro",
                    "os_version": "17.1",
                    "app_version": "1.0.0"
                }
            }
        }


class DeviceRegistrationResponse(BaseModel):
    """Response model for device registration"""
    success: bool
    platform: MobilePlatform
    message: str


class PushNotificationRequest(BaseModel):
    """Request model for sending a push notification"""
    platform: MobilePlatform = Field(..., description="Mobile platform")
    device_token: str = Field(..., description="Device push notification token")
    title: str = Field(..., min_length=1, max_length=100, description="Notification title")
    body: str = Field(..., min_length=1, max_length=500, description="Notification body")
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
                "data": {
                    "session_id": "12345",
                    "type": "reminder"
                },
                "badge": 1,
                "sound": "default"
            }
        }


class PushNotificationResponse(BaseModel):
    """Response model for push notification"""
    success: bool
    message: str


class BatchNotificationRequest(BaseModel):
    """Request model for sending batch notifications"""
    platform: MobilePlatform = Field(..., description="Mobile platform")
    device_tokens: List[str] = Field(..., min_items=1, description="List of device tokens")
    title: str = Field(..., min_length=1, max_length=100, description="Notification title")
    body: str = Field(..., min_length=1, max_length=500, description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "android",
                "device_tokens": ["token1", "token2", "token3"],
                "title": "System Update",
                "body": "New features are now available",
                "data": {"update_version": "2.0.0"}
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
                "params": {
                    "session_id": "12345",
                    "user_id": "67890"
                }
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
    platform: MobilePlatform = Field(..., description="Mobile platform")
    device_token: str = Field(..., description="Device push notification token")
    title: str = Field(..., min_length=1, max_length=100, description="Notification title")
    body: str = Field(..., min_length=1, max_length=500, description="Notification body")
    scheduled_time: str = Field(..., description="ISO format datetime string for scheduled delivery")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "ios",
                "device_token": "abc123def456...",
                "title": "Daily Medication Reminder",
                "body": "Time to take your morning medication",
                "scheduled_time": "2024-01-15T08:00:00Z",
                "data": {"medication_id": "med_123"}
            }
        }


class ScheduledReminderResponse(BaseModel):
    """Response model for scheduled reminder"""
    success: bool
    scheduled_time: str
    message: str
