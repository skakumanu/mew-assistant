"""
Session service layer for business logic.
Handles session creation, confirmation, and lifecycle management.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..database.models import Session as SessionModel
from ..database.models import SessionStatus
from ..schemas.session import SessionConfirm, SessionCreate, SessionUpdate
from ..utils.cooldown import (
    calculate_cooldown_duration,
    can_override_cooldown,
    check_cooldown,
    reset_cooldown,
    set_cooldown,
)
from ..utils.priority import should_escalate_priority


class SessionService:
    """Service class for session management operations."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    def create_session(self, session_data: SessionCreate) -> SessionModel:
        """
        Create a new session with cooldown and priority logic.

        Args:
            session_data: Session creation data

        Returns:
            Created session object

        Example:
            >>> service = SessionService(db)
            >>> session = service.create_session(session_data)
        """
        # Check for priority escalation
        should_escalate, new_priority = should_escalate_priority(
            session_data.priority, session_data.session_type.value
        )

        if should_escalate:
            priority = new_priority
        else:
            priority = session_data.priority

        # Create session
        db_session = SessionModel(
            user_id=session_data.user_id,
            session_type=session_data.session_type.value,
            title=session_data.title,
            description=session_data.description,
            priority=priority,
            scheduled_at=session_data.scheduled_at,
            status=SessionStatus.PENDING,
        )

        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)

        return db_session

    def confirm_session(self, confirm_data: SessionConfirm) -> SessionModel:
        """
        Confirm a session with cooldown checks.

        Args:
            confirm_data: Session confirmation data

        Returns:
            Confirmed session object

        Raises:
            ValueError: If session not found or already confirmed
            PermissionError: If session is in cooldown and override not allowed
        """
        session = (
            self.db.query(SessionModel).filter(SessionModel.id == confirm_data.session_id).first()
        )

        if not session:
            raise ValueError(f"Session {confirm_data.session_id} not found")

        if session.status == SessionStatus.CONFIRMED:
            raise ValueError(f"Session {confirm_data.session_id} already confirmed")

        # Check cooldown
        in_cooldown, cooldown_until = check_cooldown(session)

        if in_cooldown:
            # Check if override is allowed
            if confirm_data.override_cooldown and can_override_cooldown(session):
                reset_cooldown(session)
            else:
                raise PermissionError(
                    f"Session in cooldown until {cooldown_until}. "
                    "Use override_cooldown=true for urgent sessions."
                )

        # Confirm session
        session.status = SessionStatus.CONFIRMED
        session.confirmed_at = datetime.utcnow()

        if confirm_data.notes:
            session.notes = confirm_data.notes

        # Set cooldown for future requests
        cooldown_hours = calculate_cooldown_duration(session.session_type, session.priority)
        if cooldown_hours > 0:
            set_cooldown(session, hours=cooldown_hours)

        self.db.commit()
        self.db.refresh(session)

        return session

    def update_session(self, session_id: int, update_data: SessionUpdate) -> SessionModel:
        """
        Update session details.

        Args:
            session_id: Session ID to update
            update_data: Update data

        Returns:
            Updated session object
        """
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update fields if provided
        if update_data.status:
            session.status = update_data.status
            if update_data.status == SessionStatus.COMPLETED:
                session.completed_at = datetime.utcnow()

        if update_data.priority:
            session.priority = update_data.priority

        if update_data.title is not None:
            session.title = update_data.title

        if update_data.description is not None:
            session.description = update_data.description

        if update_data.notes is not None:
            session.notes = update_data.notes

        if update_data.scheduled_at is not None:
            session.scheduled_at = update_data.scheduled_at

        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session(self, session_id: int) -> Optional[SessionModel]:
        """Get session by ID."""
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def get_user_sessions(
        self, user_id: str, status: Optional[SessionStatus] = None, limit: int = 100
    ) -> List[SessionModel]:
        """
        Get sessions for a user with optional status filter.

        Args:
            user_id: User identifier
            status: Optional status filter
            limit: Maximum number of sessions to return

        Returns:
            List of sessions
        """
        query = self.db.query(SessionModel).filter(SessionModel.user_id == user_id)

        if status:
            query = query.filter(SessionModel.status == status)

        return query.order_by(SessionModel.created_at.desc()).limit(limit).all()
