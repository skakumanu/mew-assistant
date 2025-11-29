"""Routers package for API endpoints."""
from .auth import router as auth_router
from .session import router as session_router
from .message import router as message_router
from .summary import router as summary_router
from .calendar import router as calendar_router
from .mobile import router as mobile_router
from .mobile_api import router as mobile_api_router
from .kid_friendly import router as kid_router
from .parent_approval import router as parent_approval_router
from .voice import router as voice_router
from .oauth_simple import router as simple_oauth_router
from .ai_scheduler import router as ai_scheduler_router
from .simple_calendar import router as simple_calendar_router
from .calendar_web import router as calendar_web_router
# from .approval import router as approval_router
from . import oauth_web

__all__ = [
    "auth_router", 
    "session_router", 
    "message_router", 
    "summary_router", 
    "calendar_router", 
    "mobile_router",
    "mobile_api_router", 
    "kid_router",
    "parent_approval_router",
    "voice_router",
    "simple_oauth_router",
    "ai_scheduler_router",
    "simple_calendar_router",
    "calendar_web_router",
    # "approval_router",
    "oauth_web"
]
