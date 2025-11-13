"""
Caregiver summary router.
Handles /mew/summary for generating family insights.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db
from ..schemas.summary import SummaryRequest, SummaryResponse, SummaryList
from ..services.summary_service import SummaryService

router = APIRouter(prefix="/mew", tags=["summaries"])


@router.post("/summary", response_model=SummaryResponse, status_code=status.HTTP_201_CREATED)
async def generate_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a caregiver summary with insights and recommendations.
    
    **Purpose**: Provides special needs families with actionable insights
    about sessions, progress, and next steps.
    
    **Features**:
    - Session activity summary
    - Key points extraction
    - AI-generated recommendations (optional)
    - Custom time period support
    
    **Example Request**:
    ```json
    {
        "user_id": "user_12345",
        "session_id": null,
        "period_start": "2025-11-01T00:00:00Z",
        "period_end": "2025-11-13T23:59:59Z",
        "include_recommendations": true
    }
    ```
    
    **Response includes**:
    - Summary text
    - Key points list
    - Recommendations list
    - Time period covered
    """
    service = SummaryService(db)
    
    try:
        summary = service.generate_summary(request)
        
        # Parse JSON fields for response
        response = SummaryResponse.model_validate(summary)
        
        if summary.key_points:
            response.key_points = json.loads(summary.key_points)
        
        if summary.recommendations:
            response.recommendations = json.loads(summary.recommendations)
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific summary by ID.
    """
    service = SummaryService(db)
    summary = service.get_summary(summary_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail=f"Summary {summary_id} not found")
    
    # Parse JSON fields for response
    response = SummaryResponse.model_validate(summary)
    
    if summary.key_points:
        response.key_points = json.loads(summary.key_points)
    
    if summary.recommendations:
        response.recommendations = json.loads(summary.recommendations)
    
    return response


@router.get("/summaries/user/{user_id}", response_model=SummaryList)
async def get_user_summaries(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all summaries for a user.
    
    **Query Parameters**:
    - limit: Maximum results (default: 50)
    
    **Use Case**: View historical summaries and track progress over time.
    """
    service = SummaryService(db)
    summaries = service.get_user_summaries(user_id, limit)
    
    # Parse JSON fields for each summary
    summary_responses = []
    for summary in summaries:
        response = SummaryResponse.model_validate(summary)
        
        if summary.key_points:
            response.key_points = json.loads(summary.key_points)
        
        if summary.recommendations:
            response.recommendations = json.loads(summary.recommendations)
        
        summary_responses.append(response)
    
    return SummaryList(summaries=summary_responses, total=len(summary_responses))
