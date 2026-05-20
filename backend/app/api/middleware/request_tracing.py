"""Request tracing middleware for distributed tracing."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.infrastructure.logging import generate_request_id, set_request_id, get_logger

logger = get_logger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Add request ID and timing to all requests.

    - Generates or extracts X-Request-ID from request headers
    - Sets request ID in context for logging correlation
    - Adds X-Request-ID and X-Response-Time headers to response
    - Logs request method, path, status, and duration
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("x-request-id") or generate_request_id()
        set_request_id(request_id)

        # Track timing
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add tracing headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        # Log request
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration_ms:.1f}ms"
        )

        return response
