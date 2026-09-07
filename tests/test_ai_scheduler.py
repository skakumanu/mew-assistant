"""
Tests for AI Scheduler Service
"""

from datetime import datetime

import jwt
import pytest

from app.database.models import ActivityType, PriorityLevel, ScheduleEntry, SessionStatus
from app.services.ai_scheduler_service import AISchedulerService
from app.utils.config import settings


@pytest.mark.asyncio
async def test_detect_conflicts_basic(db_session, test_user):
    """Test basic conflict detection"""
    service = AISchedulerService(db_session)

    # Create existing schedule entry
    existing = ScheduleEntry(
        user_id=test_user.id,
        title="Therapy Session",
        activity_type=ActivityType.THERAPY,
        start_time=datetime(2025, 1, 15, 10, 0),
        end_time=datetime(2025, 1, 15, 11, 0),
        status=SessionStatus.CONFIRMED,
    )
    db_session.add(existing)
    db_session.commit()

    # Propose overlapping entry
    proposed = {
        "start_time": datetime(2025, 1, 15, 10, 30),
        "end_time": datetime(2025, 1, 15, 11, 30),
        "title": "Tutoring",
        "activity_type": "tutoring",
        "priority": "normal",
    }

    conflicts = await service.detect_conflicts(test_user.id, proposed)

    assert len(conflicts) == 1
    assert conflicts[0].conflicting_title == "Therapy Session"
    assert conflicts[0].overlap_minutes == 30
    assert conflicts[0].severity in ["medium", "high"]


@pytest.mark.asyncio
async def test_suggest_optimal_times(db_session, test_user):
    """Test AI-powered time suggestions"""
    service = AISchedulerService(db_session)

    # Create some historical patterns
    for i in range(10):
        entry = ScheduleEntry(
            user_id=test_user.id,
            title=f"Past Therapy {i}",
            activity_type=ActivityType.THERAPY,
            start_time=datetime(2024, 12, i + 1, 10, 0),
            end_time=datetime(2024, 12, i + 1, 11, 0),
            status=SessionStatus.COMPLETED,
            completed_successfully=True,
        )
        db_session.add(entry)
    db_session.commit()

    # Get suggestions
    suggestions = await service.suggest_optimal_times(
        user_id=test_user.id,
        activity_type="therapy",
        duration_minutes=60,
        preferred_date=datetime(2025, 1, 20, 0, 0),
        constraints={"earliest_hour": 8, "latest_hour": 18},
    )

    assert len(suggestions) > 0
    assert all(0 <= s.confidence_score <= 1 for s in suggestions)
    assert all(s.reasoning for s in suggestions)


@pytest.mark.asyncio
async def test_optimize_schedule(db_session, test_user):
    """Test schedule optimization"""
    service = AISchedulerService(db_session)

    # Create a suboptimal schedule
    entries = [
        ScheduleEntry(
            user_id=test_user.id,
            title="Therapy",
            activity_type=ActivityType.THERAPY,
            start_time=datetime(2025, 1, 15, 9, 0),
            end_time=datetime(2025, 1, 15, 10, 0),
            status=SessionStatus.CONFIRMED,
        ),
        ScheduleEntry(
            user_id=test_user.id,
            title="Social Activity",
            activity_type=ActivityType.SOCIAL,
            start_time=datetime(2025, 1, 15, 10, 0),
            end_time=datetime(2025, 1, 15, 11, 0),
            status=SessionStatus.CONFIRMED,
        ),
        ScheduleEntry(
            user_id=test_user.id,
            title="Another Therapy",
            activity_type=ActivityType.THERAPY,
            start_time=datetime(2025, 1, 15, 15, 0),
            end_time=datetime(2025, 1, 15, 16, 0),
            status=SessionStatus.CONFIRMED,
        ),
    ]

    for entry in entries:
        db_session.add(entry)
    db_session.commit()

    # Optimize
    result = await service.optimize_schedule(
        user_id=test_user.id,
        date=datetime(2025, 1, 15),
        optimization_goals=["minimize_transitions", "respect_energy_levels"],
    )

    assert result.improvements
    assert result.efficiency_gain_percent >= 0


