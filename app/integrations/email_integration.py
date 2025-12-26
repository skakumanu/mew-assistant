"""
Email integration for receiving and sending emails via SMTP/IMAP.

Supports:
- Sending emails via SMTP
- Receiving emails via IMAP
- Email parsing and content extraction
- Attachment handling
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailIntegration:
    """Email integration for SMTP/IMAP operations."""

    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        
        self.imap_server = getattr(settings, 'IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = getattr(settings, 'IMAP_PORT', 993)
        self.imap_user = getattr(settings, 'IMAP_USER', '')
        self.imap_password = getattr(settings, 'IMAP_PASSWORD', '')

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send an email via SMTP."""
        if not self.smtp_user or not self.smtp_password:
            return {"success": False, "message": "Email not configured"}

        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            mime_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, mime_type))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.send_message(msg, to_addrs=recipients)

            logger.info(f"Email sent successfully to {to_email}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def send_notification(
        self, to_email: str, notification_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a notification email with templated content."""
        templates = {
            "reminder": {
                "subject": "📅 Reminder: {title}",
                "body": """
                <h2>Reminder from Mew Assistant</h2>
                <p><strong>{title}</strong></p>
                <p>Time: {time}</p>
                <p>Details: {details}</p>
                """,
            },
            "summary": {
                "subject": "📊 Daily Summary - {date}",
                "body": """
                <h2>Daily Summary</h2>
                <p>Date: {date}</p>
                <p>{summary_content}</p>
                """,
            },
            "alert": {
                "subject": "⚠️ Alert: {alert_type}",
                "body": """
                <h2>Alert Notification</h2>
                <p><strong>{alert_type}</strong></p>
                <p>{message}</p>
                """,
            },
        }

        template = templates.get(notification_type)
        if not template:
            return {"success": False, "message": "Invalid notification type"}

        subject = template["subject"].format(**data)
        body = template["body"].format(**data)

        return await self.send_email(to_email, subject, body, is_html=True)


def get_email_integration() -> EmailIntegration:
    """Factory used by tests to get an EmailIntegration instance."""
    return EmailIntegration()
