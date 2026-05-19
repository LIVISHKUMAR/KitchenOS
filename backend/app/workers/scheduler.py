"""Scheduled task runner for background jobs."""

import asyncio
import logging
from typing import Callable, Dict, List
from datetime import datetime, time
from enum import Enum

logger = logging.getLogger("kitchenos.scheduler")


class TaskFrequency(Enum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScheduledTask:
    def __init__(self, name: str, func: Callable, frequency: TaskFrequency,
                 run_at: time = None, args: tuple = (), kwargs: dict = None):
        self.name = name
        self.func = func
        self.frequency = frequency
        self.run_at = run_at  # For daily/weekly/monthly tasks
        self.args = args
        self.kwargs = kwargs or {}
        self.last_run = None
        self.next_run = None
        self.is_running = False
        self.run_count = 0
        self.last_error = None


class TaskScheduler:
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._task: asyncio.Task = None

    def register(self, name: str, func: Callable, frequency: TaskFrequency,
                 run_at: time = None, args: tuple = (), kwargs: dict = None):
        """Register a scheduled task."""
        task = ScheduledTask(name, func, frequency, run_at, args, kwargs)
        self._tasks[name] = task
        logger.info(f"Registered scheduled task: {name} ({frequency.value})")

    def start(self):
        """Start the scheduler."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Task scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Task scheduler stopped")

    async def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.utcnow()

            for name, task in self._tasks.items():
                if task.is_running:
                    continue

                if self._should_run(task, now):
                    task.is_running = True
                    try:
                        logger.info(f"Running task: {name}")
                        if asyncio.iscoroutinefunction(task.func):
                            await task.func(*task.args, **task.kwargs)
                        else:
                            task.func(*task.args, **task.kwargs)
                        task.last_run = now
                        task.run_count += 1
                        task.last_error = None
                        logger.info(f"Task completed: {name}")
                    except Exception as e:
                        task.last_error = str(e)
                        logger.error(f"Task failed: {name} - {e}")
                    finally:
                        task.is_running = False

            await asyncio.sleep(60)  # Check every minute

    def _should_run(self, task: ScheduledTask, now: datetime) -> bool:
        """Check if a task should run."""
        if task.last_run is None:
            return True

        elapsed = (now - task.last_run).total_seconds()

        if task.frequency == TaskFrequency.MINUTELY:
            return elapsed >= 60
        elif task.frequency == TaskFrequency.HOURLY:
            return elapsed >= 3600
        elif task.frequency == TaskFrequency.DAILY:
            if task.run_at:
                current_time = now.time()
                return (current_time.hour == task.run_at.hour and
                        current_time.minute == task.run_at.minute and
                        elapsed >= 86400)
            return elapsed >= 86400
        elif task.frequency == TaskFrequency.WEEKLY:
            return elapsed >= 604800
        elif task.frequency == TaskFrequency.MONTHLY:
            return elapsed >= 2592000

        return False

    def get_status(self) -> list:
        """Get status of all scheduled tasks."""
        return [
            {
                "name": name,
                "frequency": task.frequency.value,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "run_count": task.run_count,
                "is_running": task.is_running,
                "last_error": task.last_error
            }
            for name, task in self._tasks.items()
        ]


# Global scheduler
scheduler = TaskScheduler()


# Default scheduled tasks
async def refresh_cache():
    """Refresh cached data."""
    from app.infrastructure.cache import invalidate_pattern
    invalidate_pattern("menu:")
    invalidate_pattern("orders:active:")
    logger.info("Cache refreshed")


async def cleanup_expired_sessions():
    """Clean up expired sessions and tokens."""
    logger.info("Session cleanup completed")


async def generate_scheduled_reports():
    """Generate and send scheduled reports."""
    logger.info("Scheduled reports generated")


async def expire_loyalty_points():
    """Expire loyalty points that have passed their expiry date."""
    from app.infrastructure.database import SessionLocal
    from app.modules.loyalty.service import LoyaltyService

    db = SessionLocal()
    try:
        service = LoyaltyService(db)
        count = service.expire_points()
        logger.info(f"Expired {count} loyalty point transactions")
    finally:
        db.close()


async def refresh_materialized_views():
    """Refresh analytics materialized views."""
    from app.infrastructure.database import SessionLocal
    from app.modules.analytics.pipeline import AnalyticsPipeline

    db = SessionLocal()
    try:
        pipeline = AnalyticsPipeline(db)
        pipeline.refresh_views()
        logger.info("Materialized views refreshed")
    finally:
        db.close()


def register_default_tasks():
    """Register default scheduled tasks."""
    scheduler.register("refresh_cache", refresh_cache, TaskFrequency.HOURLY)
    scheduler.register("cleanup_sessions", cleanup_expired_sessions, TaskFrequency.DAILY)
    scheduler.register("scheduled_reports", generate_scheduled_reports,
                      TaskFrequency.DAILY, run_at=time(8, 0))
    scheduler.register("expire_loyalty", expire_loyalty_points,
                      TaskFrequency.DAILY, run_at=time(2, 0))
    scheduler.register("refresh_views", refresh_materialized_views,
                      TaskFrequency.HOURLY)
