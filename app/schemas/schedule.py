"""Schedule-related Pydantic schemas"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """Create a new schedule entry"""

    title: str
    start_time: datetime
    end_time: datetime
    user_id: int
    location: Optional[str] = None
    activity_type: Optional[str] = None
    priority: Optional[str] = "normal"


class ScheduleConflict(BaseModel):
    """Detected schedule conflict"""

    type: str = Field(
        ...,
        description="Type of conflict: time_overlap, insufficient_break, insufficient_travel_time",
    )
    schedule1_id: int
    schedule2_id: int
    message: str
    severity: str = Field(..., description="Conflict severity: low, medium, high")
    suggested_resolution: str
    conflicting_entry_id: Optional[int] = None
    conflicting_title: Optional[str] = None
    conflict_type: Optional[str] = None
    overlap_minutes: Optional[int] = None
    suggestions: List[str] = Field(default_factory=list)


class ScheduleSuggestion(BaseModel):
    """AI-generated schedule suggestion"""

    start_time: datetime
    end_time: datetime
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    reason: str
    reasoning: Optional[str] = None
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
    optimization_goals: List[str] = Field(default_factory=lambda: ["minimize_transitions", "respect_energy_levels"])
