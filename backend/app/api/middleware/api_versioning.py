"""API versioning middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Handle API versioning via header or URL path."""

    SUPPORTED_VERSIONS = ["v1", "v2"]
    DEFAULT_VERSION = "v1"
    DEPRECATED_VERSIONS = []

    async def dispatch(self, request: Request, call_next):
        # Extract version from path: /api/v1/... or /api/v2/...
        path = request.url.path
        version = self.DEFAULT_VERSION

        if path.startswith("/api/v"):
            parts = path.split("/")
            if len(parts) > 2 and parts[2] in self.SUPPORTED_VERSIONS:
                version = parts[2]

        # Also check Accept-Version header
        header_version = request.headers.get("accept-version")
        if header_version and header_version in self.SUPPORTED_VERSIONS:
            version = header_version

        # Store version in request state
        request.state.api_version = version

        response = await call_next(request)

        # Add version headers
        response.headers["X-API-Version"] = version
        response.headers["X-API-Supported-Versions"] = ", ".join(self.SUPPORTED_VERSIONS)

        if version in self.DEPRECATED_VERSIONS:
            response.headers["X-API-Deprecated"] = "true"
            response.headers["X-API-Sunset"] = "2027-01-01"
            response.headers["Link"] = f'</api/v{self.DEFAULT_VERSION}{path}>; rel="successor-version"'

        return response
