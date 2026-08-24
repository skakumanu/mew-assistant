"""
Database models for Mew Assistant.
Tracks sessions, messages, and user interactions.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship

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
    """User roles for access control with RBAC hierarchy"""

    SUPERUSER = "SUPERUSER"  # Full system access
    ADMIN = "ADMIN"  # Organization-level access
    PARENT = "PARENT"  # Family-level access
    CAREGIVER = "CAREGIVER"  # Limited family access
    KID = "KID"  # Minimal access with approval requirements
    THERAPIST = "THERAPIST"  # Professional access
    EDUCATOR = "EDUCATOR"  # Educational access


class User(Base):
    """
    User authentication and profile management.
    Supports parents, caregivers, and tutors using Mew Assistant.
    """

    def __init__(self, **kwargs):
        """Allow initialization with keyword arguments"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for federated auth users
    full_name = Column(String, nullable=True)

    # User type and status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.PARENT)

    # Profile information
    phone = Column(String, nullable=True)
    timezone = Column(String, default="UTC")

    # Kid-friendly features
    is_kid_account = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    display_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    avatar_emoji = Column(String, default="😊")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    federated_identities = relationship(
        "FederatedIdentity", back_populates="user", cascade="all, delete-orphan"
    )
    kids = relationship("User", backref="parent", remote_side=[id])

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
    )


class FederatedIdentity(Base):
    """
    Federated authentication identities (Google, Apple, Microsoft, etc.)
    Allows users to login with their existing accounts.
    """

    __tablename__ = "federated_identities"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)  # google, apple, microsoft, etc.
    provider_user_id = Column(String, nullable=False)
    email = Column(String, nullable=False)

    # Optional profile data from provider
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)

    # OAuth tokens for API access
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="federated_identities")

    __table_args__ = (Index("idx_provider_user", "provider", "provider_user_id", unique=True),)


class Session(Base):
    """
    Core session tracking table.
    Tracks tutoring, scheduling, and caregiver sessions.
    """

    __tablename__ = "sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    session_type = Column(
        String, nullable=False, default="generic", server_default="generic"
    )  # tutoring, scheduling, caregiver_summary
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING)
    action_type = Column(String, nullable=True)
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
    __table_args__ = {"extend_existing": True}

    def __init__(self, **kwargs):
        # Accept legacy `content` kw arg used across tests and map it to `body`.
        if "content" in kwargs:
            kwargs["body"] = kwargs.pop("content")
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True, index=True)

    # Channel information
    channel = Column(Enum(ChannelType), nullable=False)
    sender = Column(String, nullable=False)  # Email address, phone number, etc.
    recipient = Column(String, nullable=True)

    # Message content
    message_id = Column(String, unique=True, index=True, nullable=True)
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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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
    """
    Parent approval required for all kid requests.
    CRITICAL: No schedule changes are applied until parent approves.
    """

    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    kid_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Request details
    request_type = Column(Enum(RequestType), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)

    # What the kid wants
    original_activity_id = Column(Integer, nullable=True)
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
    expires_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    # Applied to calendar - ONLY after parent approval
    applied_to_calendar = Column(Boolean, default=False)
    calendar_event_id = Column(String(255), nullable=True)

    # --- three-persona scheduling ---------------------------------------
    # A request is raised by a kid, a provider or the parent themselves, and
    # is parked here ONLY when the deterministic rule engine rejected it.
    requested_by = Column(String(20), default="kid", nullable=True)  # RequestedBy
    provider_org_id = Column(Integer, ForeignKey("provider_orgs.id"), nullable=True)
    change_kind = Column(String(20), nullable=True)  # move | cancel | swap_provider
    scheduled_session_id = Column(Integer, ForeignKey("scheduled_sessions.id"), nullable=True)
    new_start_utc = Column(DateTime, nullable=True)
    new_provider_person_id = Column(Integer, ForeignKey("provider_people.id"), nullable=True)

    # Codes, never sentences: the reader's locale renders them.
    reason_codes = Column(JSON, nullable=True)
    # Up to three compliant slots, closest first: [{"start": iso, "rank": 0}, ...]
    alternatives = Column(JSON, nullable=True)

    auto_applied = Column(Boolean, default=False)
    chosen_alternative_index = Column(Integer, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("idx_approval_kid_status", "kid_id", "status"),
        Index("idx_approval_parent_status", "parent_id", "status"),
        {"extend_existing": True},
    )

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

    # Relationship to audit logs for easy access in tests
    audit_logs = relationship(
        "ApprovalAuditLog", backref="approval_request", cascade="all, delete-orphan"
    )


