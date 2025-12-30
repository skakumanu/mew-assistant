"""
Structured logging configuration for Mew Assistant
Provides consistent logging with context and request tracking
"""

import json
import logging
import os
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

# Context variable for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured logs"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add exception info if present. Only include full traceback when
        # explicitly enabled by environment variable to avoid exposing stack
        # traces in production logs. Set LOG_INCLUDE_TRACEBACK=true for
        # development or when an internal support workflow requires it.
        if record.exc_info:
            exc_type = record.exc_info[0].__name__
            exc_message = str(record.exc_info[1])

            exception_info = {"type": exc_type, "message": exc_message}

            include_tb = os.getenv("LOG_INCLUDE_TRACEBACK", "false").lower() in (
                "1",
                "true",
                "yes",
            )

            if include_tb:
                # Keep traceback content but keep it intentionally optional
                exception_info["traceback"] = traceback.format_exception(*record.exc_info)

            log_data["exception"] = exception_info

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to log records"""

    def process(self, msg, kwargs):
        # Add extra data to the record
        extra = kwargs.get("extra", {})
        extra.update(
            {
                "request_id": request_id_var.get(),
                "user_id": user_id_var.get(),
            }
        )
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """
    Configure application-wide logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON-structured logging
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.LoggerAdapter:
    """
    Get a context-aware logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        Context-aware logger adapter
    """
    logger = logging.getLogger(name)
    return ContextAdapter(logger, {})


def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """
    Set request context for logging

    Args:
        request_id: Unique request identifier
        user_id: Optional user identifier
    """
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)


# Example usage logger
logger = get_logger(__name__)
