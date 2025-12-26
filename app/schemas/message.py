"""
Pydantic schemas for message ingestion.
Validates multi-channel message data (email, SMS, WhatsApp).
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChannelType(str, Enum):
    """Supported communication channels."""

    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    WEB = "web"


class MessageIngest(BaseModel):
    """
    Request schema for ingesting messages from multiple channels.
    Supports email, SMS, and WhatsApp integration.
    """

    channel: ChannelType = Field(..., description="Communication channel")
    sender: str = Field(..., description="Sender identifier (email, phone number)")
    recipient: Optional[str] = Field(None, description="Recipient identifier")
    subject: Optional[str] = Field(
        None, max_length=500, description="Message subject (email only)"
    )
    body: str = Field(..., min_length=1, description="Message body/content")
    raw_content: Optional[str] = Field(
        None, description="Raw message data for debugging"
    )
    session_id: Optional[int] = Field(None, description="Link to existing session")
    received_at: Optional[datetime] = Field(
        None, description="When message was received"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "channel": "email",
                    "sender": "parent@example.com",
                    "recipient": "mew@assistant.com",
                    "subject": "Need tutoring help",
                    "body": "My child needs help with math homework this Thursday.",
                    "session_id": None,
                    "received_at": "2025-11-13T10:00:00Z",
                },
                {
                    "channel": "sms",
                    "sender": "+1234567890",
                    "body": "Can we schedule a session for tomorrow?",
                    "session_id": 42,
                },
                {
                    "channel": "whatsapp",
                    "sender": "+1234567890",
                    "body": "Thank you for the tutoring session!",
                    "session_id": 42,
                },
            ]
        }
    )


class MessageResponse(BaseModel):
    """Response schema for ingested messages."""

    id: int
    session_id: Optional[int]
    channel: str
    sender: str
    recipient: Optional[str]
    subject: Optional[str]
    body: str
    processed: bool
    processed_at: Optional[datetime]
    received_at: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 123,
                "session_id": 42,
                "channel": "email",
                "sender": "parent@example.com",
                "recipient": "mew@assistant.com",
                "subject": "Need tutoring help",
                "body": "My child needs help with math homework.",
                "processed": True,
                "processed_at": "2025-11-13T10:05:00Z",
                "received_at": "2025-11-13T10:00:00Z",
                "created_at": "2025-11-13T10:00:30Z",
            }
        },
    )


class MessageBatchIngest(BaseModel):
    """Request schema for batch message ingestion."""

    messages: list[MessageIngest] = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {
                        "channel": "email",
                        "sender": "parent1@example.com",
                        "body": "Need help with scheduling",
                    },
                    {
                        "channel": "sms",
                        "sender": "+1234567890",
                        "body": "Confirming tomorrow's session",
                    },
                ]
            }
        }
    )
