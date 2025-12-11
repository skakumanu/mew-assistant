from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .database.connection import init_db
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
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include landing page router first
app.include_router(landing.router, tags=["landing"])

# Import other routers
from .routers import (
    auth_router, session_router, message_router, summary_router,
    calendar_router, mobile_router, voice_router, kid_router,
    simple_oauth_router, ai_scheduler_router, parent_approval_router,
    simple_calendar_router, calendar_web_router, debug_router, oauth_web
)

app.include_router(auth_router, tags=["auth"])
app.include_router(oauth_web.router, tags=["oauth"])
app.include_router(simple_oauth_router, tags=["oauth"])
app.include_router(simple_calendar_router, tags=["calendar"])
app.include_router(calendar_web_router, tags=["calendar-web"])
app.include_router(debug_router, tags=["debug"])
app.include_router(session_router, prefix="/mew", tags=["sessions"])
app.include_router(message_router, prefix="/mew", tags=["messages"])
app.include_router(summary_router, prefix="/mew", tags=["summaries"])
app.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
app.include_router(mobile_router, prefix="/mobile", tags=["mobile"])
app.include_router(voice_router, prefix="/voice", tags=["voice"])
app.include_router(kid_router, prefix="/kid", tags=["kid"])
app.include_router(ai_scheduler_router, prefix="/ai-scheduler", tags=["ai-scheduler"])
app.include_router(parent_approval_router, prefix="/approvals", tags=["approvals"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Mew Assistant"}

@app.get("/version")
async def version():
    return {"version": "landing-page-v2", "deployed": "2025-11-28T02:00:00Z"}
