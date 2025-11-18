"""Schedule-related Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class ScheduleConflict(BaseModel):
    """Detected schedule conflict"""
    conflicting_entry_id: int
    conflicting_title: str
    conflict_type: str = Field(
        ...,
        description="Type of conflict: time_overlap, duplicate_activity, location_conflict, person_unavailable"
    )
    severity: str = Field(..., description="Conflict severity: low, medium, high")
    overlap_minutes: int
    suggestions: List[str] = Field(default_factory=list)


class ScheduleSuggestion(BaseModel):
    """AI-generated schedule suggestion"""
    start_time: datetime
    end_time: datetime
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    reasoning: str
    factors: List[str] = Field(default_factory=list)


class OptimizationResult(BaseModel):
    """Schedule optimization result"""
    original_schedule: List[Dict]
    optimized_schedule: List[Dict]
    improvements: List[str]
    efficiency_gain_percent: float


class ConflictDetectionRequest(BaseModel):
    """Request for conflict detection"""
    start_time: datetime
    end_time: datetime
    title: str
    activity_type: str
    priority: Optional[str] = "normal"


class ScheduleSuggestionRequest(BaseModel):
    """Request for schedule suggestions"""
    activity_type: str
    duration_minutes: int
    preferred_date: datetime
    constraints: Optional[Dict] = None


class ScheduleOptimizationRequest(BaseModel):
    """Request for schedule optimization"""
    date: datetime
    optimization_goals: List[str] = Field(
        default_factory=lambda: ['minimize_transitions', 'respect_energy_levels']
    )
