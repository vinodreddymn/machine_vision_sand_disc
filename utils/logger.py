"""Logging configuration shared by GUI and future background services."""

from __future__ import annotations

import logging
from pathlib import Path

from config.settings import LOG_DIR


def configure_logging() -> None:
    """Configure console and rolling-session file logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(Path(LOG_DIR) / "inspection.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
