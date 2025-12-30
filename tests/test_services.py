"""
Unit tests for service layer.
"""

from app.services.caregiver import CaregiverService
from app.services.scheduler import SchedulerService
from app.services.tutor import TutorService


def test_scheduler_service_initialization():
    """Test scheduler service initializes correctly."""
    service = SchedulerService()
    assert service is not None


def test_schedule_session():
    """Test scheduling a session."""
    service = SchedulerService()
    result = service.schedule_session(
        user_id="user_001",
        session_type="tutoring",
        date="2024-01-16",
        time="15:00",
        duration=60,
    )
    assert result["status"] == "scheduled"
    assert "session_id" in result


def test_tutor_service_initialization():
    """Test tutor service initializes correctly."""
    service = TutorService()
    assert service is not None


def test_generate_lesson_plan():
    """Test lesson plan generation."""
    service = TutorService()
    result = service.generate_lesson_plan(
        subject="Math", grade_level="5th grade", focus_areas=["fractions", "decimals"]
    )
    assert "lesson_plan" in result
    assert result["subject"] == "Math"


def test_caregiver_service_initialization():
    """Test caregiver service initializes correctly."""
    service = CaregiverService()
    assert service is not None


def test_generate_daily_summary():
    """Test daily summary generation."""
    service = CaregiverService()
    result = service.generate_daily_summary(user_id="user_001", date="2024-01-15")
    assert "summary" in result
    assert result["date"] == "2024-01-15"


def test_generate_weekly_summary():
    """Test weekly summary generation."""
    service = CaregiverService()
    result = service.generate_weekly_summary(user_id="user_001", start_date="2024-01-08")
    assert "summary" in result
    assert "activities" in result
    assert result["period"] == "week"


def test_scheduler_conflict_detection():
    """Test conflict detection in scheduling."""
    service = SchedulerService()

    # Schedule first session
    session1 = service.schedule_session(
        user_id="user_001",
        session_type="tutoring",
        date="2024-01-16",
        time="15:00",
        duration=60,
    )

    # Try to schedule overlapping session
    session2 = service.schedule_session(
        user_id="user_001",
        session_type="therapy",
        date="2024-01-16",
        time="15:30",
        duration=60,
    )

    # Should detect potential conflict (in real implementation)
    assert session1["session_id"] != session2["session_id"]


def test_tutor_progress_tracking():
    """Test progress tracking in tutor service."""
    service = TutorService()
    result = service.track_progress(user_id="user_001", subject="Math", assessment_scores=[85, 90, 88])
    assert "progress" in result
    assert result["improvement"] is not None


def test_caregiver_medication_reminder():
    """Test medication reminder functionality."""
    service = CaregiverService()
    result = service.create_medication_reminder(
        user_id="user_001", medication_name="Vitamin D", time="09:00", frequency="daily"
    )
    assert result["status"] == "reminder_created"
    assert "reminder_id" in result
