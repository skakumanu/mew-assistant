"""
SMS integration using Twilio for sending text messages.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SMSIntegration:
    """SMS integration using Twilio."""

    def __init__(self):
        self.account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.from_number = getattr(settings, "TWILIO_PHONE_NUMBER", "")
        self.client = None

        self._initialize_client()

    def _initialize_client(self):
        """Initialize Twilio client."""
        try:
            if self.account_sid and self.auth_token:
                from twilio.rest import Client

                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS client initialized")
        except ImportError:
            logger.warning("Twilio package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {str(e)}")

    async def send_sms(
        self,
        to_number: str,
        message: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an SMS message."""
        if not self.client:
            return {"success": False, "message": "SMS service not configured"}

        try:
            if not to_number.startswith("+"):
                to_number = f"+{to_number}"

            kwargs = {
                "body": message,
                "from_": self.from_number,
                "to": to_number,
            }

            if media_url:
                kwargs["media_url"] = [media_url]

            msg = self.client.messages.create(**kwargs)

            logger.info(f"SMS sent to {to_number}, SID: {msg.sid}")

            return {
                "success": True,
                "message_sid": msg.sid,
                "status": msg.status,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send SMS: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def send_reminder(self, to_number: str, reminder_title: str, reminder_time: str) -> Dict[str, Any]:
        """Send a reminder SMS."""
        message = f"📅 Reminder: {reminder_title}\nTime: {reminder_time}\n\n- Mew Assistant"
        return await self.send_sms(to_number, message)

    async def send_summary(self, to_number: str, summary_text: str) -> Dict[str, Any]:
        """Send a daily summary SMS."""
        max_length = 1400
        if len(summary_text) > max_length:
            summary_text = summary_text[:max_length] + "..."

        message = f"📊 Daily Summary\n\n{summary_text}\n\n- Mew Assistant"
        return await self.send_sms(to_number, message)
