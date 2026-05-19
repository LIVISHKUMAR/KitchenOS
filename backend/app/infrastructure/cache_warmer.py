"""Cache warming and invalidation strategies."""

import asyncio
from typing import Callable, Dict, List
from datetime import datetime
import threading
import time


class CacheWarmer:
    """Pre-populate cache on startup and scheduled refresh."""

    def __init__(self):
        self._warming_tasks: Dict[str, Callable] = {}
        self._refresh_intervals: Dict[str, int] = {}  # seconds
        self._running = False
        self._thread = None

    def register(self, key: str, loader: Callable, interval: int = 300):
        """Register a cache warming task."""
        self._warming_tasks[key] = loader
        self._refresh_intervals[key] = interval

    def start(self):
        """Start background cache warming."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop background cache warming."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self):
        """Background loop for cache refresh."""
        while self._running:
            for key, loader in self._warming_tasks.items():
                try:
                    loader()
                except Exception as e:
                    print(f"Cache warming failed for {key}: {e}")

            # Sleep for minimum interval
            min_interval = min(self._refresh_intervals.values()) if self._refresh_intervals else 300
            time.sleep(min_interval)

    def warm_all(self):
        """Warm all registered caches immediately."""
        results = {}
        for key, loader in self._warming_tasks.items():
            try:
                loader()
                results[key] = "success"
            except Exception as e:
                results[key] = f"failed: {e}"
        return results


class CacheInvalidator:
    """Cache invalidation strategies."""

    def __init__(self):
        self._invalidation_rules: Dict[str, List[str]] = {}

    def register_rule(self, event: str, cache_keys: List[str]):
        """Register cache invalidation rule.

        When event occurs, invalidate the specified cache keys.
        """
        self._invalidation_rules[event] = cache_keys

    def invalidate(self, event: str, cache_delete_fn: Callable):
        """Invalidate caches for an event."""
        keys = self._invalidation_rules.get(event, [])
        for key in keys:
            try:
                cache_delete_fn(key)
            except Exception:
                pass

    def get_rules(self) -> Dict[str, List[str]]:
        """Get all invalidation rules."""
        return self._invalidation_rules.copy()


# Global instances
cache_warmer = CacheWarmer()
cache_invalidator = CacheInvalidator()

# Register default invalidation rules
cache_invalidator.register_rule("menu.updated", ["menu:items:*", "menu:categories:*"])
cache_invalidator.register_rule("order.created", ["orders:active:*", "tables:status:*"])
cache_invalidator.register_rule("order.completed", ["orders:active:*", "tables:status:*", "sales:daily:*"])
cache_invalidator.register_rule("payment.completed", ["sales:daily:*", "orders:active:*"])
cache_invalidator.register_rule("inventory.updated", ["inventory:items:*", "inventory:low-stock:*"])
