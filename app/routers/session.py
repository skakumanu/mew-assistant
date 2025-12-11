"""
Session management router.
Handles /mew/confirm and session-related endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionConfirm,
    SessionUpdate
)
from ..services.session_service import SessionService
from ..utils.cooldown import check_cooldown

router = APIRouter(prefix="/mew", tags=["sessions"])


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new session (tutoring, scheduling, or caregiver summary).
    
    **Priority escalation**: Automatically escalates priority during peak hours
    (morning prep, after-school, evening routine).
    
    **Example Request**:
    ```json
    {
        "user_id": "user_12345",
        "session_type": "tutoring",
        "title": "Math homework help",
        "priority": "normal",
        "scheduled_at": "2025-11-15T14:00:00Z"
    }
    ```
    """
    service = SessionService(db)
    
    try:
        session = service.create_session(session_data)
        
        # Add cooldown status to response
        in_cooldown, _ = check_cooldown(session)
        response = SessionResponse.model_validate(session)
        response.in_cooldown = in_cooldown
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm", response_model=SessionResponse)
async def confirm_session(
    confirm_data: SessionConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm a session with cooldown protection.
    
    **Cooldown logic**: Prevents overwhelming families with requests.
    - Normal priority: 24-hour cooldown
    - High priority: 12-hour cooldown
    - Urgent: No cooldown
    
    **Override**: Use `override_cooldown=true` for urgent sessions.
    
    **Example Request**:
    ```json
    {
        "session_id": 42,
        "notes": "Confirmed via phone",
        "override_cooldown": false
    }
    ```
    """
    service = SessionService(db)
    
    try:
        session = service.confirm_session(confirm_data)
        
        # Add cooldown status to response
        in_cooldown, _ = check_cooldown(session)
        response = SessionResponse.model_validate(session)
        response.in_cooldown = in_cooldown
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/session/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    update_data: SessionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update session details.
    
    **Updatable fields**:
    - status (pending, confirmed, active, completed, cancelled)
    - priority (low, normal, high, urgent)
    - title, description, notes
    - scheduled_at
    """
    service = SessionService(db)
    
    try:
        session = service.update_session(session_id, update_data)
        
        in_cooldown, _ = check_cooldown(session)
        response = SessionResponse.model_validate(session)
        response.in_cooldown = in_cooldown
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get session details by ID.
    """
    service = SessionService(db)
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    in_cooldown, _ = check_cooldown(session)
    response = SessionResponse.model_validate(session)
    response.in_cooldown = in_cooldown
    
    return response


@router.get("/sessions/user/{user_id}", response_model=List[SessionResponse])
async def get_user_sessions(
    user_id: str,
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all sessions for a user.
    
    **Query Parameters**:
    - status: Filter by status (optional)
    - limit: Maximum results (default: 100)
    """
    service = SessionService(db)
    
    # Convert status string to enum if provided
    status_filter = None
    if status:
        from ..database.models import SessionStatus
        try:
            status_filter = SessionStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    sessions = service.get_user_sessions(user_id, status_filter, limit)
    
    # Add cooldown status to each session
    responses = []
    for session in sessions:
        in_cooldown, _ = check_cooldown(session)
        response = SessionResponse.model_validate(session)
        response.in_cooldown = in_cooldown
        responses.append(response)
    
    return responses
