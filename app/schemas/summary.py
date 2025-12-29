"""
Pydantic schemas for caregiver summaries.
Validates summary generation requests and responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SummaryRequest(BaseModel):
    """
    Request schema for generating caregiver summaries.
    Provides insights for special needs families.
    """

    user_id: str = Field(..., description="User identifier")
    session_id: Optional[int] = Field(None, description="Specific session to summarize")
    period_start: Optional[datetime] = Field(None, description="Summary period start")
    period_end: Optional[datetime] = Field(None, description="Summary period end")
    include_recommendations: bool = Field(
        default=True, description="Include AI-generated recommendations"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_12345",
                "session_id": None,
                "period_start": "2025-11-01T00:00:00Z",
                "period_end": "2025-11-13T23:59:59Z",
                "include_recommendations": True,
            }
        }
    )


class SummaryResponse(BaseModel):
    """Response schema for caregiver summaries."""

    id: int
    session_id: int
    user_id: str
    summary_text: str
    key_points: Optional[List[str]] = Field(default=None, description="Key highlights")
    recommendations: Optional[List[str]] = Field(
        default=None, description="AI recommendations"
    )
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    generated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "session_id": 42,
                "user_id": "user_12345",
                "summary_text": (
                    "This week included 3 tutoring sessions focusing on mathematics and "
                    "reading comprehension. Student showed significant improvement in "
                    "algebra."
                ),
                "key_points": [
                    "3 tutoring sessions completed",
                    "Math: Improved algebra understanding",
                    "Reading: Working on comprehension strategies",
                ],
                "recommendations": [
                    "Continue daily math practice for 15 minutes",
                    "Introduce visual aids for reading comprehension",
                    "Schedule follow-up session next week",
                ],
                "period_start": "2025-11-01T00:00:00Z",
                "period_end": "2025-11-13T23:59:59Z",
                "generated_at": "2025-11-13T10:00:00Z",
            }
        },
    )


class SummaryList(BaseModel):
    """Response schema for listing multiple summaries."""

    summaries: List[SummaryResponse]
    total: int

    model_config = ConfigDict(
        json_schema_extra={"example": {"summaries": [], "total": 0}}
    )