class ApprovalAuditLog(Base):
    """Audit trail for all approval actions - compliance requirement"""

    __tablename__ = "approval_audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(Integer, ForeignKey("approval_requests.id"), nullable=False)

    action = Column(String(50), nullable=False)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)


class VoiceCommand(Base):
    """Voice command tracking for multi-language voice interactions"""

    __tablename__ = "voice_commands"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=True)

    audio_file_path = Column(String(500), nullable=True)
    transcribed_text = Column(Text, nullable=True)
    detected_language = Column(String(10), nullable=True)
    confidence_score = Column(Integer, nullable=True)

    intent = Column(String(100), nullable=True)
    response_text = Column(Text, nullable=True)
    response_audio_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)


class VoiceSession(Base):
    """Voice session management for continuous conversations"""

    __tablename__ = "voice_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    platform = Column(String(50), nullable=True)
    preferred_language = Column(String(10), nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class Family(Base):
    """Family unit for grouping users"""

    __tablename__ = "families"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    primary_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    language_preference = Column(String(10), default="en", nullable=False)


class ApprovalRule(Base):
    """Smart approval rules for automated decision making"""

    __tablename__ = "approval_rules"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)

    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)
    conditions = Column(Text, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)


class ActivityType(str, enum.Enum):
    """Types of activities for scheduling"""

    THERAPY = "therapy"
    TUTORING = "tutoring"
    MEDICAL = "medical"
    SOCIAL = "social"
    EXERCISE = "exercise"
    MEAL = "meal"
    SLEEP = "sleep"
    OTHER = "other"


class ScheduleEntry(Base):
    """
    Schedule entries for calendar management and AI scheduling.
    Supports conflict detection, pattern learning, and optimization.
    """

    __tablename__ = "schedule_entries"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Entry details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    activity_type = Column(Enum(ActivityType), default=ActivityType.OTHER, nullable=False)

    # Time
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    all_day = Column(Boolean, default=False)

    # Priority and status
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.NORMAL, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING, nullable=False)

    # Location and participants
    location = Column(String(255), nullable=True)
    participants = Column(Text, nullable=True)  # JSON array

    # External calendar integration
    external_calendar_id = Column(String(255), nullable=True)
    external_event_id = Column(String(255), nullable=True)
    calendar_provider = Column(String(50), nullable=True)  # google, apple, outlook

    # Completion tracking for pattern learning
    completed_successfully = Column(Boolean, nullable=True)
    completion_notes = Column(Text, nullable=True)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(Text, nullable=True)  # iCal RRULE format
    parent_recurrence_id = Column(Integer, ForeignKey("schedule_entries.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("idx_schedule_user_time", "user_id", "start_time"),
        Index("idx_schedule_type_status", "activity_type", "status"),
        {"extend_existing": True},
    )

    def requires_same_location(self, other) -> bool:
        """Check if entry requires same location as another"""
        return self.location and other.get("location") == self.location

    def involves_same_person(self, other) -> bool:
        """Check if entry involves same person as another"""
        # Placeholder - would parse participants JSON
        return False


class UserPreference(Base):
    """
    User preferences for AI scheduling and pattern learning
    """

    __tablename__ = "user_preferences"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Scheduling preferences
    allow_overlap_for_therapy = Column(Boolean, default=False)
    buffer_minutes = Column(Integer, default=15)
    earliest_schedule_hour = Column(Integer, default=7)
    latest_schedule_hour = Column(Integer, default=22)

    # Energy patterns
    peak_energy_hours = Column(Text, nullable=True)  # JSON array of hours
    low_energy_hours = Column(Text, nullable=True)  # JSON array of hours

    # Activity preferences
    preferred_therapy_days = Column(Text, nullable=True)  # JSON array of weekdays
    preferred_tutoring_times = Column(Text, nullable=True)  # JSON object

    # Optimization goals
    minimize_transitions = Column(Boolean, default=True)
    respect_energy_levels = Column(Boolean, default=True)
    balance_activities = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProfile(Base):
    """
    Extended user profile for AI personalization
    """

    __tablename__ = "user_profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Demographics
    date_of_birth = Column(DateTime, nullable=True)
    special_needs_info = Column(Text, nullable=True)  # Encrypted sensitive data

    # Contacts
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)

    # Preferences
    communication_preferences = Column(Text, nullable=True)  # JSON
    notification_preferences = Column(Text, nullable=True)  # JSON

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OAuthProvider(Base):
    """
    OAuth provider links for federated authentication
    Tracks Google, Apple, Microsoft, Facebook login connections
    """

    __tablename__ = "oauth_providers"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Provider information
    provider = Column(String(50), nullable=False)  # google, apple, microsoft, facebook
    provider_user_id = Column(String(255), nullable=False)  # User ID from provider

    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="oauth_providers")

    __table_args__ = (
        Index("idx_oauth_user_provider", "user_id", "provider"),
        Index("idx_oauth_provider_user", "provider", "provider_user_id"),
        {"extend_existing": True},
    )


