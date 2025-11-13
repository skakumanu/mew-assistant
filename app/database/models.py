"""
Database models for Mew Assistant.
Tracks sessions, messages, and user interactions.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .connection import Base


class ChannelType(str, enum.Enum):
    """Supported communication channels for multi-channel ingestion."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    WEB = "web"


class SessionStatus(str, enum.Enum):
    """Session lifecycle states."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PriorityLevel(str, enum.Enum):
    """Priority levels for session scheduling."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Session(Base):
    """
    Core session tracking table.
    Tracks tutoring, scheduling, and caregiver sessions.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # External user identifier
    session_type = Column(String, nullable=False)  # tutoring, scheduling, caregiver_summary
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING)
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.NORMAL)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Cooldown tracking
    last_interaction = Column(DateTime, default=datetime.utcnow)
    cooldown_until = Column(DateTime, nullable=True)
    
    # Session metadata
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, type={self.session_type}, status={self.status})>"


class Message(Base):
    """
    Multi-channel message ingestion tracking.
    Stores messages from email, SMS, WhatsApp, etc.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    
    # Channel information
    channel = Column(Enum(ChannelType), nullable=False)
    sender = Column(String, nullable=False)  # Email address, phone number, etc.
    recipient = Column(String, nullable=True)
    
    # Message content
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    raw_content = Column(Text, nullable=True)  # Original message for debugging
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, channel={self.channel}, sender={self.sender})>"


class CaregiverSummary(Base):
    """
    Stores generated caregiver summaries.
    Provides insights for special needs families.
    """
    __tablename__ = "caregiver_summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, index=True, nullable=False)
    
    # Summary content
    summary_text = Column(Text, nullable=False)
    key_points = Column(Text, nullable=True)  # JSON-serialized list
    recommendations = Column(Text, nullable=True)  # JSON-serialized list
    
    # Metadata
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CaregiverSummary(id={self.id}, session_id={self.session_id})>"
