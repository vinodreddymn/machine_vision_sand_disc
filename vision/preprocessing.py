"""Preprocessing steps shared by downstream inspection modules."""

from __future__ import annotations

import cv2
import numpy as np


def preprocess_image(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return grayscale and denoised grayscale images."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return gray, blurred


def create_foreground_mask(blurred: np.ndarray) -> np.ndarray:
    """Segment the dominant disk body against a darker background."""
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask
