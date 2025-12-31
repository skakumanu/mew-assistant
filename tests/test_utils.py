"""
Unit tests for utility functions.
"""

from app.utils.cooldown import CooldownManager
from app.utils.priority import PriorityManager


def test_cooldown_manager_initialization():
    """Test cooldown manager initializes correctly."""
    manager = CooldownManager()
    assert manager.default_cooldown_hours == 24


def test_cooldown_not_in_cooldown_initially():
    """Test user not in cooldown initially."""
    manager = CooldownManager()
    assert not manager.is_in_cooldown("user_001")


def test_cooldown_activation():
    """Test cooldown activates after recording."""
    manager = CooldownManager()
    manager.record_request("user_001")
    assert manager.is_in_cooldown("user_001")


def test_cooldown_expiration():
    """Test cooldown expires after duration."""
    manager = CooldownManager(default_cooldown_hours=0.0001)  # Very short cooldown
    manager.record_request("user_001")
    import time

    time.sleep(0.5)  # Wait for cooldown to expire
    assert not manager.is_in_cooldown("user_001")


def test_priority_manager_initialization():
    """Test priority manager initializes correctly."""
    manager = PriorityManager()
    assert len(manager.priority_keywords) > 0


def test_priority_detection_urgent():
    """Test urgent priority detection."""
    manager = PriorityManager()
    assert manager.detect_priority("URGENT: Need help immediately!")


def test_priority_detection_emergency():
    """Test emergency priority detection."""
    manager = PriorityManager()
    assert manager.detect_priority("Emergency situation with child")


def test_priority_detection_normal():
    """Test normal message doesn't trigger priority."""
    manager = PriorityManager()
    assert not manager.detect_priority("Can we schedule a tutoring session?")


def test_priority_override_cooldown():
    """Test priority can override cooldown."""
    cooldown_mgr = CooldownManager()
    priority_mgr = PriorityManager()

    user_id = "user_001"
    cooldown_mgr.record_request(user_id)

    # User is in cooldown
    assert cooldown_mgr.is_in_cooldown(user_id)

    # But priority message should be allowed
    urgent_message = "URGENT: Emergency help needed"
    assert priority_mgr.detect_priority(urgent_message)


def test_multiple_users_cooldown():
    """Test cooldown works independently for multiple users."""
    manager = CooldownManager()

    manager.record_request("user_001")
    manager.record_request("user_002")

    assert manager.is_in_cooldown("user_001")
    assert manager.is_in_cooldown("user_002")
    assert not manager.is_in_cooldown("user_003")
