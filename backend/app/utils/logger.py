"""
Production logging configuration for SquadSync backend.
"""

import logging
import sys

from app.config import settings


def setup_logging() -> None:
    """Configures application-wide logging with formatted output."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging_config = {
        "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
        "level": log_level,
        "handlers": [logging.StreamHandler(sys.stdout)],
    }

    logging.basicConfig(**logging_config)

    # Silence noisy external libraries in production
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
