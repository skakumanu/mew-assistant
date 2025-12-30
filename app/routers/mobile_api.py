"""
Mobile API Router
Optimized endpoints for iOS and Android mobile apps
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.database.models import User
from app.middleware.auth import get_current_user
from app.schemas.mobile import (
    AppConfigResponse,
    MobileDeviceRegister,
    MobileDeviceResponse,
    OfflineSyncRequest,
    OfflineSyncResponse,
    PushNotificationRequest,
)
from app.services.mobile_service import MobileService

router = APIRouter(prefix="/mobile", tags=["mobile"])
logger = logging.getLogger(__name__)


@router.post("/device/register", response_model=MobileDeviceResponse)
async def register_mobile_device(
    device_info: MobileDeviceRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a mobile device for push notifications and sync

    Supports:
    - iOS (APNS)
    - Android (FCM)
    - Device fingerprinting for security
    - Push notification tokens
    """
    service = MobileService(db)
    return await service.register_device(current_user.id, device_info)


@router.get("/config", response_model=AppConfigResponse)
async def get_mobile_config(
    app_version: str,
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get mobile app configuration

    Returns:
    - Feature flags
    - API endpoints
    - Update requirements
    - Sync intervals
    """
    service = MobileService(db)
    return await service.get_app_config(app_version, platform, current_user.id)


@router.post("/sync", response_model=OfflineSyncResponse)
async def sync_offline_data(
    sync_request: OfflineSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sync offline data from mobile device

    Handles:
    - Offline message queue
    - Schedule changes
    - Voice commands
    - Conflict resolution
    """
    service = MobileService(db)
    return await service.sync_offline_data(current_user.id, sync_request, background_tasks)


@router.post("/push/send", response_model=dict)
async def send_push_notification(
    notification: PushNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send push notification to user's devices

    Types:
    - Schedule reminders
    - Approval requests
    - Emergency alerts
    - System notifications
    """
    service = MobileService(db)
    return await service.send_push_notification(current_user.id, notification)


@router.get("/shortcuts/ios", response_model=dict)
async def get_ios_shortcuts(current_user: User = Depends(get_current_user)):
    """
    Get iOS Shortcuts configuration

    Returns Shortcuts app configuration for:
    - Quick scheduling
    - Voice commands
    - Siri integration
    - Widget actions
    """
    return {
        "shortcuts": [
            {
                "name": "Quick Schedule",
                "description": "Schedule an appointment with voice",
                "icon": "calendar.badge.plus",
                "actions": [
                    {
                        "type": "ask_for_input",
                        "parameter": "appointment_details",
                        "prompt": "What would you like to schedule?",
                    },
                    {
                        "type": "api_call",
                        "endpoint": "/voice/command",
                        "method": "POST",
                    },
                ],
            },
            {
                "name": "Today's Schedule",
                "description": "Get today's schedule summary",
                "icon": "list.bullet.rectangle",
                "actions": [
                    {
                        "type": "api_call",
                        "endpoint": "/mew/summary",
                        "method": "GET",
                        "parameters": {"period": "today"},
                    }
                ],
            },
            {
                "name": "Approve Request",
                "description": "Quick approve pending requests",
                "icon": "checkmark.seal",
                "actions": [
                    {
                        "type": "api_call",
                        "endpoint": "/parent-approval/pending",
                        "method": "GET",
                    }
                ],
            },
        ],
        "siri_phrases": [
            "Hey Siri, what's on my schedule today?",
            "Hey Siri, schedule an appointment with Mew",
            "Hey Siri, check pending approvals in Mew",
        ],
    }


@router.get("/widgets/config", response_model=dict)
async def get_widget_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get configuration for home screen widgets

    Supports:
    - iOS widgets (small, medium, large)
    - Android widgets
    - Real-time updates
    - Quick actions
    """
    service = MobileService(db)
    return await service.get_widget_config(current_user.id)
