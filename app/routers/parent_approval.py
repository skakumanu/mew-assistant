"""
Parent Approval Router
Endpoints for parents to review and approve/deny kid requests
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..database.models import ApprovalRequest, ApprovalStatus, User
from ..services.approval_service import ApprovalService
from ..utils.auth import get_current_user, verify_parent_account

router = APIRouter(prefix="/parent/approvals", tags=["Parent Approvals"])


class ApprovalResponse(BaseModel):
    """Parent's response to kid request"""

    approved: bool = Field(..., description="Approve or deny the request")
    parent_note: Optional[str] = Field(None, max_length=500, description="Message for your kid")
    alternative_suggestion: Optional[str] = Field(None, max_length=300, description="Alternative suggestion")


class ApprovalRequestDetail(BaseModel):
    """Detailed approval request for display"""

    id: int
    kid_name: str
    kid_emoji: Optional[str]
    request_type: str
    requested_activity: Optional[str]
    requested_time: Optional[str]
    kid_reason: Optional[str]
    status: str
    created_at: str
    expires_at: Optional[str]
    original_activity_name: Optional[str]

    class Config:
        from_attributes = True


@router.get("/pending", response_model=List[ApprovalRequestDetail])
async def get_pending_approvals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get all pending approval requests waiting for parent review.
    Shows requests from all linked kids.
    """
    verify_parent_account(current_user)

    approval_service = ApprovalService(db)
    pending_requests = approval_service.get_pending_requests(current_user.id)

    # Enrich with kid and activity details
    result = []
    for request in pending_requests:
        kid = db.query(User).filter(User.id == request.kid_id).first()

        result.append(
            ApprovalRequestDetail(
                id=request.id,
                kid_name=kid.display_name or kid.username,
                kid_emoji=request.kid_emoji,
                request_type=request.request_type.value,
                requested_activity=request.requested_activity,
                requested_time=request.requested_time,
                kid_reason=request.kid_reason,
                status=request.status.value,
                created_at=request.created_at.isoformat(),
                expires_at=(request.expires_at.isoformat() if request.expires_at else None),
                original_activity_name=None,  # TODO: Fetch from calendar
            )
        )

    return result


@router.post("/{request_id}/approve")
async def approve_request(
    request_id: int,
    response: ApprovalResponse,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Approve a kid's request.
    CRITICAL: Only after approval is the change applied to the calendar.

    The parent can include:
    - A note to the kid explaining the approval
    - An alternative suggestion if modifying the request
    """
    verify_parent_account(current_user)

    if not response.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /deny endpoint to deny requests",
        )

    approval_service = ApprovalService(db)

    # Get client info for audit trail
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    approved_request = approval_service.approve_request(
        request_id=request_id,
        parent_id=current_user.id,
        parent_note=response.parent_note,
        alternative_suggestion=response.alternative_suggestion,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {
        "success": True,
        "message": "Request approved and applied to calendar",
        "request_id": approved_request.id,
        "applied_to_calendar": approved_request.applied_to_calendar,
        "calendar_event_id": approved_request.calendar_event_id,
    }


@router.post("/{request_id}/deny")
async def deny_request(
    request_id: int,
    response: ApprovalResponse,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deny a kid's request.
    No changes are made to the calendar.

    IMPORTANT: Include a kind, explanatory note for the kid.
    Consider providing an alternative suggestion.
    """
    verify_parent_account(current_user)

    if response.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /approve endpoint to approve requests",
        )

    # Require parent note for denials (be kind to kids!)
    if not response.parent_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please include a note explaining why to your kid",
        )

    approval_service = ApprovalService(db)

    # Get client info for audit trail
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    denied_request = approval_service.deny_request(
        request_id=request_id,
        parent_id=current_user.id,
        parent_note=response.parent_note,
        alternative_suggestion=response.alternative_suggestion,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {
        "success": True,
        "message": "Request denied with explanation sent to kid",
        "request_id": denied_request.id,
    }


@router.get("/history")
async def get_approval_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get history of all approval requests (approved, denied, expired).
    Useful for tracking patterns and kid preferences.
    """
    verify_parent_account(current_user)

    requests = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.parent_id == current_user.id)
        .order_by(ApprovalRequest.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for req in requests:
        kid = db.query(User).filter(User.id == req.kid_id).first()
        result.append(
            {
                "id": req.id,
                "kid_name": kid.display_name or kid.username,
                "request_type": req.request_type.value,
                "requested_activity": req.requested_activity,
                "status": req.status.value,
                "created_at": req.created_at.isoformat(),
                "processed_at": (req.processed_at.isoformat() if req.processed_at else None),
                "parent_note": req.parent_note,
                "applied_to_calendar": req.applied_to_calendar,
            }
        )

    return {"total": len(result), "requests": result}


@router.get("/stats")
async def get_approval_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get statistics about approval requests.
    Helps parents understand their kids' patterns and needs.
    """
    verify_parent_account(current_user)

    # Count by status
    pending = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.parent_id == current_user.id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
        .count()
    )

    approved = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.parent_id == current_user.id,
            ApprovalRequest.status == ApprovalStatus.APPROVED,
        )
        .count()
    )

    denied = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.parent_id == current_user.id,
            ApprovalRequest.status == ApprovalStatus.DENIED,
        )
        .count()
    )

    expired = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.parent_id == current_user.id,
            ApprovalRequest.status == ApprovalStatus.EXPIRED,
        )
        .count()
    )

    # Get approval rate
    total_processed = approved + denied
    approval_rate = (approved / total_processed * 100) if total_processed > 0 else 0

    return {
        "pending": pending,
        "approved": approved,
        "denied": denied,
        "expired": expired,
        "total": pending + approved + denied + expired,
        "approval_rate": round(approval_rate, 1),
        "message": "Always consider your kid's perspective! 💙",
    }
