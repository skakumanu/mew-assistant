"""
Pydantic models for voice platform integrations
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class VoicePlatformRequest(BaseModel):
    """Base voice platform request"""
    platform: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


class VoicePlatformResponse(BaseModel):
    """Base voice platform response"""
    platform: str
    success: bool
    response: str
    data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class SiriRequest(BaseModel):
    """Apple Siri/SiriKit request"""
    intent: str
    slots: Dict[str, Any]
    user_id: str
    device_type: Optional[str] = None  # iPhone, iPad, HomePod, Watch
    interaction_id: Optional[str] = None


class AlexaRequest(BaseModel):
    """Amazon Alexa skill request"""
    version: str = "1.0"
    session: Dict[str, Any]
    request: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class GoogleAssistantRequest(BaseModel):
    """Google Assistant action request"""
    user: Dict[str, Any]
    conversation: Dict[str, Any]
    inputs: List[Dict[str, Any]]
    surface: Optional[Dict[str, Any]] = None
    availableSurfaces: Optional[List[Dict[str, Any]]] = None


class TeslaRequest(BaseModel):
    """Tesla voice command request"""
    vehicle_id: str
    user_id: str
    command: str
    parameters: Dict[str, Any]
    location: Optional[Dict[str, float]] = None  # lat, lon
    driving: bool = False
