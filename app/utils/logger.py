"""
Structured logging configuration for Mew Assistant.
Provides consistent logging across all modules with JSON formatting for production.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
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
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """Human-readable formatter for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        name = record.name
        message = record.getMessage()
        
        base_msg = f"[{timestamp}] {level:8s} {name:25s} | {message}"
        
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)
        
        return base_msg


def setup_logger(
    name: str,
    level: str = "INFO",
    use_json: bool = False,
    log_file: str | None = None
) -> logging.Logger:
    """
    Set up a logger with consistent configuration.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting (for production)
        log_file: Optional file path to write logs to
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if logger.handlers:
        return logger
    
    formatter = JSONFormatter() if use_json else StandardFormatter()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with standard configuration.
    Uses environment variable LOG_LEVEL if set, otherwise defaults to INFO.
    """
    import os
    level = os.getenv("LOG_LEVEL", "INFO")
    use_json = os.getenv("LOG_FORMAT", "standard") == "json"
    log_file = os.getenv("LOG_FILE")
    
    return setup_logger(name, level, use_json, log_file)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log records.
    Useful for adding user_id, session_id, etc. to all logs.
    """
    
    def process(self, msg: str, kwargs: Any) -> tuple:
        extra = kwargs.get("extra", {})
        
        if "user_id" in self.extra:
            extra["user_id"] = self.extra["user_id"]
        
        if "session_id" in self.extra:
            extra["session_id"] = self.extra["session_id"]
        
        if "request_id" in self.extra:
            extra["request_id"] = self.extra["request_id"]
        
        kwargs["extra"] = extra
        return msg, kwargs