# ---------------------------------------------------------------------------
# Three-persona scheduling (parent / kid / service provider)
#
# The parent declares rules once. The kid and the provider propose changes
# through a single write path. Anything that satisfies every active rule is
# applied immediately and recorded in a quiet log; anything that does not
# reaches the parent as one card with three compliant alternatives attached.
#
# See app/services/rule_engine.py for the deterministic evaluator and
# app/services/change_request_service.py for the loop itself.
# ---------------------------------------------------------------------------


# "Parent" and "guardian" are interchangeable throughout: same person, same
# permissions, same routes. A family picks the word they use; the stored
# value is always "parent" so nothing downstream has to know which.
CAREGIVER_TERMS = ("parent", "guardian")
DEFAULT_CAREGIVER_TERM = "parent"


class ProviderKind(str, enum.Enum):
    """What kind of service an organisation delivers."""

    ABA = "aba"
    SPEECH = "speech"
    OT = "ot"
    SCHOOL = "school"
    TRANSPORT = "transport"
    OTHER = "other"


class SessionSource(str, enum.Enum):
    """Where a scheduled session came from."""

    CALENDAR = "calendar"
    MANUAL = "manual"


class RequestedBy(str, enum.Enum):
    """
    Which persona raised a change request.

    "parent" and "guardian" are the same persona under two names. Plenty of
    children are raised by a grandparent, a foster carer or a legal guardian,
    so both words are accepted everywhere and stored as ``parent``; which one
    a family reads is ``RuleSet.caregiver_term``.
    """

    KID = "kid"
    PROVIDER = "provider"
    PARENT = "parent"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str) and value.strip().lower() in CAREGIVER_TERMS:
            return cls.PARENT
        return None


class ChangeKind(str, enum.Enum):
    """The three things a kid or provider can ask for."""

    MOVE = "move"
    CANCEL = "cancel"
    SWAP_PROVIDER = "swap_provider"


class LogTone(str, enum.Enum):
    """Whether a log row happened on its own or because a parent decided."""

    AUTO = "auto"
    MANUAL = "manual"


class ProviderOrg(Base):
    """A service organisation: an ABA clinic, a speech practice, a school."""

    __tablename__ = "provider_orgs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    kind = Column(String(20), default=ProviderKind.OTHER.value, nullable=False)

    # The calendar the org already works in - no portal login is introduced.
    calendar_provider = Column(String(50), nullable=True)  # google/microsoft/apple/calendly/ics
    calendar_account_id = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    people = relationship("ProviderPerson", back_populates="org", cascade="all, delete-orphan")


class ProviderPerson(Base):
    """An individual therapist inside a provider organisation."""

    __tablename__ = "provider_people"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("provider_orgs.id"), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)

    # Optional link to a login, for providers who sign in to Mew directly.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    org = relationship("ProviderOrg", back_populates="people")


class ScheduledSession(Base):
    """
    A session on the child's schedule.

    Named ``ScheduledSession`` rather than ``Session`` because this module
    already carries a ``Session`` model for assistant conversations, and
    ``sqlalchemy.orm.Session`` is imported all over the service layer.
    """

    __tablename__ = "scheduled_sessions"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider_org_id = Column(Integer, ForeignKey("provider_orgs.id"), nullable=True)
    provider_person_id = Column(Integer, ForeignKey("provider_people.id"), nullable=True)

    title = Column(String(200), nullable=False)
    activity_type = Column(String(50), default="other", nullable=False)

    start_utc = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60, nullable=False)
    location = Column(String(255), nullable=True)

    source = Column(String(20), default=SessionSource.CALENDAR.value, nullable=False)
    external_event_id = Column(String(255), nullable=True)

    is_cancelled = Column(Boolean, default=False, nullable=False)
    # Drives the "updated" pill in the parent's week view.
    last_changed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    org = relationship("ProviderOrg")
    person = relationship("ProviderPerson")

    __table_args__ = (
        Index("idx_scheduled_session_child_start", "child_id", "start_utc"),
        {"extend_existing": True},
    )


