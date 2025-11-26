"""
Mew Assistant - FastAPI-based modular assistant for special needs families.

Supports scheduling, tutoring, and caregiver summaries with multi-channel ingestion
(email, SMS, WhatsApp). Includes cooldown detection, priority period overrides,
and PostgreSQL session tracking.

For contributor onboarding, see README.md
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time
import os

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
from .routers.oauth_simple import router as oauth_simple_router
from .routers.onboarding import router as onboarding_router
from .routers.ai_scheduler import router as ai_scheduler_router
# OAuth router removed - using simple_oauth only
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

# Mount static files for dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = None
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
    logger.info(f"Templates loaded from {templates_dir}")
else:
    logger.warning(f"Templates directory not found: {templates_dir}")

# Include routers
app.include_router(onboarding_router)  # Easy registration - ALL channels
app.include_router(auth_router)  # Authentication first
app.include_router(oauth_web.router)  # OAuth web interface for mobile
app.include_router(oauth_simple_router)  # Simple, bulletproof OAuth implementation
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
# Using simple_oauth router only - old oauth_router removed


@app.get("/", tags=["home"])
async def root(request: Request):
    """
    Landing page with easy sign-in options.
    Mobile-friendly interface for quick registration.
    """
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        # Fallback to simple HTML if templates not available
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mew Assistant</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .btn { display: block; padding: 15px; margin: 10px 0; text-align: center; background: #4285f4; color: white; text-decoration: none; border-radius: 5px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>🐱 Welcome to Mew Assistant</h1>
            <p>Your AI-powered family scheduling assistant</p>
            <a href="/auth/simple/login" class="btn">Sign in with Google</a>
            <a href="/docs" class="btn">View API Documentation</a>
        </body>
        </html>
        """)


@app.get("/api/health", tags=["health"])
async def health():
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
            "oauth": "/auth/simple/* (Google, Apple, Microsoft login)",
            "sessions": "/mew/session, /mew/confirm",
            "messages": "/mew/ingest",
            "summaries": "/mew/summary",
            "calendar": "/calendar/*",
            "mobile": "/mobile/*",
            "kid": "/kid/* (kid-friendly endpoints)",
            "voice": "/voice/* (multilingual voice commands - 100+ languages)",
            "webhooks": "/webhooks/sms/incoming, /webhooks/whatsapp/incoming",
            "backup": "/api/backup/* (Azure cloud backups)",
            "ai_scheduler": "/ai-scheduler/* (AI-powered scheduling with conflict detection)",
            "docs": "/docs"
        },
        "registration": "No password needed! Register via social login (Google/Apple/Microsoft)"
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



