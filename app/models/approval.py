"""
Parent Approval Models
Tracks all requests from kids that require parent approval
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class ApprovalStatus(str, enum.Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class RequestType(str, enum.Enum):
    """Types of requests that need approval"""
    SCHEDULE_CHANGE = "schedule_change"
    ACTIVITY_SUGGESTION = "activity_suggestion"
    SKIP_ACTIVITY = "skip_activity"
    TIME_CHANGE = "time_change"
    NEW_EVENT = "new_event"


class ApprovalRequest(Base):
    """Parent approval required for all kid requests"""
    __tablename__ = "approval_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    kid_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Request details
    request_type = Column(Enum(RequestType), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    
    # What the kid wants
    original_activity_id = Column(Integer, nullable=True)  # If changing existing activity
    requested_activity = Column(String(200), nullable=True)
    requested_time = Column(String(100), nullable=True)
    kid_reason = Column(Text, nullable=True)
    kid_emoji = Column(String(10), nullable=True)
    
    # Parent response
    parent_approved = Column(Boolean, nullable=True)
    parent_note = Column(Text, nullable=True)
    parent_alternative = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Auto-expire after 24 hours
    processed_at = Column(DateTime, nullable=True)
    
    # Applied to calendar
    applied_to_calendar = Column(Boolean, default=False)
    calendar_event_id = Column(String(255), nullable=True)
    
    # Relationships
    kid = relationship("User", foreign_keys=[kid_id], backref="approval_requests_sent")
    parent = relationship("User", foreign_keys=[parent_id], backref="approval_requests_received")
    
    def is_expired(self) -> bool:
        """Check if request has expired"""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False
    
    def can_approve(self) -> bool:
        """Check if request can still be approved"""
        return (
            self.status == ApprovalStatus.PENDING 
            and not self.is_expired()
            and not self.applied_to_calendar
        )


class ApprovalAuditLog(Base):
    """Audit trail for all approval actions"""
    __tablename__ = "approval_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(Integer, ForeignKey("approval_requests.id"), nullable=False)
    
    action = Column(String(50), nullable=False)  # created, approved, denied, expired, applied
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    approval_request = relationship("ApprovalRequest", backref="audit_logs")
    user = relationship("User")
