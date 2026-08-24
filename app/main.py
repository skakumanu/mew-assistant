import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database.connection import init_db
from .middleware import CORSSecurityMiddleware, ErrorHandlingMiddleware, RequestLoggingMiddleware
from .middleware.bot_protection import BotProtectionMiddleware
from .routers import landing

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Mew Assistant...")
    await init_db()
    yield
    logger.info("Shutting down Mew Assistant...")


app = FastAPI(
    title="Mew Assistant API",
    description="AI-powered scheduling assistant for special needs families",
    version="1.0.0",
    lifespan=lifespan,
)


# Application middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(BotProtectionMiddleware)
app.add_middleware(CORSSecurityMiddleware)

# Ensure CORSMiddleware is outermost so preflight requests are handled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stylesheet and client runtime for the three persona screens.
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Include landing page router first
app.include_router(landing.router, tags=["landing"])

# flake8: noqa
# Import other routers (moved below app to avoid circular imports)
from .routers import auth_router  # noqa: E402
from .routers import calendar_router  # noqa: E402
from .routers import (
    ai_scheduler_router,
    calendar_web_router,
    change_requests_router,
    debug_router,
    kid_router,
    message_router,
    mew_ui_router,
    mobile_router,
    oauth_web,
    parent_approval_router,
    parent_log_router,
    provider_router,
    rules_router,
    session_router,
    simple_calendar_router,
    simple_oauth_router,
    summary_router,
    voice_requests_router,
    voice_router,
)

app.include_router(auth_router, tags=["auth"])
app.include_router(oauth_web.router, tags=["oauth"])
app.include_router(simple_oauth_router, tags=["oauth"])
app.include_router(simple_calendar_router, tags=["calendar"])
app.include_router(calendar_web_router, tags=["calendar-web"])
app.include_router(debug_router, tags=["debug"])
app.include_router(session_router, tags=["sessions"])
app.include_router(message_router, tags=["messages"])
app.include_router(summary_router, tags=["summaries"])
app.include_router(calendar_router, tags=["calendar"])
app.include_router(mobile_router, tags=["mobile"])
app.include_router(voice_router, tags=["voice"])
app.include_router(kid_router, tags=["kid"])
app.include_router(ai_scheduler_router, tags=["ai-scheduler"])
# "Parent" and "guardian" are interchangeable: the same handlers answer on
# both paths, so a family that says "guardian" never reads "parent" in a URL.
for _caregiver_prefix in ("/parent", "/guardian"):
    app.include_router(parent_approval_router, prefix=_caregiver_prefix, tags=["approvals"])

# Three-persona scheduling: rules in, requests through one write path, and
# the provider's own view of the sessions they already run.
app.include_router(rules_router, tags=["rules"])
app.include_router(change_requests_router, tags=["change-requests"])
for _caregiver_prefix in ("/parent", "/guardian"):
    app.include_router(parent_log_router, prefix=_caregiver_prefix, tags=["approvals"])
app.include_router(provider_router, tags=["provider"])
app.include_router(mew_ui_router, tags=["mew-ui"])

# Voice may REQUEST anything and approve nothing.
app.include_router(voice_requests_router, tags=["voice"])


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Mew Assistant",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/version")
async def version():
    return {"version": "landing-page-v2", "deployed": "2025-11-28T02:00:00Z"}
