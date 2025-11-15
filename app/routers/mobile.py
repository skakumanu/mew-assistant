"""
Mobile Router
Endpoints for mobile device management and push notifications
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.schemas.mobile import (
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
    PushNotificationRequest,
    PushNotificationResponse,
    BatchNotificationRequest,
    BatchNotificationResponse,
    DeepLinkRequest,
    DeepLinkResponse,
    ScheduledReminderRequest,
    ScheduledReminderResponse
)
from app.integrations.mobile_integration import MobileIntegration
from app.utils.auth import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/mobile", tags=["Mobile"])
mobile_integration = MobileIntegration()


@router.post("/register", response_model=DeviceRegistrationResponse)
async def register_device(
    registration_data: DeviceRegistrationRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a mobile device for push notifications
    
    Supports both iOS (APNs) and Android (FCM) devices
    """
    try:
        success = await mobile_integration.register_device(
            user_id=current_user.id,
            platform=registration_data.platform,
            device_token=registration_data.device_token,
            device_info=registration_data.device_info
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register device"
            )
        
        return DeviceRegistrationResponse(
            success=True,
            platform=registration_data.platform,
            message="Device registered successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device registration error: {str(e)}"
        )


@router.delete("/unregister/{device_token}")
async def unregister_device(
    device_token: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unregister a mobile device
    """
    try:
        success = await mobile_integration.unregister_device(
            user_id=current_user.id,
            device_token=device_token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to unregister device"
            )
        
        return {"success": True, "message": "Device unregistered successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device unregistration error: {str(e)}"
        )


@router.post("/notifications/send", response_model=PushNotificationResponse)
async def send_push_notification(
    notification_data: PushNotificationRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a push notification to a mobile device
    
    Supports both iOS (APNs) and Android (FCM) platforms
    """
    try:
        success = await mobile_integration.send_push_notification(
            platform=notification_data.platform,
            device_token=notification_data.device_token,
            title=notification_data.title,
            body=notification_data.body,
            data=notification_data.data,
            badge=notification_data.badge,
            sound=notification_data.sound
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send push notification"
            )
        
        return PushNotificationResponse(
            success=True,
            message="Push notification sent successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Push notification error: {str(e)}"
        )


@router.post("/notifications/batch", response_model=BatchNotificationResponse)
async def send_batch_notifications(
    batch_data: BatchNotificationRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send push notifications to multiple devices
    """
    try:
        results = await mobile_integration.send_batch_notifications(
            platform=batch_data.platform,
            device_tokens=batch_data.device_tokens,
            title=batch_data.title,
            body=batch_data.body,
            data=batch_data.data
        )
        
        return BatchNotificationResponse(
            success=True,
            total_sent=results['success'],
            failed=results['failed'],
            message=f"Sent {results['success']} notifications successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch notification error: {str(e)}"
        )


@router.post("/deeplink", response_model=DeepLinkResponse)
async def generate_deep_link(
    deeplink_data: DeepLinkRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate deep links for mobile app navigation
    
    Creates platform-specific deep links for iOS and Android
    """
    try:
        links = mobile_integration.generate_deep_link(
            screen=deeplink_data.screen,
            params=deeplink_data.params
        )
        
        return DeepLinkResponse(
            ios_link=links['ios'],
            android_link=links['android'],
            universal_link=links['universal'],
            success=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deep link generation error: {str(e)}"
        )


@router.post("/reminders/schedule", response_model=ScheduledReminderResponse)
async def schedule_reminder(
    reminder_data: ScheduledReminderRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Schedule a reminder notification for later delivery
    """
    try:
        success = await mobile_integration.send_scheduled_reminder(
            user_id=current_user.id,
            platform=reminder_data.platform,
            device_token=reminder_data.device_token,
            title=reminder_data.title,
            body=reminder_data.body,
            scheduled_time=reminder_data.scheduled_time,
            data=reminder_data.data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to schedule reminder"
            )
        
        return ScheduledReminderResponse(
            success=True,
            scheduled_time=reminder_data.scheduled_time,
            message="Reminder scheduled successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reminder scheduling error: {str(e)}"
        )
