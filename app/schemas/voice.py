"""Voice command schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class VoiceCommandCreate(BaseModel):
    """Voice command input"""
    audio_data: bytes = Field(..., description="Audio data in WAV format")
    session_id: Optional[str] = Field(None, description="Conversation session ID")
    preferred_language: Optional[str] = Field(None, description="Preferred language code (e.g., en-US)")


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
                "entities": {
                    "datetime": "2024-01-16T15:00:00",
                    "activity": "therapy"
                },
                "confidence": 0.95,
                "suggested_action": {
                    "type": "create_event",
                    "parameters": {"datetime": "2024-01-16T15:00:00"}
                }
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


class SupportedLanguagesResponse(BaseModel):
    """Supported languages list"""
    languages: Dict[str, str]
    count: int
