"""
User and Family Models - Multi-channel Registration Support
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class User(Base):
    """
    User model with multi-channel registration support
    Supports: email, phone, social login, voice registration
    """
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    email = Column(String, unique=True, nullable=True, index=True)
    phone = Column(String, unique=True, nullable=True, index=True)
    full_name = Column(String, nullable=True)
    
    # Authentication
    hashed_password = Column(String, nullable=True)  # Optional - supports passwordless
    auth_provider = Column(String, nullable=True)  # google, apple, microsoft, etc.
    auth_provider_id = Column(String, nullable=True)
    
    # Verification
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # Profile
    role = Column(String, default="parent")  # parent, child, caregiver
    age = Column(Integer, nullable=True)  # For child accounts
    
    # Preferences
    language_preference = Column(String, default="en")
    timezone = Column(String, default="UTC")
    
    # Status
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    
    # Relationships
    family_id = Column(Integer, ForeignKey("families.id"), nullable=True)
    family = relationship("Family", back_populates="members")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Multi-channel tracking
    registration_channel = Column(String, nullable=True)  # email, phone, voice, social
    device_ids = Column(JSON, default=list)  # Track registered devices
    voice_profile = Column(JSON, nullable=True)  # Voice biometric data (optional)


class Family(Base):
    """
    Family group for managing schedules and approvals
    """
    __tablename__ = "families"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="My Family")
    
    # Primary account holder
    primary_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Settings
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")
    settings = Column(JSON, default=dict)  # Family-specific preferences
    
    # Relationships
    members = relationship("User", back_populates="family")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
