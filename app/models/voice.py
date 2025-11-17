"""Voice command database models"""

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class VoiceCommand(Base):
    """Voice command history"""
    __tablename__ = "voice_commands"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=True)
    transcription = Column(Text, nullable=False)
    detected_language = Column(String(10), nullable=False)
    confidence_score = Column(Float, default=0.0)
    intent = Column(String(50), nullable=True)
    entities = Column(JSON, default={})
    raw_audio_path = Column(String(500), nullable=True)
    processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="voice_commands")


class VoiceSession(Base):
    """Continuous voice conversation session"""
    __tablename__ = "voice_sessions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(10), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    command_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="voice_sessions")
