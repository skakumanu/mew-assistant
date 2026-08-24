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
from ..schemas.change_request import (
    AlternativeOut,
    ChooseAlternativeIn,
    LogEntryOut,
    PendingRequestOut,
)
from ..services.approval_service import ApprovalService
from ..services.change_request_service import ChangeRequestService
from ..services.presenter import Presenter
from ..utils.auth import get_current_user, verify_parent_account
from ..utils.locale_context import translator_for

router = APIRouter(prefix="/parent/approvals", tags=["Parent Approvals"])


class ApprovalResponse(BaseModel):
    """Parent's response to kid request"""

    approved: bool = Field(..., description="Approve or deny the request")
    parent_note: Optional[str] = Field(None, max_length=500, description="Message for your kid")
    alternative_suggestion: Optional[str] = Field(
        None, max_length=300, description="Alternative suggestion"
    )


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

    # Why the rule engine parked this request, and the compliant slots that
    # would clear it. Codes are stored; the sentences are rendered per reader.
    requested_by: Optional[str] = None
    change_kind: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    alternatives: List[AlternativeOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


@router.get("/pending", response_model=List[ApprovalRequestDetail])
async def get_pending_approvals(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all pending approval requests waiting for parent review.
    Shows requests from all linked kids.
    """
    verify_parent_account(current_user)

    approval_service = ApprovalService(db)
    pending_requests = approval_service.get_pending_requests(current_user.id)

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)

    # Enrich with kid and activity details
    result = []
    for request in pending_requests:
        kid = db.query(User).filter(User.id == request.kid_id).first()

        result.append(
            ApprovalRequestDetail(
                id=request.id,
                kid_name=(kid.display_name or kid.username or kid.email) if kid else "",
                kid_emoji=request.kid_emoji,
                request_type=request.request_type.value,
                requested_activity=request.requested_activity,
                requested_time=request.requested_time,
                kid_reason=request.kid_reason,
                status=request.status.value,
                created_at=request.created_at.isoformat(),
                expires_at=(request.expires_at.isoformat() if request.expires_at else None),
                original_activity_name=None,  # TODO: Fetch from calendar
                requested_by=request.requested_by,
                change_kind=request.change_kind,
                reason_codes=list(request.reason_codes or []),
                alternatives=presenter.alternatives(request.alternatives),
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

    # "Allow their time anyway": the parent overrode a rule, so the schedule
    # moves to exactly what was asked for and the log records who decided.
    if approved_request.scheduled_session_id:
        await ChangeRequestService(db).apply_approved(approved_request, current_user)

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

    # The schedule is untouched, but the parent's log still records the
    # decision so "Handled for you" tells the whole story.
    if denied_request.scheduled_session_id:
        ChangeRequestService(db).record_denied(denied_request, current_user)

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
async def get_approval_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
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


@router.get("/inbox", response_model=List[PendingRequestOut])
async def get_inbox(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    The "Needs you" tab: one card per parked request.

    Each card carries the headline, the detail line, the rule that was not
    satisfied and the three compliant alternatives - everything the parent
    needs to decide in one tap, rendered in their own language.
    """
    verify_parent_account(current_user)

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)

    pending = ApprovalService(db).get_pending_requests(current_user.id)
    return [presenter.pending_request(request) for request in pending]


@router.post("/{request_id}/choose")
async def choose_alternative(
    request_id: int,
    choice: ChooseAlternativeIn,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Approve one of the three compliant alternatives.

    This is the primary path in the design: the parent taps a time that
    already fits their rules, and the requester is told the new time rather
    than being told no.
    """
    verify_parent_account(current_user)

    approval_request = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found"
        )
    if approval_request.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this request",
        )
    if not approval_request.can_approve():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request cannot be approved (expired or already processed)",
        )

    service = ChangeRequestService(db)
    session = await service.choose_alternative(
        approval_request, current_user, choice.alternative_index
    )

    translator = translator_for(request.headers.get("accept-language"), current_user, db)
    return {
        "success": True,
        "request_id": approval_request.id,
        "session_id": session.id,
        "start_utc": session.start_utc.isoformat(),
        "when": translator.when(session.start_utc),
    }


# The quiet log lives outside the approvals prefix: it is not a decision
# surface, it is the record of everything that did not need one.
parent_router = APIRouter(prefix="/parent", tags=["Parent Approvals"])


@parent_router.get("/log", response_model=List[LogEntryOut])
async def get_change_log(
    http_request: Request,
    limit: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    "Handled for you": what changed without the parent having to decide.

    Rows are stored as locale keys plus parameters, so this reads correctly
    in whatever language the parent is using right now.
    """
    verify_parent_account(current_user)

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)

    entries = ChangeRequestService(db).log_for_parent(current_user.id, limit=max(1, min(limit, 50)))
    return [presenter.log_entry(entry) for entry in entries]


@parent_router.get("/week")
async def get_week(
    http_request: Request,
    child_id: Optional[int] = None,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    The Week tab: one heading per day, sessions underneath, empty days named.

    A day with nothing on it says so rather than disappearing, and a session
    that moved carries an "updated" pill so the parent can see at a glance
    what the rules handled for them.
    """
    verify_parent_account(current_user)

    from datetime import datetime, timedelta

    from ..database.models import ScheduledSession

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)

    children = (
        [child_id]
        if child_id
        else [kid.id for kid in db.query(User).filter(User.parent_id == current_user.id).all()]
    )

    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    span = max(1, min(days, 31))
    end = start + timedelta(days=span)

    rows = (
        db.query(ScheduledSession)
        .filter(
            ScheduledSession.child_id.in_(children or [-1]),
            ScheduledSession.is_cancelled.is_(False),
            ScheduledSession.start_utc >= start,
            ScheduledSession.start_utc < end,
        )
        .order_by(ScheduledSession.start_utc.asc())
        .all()
    )

    by_day = {}
    for row in rows:
        by_day.setdefault(row.start_utc.date(), []).append(row)

    out = []
    for offset in range(span):
        day = (start + timedelta(days=offset)).date()
        sessions = by_day.get(day, [])
        out.append(
            {
                "date": day.isoformat(),
                "name": translator.days[day.weekday()],
                "label": translator.date_label(start + timedelta(days=offset)),
                "empty": not sessions,
                "sessions": [
                    {
                        **presenter.session(row).model_dump(mode="json"),
                        "time_label": translator.time(row.start_utc),
                    }
                    for row in sessions
                ],
            }
        )
    return out
