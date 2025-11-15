"""
Database models for Mew Assistant.
Tracks sessions, messages, and user interactions.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, ForeignKey, Index
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


class UserRole(str, enum.Enum):
    """User roles for access control"""
    ADMIN = "admin"
    CAREGIVER = "caregiver"
    PARENT = "parent"
    THERAPIST = "therapist"
    EDUCATOR = "educator"


class User(Base):
    """
    User authentication and profile management.
    Supports parents, caregivers, and tutors using Mew Assistant.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
    # User type and status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.PARENT)
    
    # Profile information
    phone = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
    )


class Session(Base):
    """
    Core session tracking table.
    Tracks tutoring, scheduling, and caregiver sessions.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
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
    user = relationship("User", back_populates="sessions")
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
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
    user = relationship("User", back_populates="messages")
    
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


class APIKey(Base):
    """API Key model for external integrations"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)
    
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime)
    
    scopes = Column(Text)  # JSON array of allowed scopes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.key_name}, prefix={self.key_prefix})>"
