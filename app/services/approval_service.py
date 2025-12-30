"""
Parental Approval Service
Handles all kid requests that require parent approval before execution
CRITICAL: All schedule changes from kids MUST go through this service
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..database.models import (
    ApprovalAuditLog,
    ApprovalRequest,
    ApprovalStatus,
    RequestType,
    User,
)
from ..services.calendar_service import CalendarService
from ..services.notification_service import NotificationService


class ApprovalService:
    """
    Central service for managing parental approval workflow.
    Ensures no kid requests are executed without parent authorization.
    """

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.calendar_service = CalendarService(db)

    def create_approval_request(
        self,
        kid_id: int,
        parent_id: int,
        request_type: RequestType,
        activity_id: Optional[int] = None,
        requested_activity: Optional[str] = None,
        requested_time: Optional[str] = None,
        reason: Optional[str] = None,
        emoji: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        Create a new approval request from a kid.
        Request is in PENDING status and awaits parent approval.
        """
        # Verify kid account
        kid = self.db.query(User).filter(User.id == kid_id).first()
        if not kid or not kid.is_kid_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid kid account"
            )

        # Verify parent relationship
        if kid.parent_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Parent relationship not verified",
            )

        # Create approval request
        approval_request = ApprovalRequest(
            kid_id=kid_id,
            parent_id=parent_id,
            request_type=request_type,
            status=ApprovalStatus.PENDING,
            original_activity_id=activity_id,
            requested_activity=requested_activity,
            requested_time=requested_time,
            kid_reason=reason,
            kid_emoji=emoji,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),  # Auto-expire after 24h
        )

        self.db.add(approval_request)
        self.db.commit()
        self.db.refresh(approval_request)

        # Create audit log
        self._log_action(
            approval_request_id=approval_request.id,
            action="created",
            performed_by=kid_id,
            notes=f"Kid requested: {request_type.value}",
        )

        # Notify parent immediately
        parent = self.db.query(User).filter(User.id == parent_id).first()
        self.notification_service.notify_parent_approval_needed(
            parent=parent,
            kid_name=kid.display_name or kid.username,
            request=approval_request,
        )

        return approval_request

    def approve_request(
        self,
        request_id: int,
        parent_id: int,
        parent_note: Optional[str] = None,
        alternative_suggestion: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        Parent approves the kid's request.
        ONLY after approval is the change applied to the calendar.
        """
        approval_request = self._get_and_validate_request(request_id, parent_id)

        if not approval_request.can_approve():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request cannot be approved (expired or already processed)",
            )

        # Update approval status
        old_status = approval_request.status
        approval_request.status = ApprovalStatus.APPROVED
        approval_request.parent_approved = True
        approval_request.parent_note = parent_note
        approval_request.parent_alternative = alternative_suggestion
        approval_request.approved_at = datetime.utcnow()
        approval_request.processed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(approval_request)

        # Create audit log
        self._log_action(
            approval_request_id=request_id,
            action="approved",
            performed_by=parent_id,
            old_status=old_status.value,
            new_status=ApprovalStatus.APPROVED.value,
            notes=parent_note,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Apply to calendar ONLY after approval
        try:
            self._apply_to_calendar(approval_request)
        except Exception as e:
            # Log error but don't fail the approval
            self._log_action(
                approval_request_id=request_id,
                action="calendar_sync_failed",
                performed_by=parent_id,
                notes=f"Error applying to calendar: {str(e)}",
            )

        # Notify kid of approval
        kid = self.db.query(User).filter(User.id == approval_request.kid_id).first()
        self.notification_service.notify_kid_request_approved(
            kid=kid, request=approval_request, parent_note=parent_note
        )

        return approval_request

    def deny_request(
        self,
        request_id: int,
        parent_id: int,
        parent_note: Optional[str] = None,
        alternative_suggestion: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        Parent denies the kid's request.
        No changes are made to the calendar.
        """
        approval_request = self._get_and_validate_request(request_id, parent_id)

        if not approval_request.can_approve():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request cannot be denied (expired or already processed)",
            )

        # Update denial status
        old_status = approval_request.status
        approval_request.status = ApprovalStatus.DENIED
        approval_request.parent_approved = False
        approval_request.parent_note = parent_note
        approval_request.parent_alternative = alternative_suggestion
        approval_request.processed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(approval_request)

        # Create audit log
        self._log_action(
            approval_request_id=request_id,
            action="denied",
            performed_by=parent_id,
            old_status=old_status.value,
            new_status=ApprovalStatus.DENIED.value,
            notes=parent_note,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Notify kid with kind message
        kid = self.db.query(User).filter(User.id == approval_request.kid_id).first()
        self.notification_service.notify_kid_request_denied(
            kid=kid,
            request=approval_request,
            parent_note=parent_note,
            alternative=alternative_suggestion,
        )

        return approval_request

    def get_pending_requests(self, parent_id: int) -> List[ApprovalRequest]:
        """Get all pending approval requests for a parent"""
        return (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.parent_id == parent_id,
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .order_by(ApprovalRequest.created_at.desc())
            .all()
        )

    def get_kid_requests(self, kid_id: int, limit: int = 50) -> List[ApprovalRequest]:
        """Get request history for a kid"""
        return (
            self.db.query(ApprovalRequest)
            .filter(ApprovalRequest.kid_id == kid_id)
            .order_by(ApprovalRequest.created_at.desc())
            .limit(limit)
            .all()
        )

    def expire_old_requests(self) -> int:
        """
        Background job: Expire requests older than 24 hours.
        Returns count of expired requests.
        """
        expired_count = 0
        pending_requests = (
            self.db.query(ApprovalRequest)
            .filter(ApprovalRequest.status == ApprovalStatus.PENDING)
            .all()
        )

        for request in pending_requests:
            if request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                request.processed_at = datetime.utcnow()

                self._log_action(
                    approval_request_id=request.id,
                    action="expired",
                    performed_by=request.parent_id,
                    old_status=ApprovalStatus.PENDING.value,
                    new_status=ApprovalStatus.EXPIRED.value,
                    notes="Auto-expired after 24 hours",
                )

                expired_count += 1

        if expired_count > 0:
            self.db.commit()

        return expired_count

    def _get_and_validate_request(
        self, request_id: int, parent_id: int
    ) -> ApprovalRequest:
        """Get approval request and validate parent access"""
        approval_request = (
            self.db.query(ApprovalRequest)
            .filter(ApprovalRequest.id == request_id)
            .first()
        )

        if not approval_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval request not found",
            )

        if approval_request.parent_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to process this request",
            )

        return approval_request

    def _apply_to_calendar(self, approval_request: ApprovalRequest):
        """
        Apply approved request to calendar.
        CRITICAL: Only called after parent approval.
        """
        if approval_request.request_type == RequestType.NEW_EVENT:
            event_id = self.calendar_service.create_event(
                user_id=approval_request.parent_id,
                title=approval_request.requested_activity,
                time=approval_request.requested_time,
                notes=f"Requested by kid: {approval_request.kid_reason}",
            )
            approval_request.calendar_event_id = event_id
            approval_request.applied_to_calendar = True

        elif approval_request.request_type == RequestType.SCHEDULE_CHANGE:
            if approval_request.original_activity_id:
                self.calendar_service.update_event(
                    event_id=approval_request.original_activity_id,
                    updates={
                        "time": approval_request.requested_time,
                        "notes": f"Changed by kid request: {approval_request.kid_reason}",
                    },
                )
                approval_request.applied_to_calendar = True

        elif approval_request.request_type == RequestType.SKIP_ACTIVITY:
            if approval_request.original_activity_id:
                self.calendar_service.cancel_event(
                    event_id=approval_request.original_activity_id,
                    reason=f"Kid requested skip: {approval_request.kid_reason}",
                )
                approval_request.applied_to_calendar = True

        self.db.commit()

    def _log_action(
        self,
        approval_request_id: int,
        action: str,
        performed_by: int,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Create audit log entry for compliance"""
        audit_log = ApprovalAuditLog(
            approval_request_id=approval_request_id,
            action=action,
            performed_by=performed_by,
            timestamp=datetime.utcnow(),
            old_status=old_status,
            new_status=new_status,
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        self.db.commit()
