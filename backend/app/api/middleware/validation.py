"""Request validation and sanitization middleware."""

import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests."""

    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
    BLOCKED_PATTERNS = [
        r"<script[^>]*>",  # XSS
        r"javascript:",  # XSS
        r"on\w+\s*=",  # Event handlers
        r"union\s+select",  # SQL injection
        r"drop\s+table",  # SQL injection
        r"insert\s+into",  # SQL injection
        r"delete\s+from",  # SQL injection
    ]

    SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"}
            )

        # Validate query parameters
        for key, value in request.query_params.items():
            if self._contains_malicious_content(value):
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Invalid characters in parameter: {key}"}
                )

        # Validate path parameters
        for key, value in request.path_params.items():
            if isinstance(value, str) and self._contains_malicious_content(value):
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Invalid characters in path parameter: {key}"}
                )

        return await call_next(request)

    def _contains_malicious_content(self, value: str) -> bool:
        """Check if value contains potentially malicious content."""
        value_lower = value.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, value_lower):
                return True
        return False
