"""Image loading and Qt conversion helpers."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtGui import QImage


def load_bgr_image(path: str | Path) -> np.ndarray:
    """Load an image in OpenCV BGR format and fail clearly on bad files."""
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to load image: {path}")
    return image


def bgr_to_qimage(image: np.ndarray) -> QImage:
    """Convert a BGR OpenCV image into an owned Qt RGB image."""
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    return QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888).copy()
