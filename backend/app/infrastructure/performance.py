"""Performance optimization utilities."""

import time
import logging
from typing import Optional, Callable, Any
from functools import wraps
from contextlib import contextmanager
from collections import defaultdict

logger = logging.getLogger("kitchenos.performance")


class QueryProfiler:
    """Profile database queries for performance analysis."""

    def __init__(self):
        self._queries: list = []
        self._slow_queries: list = []
        self.SLOW_THRESHOLD = 0.5  # seconds

    @contextmanager
    def track(self, query: str, params: dict = None):
        """Track a database query."""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            entry = {
                "query": query[:200],
                "duration": duration,
                "timestamp": time.time()
            }
            self._queries.append(entry)

            if duration > self.SLOW_THRESHOLD:
                self._slow_queries.append(entry)
                logger.warning(f"Slow query ({duration:.3f}s): {query[:100]}")

            # Keep only last 1000 queries
            if len(self._queries) > 1000:
                self._queries = self._queries[-1000:]

    def get_slow_queries(self, limit: int = 20) -> list:
        """Get slow queries."""
        return sorted(self._slow_queries, key=lambda x: x["duration"], reverse=True)[:limit]

    def get_stats(self) -> dict:
        """Get query statistics."""
        if not self._queries:
            return {"total_queries": 0}

        durations = [q["duration"] for q in self._queries]
        return {
            "total_queries": len(self._queries),
            "slow_queries": len(self._slow_queries),
            "avg_duration": round(sum(durations) / len(durations), 3),
            "max_duration": round(max(durations), 3),
            "min_duration": round(min(durations), 3)
        }


class NPlusOneDetector:
    """Detect N+1 query patterns."""

    def __init__(self):
        self._query_counts: dict = defaultdict(int)
        self._alerts: list = []

    def record_query(self, query_type: str, entity: str):
        """Record a query for N+1 detection."""
        key = f"{query_type}:{entity}"
        self._query_counts[key] += 1

        # Alert if too many similar queries
        if self._query_counts[key] > 10:
            self._alerts.append({
                "type": "potential_n_plus_1",
                "query_type": query_type,
                "entity": entity,
                "count": self._query_counts[key]
            })

    def reset(self):
        """Reset query counts (call at end of request)."""
        self._query_counts.clear()

    def get_alerts(self) -> list:
        """Get N+1 alerts."""
        return self._alerts[-50:]


class ResponseCache:
    """Cache API responses."""

    def __init__(self, default_ttl: int = 60):
        self._cache: dict = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached response."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry["expires"]:
                return entry["data"]
            else:
                del self._cache[key]
        return None

    def set(self, key: str, data: Any, ttl: int = None):
        """Cache a response."""
        self._cache[key] = {
            "data": data,
            "expires": time.time() + (ttl or self._default_ttl)
        }

    def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        keys_to_delete = [k for k in self._cache if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]

    def clear(self):
        """Clear all cache."""
        self._cache.clear()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "memory_estimate_kb": len(str(self._cache)) / 1024
        }


# Global instances
query_profiler = QueryProfiler()
n_plus_one_detector = NPlusOneDetector()
response_cache = ResponseCache()


def cached_response(ttl: int = 60, key_func: Callable = None):
    """Decorator to cache API responses."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Check cache
            cached = response_cache.get(cache_key)
            if cached is not None:
                return cached

            # Execute and cache
            result = await func(*args, **kwargs)
            response_cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
