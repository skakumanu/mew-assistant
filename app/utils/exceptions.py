"""
Custom exception classes for Mew Assistant
Provides domain-specific exceptions with proper HTTP status codes
"""

from typing import Optional, Dict, Any


class MewException(Exception):
    """Base exception for all Mew-specific errors"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(MewException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(MewException):
    """Raised when user lacks permission"""
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(MewException):
    """Raised when resource is not found"""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, status_code=404, details={"resource": resource, "identifier": identifier})


class ValidationError(MewException):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=422, details=details)


class RateLimitError(MewException):
    """Raised when rate limit is exceeded"""
    def __init__(self, retry_after: int):
        message = f"Rate limit exceeded. Try again in {retry_after} seconds"
        super().__init__(message, status_code=429, details={"retry_after": retry_after})


class CooldownError(MewException):
    """Raised when request is in cooldown period"""
    def __init__(self, remaining_seconds: int):
        message = f"Request in cooldown. Try again in {remaining_seconds} seconds"
        super().__init__(message, status_code=429, details={"cooldown_remaining": remaining_seconds})


class DatabaseError(MewException):
    """Raised when database operation fails"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)


class ExternalServiceError(MewException):
    """Raised when external service call fails"""
    def __init__(self, service: str, message: str = "External service unavailable"):
        super().__init__(
            message,
            status_code=503,
            details={"service": service}
        )


class ConfigurationError(MewException):
    """Raised when configuration is invalid or missing"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
