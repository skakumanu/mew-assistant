"""
Priority period override logic for Mew Assistant.
Handles special time periods and escalation rules.
"""
from datetime import datetime, time
from typing import List, Tuple
from ..database.models import PriorityLevel


class PriorityManager:
    """Manages priority levels and overrides."""
    
    def __init__(self):
        """Initialize priority manager."""
        self.priority_overrides = {}
        # simple keyword-based detector used by tests
        self.priority_keywords = [
            'urgent', 'emergency', 'help', 'asap', 'critical', 'immediately', 'need help'
        ]
    
    def set_priority(self, session_id: str, priority: PriorityLevel):
        """Set priority level for a session."""
        self.priority_overrides[session_id] = priority
    
    def get_priority(self, session_id: str) -> PriorityLevel:
        """Get priority level for a session."""
        return self.priority_overrides.get(session_id, PriorityLevel.NORMAL)
    
    def can_override_cooldown(self, session_id: str) -> bool:
        """Check if session can override cooldown."""
        priority = self.get_priority(session_id)
        return priority in [PriorityLevel.HIGH, PriorityLevel.URGENT]

    def detect_priority(self, message: str) -> bool:
        """Detect whether a message should be treated as high priority.

        Simple case-insensitive keyword matching for unit tests.
        """
        if not message:
            return False
        msg = message.lower()
        for kw in self.priority_keywords:
            if kw in msg:
                return True
        return False


# Priority time windows (start_time, end_time) in 24-hour format
PRIORITY_PERIODS = [
    (time(7, 0), time(9, 0)),    # Morning school prep: 7am-9am
    (time(15, 0), time(18, 0)),  # After-school: 3pm-6pm
    (time(19, 0), time(21, 0)),  # Evening routine: 7pm-9pm
]


def is_priority_period(check_time: datetime = None) -> Tuple[bool, str]:
    """
    Check if current time falls within a priority period.
    
    Args:
        check_time: Time to check (defaults to now)
        
    Returns:
        Tuple of (is_priority, period_name)
        
    Example:
        >>> is_priority, period = is_priority_period()
        >>> if is_priority:
        ...     print(f"Priority period: {period}")
    """
    if check_time is None:
        check_time = datetime.utcnow()
    
    current_time = check_time.time()
    
    for start, end in PRIORITY_PERIODS:
        if start <= current_time <= end:
            if start == time(7, 0):
                return True, "morning_prep"
            elif start == time(15, 0):
                return True, "after_school"
            elif start == time(19, 0):
                return True, "evening_routine"
    
    return False, ""


def should_escalate_priority(
    current_priority: PriorityLevel,
    session_type: str,
    check_time: datetime = None
) -> Tuple[bool, PriorityLevel]:
    """
    Determine if session priority should be escalated based on time and type.
    
    Args:
        current_priority: Current priority level
        session_type: Type of session
        check_time: Time to check (defaults to now)
        
    Returns:
        Tuple of (should_escalate, new_priority)
        
    Example:
        >>> should_escalate, new_priority = should_escalate_priority(
        ...     PriorityLevel.NORMAL, "tutoring"
        ... )
    """
    is_priority, period = is_priority_period(check_time)
    
    # Don't escalate URGENT or HIGH priority
    if current_priority in [PriorityLevel.URGENT, PriorityLevel.HIGH]:
        return False, current_priority
    
    # During priority periods, escalate tutoring and scheduling
    if is_priority and session_type in ["tutoring", "scheduling"]:
        if current_priority == PriorityLevel.LOW:
            return True, PriorityLevel.NORMAL
        elif current_priority == PriorityLevel.NORMAL:
            return True, PriorityLevel.HIGH
    
    return False, current_priority


def get_priority_window_info() -> List[dict]:
    """
    Get information about all priority time windows.
    
    Returns:
        List of dictionaries with priority window details
        
    Example:
        >>> windows = get_priority_window_info()
        >>> for window in windows:
        ...     print(f"{window['name']}: {window['start']}-{window['end']}")
    """
    windows = [
        {
            "name": "morning_prep",
            "description": "Morning school preparation",
            "start": "07:00",
            "end": "09:00"
        },
        {
            "name": "after_school",
            "description": "After-school activities",
            "start": "15:00",
            "end": "18:00"
        },
        {
            "name": "evening_routine",
            "description": "Evening routine and homework",
            "start": "19:00",
            "end": "21:00"
        }
    ]
    return windows


def is_weekend(check_time: datetime = None) -> bool:
    """
    Check if given time falls on weekend (Saturday or Sunday).
    
    Args:
        check_time: Time to check (defaults to now)
        
    Returns:
        True if weekend
        
    Example:
        >>> if is_weekend():
        ...     # Apply weekend scheduling rules
    """
    if check_time is None:
        check_time = datetime.utcnow()
    
    return check_time.weekday() >= 5  # 5=Saturday, 6=Sunday
