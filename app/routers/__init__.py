"""Routers package for API endpoints."""

# from .approval import router as approval_router
from . import oauth_web
from .ai_scheduler import router as ai_scheduler_router
from .auth import router as auth_router
from .calendar import router as calendar_router
from .calendar_sync import router as calendar_sync_router
from .calendar_web import router as calendar_web_router
from .debug_page import router as debug_router
from .kid_friendly import router as kid_router
from .message import router as message_router
from .mew_ui import router as mew_ui_router
from .mobile import router as mobile_router
from .notifications import router as notifications_router
from .oauth_simple import router as simple_oauth_router
from .onboarding_setup import router as onboarding_setup_router
from .parent_approval import parent_router as parent_log_router
from .parent_approval import router as parent_approval_router
from .provider import router as provider_router
from .requests import router as change_requests_router
from .rules import router as rules_router
from .session import router as session_router
from .simple_calendar import router as simple_calendar_router
from .smart_approval import router as smart_approval_router
from .summary import router as summary_router
from .voice import router as voice_router
from .voice_requests import router as voice_requests_router
from .webhooks import router as webhooks_router

__all__ = [
    "auth_router",
    "session_router",
    "message_router",
    "summary_router",
    "calendar_router",
    "mobile_router",
    "kid_router",
    "parent_approval_router",
    "parent_log_router",
    "rules_router",
    "change_requests_router",
    "provider_router",
    "calendar_sync_router",
    "smart_approval_router",
    "notifications_router",
    "onboarding_setup_router",
    "mew_ui_router",
    "voice_requests_router",
    "voice_router",
    "simple_oauth_router",
    "ai_scheduler_router",
    "simple_calendar_router",
    "calendar_web_router",
    # "approval_router",
    "oauth_web",
    "debug_router",
    "webhooks_router",
]
