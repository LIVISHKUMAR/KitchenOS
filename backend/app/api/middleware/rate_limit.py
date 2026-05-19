"""Rate limiting middleware using Redis sliding window."""

import time
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.infrastructure.cache import get_redis
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with per-tenant and per-IP limits."""

    # Default limits
    DEFAULT_RATE = 100  # requests
    DEFAULT_WINDOW = 60  # seconds

    # Endpoint-specific limits
    ENDPOINT_LIMITS = {
        "/api/v1/auth/token": (5, 60),      # 5 login attempts per minute
        "/api/v1/auth/register": (3, 3600),  # 3 registrations per hour
        "/api/v1/orders/": (50, 60),         # 50 order creates per minute
    }

    # Paths to skip rate limiting
    SKIP_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json", "/api/v1/ws"}

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Skip for WebSocket
        if request.url.path.startswith("/api/v1/ws"):
            return await call_next(request)

        # Skip rate limiting entirely in debug mode to allow testing
        if settings.DEBUG:
            return await call_next(request)

        r = get_redis()
        if r is None:
            # Redis unavailable, skip rate limiting
            return await call_next(request)

        try:
            # Determine rate limit
            path = request.url.path
            rate, window = self.ENDPOINT_LIMITS.get(path, (self.DEFAULT_RATE, self.DEFAULT_WINDOW))

            # Build rate limit key
            client_ip = request.client.host if request.client else "unknown"
            tenant_id = "anon"

            # Try to extract tenant from token
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                from app.core.security import decode_token
                payload = decode_token(auth[7:])
                if payload:
                    tenant_id = payload.get("tenant_id", "anon")

            key = f"ratelimit:{tenant_id}:{client_ip}:{path}:{window}"

            # Sliding window check
            now = time.time()
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = pipe.execute()

            request_count = results[2]

            if request_count > rate:
                retry_after = int(window - (now - r.zrange(key, 0, 0, withscores=True)[0][1]))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded", "retry_after": max(1, retry_after)},
                    headers={"Retry-After": str(max(1, retry_after))}
                )

            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rate)
            response.headers["X-RateLimit-Remaining"] = str(max(0, rate - request_count))
            response.headers["X-RateLimit-Reset"] = str(int(now + window))
            return response

        except Exception:
            # On error, allow the request
            return await call_next(request)
