"""
Mew Assistant - FastAPI-based modular assistant for special needs families.

Supports scheduling, tutoring, and caregiver summaries with multi-channel ingestion
(email, SMS, WhatsApp). Includes cooldown detection, priority period overrides,
and PostgreSQL session tracking.

For contributor onboarding, see README.md
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from .routers import (
    session_router, 
    message_router, 
    summary_router, 
    auth_router,
    calendar_router,
    mobile_router,
    mobile_api_router,
    kid_router,
    parent_approval_router,
    voice_router,
    oauth_web
)
from .routers.webhooks import router as webhooks_router
from .routers.backup import router as backup_router
from .routers.voice_platforms import router as voice_platforms_router
from .routers.onboarding import router as onboarding_router
from .routers.ai_scheduler import router as ai_scheduler_router
from .routers.oauth import router as oauth_router
from .database import Base
from .middleware import register_exception_handlers, RequestIDMiddleware
from .middleware.compliance import ComplianceMiddleware
from .middleware.security import SecurityMiddleware
from .utils.logger import get_logger

# Setup structured logging
logger = get_logger(__name__)

# Lazy database initialization - only create tables when DB is available
try:
    from .database import engine
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not connect to database: {e}")
    logger.info("Database tables will be created when connection is available")

# Initialize FastAPI app
app = FastAPI(
    title="Mew Assistant",
    description="Modular assistant for special needs families supporting scheduling, tutoring, and caregiver summaries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware in correct order (last added = first executed)
# 1. CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Bot protection (rate limiting, suspicious content detection)
from app.middleware.bot_protection import BotProtectionMiddleware
app.add_middleware(BotProtectionMiddleware, rate_limit=100, window_seconds=60)

# 3. Request ID tracking
app.add_middleware(RequestIDMiddleware)

# 4. Security middleware (rate limiting, XSS, SQL injection prevention)
app.add_middleware(SecurityMiddleware)

# 5. Compliance middleware (HIPAA, COPPA, FERPA)
app.add_middleware(ComplianceMiddleware)

# 6. Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(onboarding_router)  # Easy registration - ALL channels
app.include_router(auth_router)  # Authentication first
app.include_router(oauth_web.router)  # OAuth web interface for mobile
app.include_router(session_router)
app.include_router(message_router)
app.include_router(summary_router)
app.include_router(calendar_router)
app.include_router(mobile_router)
app.include_router(mobile_api_router)  # Enhanced mobile API with widgets and shortcuts
app.include_router(kid_router)  # Kid-friendly endpoints
app.include_router(parent_approval_router)  # Parent approval workflow - CRITICAL for kid safety
app.include_router(voice_router)  # Voice commands with multilingual support
app.include_router(voice_platforms_router)  # Multi-platform voice assistants (Siri, Alexa, Google, Tesla)
app.include_router(webhooks_router)  # Webhook endpoints for external integrations
app.include_router(backup_router)  # Cloud backup and restore - Azure integration
app.include_router(ai_scheduler_router)  # AI-powered scheduling with conflict detection and optimization
app.include_router(oauth_router)  # OAuth federated authentication (Google, Apple, Microsoft, Facebook)


@app.get("/", tags=["health"])
async def root():
    """
    Health check endpoint.
    Returns basic information about the Mew Assistant API.
    """
    return {
        "message": "Mew Assistant is running!",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "onboarding": "/api/v1/onboarding/* (easy registration - email, phone, voice, social)",
            "auth": "/auth/register, /auth/login, /auth/me",
            "oauth": "/auth/oauth/* (Google, Apple, Microsoft, Facebook login)",
            "sessions": "/mew/session, /mew/confirm",
            "messages": "/mew/ingest",
            "summaries": "/mew/summary",
            "calendar": "/calendar/*",
            "mobile": "/mobile/*",
            "kid": "/kid/* (kid-friendly endpoints)",
            "voice": "/voice/* (multilingual voice commands - 20+ languages)",
            "webhooks": "/webhooks/sms/incoming, /webhooks/whatsapp/incoming",
            "backup": "/api/backup/* (Azure cloud backups)",
            "ai_scheduler": "/ai-scheduler/* (AI-powered scheduling with conflict detection)",
            "docs": "/docs"
        },
        "registration": "No password needed! Register via email, phone, voice, or social login (Google/Apple/Microsoft/Facebook)"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Detailed health check endpoint.
    Used by monitoring systems and load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "database": "connected"  # Add actual DB health check in production
    }



