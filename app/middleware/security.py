"""
Security Middleware for Mew Assistant

Implements security best practices:
- Rate limiting
- Input validation and sanitization
- SQL injection prevention
- XSS prevention
- CSRF protection
- Content Security Policy
"""

import hashlib
import os
import re
import time
import urllib.parse
from collections import defaultdict
from typing import Dict, Optional

import bleach
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.exceptions import RateLimitExceeded, SecurityViolationError
from app.utils.logger import get_logger
from app.utils.privacy import PIIDetector

logger = get_logger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware
    """

    # Dangerous patterns that indicate potential attacks
    DANGEROUS_PATTERNS = [
        re.compile(r"(\bUNION\b.*\bSELECT\b)", re.IGNORECASE),  # SQL injection
        re.compile(
            r"(\bOR\b\s+['\"][^'\"]+['\"]\s*=\s*['\"][^'\"]+['\"])", re.IGNORECASE
        ),  # tautology SQLi
        re.compile(r"(--|;)", re.IGNORECASE),  # SQL comment/terminator
        # Note: XSS filtering moved to bleach.clean in sanitize_html
        re.compile(r"(javascript:|data:|vbscript:)", re.IGNORECASE),  # Protocol injection
        re.compile(r"(\.\./|\.\./\.\./)", re.IGNORECASE),  # Path traversal
        re.compile(r"(\bEXEC\b|\bEVAL\b|\bDROP\b)", re.IGNORECASE),  # Command injection
    ]

    # Rate limiting: requests per minute per IP
    RATE_LIMITS = {
        "/mew/ingest": 60,  # 60 requests per minute
        "/mew/confirm": 30,
        "/mew/summary": 20,
        "/auth/login": 5,  # Strict limit for auth endpoints
        "/auth/register": 5,
    }

    def __init__(self, app):
        super().__init__(app)
        self.request_counts: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        try:
            # Expose middleware instance on app.state for test helpers to reset rate limits
            if hasattr(app, "state"):
                app.state.security_middleware = self
        except Exception:
            pass

        # Headers to skip running SQLi heuristics against (common harmless headers)
        self.HEADER_SQLI_SKIP = {
            "accept",
            "user-agent",
            "accept-encoding",
            "accept-language",
            "connection",
            "host",
            "content-type",
            "content-length",
        }

    def reset_state(self):
        """Reset in-memory counters and state (used by tests)."""
        try:
            self.request_counts.clear()
        except Exception:
            pass

    async def dispatch(self, request: Request, call_next):
        """
        Process security checks for each request
        """
        client_ip = request.client.host
        path = request.url.path

        # 1. Run bot-protection / suspicious-content checks first if available
        #    so malicious requests are rejected with security errors instead
        #    of being swallowed by rate limits. BotProtectionMiddleware is
        #    exposed on app.state by its initializer in tests.
        from fastapi.responses import JSONResponse

        try:
            # 1. Bot protection check (external middleware) if available
            bot_mw = getattr(request.app.state, "bot_protection_middleware", None)
            if bot_mw is not None:
                check = getattr(bot_mw, "_check_suspicious_content", None)
                if callable(check):
                    blocked = await check(request)
                    if blocked:
                        raise SecurityViolationError("Potentially malicious request detected")

            # 2. Internal scanning for malicious payloads
            await self._scan_request(request)

            # 3. Validate request size
            await self._check_request_size(request)

            # 4. Rate limiting
            await self._check_rate_limit(client_ip, path)

            # 5. CSRF protection for state-changing methods
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                await self._verify_csrf_token(request)

            # 6. Process request
            response = await call_next(request)
        except SecurityViolationError as se:
            # Log full details internally, return generic message to client
            logger.warning(f"Security violation: {str(se)}")
            return JSONResponse(status_code=403, content={"detail": "Access forbidden"})
        except RateLimitExceeded as rexc:
            # Log full details internally, return generic message to client
            logger.warning(f"Rate limit exceeded: {str(rexc)}")
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        except Exception as exc:
            logger.exception("Unexpected error in security middleware: %s", exc)
            return JSONResponse(status_code=500, content={"detail": "Internal security error"})

        # 6. Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

    async def _check_rate_limit(self, client_ip: str, path: str):
        """
        Implement rate limiting per IP address
        """
        # If running tests, skip strict rate limiting to avoid cross-test
        # interference; tests that actually assert rate-limit behavior
        # should manage the middleware state themselves.
        # Only skip strict rate limiting in test mode when explicitly requested
        # via `TESTING_SKIP_STRICT_RATE_LIMIT=true`. This avoids disabling
        # tests that assert rate-limiting while still allowing a bypass when
        # needed in CI or local debugging.
        if (
            os.environ.get("TESTING", "").lower() == "true"
            and os.environ.get("TESTING_SKIP_STRICT_RATE_LIMIT", "").lower() == "true"
        ):
            return

        # If running under pytest/TestClient, avoid carrying counters across
        # tests for the in-process test client named 'testclient'. Tests that
        # assert rate-limiting explicitly should unset
        # `TESTING_SKIP_STRICT_RATE_LIMIT` themselves.
        if os.environ.get("TESTING", "").lower() == "true" and client_ip == "testclient":
            if os.environ.get("TESTING_SKIP_STRICT_RATE_LIMIT", "").lower() == "true":
                # Clear any stored counters for this test client to avoid
                # cross-test 429s and be deterministic in test runs.
                try:
                    self.request_counts.pop(client_ip, None)
                except Exception:
                    pass
                return

        # Find matching rate limit
        rate_limit = None
        for endpoint, limit in self.RATE_LIMITS.items():
            if path.startswith(endpoint):
                rate_limit = limit
                break

        if not rate_limit:
            rate_limit = 100  # Default rate limit

        # Clean up old requests (older than 1 minute)
        current_time = time.time()
        self.request_counts[client_ip][path] = [
            req_time
            for req_time in self.request_counts[client_ip][path]
            if current_time - req_time < 60
        ]

        # Check if rate limit exceeded
        request_count = len(self.request_counts[client_ip][path])
        if request_count >= rate_limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            raise RateLimitExceeded(
                f"Rate limit exceeded. Maximum {rate_limit} requests per minute allowed."
            )

        # Record this request
        self.request_counts[client_ip][path].append(current_time)

    async def _check_request_size(self, request: Request):
        """
        Prevent large payload attacks
        """
        content_length = request.headers.get("content-length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > 10:  # 10 MB limit
                logger.warning(f"Large request blocked: {size_mb:.2f}MB from {request.client.host}")
                raise SecurityViolationError("Request payload too large. Maximum 10MB allowed.")

    async def _scan_request(self, request: Request):
        """
        Scan request for malicious patterns and PII leakage
        """
        # Scan URL parameters (URL-decode before scanning)
        query_string = urllib.parse.unquote_plus(str(request.url.query))
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(query_string):
                logger.error(f"Malicious pattern detected in query: {query_string}")
                raise SecurityViolationError("Potentially malicious request detected")

        # Additional XSS heuristics (e.g., event handlers like onerror)
        if XSSPrevention.contains_xss(query_string):
            logger.error(f"XSS pattern detected in query: {query_string}")
            raise SecurityViolationError("Potentially malicious request detected")

        # Additional SQLi heuristics (cover encoded payloads/tautologies)
        sqli_match = False
        try:
            sqli_match = SQLInjectionPrevention.is_sql_injection_attempt(query_string)
        except Exception:
            sqli_match = False
        if sqli_match:
            logger.error(f"SQL injection heuristics matched in query: {query_string}")
            raise SecurityViolationError("Potentially malicious request detected")

        # Check for PII in URL (should never be in URL)
        if PIIDetector.contains_pii(query_string):
            logger.error(f"PII detected in URL query string from {request.client.host}")
            raise SecurityViolationError("Sensitive data should not be sent in URL")

        # Scan headers
        for header_name, header_value in request.headers.items():
            # Skip SQLi heuristics for common harmless headers to avoid false positives
            if header_name.lower() in getattr(self, "HEADER_SQLI_SKIP", set()):
                # Still run simple dangerous-pattern matches (e.g., explicit script tags)
                for pattern in self.DANGEROUS_PATTERNS:
                    if pattern.search(str(header_value)):
                        logger.error(f"Malicious pattern in header {header_name}: {header_value}")
                        raise SecurityViolationError("Potentially malicious request detected")
                continue

            for pattern in self.DANGEROUS_PATTERNS:
                if pattern.search(str(header_value)):
                    logger.error(f"Malicious pattern in header {header_name}: {header_value}")
                    raise SecurityViolationError("Potentially malicious request detected")

            # Also run SQLi heuristics against header values for non-whitelisted headers
            header_sqli = False
            try:
                header_sqli = SQLInjectionPrevention.is_sql_injection_attempt(str(header_value))
            except Exception:
                header_sqli = False
            if header_sqli:
                logger.error(
                    f"SQL injection heuristics matched in header {header_name}: {header_value}"
                )
                raise SecurityViolationError("Potentially malicious request detected")

    async def _verify_csrf_token(self, request: Request):
        """
        Verify CSRF token for state-changing operations
        """
        # Skip CSRF for API endpoints with Bearer token
        if request.headers.get("Authorization", "").startswith("Bearer "):
            return

        # Skip CSRF for public registration/login/voice endpoints
        public_endpoints = [
            "/auth/register",
            "/auth/login",
            "/auth/magic-link",
            "/auth/reset-password",
            "/voice/",
            "/api/v1/voice/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        if any(request.url.path.startswith(endpoint) for endpoint in public_endpoints):
            return

        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            logger.warning(f"Missing CSRF token from {request.client.host}")
            raise SecurityViolationError("CSRF token required for this operation")

        # In production, verify token against session
        # For now, just check it exists


class InputSanitizer:
    """
    Sanitize user inputs to prevent injection attacks
    """

    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Remove dangerous HTML tags and attributes using bleach library.
        Bleach uses an HTML parser instead of regex, preventing XSS bypasses.
        """
        allowed_tags = ["p", "br", "strong", "em", "u", "ol", "ul", "li"]
        allowed_attributes = {}

        # Use bleach.clean which properly parses HTML instead of regex matching
        # This prevents XSS bypasses through malformed HTML
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)

    @staticmethod
    def sanitize_sql(text: str) -> str:
        """
        Escape SQL special characters (use parameterized queries instead when possible)
        """
        # This is a backup - always use parameterized queries
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
        sanitized = text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        return sanitized

    @staticmethod
    def sanitize_path(path: str) -> str:
        """
        Prevent path traversal attacks
        """
        # Remove dangerous path components
        sanitized = path.replace("..", "").replace("//", "/")

        # Only allow alphanumeric, dash, underscore, slash
        sanitized = re.sub(r"[^a-zA-Z0-9/_-]", "", sanitized)

        return sanitized

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal
        """
        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Only allow safe characters
        filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)

        # Prevent hidden files
        if filename.startswith("."):
            filename = filename[1:]

        return filename


class EncryptionHelper:
    """
    Helper for encrypting sensitive data
    """

    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
        """
        One-way hash for sensitive data (e.g., for indexing without storing plaintext)
        """
        if salt:
            data = f"{data}{salt}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token
        """
        import secrets

        return secrets.token_urlsafe(length)


