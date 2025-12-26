"""
Cooldown detection logic for Mew Assistant.
Prevents overwhelming families with too many requests.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from ..database.models import PriorityLevel, Session


class CooldownManager:
    """Manages cooldown periods for users."""

    def __init__(self, default_cooldown_hours: int = 24):
        """Initialize cooldown manager."""
        self.default_cooldown_hours = default_cooldown_hours
        self.cooldowns: Dict[str, datetime] = {}

    def is_in_cooldown(self, user_id: str) -> bool:
        """Check if user is in cooldown period."""
        if user_id not in self.cooldowns:
            return False
        return datetime.utcnow() < self.cooldowns[user_id]

    def record_request(self, user_id: str):
        """Record a request and start cooldown period."""
        self.cooldowns[user_id] = datetime.utcnow() + timedelta(
            hours=self.default_cooldown_hours
        )

    def get_cooldown_until(self, user_id: str) -> Optional[datetime]:
        """Get when cooldown ends for user."""
        return self.cooldowns.get(user_id)


class CooldownDetector:
    """Detects and manages cooldown periods."""

    def __init__(self):
        """Initialize cooldown detector."""
        self.manager = CooldownManager()

    def check(self, user_id: str) -> Tuple[bool, Optional[datetime]]:
        """Check if user is in cooldown."""
        in_cooldown = self.manager.is_in_cooldown(user_id)
        until = self.manager.get_cooldown_until(user_id) if in_cooldown else None
        return in_cooldown, until

    # Backwards-compatible alias expected by tests
    def check_cooldown(
        self, user_id: str, messages: Optional[list] = None
    ) -> Tuple[bool, Optional[datetime]]:
        """Alias for `check` that matches older test expectations.

        `messages` parameter is accepted for compatibility but ignored
        by this simple implementation.
        """
        return self.check(user_id)


def check_cooldown(session: Session) -> Tuple[bool, Optional[datetime]]:
    """
    Check if a session is in cooldown period.

    Args:
        session: Session object to check

    Returns:
        Tuple of (is_in_cooldown, cooldown_until)

    Example:
        >>> in_cooldown, until = check_cooldown(session)
        >>> if in_cooldown:
        ...     print(f"Please wait until {until}")
    """
    if not session.cooldown_until:
        return False, None

    now = datetime.utcnow()
    if now < session.cooldown_until:
        return True, session.cooldown_until

    return False, None


def set_cooldown(session: Session, hours: int = 24) -> datetime:
    """
    Set cooldown period for a session.

    Args:
        session: Session object to set cooldown for
        hours: Number of hours for cooldown (default 24)

    Returns:
        Datetime when cooldown expires

    Example:
        >>> cooldown_until = set_cooldown(session, hours=12)
    """
    cooldown_until = datetime.utcnow() + timedelta(hours=hours)
    session.cooldown_until = cooldown_until
    session.last_interaction = datetime.utcnow()
    return cooldown_until


def can_override_cooldown(
    session: Session, priority: Optional[PriorityLevel] = None
) -> bool:
    """
    Check if cooldown can be overridden based on priority.

    Args:
        session: Session object
        priority: Priority level to check (uses session priority if None)

    Returns:
        True if cooldown can be overridden

    Example:
        >>> if can_override_cooldown(session, PriorityLevel.URGENT):
        ...     session.cooldown_until = None
    """
    check_priority = priority or session.priority

    # URGENT and HIGH priority can always override cooldown
    if check_priority in [PriorityLevel.URGENT, PriorityLevel.HIGH]:
        return True

    return False


def calculate_cooldown_duration(session_type: str, priority: PriorityLevel) -> int:
    """
    Calculate appropriate cooldown duration based on session type and priority.

    Args:
        session_type: Type of session
        priority: Priority level

    Returns:
        Cooldown duration in hours

    Example:
        >>> hours = calculate_cooldown_duration("tutoring", PriorityLevel.NORMAL)
        >>> # Returns 24 hours for normal priority tutoring
    """
    # Base cooldown by session type (in hours)
    base_cooldown = {
        "tutoring": 24,
        "scheduling": 12,
        "caregiver_summary": 48,
    }

    # Priority modifiers
    priority_modifiers = {
        PriorityLevel.LOW: 1.5,  # Longer cooldown
        PriorityLevel.NORMAL: 1.0,  # Normal cooldown
        PriorityLevel.HIGH: 0.5,  # Shorter cooldown
        PriorityLevel.URGENT: 0.0,  # No cooldown
    }

    base = base_cooldown.get(session_type, 24)
    modifier = priority_modifiers.get(priority, 1.0)

    return int(base * modifier)


def reset_cooldown(session: Session) -> None:
    """
    Reset/clear cooldown for a session.

    Args:
        session: Session object to reset cooldown for

    Example:
        >>> reset_cooldown(session)  # Clears cooldown_until field
    """
    session.cooldown_until = None
