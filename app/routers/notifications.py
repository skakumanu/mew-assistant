"""
What you were told, and can still read.

Notifications are stored, not fired and forgotten. A child who was not
looking at the screen when the answer arrived finds it here, phrased the
same way, whenever they next look - which is what the design means by an
outcome surviving the session moving off today.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..database.models import Notification, User
from ..services.notification_delivery import NotificationDelivery
from ..utils.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationOut(BaseModel):
    """One notification, rendered in the reader's own language."""

    id: int
    kind: str
    text: str
    created_at: datetime
    read: bool
    session_id: Optional[int] = None
    request_id: Optional[int] = None


@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    http_request: Request,
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Everything you have been told, newest first.

    Sentences are rendered now rather than when they were stored, so someone
    who changes language reads their whole history in the new one.
    """
    service = NotificationDelivery(db)
    return [
        NotificationOut(
            id=row.id,
            kind=row.kind,
            text=service.render(row, current_user),
            created_at=row.created_at,
            read=row.read_at is not None,
            session_id=row.scheduled_session_id,
            request_id=row.approval_request_id,
        )
        for row in service.for_user(current_user, limit=limit, unread_only=unread_only)
    ]


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Mark one notification read. Only your own."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.recipient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification")

    NotificationDelivery(db).mark_read(notification)
    return {"success": True, "id": notification.id}
