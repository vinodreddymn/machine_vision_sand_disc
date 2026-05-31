from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from disk_vision_inspector.shared.constants import LOG_DIR


def configure_service_logging(*, service_name: str, level: int = logging.INFO) -> None:
    """Configure per-service console + rotating file logging.

    This is intentionally independent of `utils/logger.py` to avoid changing
    behavior of the legacy runtime while enabling industrial-grade logging
    for new modular services.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logfile = Path(LOG_DIR) / f"{service_name}.log"

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers if called multiple times.
    if any(isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == str(logfile) for h in root.handlers):
        return

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(logfile, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8")
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

