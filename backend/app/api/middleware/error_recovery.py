"""Error recovery middleware and utilities."""

import logging
import traceback
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("kitchenos.error_recovery")


class ErrorRecoveryMiddleware(BaseHTTPMiddleware):
    """Global error recovery middleware."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled error on {request.method} {request.url.path}: {e}")
            logger.error(traceback.format_exc())

            # Return user-friendly error
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An unexpected error occurred. Please try again.",
                    "request_id": id(request),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


class RetryHandler:
    """Handle retries for failed operations."""

    @staticmethod
    async def with_retry(func, max_retries: int = 3, delay: float = 1.0):
        """Execute a function with retry logic."""
        import asyncio

        last_error = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))

        raise last_error


class GracefulDegradation:
    """Handle graceful degradation when services are unavailable."""

    @staticmethod
    def handle_printer_failure(error: Exception) -> dict:
        """Handle printer failure gracefully."""
        logger.warning(f"Printer failure: {error}")
        return {
            "status": "printer_unavailable",
            "message": "Printer is not available. KOT will be queued for retry.",
            "action": "queue_for_retry"
        }

    @staticmethod
    def handle_payment_failure(error: Exception) -> dict:
        """Handle payment failure gracefully."""
        logger.warning(f"Payment failure: {error}")
        return {
            "status": "payment_failed",
            "message": "Payment processing failed. Please try again or use a different method.",
            "action": "retry_or_alternate"
        }

    @staticmethod
    def handle_network_failure(error: Exception) -> dict:
        """Handle network failure gracefully."""
        logger.warning(f"Network failure: {error}")
        return {
            "status": "offline",
            "message": "Network unavailable. Orders will be saved locally and synced when online.",
            "action": "switch_to_offline"
        }
