"""
AI Scheduler Router
Endpoints for AI-powered scheduling features
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.database.models import User
from app.middleware.auth import get_current_user
from app.schemas.schedule import (
    ConflictDetectionRequest,
    OptimizationResult,
    ScheduleConflict,
    ScheduleOptimizationRequest,
    ScheduleSuggestion,
    ScheduleSuggestionRequest,
)
from app.services.ai_scheduler_service import AISchedulerService

router = APIRouter(prefix="/ai-scheduler", tags=["AI Scheduler"])


@router.post("/detect-conflicts", response_model=List[ScheduleConflict])
async def detect_conflicts(
    request: ConflictDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Detect scheduling conflicts for a proposed entry

    Returns list of conflicts with severity and resolution suggestions
    """
    service = AISchedulerService(db)

    proposed_entry = {
        "start_time": request.start_time,
        "end_time": request.end_time,
        "title": request.title,
        "activity_type": request.activity_type,
        "priority": request.priority,
    }

    conflicts = await service.detect_conflicts(current_user.id, proposed_entry)

    return conflicts


@router.post("/suggest-times", response_model=List[ScheduleSuggestion])
async def suggest_optimal_times(
    request: ScheduleSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get AI-powered suggestions for optimal scheduling times

    Returns top 5 suggested time slots with confidence scores and reasoning
    """
    service = AISchedulerService(db)

    suggestions = await service.suggest_optimal_times(
        user_id=current_user.id,
        activity_type=request.activity_type,
        duration_minutes=request.duration_minutes,
        preferred_date=request.preferred_date,
        constraints=request.constraints,
    )

    return suggestions


@router.post("/optimize-schedule", response_model=OptimizationResult)
async def optimize_schedule(
    request: ScheduleOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Optimize entire day's schedule based on specified goals

    Goals can include:
    - minimize_transitions: Reduce travel and context switching
    - respect_energy_levels: Schedule based on user's energy patterns
    - balance_activities: Balance different activity types throughout day
    """
    service = AISchedulerService(db)

    result = await service.optimize_schedule(
        user_id=current_user.id,
        date=request.date,
        optimization_goals=request.optimization_goals,
    )

    return result


@router.get("/learning-status")
async def get_learning_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get status of AI learning from user patterns

    Shows how much data has been collected and which patterns are available
    """
    service = AISchedulerService(db)

    # Get pattern status for common activities
    activity_types = ["therapy", "tutoring", "medical", "social"]
    status = {}

    for activity in activity_types:
        patterns = await service._learn_user_patterns(current_user.id, activity)
        status[activity] = {
            "has_patterns": patterns.get("has_patterns", False),
            "data_points": (
                patterns.get("data_points", 0) if patterns.get("has_patterns") else 0
            ),
        }

    return {
        "user_id": current_user.id,
        "learning_status": status,
        "recommendation": (
            "Continue using Mew to improve scheduling suggestions"
            if not any(s["has_patterns"] for s in status.values())
            else "AI is learning your patterns and can provide personalized suggestions"
        ),
    }
