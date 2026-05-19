"""Filesystem helpers for inspection outputs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from config.settings import OUTPUT_DIR


def ensure_output_directories() -> None:
    """Create output folders used by PASS/FAIL exports."""
    for folder in ("passed", "failed", "logs"):
        (OUTPUT_DIR / folder).mkdir(parents=True, exist_ok=True)


def save_result_image(image: np.ndarray, passed: bool, stem: str) -> Path:
    """Save an annotated image using a timestamp-safe name."""
    ensure_output_directories()
    destination = OUTPUT_DIR / ("passed" if passed else "failed")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = destination / f"{stem}_{timestamp}.png"
    cv2.imwrite(str(path), image)
    return path
