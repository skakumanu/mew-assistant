"""Voice command schemas"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VoiceCommandCreate(BaseModel):
    """Voice command input"""

    audio_data: bytes = Field(..., description="Audio data in WAV format")
    session_id: Optional[str] = Field(None, description="Conversation session ID")
    preferred_language: Optional[str] = Field(
        None, description="Preferred language code (e.g., en-US)"
    )


class VoiceCommandResponse(BaseModel):
    """Voice command processing result"""

    success: bool
    command_id: Optional[int] = None
    transcription: Optional[str] = None
    detected_language: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    suggested_action: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "command_id": 123,
                "transcription": "Schedule therapy session for tomorrow at 3pm",
                "detected_language": "en-US",
                "intent": "schedule",
                "entities": {"datetime": "2024-01-16T15:00:00", "activity": "therapy"},
                "confidence": 0.95,
                "suggested_action": {
                    "type": "create_event",
                    "parameters": {"datetime": "2024-01-16T15:00:00"},
                },
            }
        }


class VoiceSessionCreate(BaseModel):
    """Start voice session"""

    language: Optional[str] = Field("en-US", description="Preferred language")


class VoiceSessionResponse(BaseModel):
    """Voice session info"""

    session_id: str
    user_id: int
    language: str
    started_at: datetime
    command_count: int

    class Config:
        from_attributes = True


class VoiceLanguageInfo(BaseModel):
    """Information about a supported language"""

    code: str = Field(..., description="Language code (e.g., en-US, es-ES)")
    name: str = Field(..., description="Language name (e.g., English, Spanish)")

    class Config:
        json_schema_extra = {
            "example": {"code": "en-US", "name": "English (United States)"}
        }


class SupportedLanguagesResponse(BaseModel):
    """Supported languages list"""

    languages: Dict[str, str]
    count: int


class VoiceCommandRequest(BaseModel):
    """Request model for voice command processing"""

    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    language: Optional[str] = Field(None, description="Expected language code")

    class Config:
        json_schema_extra = {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10...",
                "session_id": "session_123",
                "language": "en-US",
            }
        }


class VoiceTranscription(BaseModel):
    """Voice transcription result"""

    text: str
    language: str
    confidence: float = 1.0


class VoiceStatisticsResponse(BaseModel):
    """Voice command statistics"""

    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    languages_used: Dict[str, int] = {}
    avg_confidence: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "total_commands": 150,
                "successful_commands": 145,
                "failed_commands": 5,
                "languages_used": {"en-US": 100, "es-ES": 50},
                "avg_confidence": 0.92,
            }
        }
