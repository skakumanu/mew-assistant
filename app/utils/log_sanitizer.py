"""
Log Sanitizer - Prevents log injection attacks
"""

import re
from typing import Any


def sanitize_for_log(value: Any) -> str:
    """
    Sanitize user input before logging to prevent log injection attacks.

    Removes newlines, carriage returns, and other control characters
    that could be used to inject fake log entries.

    Args:
        value: The value to sanitize (will be converted to string)

    Returns:
        Sanitized string safe for logging
    """
    if value is None:
        return "None"

    # Convert to string
    str_value = str(value)

    # Remove control characters (newlines, carriage returns, etc.)
    # Keep only printable ASCII and common unicode characters
    sanitized = re.sub(r"[\r\n\t\x00-\x1f\x7f-\x9f]", "", str_value)

    # Limit length to prevent log flooding
    max_length = 200
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized


def sanitize_email(email: str) -> str:
    """
    Sanitize email address for logging.

    Args:
        email: Email address

    Returns:
        Sanitized email safe for logging
    """
    if not email:
        return "unknown@unknown.com"

    # Basic email validation and sanitization
    sanitized = sanitize_for_log(email)

    # Ensure it looks like an email
    if "@" not in sanitized or len(sanitized) > 100:
        return "invalid@email.com"

    return sanitized


def sanitize_user_id(user_id: Any) -> str:
    """
    Sanitize user ID for logging.

    Args:
        user_id: User ID (int or string)

    Returns:
        Sanitized user ID safe for logging
    """
    if user_id is None:
        return "unknown"

    # Convert to string and remove any non-alphanumeric characters
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "", str(user_id))

    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:50]

    return sanitized if sanitized else "invalid"
