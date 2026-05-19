"""Background webhook delivery worker."""

import asyncio
import logging
from datetime import datetime

from app.infrastructure.database import SessionLocal
from app.modules.webhook.delivery import WebhookDeliveryService

logger = logging.getLogger("kitchenos.webhook_worker")


class WebhookWorker:
    """Background worker for processing webhook deliveries."""

    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval
        self._running = False
        self._task: asyncio.Task = None

    def start(self):
        """Start the webhook worker."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Webhook worker started")

    def stop(self):
        """Stop the webhook worker."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Webhook worker stopped")

    async def _run_loop(self):
        """Main worker loop."""
        while self._running:
            try:
                db = SessionLocal()
                try:
                    service = WebhookDeliveryService(db)
                    result = await service.process_pending_deliveries(limit=50)
                    if result["processed"] > 0:
                        logger.info(
                            f"Webhook delivery: {result['processed']} processed, "
                            f"{result['success']} success, {result['failed']} failed"
                        )
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Webhook worker error: {e}")

            await asyncio.sleep(self.poll_interval)

    def get_status(self) -> dict:
        """Get worker status."""
        return {
            "running": self._running,
            "poll_interval": self.poll_interval
        }


# Global worker
webhook_worker = WebhookWorker()