class RuleSet(Base):
    """
    The parent's declared defaults for one child.

    Every nullable field is an inactive rule - that is exactly how the six
    toggles in the parent's Rules tab work.
    """

    __tablename__ = "rule_sets"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    timezone = Column(String(64), default="America/Chicago", nullable=False)

    min_notice_hours = Column(Integer, nullable=True, default=24)
    earliest_start = Column(Time, nullable=True)
    latest_end = Column(Time, nullable=True)
    require_same_provider_person = Column(Boolean, default=True, nullable=False)
    buffer_minutes = Column(Integer, nullable=True, default=45)
    cancellation_needs_approval = Column(Boolean, default=True, nullable=False)
    allowed_weekdays = Column(JSON, nullable=True)  # [0..6], Mon=0. None = any day

    # Parent notification is a preference, not part of the rule evaluation.
    notify_on_auto_approve = Column(Boolean, default=True, nullable=False)

    # Which of the two interchangeable words this family reads: "parent" or
    # "guardian". It changes the label, never the permissions or the routes.
    caregiver_term = Column(String(20), default=DEFAULT_CAREGIVER_TERM, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    protected_blocks = relationship(
        "ProtectedBlock", back_populates="ruleset", cascade="all, delete-orphan"
    )
    weekly_caps = relationship("WeeklyCap", back_populates="ruleset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ruleset_parent_child", "parent_id", "child_id"),
        {"extend_existing": True},
    )


class ProtectedBlock(Base):
    """A daily window that may never be overlapped: meals, meds, nap, prayer."""

    __tablename__ = "protected_blocks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    ruleset_id = Column(Integer, ForeignKey("rule_sets.id"), nullable=False, index=True)

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    weekdays = Column(JSON, nullable=True)  # None = every day
    # A locale key, never a sentence: "block.midday" resolves per reader.
    label_key = Column(String(100), default="block.custom", nullable=False)

    ruleset = relationship("RuleSet", back_populates="protected_blocks")


class WeeklyCap(Base):
    """At most N sessions of one activity type per ISO week."""

    __tablename__ = "weekly_caps"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    ruleset_id = Column(Integer, ForeignKey("rule_sets.id"), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)
    max_sessions = Column(Integer, nullable=False)

    ruleset = relationship("RuleSet", back_populates="weekly_caps")


class ChangeLogEntry(Base):
    """
    The quiet log the parent reads under "Handled for you".

    Stores a locale KEY plus parameters, never a rendered sentence, so the
    same entry reads correctly for a parent in Spanish and a provider in
    English.
    """

    __tablename__ = "change_log_entries"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_request_id = Column(Integer, ForeignKey("approval_requests.id"), nullable=True)

    text_key = Column(String(100), nullable=False)  # e.g. "parent.log_moved"
    params = Column(JSON, nullable=True)  # {"title": ..., "when": ...}
    meta_key = Column(String(100), nullable=True)  # e.g. "parent.meta_auto"
    meta_params = Column(JSON, nullable=True)
    tone = Column(String(10), default=LogTone.AUTO.value, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_change_log_parent_created", "parent_id", "created_at"),
        {"extend_existing": True},
    )


class UserLocale(Base):
    """
    Per-person UI locale.

    Resolved from the device (``Accept-Language``) unless the person picked
    one explicitly; ``source`` records which. Never inferred from the content
    of a message.
    """

    __tablename__ = "user_locales"
    __table_args__ = {"extend_existing": True}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    locale = Column(String(16), default="en", nullable=False)
    dir = Column(String(3), default="ltr", nullable=False)
    clock = Column(String(3), default="12h", nullable=False)
    source = Column(String(10), default="device", nullable=False)  # device | explicit
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationKind(str, enum.Enum):
    """Why a notification exists. Never a bare ping - each carries a sentence."""

    AUTO_APPLIED = "auto_applied"  # a change cleared the rules on its own
    NEEDS_YOU = "needs_you"  # a request is waiting on the caregiver
    OUTCOME = "outcome"  # the answer, back to whoever asked


class Notification(Base):
    """
    A durable, readable notification.

    Stored rather than fired-and-forgotten, for two reasons the design is
    explicit about:

      * "Kid outcome messaging must survive the session moving off today" -
        a child who was not looking at the screen when the answer arrived
        must still find it, phrased the same way, whenever they next look.
      * Nothing is announced in a single channel. The row holds a locale KEY
        plus parameters, so the push, the email and the screen all say the
        same sentence, and a chime is never the only signal.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approval_request_id = Column(Integer, ForeignKey("approval_requests.id"), nullable=True)
    scheduled_session_id = Column(Integer, ForeignKey("scheduled_sessions.id"), nullable=True)

    kind = Column(String(20), nullable=False)
    text_key = Column(String(100), nullable=False)
    params = Column(JSON, nullable=True)

    # Which channels actually accepted it, e.g. ["in_app", "email"]. In-app
    # is always present: the row itself is the in-app delivery.
    delivered_channels = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_notification_recipient_created", "recipient_id", "created_at"),
        {"extend_existing": True},
    )
