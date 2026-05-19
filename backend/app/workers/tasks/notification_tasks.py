import logging

logger = logging.getLogger(__name__)


def send_order_ready_notification(order_id: str):
    """
    Send notification when order is ready.
    In development, this just logs.
    """
    logger.info(f"[Notification] Order {order_id} is ready for pickup")


class send_order_ready_notification:
    """Mock Celery task-like object for development."""

    @staticmethod
    def delay(order_id: str):
        logger = logging.getLogger(__name__)
        logger.info(f"[Notification] Order {order_id} is ready for pickup")
