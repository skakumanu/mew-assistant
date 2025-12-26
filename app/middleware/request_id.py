"""
Request ID middleware for request tracking
Adds unique ID to each request for distributed tracing
"""

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.logging import clear_request_context, set_request_context


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates and tracks unique request IDs
    Adds X-Request-ID header to responses
    """

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set in logging context
        set_request_context(request_id)

        # Add to request state for access in route handlers
        request.state.request_id = request_id

        try:
            response: Response = await call_next(request)
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Clear context after request
            clear_request_context()
