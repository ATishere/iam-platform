"""Structured logging configuration.

For Phase 1 we use stdlib logging with a JSON-ish format. Sensitive
field redaction is enforced at audit-service level (Phase 4), not here.
"""

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Tắt noise của uvicorn access log trùng với app log
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
