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

from .routers import session_router, message_router, summary_router, auth_router
from .database import Base
from .middleware.error_handler import register_exception_handlers
from .middleware.request_id import RequestIDMiddleware
from .utils.logging import setup_logging, get_logger

# Setup structured logging
setup_logging(log_level="INFO", json_format=False)
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

# Add request ID middleware (first to track all requests)
app.add_middleware(RequestIDMiddleware)

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
register_exception_handlers(app)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header to all requests."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(auth_router)  # Authentication first
app.include_router(session_router)
app.include_router(message_router)
app.include_router(summary_router)


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
            "auth": "/auth/register, /auth/login, /auth/me",
            "sessions": "/mew/session, /mew/confirm",
            "messages": "/mew/ingest",
            "summaries": "/mew/summary",
            "docs": "/docs"
        }
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



