"""Structured logging with request ID correlation."""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable for request ID (thread-safe, async-safe)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set request ID in context."""
    request_id_var.set(request_id)


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())[:12]


class RequestIDFilter(logging.Filter):
    """Add request_id to all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or '-'
        return True


def setup_logging(debug: bool = False) -> None:
    """Configure structured logging for the application.

    Args:
        debug: If True, use human-readable format. If False, use JSON format.
    """
    # Remove existing handlers
    root = logging.getLogger()
    root.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIDFilter())

    if debug:
        # Human-readable format for development
        format_str = (
            "%(asctime)s | %(levelname)-8s | %(request_id)s | "
            "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )
        handler.setFormatter(logging.Formatter(format_str, datefmt="%H:%M:%S"))
    else:
        # JSON format for production
        import json
        from datetime import datetime, timezone

        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "request_id": getattr(record, 'request_id', '-'),
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info and record.exc_info[0]:
                    log_entry["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_entry)

        handler.setFormatter(JSONFormatter())

    root.addHandler(handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if debug else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
