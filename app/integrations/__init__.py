"""
External service integrations for Mew Assistant.

This package contains integrations for:
- Email (SMTP/IMAP)
- SMS (Twilio)
- WhatsApp (Twilio)
- AI providers (OpenAI, Anthropic)
- Calendar (Google Calendar)
- Mobile (iOS/Android Push Notifications)
- Voice (Azure Speech Services - 100+ languages)
"""

from .email_integration import EmailIntegration
from .sms_integration import SMSIntegration
from .whatsapp_integration import WhatsAppIntegration
from .ai_integration import AIIntegration
from .calendar_integration import CalendarIntegration
from .mobile_integration import MobileIntegration
from .voice_integration import VoiceIntegration

__all__ = [
    "EmailIntegration",
    "SMSIntegration",
    "WhatsAppIntegration",
    "AIIntegration",
    "CalendarIntegration",
    "MobileIntegration",
    "VoiceIntegration",
]
