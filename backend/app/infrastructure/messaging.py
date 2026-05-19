import logging

logger = logging.getLogger(__name__)


def publish(queue: str, message: dict):
    """
    Publish a message to a queue.
    In development without RabbitMQ, this is a no-op that logs the message.
    """
    logger.info(f"[Messaging] Would publish to '{queue}': {message}")
