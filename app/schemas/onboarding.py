"""
Onboarding Schemas - Easy Registration Data Models
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class QuickRegistrationRequest(BaseModel):
    """Quick registration from any channel"""
    channel: str = Field(
        ...,
        description="Registration channel: email, phone, sms, voice, siri, alexa, grok, whatsapp"
    )
    identifier: str = Field(
        ...,
        description="Email, phone number, or device ID"
    )
    name: Optional[str] = Field(None, description="User's name (optional)")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context (language, timezone, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "channel": "email",
                "identifier": "parent@example.com",
                "name": "Jane Smith",
                "metadata": {
                    "language": "en",
                    "timezone": "America/New_York",
                    "source": "mobile_app"
                }
            }
        }


class MagicLinkRequest(BaseModel):
    """Verify magic link or code"""
    magic_token: str = Field(..., description="Magic link token or SMS code")
    additional_info: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Any additional info to complete profile"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "magic_token": "abc123xyz789",
                "additional_info": {
                    "timezone": "America/Los_Angeles",
                    "language": "en"
                }
            }
        }


class VoiceRegistrationRequest(BaseModel):
    """Voice-initiated registration"""
    platform: str = Field(
        ...,
        description="Voice platform: siri, alexa, grok, google_assistant, etc."
    )
    device_id: str = Field(..., description="Unique device identifier")
    voice_print: Optional[str] = Field(None, description="Voice biometric (optional)")
    language: str = Field(default="en", description="Detected language code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "siri",
                "device_id": "iPhone-12345",
                "language": "en"
            }
        }


class SocialLoginRequest(BaseModel):
    """Social login (Google, Apple, Microsoft)"""
    provider: str = Field(
        ...,
        description="OAuth provider: google, apple, microsoft, facebook"
    )
    provider_user_id: str = Field(..., description="User ID from provider")
    email: EmailStr = Field(..., description="Email from social provider")
    name: str = Field(..., description="Full name from social provider")
    profile_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional profile data (photo, locale, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "google",
                "provider_user_id": "google_12345",
                "email": "user@gmail.com",
                "name": "John Doe",
                "profile_data": {
                    "picture": "https://...",
                    "locale": "en-US"
                }
            }
        }


class FamilySetupRequest(BaseModel):
    """Quick family setup"""
    user_id: int = Field(..., description="User ID completing setup")
    family_data: Dict[str, Any] = Field(
        ...,
        description="Family configuration"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "family_data": {
                    "name": "The Smith Family",
                    "timezone": "America/New_York",
                    "language": "en",
                    "notifications": {
                        "email": True,
                        "sms": True,
                        "push": True
                    }
                }
            }
        }


class OnboardingResponse(BaseModel):
    """Unified onboarding response"""
    status: str = Field(
        ...,
        description="Status: pending, success, existing_user, recognized, etc."
    )
    message: str = Field(..., description="Human-readable message")
    user_id: Optional[int] = None
    family_id: Optional[int] = None
    next_step: Optional[str] = Field(
        None,
        description="Next onboarding step: family_setup, verify_email, etc."
    )
    access_token: Optional[str] = None
    magic_token: Optional[str] = None
    voice_code: Optional[str] = None
    voice_response: Optional[str] = Field(
        None,
        description="Text for voice assistants to speak"
    )
    expires_in: Optional[int] = Field(
        None,
        description="Token expiration in seconds"
    )
    requires_setup: Optional[bool] = None
    quick_actions: Optional[List[str]] = Field(
        None,
        description="Suggested next actions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Welcome to Mew! Let's set up your family.",
                "user_id": 1,
                "next_step": "family_setup",
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "quick_actions": [
                    "Add family members",
                    "Connect calendar",
                    "Enable voice commands"
                ]
            }
        }


class OnboardingStatusResponse(BaseModel):
    """Onboarding status check"""
    user_id: int
    onboarding_completed: bool
    steps_remaining: List[str] = Field(
        default_factory=list,
        description="List of incomplete steps"
    )
    estimated_time: str = Field(
        default="2 minutes",
        description="Estimated time to complete"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "onboarding_completed": False,
                "steps_remaining": ["family_setup", "connect_calendar"],
                "estimated_time": "2 minutes"
            }
        }
