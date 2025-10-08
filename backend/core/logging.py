"""
Logging configuration for the backend
"""

import sys
from typing import Any, Dict

import structlog


def setup_logging() -> None:
    """Setup structured logging"""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    import logging

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a logger instance"""
    return structlog.get_logger(name)


def log_request_info(
    request_id: str, method: str, path: str, **kwargs
) -> Dict[str, Any]:
    """Create standardized request log info"""
    return {"request_id": request_id, "method": method, "path": path, **kwargs}
