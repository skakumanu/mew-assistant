"""
External service integrations for Mew Assistant.

This package contains integrations for:
- Email (SMTP/IMAP)
- SMS (Twilio)
- WhatsApp (Twilio)
- AI providers (OpenAI, Anthropic)
- Calendar (Google Calendar)
"""

from .email_integration import EmailIntegration
from .sms_integration import SMSIntegration
from .whatsapp_integration import WhatsAppIntegration
from .ai_integration import AIIntegration
from .calendar_integration import CalendarIntegration

__all__ = [
    "EmailIntegration",
    "SMSIntegration",
    "WhatsAppIntegration",
    "AIIntegration",
    "CalendarIntegration",
]
