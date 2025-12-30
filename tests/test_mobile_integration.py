"""
Tests for Mobile Integration
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.integrations.mobile_integration import MobileIntegration, MobilePlatform


@pytest.fixture
def mobile_integration():
    """Create mobile integration instance"""
    return MobileIntegration()


@pytest.mark.asyncio
async def test_initialize_apns(mobile_integration):
    """Test Apple Push Notification Service initialization"""
    credentials = {
        "key_path": "/path/to/key.p8",
        "key_id": "TEST_KEY_ID",
        "team_id": "TEST_TEAM_ID",
        "topic": "com.mewassistant.app",
    }

    with patch("app.integrations.mobile_integration.APNs") as mock_apns:
        mock_apns.return_value = Mock()

        result = await mobile_integration.initialize_apns(credentials)

        assert result is True
        assert mobile_integration.apns_client is not None


@pytest.mark.asyncio
async def test_initialize_fcm(mobile_integration):
    """Test Firebase Cloud Messaging initialization"""
    credentials = {"service_account_path": "/path/to/service-account.json"}

    with (
        patch("app.integrations.mobile_integration.firebase_admin") as mock_firebase,
        patch("app.integrations.mobile_integration.fb_creds") as mock_creds,
    ):
        mock_creds.Certificate.return_value = Mock()
        mock_firebase.initialize_app.return_value = None

        result = await mobile_integration.initialize_fcm(credentials)

        assert result is True
        assert mobile_integration.fcm_client is True


@pytest.mark.asyncio
async def test_send_apns_notification(mobile_integration):
    """Test sending iOS push notification"""
    mobile_integration.apns_client = Mock()
    mobile_integration.apns_client.send_notification = AsyncMock()

    with patch("app.integrations.mobile_integration.NotificationRequest") as mock_request:
        mock_request.return_value = Mock(message={})

        result = await mobile_integration.send_push_notification(
            platform=MobilePlatform.IOS,
            device_token="test_ios_token",
            title="Test Notification",
            body="This is a test",
            data={"key": "value"},
            badge=1,
            sound="default",
        )

        assert result is True


@pytest.mark.asyncio
async def test_send_fcm_notification(mobile_integration):
    """Test sending Android push notification"""
    mobile_integration.fcm_client = True

    with patch("app.integrations.mobile_integration.messaging") as mock_messaging:
        mock_messaging.Notification.return_value = Mock()
        mock_messaging.AndroidConfig.return_value = Mock()
        mock_messaging.AndroidNotification.return_value = Mock()
        mock_messaging.Message.return_value = Mock()
        mock_messaging.send.return_value = "message_id_123"

        result = await mobile_integration.send_push_notification(
            platform=MobilePlatform.ANDROID,
            device_token="test_android_token",
            title="Test Notification",
            body="This is a test",
            data={"key": "value"},
            sound="default",
        )

        assert result is True


@pytest.mark.asyncio
async def test_send_batch_notifications(mobile_integration):
    """Test sending batch notifications"""
    mobile_integration.fcm_client = True

    with patch("app.integrations.mobile_integration.messaging") as mock_messaging:
        mock_messaging.Notification.return_value = Mock()
        mock_messaging.AndroidConfig.return_value = Mock()
        mock_messaging.AndroidNotification.return_value = Mock()
        mock_messaging.Message.return_value = Mock()
        mock_messaging.send.return_value = "message_id"

        device_tokens = ["token1", "token2", "token3"]

        results = await mobile_integration.send_batch_notifications(
            platform=MobilePlatform.ANDROID,
            device_tokens=device_tokens,
            title="Batch Notification",
            body="This is a batch test",
            data={"batch": "true"},
        )

        assert results["total"] == 3
        assert results["success"] + results["failed"] == 3


def test_generate_deep_link(mobile_integration):
    """Test deep link generation"""
    links = mobile_integration.generate_deep_link(
        screen="session/details", params={"session_id": "123", "user_id": "456"}
    )

    assert "ios" in links
    assert "android" in links
    assert "universal" in links
    assert "session/details" in links["ios"]
    assert "session_id=123" in links["ios"]
    assert "user_id=456" in links["ios"]


@pytest.mark.asyncio
async def test_register_device(mobile_integration):
    """Test device registration"""
    result = await mobile_integration.register_device(
        user_id="user_123",
        platform=MobilePlatform.IOS,
        device_token="test_token",
        device_info={"model": "iPhone 14", "os_version": "17.0"},
    )

    assert result is True


@pytest.mark.asyncio
async def test_unregister_device(mobile_integration):
    """Test device unregistration"""
    result = await mobile_integration.unregister_device(
        user_id="user_123", device_token="test_token"
    )

    assert result is True


@pytest.mark.asyncio
async def test_schedule_reminder(mobile_integration):
    """Test scheduling a reminder"""
    result = await mobile_integration.send_scheduled_reminder(
        user_id="user_123",
        platform=MobilePlatform.IOS,
        device_token="test_token",
        title="Reminder",
        body="This is a scheduled reminder",
        scheduled_time="2024-01-15T10:00:00Z",
        data={"reminder_id": "rem_123"},
    )

    assert result is True


@pytest.mark.asyncio
async def test_send_notification_without_client(mobile_integration):
    """Test sending notification without initialized client"""
    result = await mobile_integration.send_push_notification(
        platform=MobilePlatform.IOS,
        device_token="test_token",
        title="Test",
        body="Test body",
        data=None,
        badge=None,
        sound="default",
    )

    assert result is False


@pytest.mark.asyncio
async def test_send_notification_invalid_platform(mobile_integration):
    """Test sending notification with invalid platform"""
    result = await mobile_integration.send_push_notification(
        platform="invalid_platform",
        device_token="test_token",
        title="Test",
        body="Test body",
    )

    assert result is False