class SQLInjectionPrevention:
    """
    Additional SQL injection prevention utilities
    """

    SQL_KEYWORDS = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "EXEC",
        "EXECUTE",
        "UNION",
        "DECLARE",
        "CAST",
    }

    @classmethod
    def is_sql_injection_attempt(cls, text: str) -> bool:
        """
        Detect potential SQL injection attempts
        """
        # Work on a normalized version of the text (upper-case) and URL-decoded
        # form to catch encoded payloads.
        try:
            decoded = urllib.parse.unquote_plus(text)
        except Exception:
            decoded = text
        upper_text = decoded.upper()

        # Quick checks for SQL comment/terminator characters which are strong indicators
        if "--" in text or ";" in text or "/*" in text or "*/" in text:
            return True

        # Check for SQL keywords
        for keyword in cls.SQL_KEYWORDS:
            if keyword in upper_text:
                # Check if it's in a suspicious context
                if "UNION" in upper_text:
                    return True

        # Detect common tautology patterns like "OR '1'='1'" or "OR 1=1"
        try:
            # Accept more tolerant tautology patterns, allowing optional quotes
            tautology_pattern = re.compile(
                r"\bOR\b\s+['\"]?[^'\"\s]+['\"]?\s*=\s*['\"]?[^'\"\s]+['\"]?",
                re.IGNORECASE,
            )
            if tautology_pattern.search(text):
                return True
            if re.search(r"\bOR\b\s+\d+\s*=\s*\d+", text, re.IGNORECASE):
                return True
            # Also catch unquoted numeric tautologies and common variants
            if re.search(
                r"\bOR\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",
                decoded,
                re.IGNORECASE,
            ):
                return True
            if re.search(r"\bAND\b\s+\d+\s*=\s*\d+", decoded, re.IGNORECASE):
                return True
        except Exception:
            pass

        return False

    @classmethod
    def validate_input(cls, text: str, field_name: str) -> str:
        """
        Validate input doesn't contain SQL injection
        """
        if cls.is_sql_injection_attempt(text):
            logger.error(f"SQL injection attempt detected in {field_name}: {text[:100]}")
            raise SecurityViolationError(f"Invalid input for {field_name}")

        return text


class XSSPrevention:
    """
    Cross-Site Scripting (XSS) prevention utilities
    """

    DANGEROUS_TAGS = ["script", "iframe", "object", "embed", "applet"]

    @classmethod
    def contains_xss(cls, text: str) -> bool:
        """
        Detect potential XSS attacks
        """
        lower_text = text.lower()

        # Check for dangerous tags
        for tag in cls.DANGEROUS_TAGS:
            if f"<{tag}" in lower_text:
                return True

        # Check for javascript: protocol
        if "javascript:" in lower_text or "data:text/html" in lower_text:
            return True

        # Check for event handlers
        if re.search(r"on\w+\s*=", lower_text):
            return True

        return False

    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Remove XSS vectors from text
        """
        if cls.contains_xss(text):
            logger.warning(f"XSS attempt detected and sanitized: {text[:100]}")
            return InputSanitizer.sanitize_html(text)
        return text
