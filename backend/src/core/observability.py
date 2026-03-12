from __future__ import annotations

import logging
import logging.config
from typing import Any, Dict

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

def configure_observability() -> None:
    """Apply logging configuration at runtime."""

    logging.config.dictConfig(LOGGING_CONFIG)  # type: ignore[attr-defined]
