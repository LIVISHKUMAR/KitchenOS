"""Response compression middleware."""

import gzip
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Gzip compression for API responses."""

    MIN_SIZE = 500  # Only compress responses > 500 bytes
    COMPRESSIBLE_TYPES = [
        "application/json",
        "text/html",
        "text/plain",
        "text/css",
        "application/javascript",
    ]

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response

        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.COMPRESSIBLE_TYPES):
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                body += chunk.encode()
            else:
                body += chunk

        # Only compress if large enough
        if len(body) < self.MIN_SIZE:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        # Compress
        compressed = gzip.compress(body)

        # Return compressed response
        headers = dict(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(len(compressed))

        return Response(
            content=compressed,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )
