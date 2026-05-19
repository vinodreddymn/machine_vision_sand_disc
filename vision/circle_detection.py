"""Outer disk profile detection and edge-quality measurements."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(slots=True)
class OuterCircleResult:
    center: tuple[int, int]
    radius: int
    contour: np.ndarray
    area: float
    circularity: float
    area_loss_ratio: float
    radial_deviation_ratio: float
    solidity: float


def detect_outer_circle(mask: np.ndarray) -> OuterCircleResult | None:
    """Find the largest external contour and fit a minimum enclosing circle."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    perimeter = float(cv2.arcLength(contour, True))
    circularity = 0.0 if perimeter == 0 else float(4 * np.pi * area / (perimeter**2))
    (x, y), radius = cv2.minEnclosingCircle(contour)
    ideal_area = float(np.pi * radius**2)
    area_loss_ratio = max(0.0, 1.0 - area / ideal_area) if ideal_area else 1.0
    contour_points = contour.reshape(-1, 2).astype(np.float64)
    radial_distances = np.linalg.norm(contour_points - np.array([x, y]), axis=1)
    radial_deviation_ratio = (
        float(np.std(radial_distances) / np.mean(radial_distances)) if radial_distances.size else 1.0
    )
    hull_area = float(cv2.contourArea(cv2.convexHull(contour)))
    solidity = area / hull_area if hull_area else 0.0
    return OuterCircleResult(
        center=(round(x), round(y)),
        radius=round(radius),
        contour=contour,
        area=area,
        circularity=circularity,
        area_loss_ratio=area_loss_ratio,
        radial_deviation_ratio=radial_deviation_ratio,
        solidity=float(solidity),
    )
