"""
Bot Protection Middleware
Protects against automated attacks, spam, and abuse
"""

import hashlib
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class BotProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"eval\(",
            r"base64",
            r"union.*select",
            r"drop.*table",
            r"\bOR\b\s+['\"][^'\"]+['\"]\s*=\s*['\"][^'\"]+['\"]",
            r"(--|;)",
        ]
        try:
            if hasattr(app, "state"):
                app.state.bot_protection_middleware = self
        except Exception:
            pass

    def reset_state(self):
        """Reset in-memory counters and blocked IPs for deterministic tests."""
        try:
            self.request_counts.clear()
        except Exception:
            pass
        try:
            self.blocked_ips.clear()
        except Exception:
            pass

    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = self._get_client_ip(request)
        client_id = self._generate_client_id(request, client_ip)

        # Check if IP is blocked
        # If running tests, clear any transient blocks for the in-process
        # TestClient (host 'testclient') when TESTING_SKIP_STRICT_RATE_LIMIT
        # is enabled to avoid cross-test interference.
        if (
            os.environ.get("TESTING", "").lower() == "true"
            and client_ip == "testclient"
        ):
            if os.environ.get("TESTING_SKIP_STRICT_RATE_LIMIT", "").lower() == "true":
                try:
                    self.request_counts.pop(client_id, None)
                except Exception:
                    pass
                try:
                    if client_ip in self.blocked_ips:
                        del self.blocked_ips[client_ip]
                except Exception:
                    pass

        if client_ip in self.blocked_ips:
            block_until = self.blocked_ips[client_ip]
            if datetime.utcnow() < block_until:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Too many requests. Your IP has been temporarily blocked.",
                        "retry_after": (block_until - datetime.utcnow()).seconds,
                    },
                )
            else:
                del self.blocked_ips[client_ip]

        # Rate limiting check. Only skip strict rate limits in test mode when
        # explicitly requested via `TESTING_SKIP_STRICT_RATE_LIMIT=true`.
        if not (
            os.environ.get("TESTING", "").lower() == "true"
            and os.environ.get("TESTING_SKIP_STRICT_RATE_LIMIT", "").lower() == "true"
        ):
            if not self._check_rate_limit(client_id):
                # Block IP for 15 minutes
                self.blocked_ips[client_ip] = datetime.utcnow() + timedelta(minutes=15)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded. Your IP has been temporarily blocked.",
                        "retry_after": 900,
                    },
                )

        # Check for suspicious patterns in request
        if await self._check_suspicious_content(request):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Request contains suspicious content"},
            )

        # Check User-Agent
        if not self._check_user_agent(request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Invalid or missing User-Agent"},
            )

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP from request"""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _generate_client_id(self, request: Request, ip: str) -> str:
        """Generate unique client identifier"""
        user_agent = request.headers.get("User-Agent", "")
        fingerprint = f"{ip}:{user_agent}"
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client exceeds rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old requests
        self.request_counts[client_id] = [
            req_time
            for req_time in self.request_counts[client_id]
            if req_time > window_start
        ]

        # Check rate limit
        if len(self.request_counts[client_id]) >= self.rate_limit:
            return False

        # Add current request
        self.request_counts[client_id].append(now)
        return True

    async def _check_suspicious_content(self, request: Request) -> bool:
        """Check for malicious patterns in request"""
        # Check URL path
        if any(
            re.search(pattern, request.url.path, re.IGNORECASE)
            for pattern in self.suspicious_patterns
        ):
            return True

        # Check query parameters
        for key, value in request.query_params.items():
            combined = f"{key}={value}"
            if any(
                re.search(pattern, combined, re.IGNORECASE)
                for pattern in self.suspicious_patterns
            ):
                return True
            # Quick heuristic: detect common tautology SQL injections like "OR '1'='1'"
            if re.search(r"\bOR\b", combined, re.IGNORECASE) and (
                "=" in combined or "--" in combined or ";" in combined
            ):
                return True

        # Check body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_str = body.decode("utf-8", errors="ignore")
                if any(
                    re.search(pattern, body_str, re.IGNORECASE)
                    for pattern in self.suspicious_patterns
                ):
                    return True
            except Exception:
                # Ignore errors reading or decoding the request body; skip body content check if it fails
                pass

        return False

    def _check_user_agent(self, request: Request) -> bool:
        """Validate User-Agent header"""
        user_agent = request.headers.get("User-Agent", "")

        # Skip for health checks and docs
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return True

        # Require User-Agent for API endpoints
        if not user_agent:
            return False

        # Block known bad bots
        bad_bots = ["sqlmap", "nikto", "nmap", "masscan", "bot", "crawler", "spider"]
        if any(bot in user_agent.lower() for bot in bad_bots):
            return False

        return True


# CAPTCHA verification for critical operations
class CaptchaVerifier:
    """Simple CAPTCHA verification (can be enhanced with reCAPTCHA/hCaptcha)"""

    def __init__(self):
        self.pending_verifications: Dict[str, Tuple[str, datetime]] = {}

    def generate_challenge(self, user_id: str) -> dict:
        """Generate a simple math CAPTCHA"""
        import random

        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        answer = num1 + num2

        challenge_id = hashlib.sha256(
            f"{user_id}{datetime.utcnow()}".encode()
        ).hexdigest()[:16]
        self.pending_verifications[challenge_id] = (
            str(answer),
            datetime.utcnow() + timedelta(minutes=5),
        )

        return {
            "challenge_id": challenge_id,
            "question": f"What is {num1} + {num2}?",
            "expires_in": 300,
        }

    def verify_response(self, challenge_id: str, response: str) -> bool:
        """Verify CAPTCHA response"""
        if challenge_id not in self.pending_verifications:
            return False

        expected_answer, expires_at = self.pending_verifications[challenge_id]

        if datetime.utcnow() > expires_at:
            del self.pending_verifications[challenge_id]
            return False

        if response.strip() == expected_answer:
            del self.pending_verifications[challenge_id]
            return True

        return False

    def cleanup_expired(self):
        """Remove expired challenges"""
        now = datetime.utcnow()
        expired = [
            cid for cid, (_, exp) in self.pending_verifications.items() if now > exp
        ]
        for cid in expired:
            del self.pending_verifications[cid]


captcha_verifier = CaptchaVerifier()
