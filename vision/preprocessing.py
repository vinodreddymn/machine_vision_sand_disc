"""Preprocessing steps shared by downstream inspection modules."""

from __future__ import annotations

import cv2
import numpy as np


def preprocess_image(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return grayscale and denoised grayscale images for robust disk detection."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)
    blurred = cv2.bilateralFilter(equalized, 9, 75, 75)
    return equalized, blurred


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep only the largest connected foreground component."""
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num_labels <= 1:
        return mask
    largest_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    filtered = np.zeros_like(mask)
    filtered[labels == largest_label] = 255
    return filtered


def create_foreground_mask(blurred: np.ndarray) -> np.ndarray:
    """Segment the dominant disk body against a darker background."""
    _, global_mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive_mask = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5,
    )
    mask = cv2.bitwise_or(global_mask, adaptive_mask)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((11, 11), np.uint8))
    return keep_largest_component(mask)
