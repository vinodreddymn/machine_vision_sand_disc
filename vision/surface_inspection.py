"""Surface anomaly detection inside the usable abrasive region."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from vision.circle_detection import OuterCircleResult
from vision.hole_detection import HoleMeasurement


@dataclass(slots=True)
class SurfaceDefect:
    contour: np.ndarray
    area: float
    bbox: tuple[int, int, int, int]
    aspect_ratio: float
    severity: str


def detect_surface_defects(
    gray: np.ndarray,
    outer: OuterCircleResult,
    holes: list[HoleMeasurement],
    min_area: float,
) -> list[SurfaceDefect]:
    """Find local dark anomalies while excluding the outer edge and valid holes."""
    inspection_mask = np.zeros_like(gray)
    cv2.circle(inspection_mask, outer.center, max(int(outer.radius * 0.88), 1), 255, -1)
    for hole in holes:
        cv2.circle(inspection_mask, hole.center, round(hole.diameter), 0, -1)

    valid_pixels = gray[inspection_mask > 0]
    if valid_pixels.size == 0:
        return []
    nominal_intensity = float(np.median(valid_pixels))
    # Use a slightly less aggressive global dark threshold to catch moderate defects
    threshold_value = max(0, round(nominal_intensity - 12))
    _, dark_anomalies = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # Use smaller structuring element for local background to preserve medium-sized defects
    local_background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    blackhat = cv2.subtract(local_background, gray)
    _, thin_anomalies = cv2.threshold(blackhat, 8, 255, cv2.THRESH_BINARY)

    anomalies = cv2.bitwise_or(dark_anomalies, thin_anomalies)
    anomalies = cv2.bitwise_and(anomalies, inspection_mask)
    anomalies = cv2.morphologyEx(anomalies, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    anomalies = cv2.morphologyEx(anomalies, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))

    contours, _ = cv2.findContours(anomalies, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    defects: list[SurfaceDefect] = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        x, y, width, height = cv2.boundingRect(contour)
        long_side = max(width, height)
        short_side = max(min(width, height), 1)
        aspect_ratio = float(long_side / short_side)
        crack_like = aspect_ratio >= 4.0 and area >= max(min_area * 0.35, 20)
        if area < min_area and not crack_like:
            continue
        severity = "crack" if crack_like else "surface"
        defects.append(
            SurfaceDefect(
                contour=contour,
                area=area,
                bbox=(x, y, width, height),
                aspect_ratio=aspect_ratio,
                severity=severity,
            )
        )
    return defects
