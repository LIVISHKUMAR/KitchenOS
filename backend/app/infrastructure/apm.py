"""Application Performance Monitoring (APM)."""

import time
import logging
from typing import Optional
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger("kitchenos.apm")


class PerformanceTracker:
    """Track request performance and slow queries."""

    SLOW_REQUEST_THRESHOLD = 1.0  # seconds
    SLOW_QUERY_THRESHOLD = 0.5  # seconds

    def __init__(self):
        self._metrics = {
            "total_requests": 0,
            "slow_requests": 0,
            "errors": 0,
            "avg_response_time": 0.0
        }
        self._response_times = []

    @contextmanager
    def track_request(self, method: str, path: str):
        """Track request timing."""
        start = time.time()
        self._metrics["total_requests"] += 1

        try:
            yield
        except Exception as e:
            self._metrics["errors"] += 1
            raise
        finally:
            duration = time.time() - start
            self._response_times.append(duration)

            # Keep only last 1000 response times
            if len(self._response_times) > 1000:
                self._response_times = self._response_times[-1000:]

            self._metrics["avg_response_time"] = (
                sum(self._response_times) / len(self._response_times)
            )

            if duration > self.SLOW_REQUEST_THRESHOLD:
                self._metrics["slow_requests"] += 1
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.3f}s"
                )

    @contextmanager
    def track_query(self, query: str):
        """Track database query timing."""
        start = time.time()

        try:
            yield
        finally:
            duration = time.time() - start

            if duration > self.SLOW_QUERY_THRESHOLD:
                logger.warning(
                    f"Slow query ({duration:.3f}s): {query[:200]}"
                )

    def get_metrics(self) -> dict:
        """Get performance metrics."""
        return {
            **self._metrics,
            "p50_response_time": self._percentile(50),
            "p95_response_time": self._percentile(95),
            "p99_response_time": self._percentile(99),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _percentile(self, p: int) -> float:
        """Calculate response time percentile."""
        if not self._response_times:
            return 0.0
        sorted_times = sorted(self._response_times)
        index = int(len(sorted_times) * p / 100)
        return round(sorted_times[min(index, len(sorted_times) - 1)], 3)


class ErrorTracker:
    """Track and categorize errors."""

    def __init__(self):
        self._errors = []
        self._error_counts = {}

    def track_error(self, error_type: str, message: str, path: str = None):
        """Track an error occurrence."""
        error = {
            "type": error_type,
            "message": message[:500],
            "path": path,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._errors.append(error)

        # Keep only last 1000 errors
        if len(self._errors) > 1000:
            self._errors = self._errors[-1000:]

        # Count by type
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def get_errors(self, limit: int = 50) -> list:
        """Get recent errors."""
        return self._errors[-limit:]

    def get_error_counts(self) -> dict:
        """Get error counts by type."""
        return self._error_counts.copy()


# Global instances
performance_tracker = PerformanceTracker()
error_tracker = ErrorTracker()


def track_performance(func):
    """Decorator to track function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error_tracker.track_error(
                error_type=type(e).__name__,
                message=str(e),
                path=func.__name__
            )
            raise
        finally:
            duration = time.time() - start
            if duration > 1.0:
                logger.warning(f"Slow function {func.__name__}: {duration:.3f}s")
    return wrapper
