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


def _circle_contour(center: tuple[float, float], radius: float, points: int = 64) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * np.pi, points, endpoint=False)
    circle_points = np.column_stack(
        (
            np.round(center[0] + np.cos(angles) * radius).astype(np.int32),
            np.round(center[1] + np.sin(angles) * radius).astype(np.int32),
        )
    )
    return circle_points.reshape(-1, 1, 2)


def _build_outer_circle_result(contour: np.ndarray) -> OuterCircleResult:
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


def _outer_circle_from_hough(blurred: np.ndarray, min_radius: int, max_radius: int) -> OuterCircleResult | None:
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(min_radius, 24),
        param1=80,
        param2=22,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if circles is None:
        return None

    best_circle = max(circles[0], key=lambda circle: circle[2])
    center = (float(best_circle[0]), float(best_circle[1]))
    radius = float(best_circle[2])
    contour = _circle_contour(center, radius)
    return _build_outer_circle_result(contour)


def _outer_circle_from_edges(gray: np.ndarray, min_radius: int, max_radius: int) -> OuterCircleResult | None:
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(best_contour) < np.pi * (min_radius ** 2) * 0.4:
        return None

    return _build_outer_circle_result(best_contour)


def detect_outer_circle(mask: np.ndarray, blurred: np.ndarray | None = None) -> OuterCircleResult | None:
    """Find the disk outer profile using contour, edge, and Hough fallbacks."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    outer: OuterCircleResult | None = None
    if contours:
        best_contour = max(contours, key=cv2.contourArea)
        outer = _build_outer_circle_result(best_contour)

    if blurred is not None:
        height, width = blurred.shape[:2]
        min_radius = max(int(min(height, width) * 0.10), 80)
        max_radius = min(int(min(height, width) * 0.60), 500)

        if outer is None:
            edge_result = _outer_circle_from_edges(blurred, min_radius, max_radius)
            if edge_result is not None:
                return edge_result
            return _outer_circle_from_hough(blurred, min_radius, max_radius)

        low_quality = (
            outer.circularity < 0.80
            or outer.area_loss_ratio > 0.18
            or outer.radial_deviation_ratio > 0.12
        )
        if low_quality:
            edge_result = _outer_circle_from_edges(blurred, min_radius, max_radius)
            if edge_result is not None:
                return edge_result
            hough_result = _outer_circle_from_hough(blurred, min_radius, max_radius)
            if hough_result is not None:
                return hough_result

    return outer
