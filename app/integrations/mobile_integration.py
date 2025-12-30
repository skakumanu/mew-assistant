"""
Mobile Device Integration Module
Support for iOS (Apple) and Android push notifications and deep linking
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Module-level placeholders that tests patch
APNs = None
firebase_admin = None
NotificationRequest = None
messaging = None
fb_creds = None


class MobilePlatform(str, Enum):
    """Supported mobile platforms"""

    IOS = "ios"
    ANDROID = "android"


class MobileIntegration:
    """
    Mobile device integration for push notifications and deep linking
    Supports both iOS (APNs) and Android (FCM)
    """

    def __init__(self):
        self.apns_client = None
        self.fcm_client = None
        logger.info("Mobile integration initialized")

    async def initialize_apns(self, credentials: Dict[str, Any]) -> bool:
        """
        Initialize Apple Push Notification Service (APNs)

        Args:
            credentials: APNs credentials (key_id, team_id, key_path, topic)

        Returns:
            bool: Initialization success status
        """
        try:
            # Prefer module-level APNs (tests patch this), otherwise try import
            APNs_cls = APNs
            if APNs_cls is None:
                from aioapns import APNs as APNs_cls

            self.apns_client = APNs_cls(
                key=credentials.get("key_path"),
                key_id=credentials.get("key_id"),
                team_id=credentials.get("team_id"),
                topic=credentials.get("topic", "com.mewassistant.app"),
            )

            logger.info("Apple Push Notification Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize APNs: {e}")
            return False

    async def initialize_fcm(self, credentials: Dict[str, Any]) -> bool:
        """
        Initialize Firebase Cloud Messaging (FCM)

        Args:
            credentials: FCM credentials (service_account_path)

        Returns:
            bool: Initialization success status
        """
        try:
            # Prefer patched module-level objects when tests stub them
            firebase_mod = firebase_admin
            fb_credentials = fb_creds
            if firebase_mod is None or fb_credentials is None:
                import firebase_admin as firebase_mod
                from firebase_admin import credentials as fb_credentials

            cred = fb_credentials.Certificate(credentials.get("service_account_path"))
            firebase_mod.initialize_app(cred)

            self.fcm_client = True
            logger.info("Firebase Cloud Messaging initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {e}")
            return False

    async def send_push_notification(
        self,
        platform: MobilePlatform,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None,
        sound: str = "default",
    ) -> bool:
        """
        Send push notification to mobile device

        Args:
            platform: Mobile platform (ios or android)
            device_token: Device push token
            title: Notification title
            body: Notification body
            data: Additional data payload
            badge: Badge count (iOS)
            sound: Notification sound

        Returns:
            bool: Send success status
        """
        try:
            if platform == MobilePlatform.IOS:
                return await self._send_apns_notification(
                    device_token, title, body, data, badge, sound
                )
            elif platform == MobilePlatform.ANDROID:
                return await self._send_fcm_notification(
                    device_token, title, body, data, sound
                )
            else:
                logger.error(f"Unsupported mobile platform: {platform}")
                return False
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    async def _send_apns_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]],
        badge: Optional[int],
        sound: str,
    ) -> bool:
        """Send notification via APNs"""
        if not self.apns_client:
            logger.error("APNs client not initialized")
            return False

        try:
            # Prefer patched NotificationRequest in module scope for tests
            NR = NotificationRequest
            if NR is None:
                from aioapns import NotificationRequest as NR

            alert = {"title": title, "body": body}
            notification = NR(
                device_token=device_token,
                message={
                    "aps": {
                        "alert": alert,
                        "sound": sound,
                        "badge": badge if badge is not None else 0,
                    }
                },
            )

            if data:
                # Ensure message exists and merge
                if hasattr(notification, "message") and isinstance(
                    notification.message, dict
                ):
                    notification.message.update(data)

            await self.apns_client.send_notification(notification)
            logger.info(f"APNs notification sent to device: {device_token[:8]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send APNs notification: {e}")
            return False

    async def _send_fcm_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]],
        sound: str,
    ) -> bool:
        """Send notification via FCM"""
        if not self.fcm_client:
            logger.error("FCM client not initialized")
            return False

        try:
            # Prefer patched messaging in module scope for tests
            messaging_mod = messaging
            if messaging_mod is None:
                from firebase_admin import messaging as messaging_mod

            notification = messaging_mod.Notification(title=title, body=body)
            android_config = messaging_mod.AndroidConfig(
                notification=messaging_mod.AndroidNotification(
                    sound=sound, priority="high"
                )
            )

            message = messaging_mod.Message(
                notification=notification,
                token=device_token,
                data=data or {},
                android=android_config,
            )
            response = messaging_mod.send(message)
            logger.info(f"FCM notification sent: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to send FCM notification: {e}")
            return False

    async def send_batch_notifications(
        self,
        platform: MobilePlatform,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, int]:
        """
        Send batch push notifications to multiple devices

        Args:
            platform: Mobile platform
            device_tokens: List of device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            Dict with success and failure counts
        """
        success_count = 0
        failure_count = 0

        for token in device_tokens:
            result = await self.send_push_notification(
                platform, token, title, body, data
            )
            if result:
                success_count += 1
            else:
                failure_count += 1

        logger.info(
            f"Batch notification results - Success: {success_count}, "
            f"Failed: {failure_count}"
        )

        return {
            "success": success_count,
            "failed": failure_count,
            "total": len(device_tokens),
        }

    def generate_deep_link(
        self, screen: str, params: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Generate deep links for mobile app navigation

        Args:
            screen: Target screen/route in the app
            params: Query parameters

        Returns:
            Dict containing iOS and Android deep links
        """
        base_ios = "mewassistant://"
        base_android = "mewassistant://"

        path = screen.strip("/")
        query_string = ""

        if params:
            query_parts = [f"{k}={v}" for k, v in params.items()]
            query_string = "?" + "&".join(query_parts)

        ios_link = f"{base_ios}{path}{query_string}"
        android_link = f"{base_android}{path}{query_string}"

        # Universal links (iOS) and App Links (Android)
        universal_link = f"https://app.mewassistant.com/{path}{query_string}"

        logger.info(f"Generated deep links for screen: {screen}")

        return {"ios": ios_link, "android": android_link, "universal": universal_link}

    async def register_device(
        self,
        user_id: str,
        platform: MobilePlatform,
        device_token: str,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a mobile device for push notifications

        Args:
            user_id: User identifier
            platform: Mobile platform
            device_token: Device push token
            device_info: Additional device information

        Returns:
            bool: Registration success status
        """
        try:
            # Store device token in database for future notifications
            # This would integrate with your database layer

            logger.info(
                f"Registered {platform} device for user {user_id}: "
                f"{device_token[:8]}..."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return False

    async def unregister_device(self, user_id: str, device_token: str) -> bool:
        """
        Unregister a mobile device

        Args:
            user_id: User identifier
            device_token: Device push token

        Returns:
            bool: Unregistration success status
        """
        try:
            # Remove device token from database

            logger.info(f"Unregistered device for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister device: {e}")
            return False

    async def send_scheduled_reminder(
        self,
        user_id: str,
        platform: MobilePlatform,
        device_token: str,
        title: str,
        body: str,
        scheduled_time: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Schedule a reminder notification for later delivery

        Args:
            user_id: User identifier
            platform: Mobile platform
            device_token: Device push token
            title: Notification title
            body: Notification body
            scheduled_time: ISO format datetime string
            data: Additional data payload

        Returns:
            bool: Scheduling success status
        """
        try:
            # This would integrate with a job scheduler (e.g., Celery, APScheduler)
            # For now, we'll log the scheduled reminder

            logger.info(
                f"Scheduled reminder for user {user_id} at {scheduled_time}: {title}"
            )

            # In production, you would:
            # 1. Store the reminder in the database
            # 2. Schedule a background job to send the notification at scheduled_time
            # 3. Use a task queue like Celery with Redis/RabbitMQ

            return True
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {e}")
            return False


def get_mobile_integration() -> MobileIntegration:
    """Factory used by tests to get a MobileIntegration instance."""
    return MobileIntegration()
