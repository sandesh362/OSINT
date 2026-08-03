"""Central logging setup used by all features."""

import logging

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure the process logger once, using the configured log level."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced application logger."""
    return logging.getLogger(name)
