"""
Global error handler middleware for FastAPI
Catches and formats all exceptions consistently
"""

import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.exceptions import MewException
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def mew_exception_handler(request: Request, exc: MewException) -> JSONResponse:
    """Handle custom Mew exceptions"""
    logger.warning(
        f"Mew exception: {exc.message}",
        extra={
            "extra_data": {
                "status_code": exc.status_code,
                "path": request.url.path,
                "details": exc.details,
            }
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details,
                "path": request.url.path,
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={"extra_data": {"status_code": exc.status_code, "path": request.url.path}},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "HTTPException",
                "path": request.url.path,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        "Validation error",
        extra={"extra_data": {"path": request.url.path, "errors": errors}},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation error",
                "type": "ValidationError",
                "details": {"errors": errors},
                "path": request.url.path,
            }
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors"""
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "extra_data": {
                "path": request.url.path,
                "error_type": exc.__class__.__name__,
            }
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "message": "Database service unavailable",
                "type": "DatabaseError",
                "path": request.url.path,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    # Avoid including full tracebacks in structured logs by default.
    # Include only exception type and message; keep full traceback out
    # of logs unless explicitly enabled via `LOG_INCLUDE_TRACEBACK`.
    tb_allowed = False
    try:
        import os

        tb_allowed = os.getenv("LOG_INCLUDE_TRACEBACK", "false").lower() in (
            "1",
            "true",
            "yes",
        )
    except Exception:
        tb_allowed = False

    extra_data = {
        "path": request.url.path,
        "error_type": exc.__class__.__name__,
    }

    if tb_allowed:
        extra_data["traceback"] = traceback.format_exc()

    logger.error(
        "Unhandled exception",
        extra={"extra_data": extra_data},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "type": "InternalError",
                "path": request.url.path,
            }
        },
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(MewException, mew_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