@pytest.mark.asyncio
async def test_conflict_severity_calculation(db_session, test_user):
    """Test conflict severity is calculated correctly"""
    service = AISchedulerService(db_session)

    # High priority conflict
    existing = ScheduleEntry(
        user_id=test_user.id,
        title="Critical Medical",
        activity_type=ActivityType.MEDICAL,
        priority=PriorityLevel.URGENT,
        start_time=datetime(2025, 1, 15, 10, 0),
        end_time=datetime(2025, 1, 15, 11, 0),
        status=SessionStatus.CONFIRMED,
    )
    db_session.add(existing)
    db_session.commit()

    proposed = {
        "start_time": datetime(2025, 1, 15, 10, 15),
        "end_time": datetime(2025, 1, 15, 11, 15),
        "title": "Regular Activity",
        "activity_type": "social",
        "priority": "normal",
    }

    conflicts = await service.detect_conflicts(test_user.id, proposed)

    assert len(conflicts) == 1
    assert conflicts[0].severity == "high"


@pytest.mark.asyncio
async def test_no_conflicts_when_no_overlap(db_session, test_user):
    """Test that no conflicts are returned for non-overlapping times"""
    service = AISchedulerService(db_session)

    # Create existing entry
    existing = ScheduleEntry(
        user_id=test_user.id,
        title="Morning Therapy",
        activity_type=ActivityType.THERAPY,
        start_time=datetime(2025, 1, 15, 9, 0),
        end_time=datetime(2025, 1, 15, 10, 0),
        status=SessionStatus.CONFIRMED,
    )
    db_session.add(existing)
    db_session.commit()

    # Propose non-overlapping entry
    proposed = {
        "start_time": datetime(2025, 1, 15, 14, 0),
        "end_time": datetime(2025, 1, 15, 15, 0),
        "title": "Afternoon Tutoring",
        "activity_type": "tutoring",
        "priority": "normal",
    }

    conflicts = await service.detect_conflicts(test_user.id, proposed)

    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_pattern_learning_threshold(db_session, test_user):
    """Test that pattern learning requires minimum data points"""
    service = AISchedulerService(db_session)

    # Create only 2 historical entries (below threshold of 5)
    for i in range(2):
        entry = ScheduleEntry(
            user_id=test_user.id,
            title=f"Therapy {i}",
            activity_type=ActivityType.THERAPY,
            start_time=datetime(2024, 12, i + 1, 10, 0),
            end_time=datetime(2024, 12, i + 1, 11, 0),
            status=SessionStatus.COMPLETED,
        )
        db_session.add(entry)
    db_session.commit()

    patterns = await service._learn_user_patterns(test_user.id, "therapy")

    assert patterns["has_patterns"] is False


def test_a_tampered_bearer_token_is_rejected_with_401_not_500(client, test_user):
    """
    Regression guard for app/middleware/auth.py's get_current_user: a token
    that fails to decode for any reason other than expiry (bad signature,
    here) must return a clean 401, not crash. This dependency previously
    caught `jwt.JWTError` - an exception name from python-jose, not the
    real PyJWT this file actually imports - so any non-expired decode
    failure fell straight through the except clause into an unhandled
    AttributeError (a 500) instead of ever reaching this branch.
    """
    tampered_token = jwt.encode({"sub": test_user.id}, "not-the-real-secret", algorithm=settings.ALGORITHM)

    response = client.post(
        "/ai-scheduler/detect-conflicts",
        json={
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:00:00",
            "title": "Tutoring",
            "activity_type": "tutoring",
        },
        headers={"Authorization": f"Bearer {tampered_token}"},
    )

    assert response.status_code == 401
