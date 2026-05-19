"""Redis caching layer for frequently accessed data."""

import json
from typing import Optional, Any
from functools import wraps
import hashlib

from app.core.config import settings

# Redis client (lazy initialization)
_redis_client = None


def get_redis():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


def cache_key(*args) -> str:
    """Generate a cache key from arguments."""
    key_str = ":".join(str(a) for a in args)
    return f"kitchenos:{hashlib.md5(key_str.encode()).hexdigest()}"


def get_cached(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = get_redis()
    if r is None:
        return None
    try:
        value = r.get(key)
        if value:
            return json.loads(value)
    except Exception:
        pass
    return None


def set_cached(key: str, value: Any, ttl: Optional[int] = None):
    """Set value in cache."""
    r = get_redis()
    if r is None:
        return
    try:
        ttl = ttl or settings.CACHE_TTL
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def delete_cached(key: str):
    """Delete value from cache."""
    r = get_redis()
    if r is None:
        return
    try:
        r.delete(key)
    except Exception:
        pass


def invalidate_pattern(pattern: str):
    """Delete all keys matching a pattern."""
    r = get_redis()
    if r is None:
        return
    try:
        keys = r.keys(f"kitchenos:{pattern}*")
        if keys:
            r.delete(*keys)
    except Exception:
        pass


def cached(ttl: int = 300, prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key = cache_key(prefix or func.__name__, *args, *sorted(kwargs.items()))

            # Try cache first
            result = get_cached(key)
            if result is not None:
                return result

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                set_cached(key, result, ttl)

            return result
        return wrapper
    return decorator


# Cache key constants
CACHE_KEYS = {
    "menu_items": "menu:items",
    "menu_categories": "menu:categories",
    "tenant_config": "tenant:config",
    "branch_config": "branch:config",
    "active_orders": "orders:active",
    "table_status": "tables:status",
    "daily_sales": "sales:daily",
    "tax_config": "tax:config",
}


def invalidate_menu_cache(branch_id: str):
    """Invalidate all menu-related cache for a branch."""
    invalidate_pattern(f"{CACHE_KEYS['menu_items']}:{branch_id}")
    invalidate_pattern(f"{CACHE_KEYS['menu_categories']}:{branch_id}")


def invalidate_order_cache(branch_id: str):
    """Invalidate order-related cache for a branch."""
    invalidate_pattern(f"{CACHE_KEYS['active_orders']}:{branch_id}")
    invalidate_pattern(f"{CACHE_KEYS['table_status']}:{branch_id}")
