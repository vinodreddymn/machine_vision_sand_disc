"""Punched-hole detection and geometry measurements."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from vision.circle_detection import OuterCircleResult


@dataclass(slots=True)
class HoleMeasurement:
    center: tuple[int, int]
    diameter: float
    circularity: float
    equivalent_diameter: float
    axis_ratio: float
    solidity: float
    diameter_variation_ratio: float
    edge_irregularity_ratio: float
    radial_ratio: float
    angle_deg: float
    contour: np.ndarray

    @property
    def is_irregular(self) -> bool:
        return self.circularity < 0.78 or self.solidity < 0.94 or self.axis_ratio < 0.82

    @property
    def is_multi_diameter(self) -> bool:
        return self.diameter_variation_ratio > 0.18

    @property
    def is_torn(self) -> bool:
        return self.edge_irregularity_ratio > 0.22 or self.solidity < 0.88


def _circle_contour(center: tuple[float, float], radius: float, points: int = 32) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * np.pi, points, endpoint=False)
    circle_points = np.column_stack(
        (
            np.round(center[0] + np.cos(angles) * radius).astype(np.int32),
            np.round(center[1] + np.sin(angles) * radius).astype(np.int32),
        )
    )
    return circle_points.reshape(-1, 1, 2)


def _build_hole_measurement(contour: np.ndarray, outer: OuterCircleResult) -> HoleMeasurement | None:
    area = float(cv2.contourArea(contour))
    if area < 30:
        return None
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter == 0:
        return None

    (x, y), radius = cv2.minEnclosingCircle(contour)
    equivalent_diameter = float(np.sqrt(4 * area / np.pi))
    hull_area = float(cv2.contourArea(cv2.convexHull(contour)))
    solidity = area / hull_area if hull_area else 0.0
    axis_ratio = 1.0
    if len(contour) >= 5:
        (_, _), (axis_a, axis_b), _ = cv2.fitEllipse(contour)
        major_axis, minor_axis = sorted((axis_a, axis_b), reverse=True)
        axis_ratio = float(minor_axis / major_axis) if major_axis else 0.0

    points = contour.reshape(-1, 2).astype(np.float64)
    radial_distances = np.linalg.norm(points - np.array([x, y]), axis=1)
    median_radius = float(np.median(radial_distances)) if radial_distances.size else 0.0
    diameter_variation_ratio = (
        float((np.percentile(radial_distances, 90) - np.percentile(radial_distances, 10)) / median_radius)
        if median_radius
        else 1.0
    )
    edge_irregularity_ratio = (
        float(np.mean(np.abs(radial_distances - median_radius)) / median_radius) if median_radius else 1.0
    )
    distance = float(np.hypot(x - outer.center[0], y - outer.center[1]))
    radial_ratio = distance / outer.radius if outer.radius else 0.0
    if not 0.40 <= radial_ratio <= 0.88:
        return None

    angle = float(np.degrees(np.arctan2(-(y - outer.center[1]), x - outer.center[0])) % 360)
    return HoleMeasurement(
        center=(round(x), round(y)),
        diameter=float(radius * 2),
        circularity=float(4 * np.pi * area / (perimeter**2)),
        equivalent_diameter=equivalent_diameter,
        axis_ratio=axis_ratio,
        solidity=float(solidity),
        diameter_variation_ratio=diameter_variation_ratio,
        edge_irregularity_ratio=edge_irregularity_ratio,
        radial_ratio=radial_ratio,
        angle_deg=angle,
        contour=contour,
    )


def _detect_holes_from_contours(gray: np.ndarray, outer: OuterCircleResult) -> list[HoleMeasurement]:
    disk_mask = np.zeros_like(gray)
    cv2.circle(disk_mask, outer.center, max(outer.radius - 4, 1), 255, -1)
    _, global_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    adaptive_thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        15,
    )
    # Use conservative closing/opening to avoid merging nearby holes
    candidates = cv2.bitwise_or(global_thresh, adaptive_thresh)
    candidates = cv2.bitwise_and(candidates, disk_mask)
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_ERODE, np.ones((3, 3), np.uint8))

    contours, _ = cv2.findContours(candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    holes: list[HoleMeasurement] = []
    for contour in contours:
        measurement = _build_hole_measurement(contour, outer)
        if measurement is not None:
            holes.append(measurement)
    return holes


def _parse_hough_circles(
    gray: np.ndarray,
    outer: OuterCircleResult,
    existing_centers: list[tuple[int, int]],
    hole_diameter_range: tuple[int, int] | None = None,
) -> list[HoleMeasurement]:
    blurred = cv2.medianBlur(gray, 7)
    min_diameter, max_diameter = hole_diameter_range or (12, 70)
    min_radius = max(int(min_diameter / 2 * 0.75), 6)
    max_radius = min(int(max_diameter / 2 * 1.25), outer.radius - 10)
    if min_radius >= max_radius:
        return []

    disk_mask = np.zeros_like(gray)
    cv2.circle(disk_mask, outer.center, max(outer.radius - 6, 1), 255, -1)
    ring = cv2.bitwise_and(blurred, blurred, mask=disk_mask)
    circles = cv2.HoughCircles(
        ring,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(int(outer.radius * 0.15), 20),
        param1=80,
        param2=18,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if circles is None:
        return []

    holes: list[HoleMeasurement] = []
    for x, y, radius in circles[0]:
        center = (float(x), float(y))
        # avoid duplicates near already-detected centers (use relative threshold)
        min_sep = max(int(outer.radius * 0.06), 14)
        if any(np.hypot(x - cx, y - cy) < min_sep for cx, cy in existing_centers):
            continue
        contour = _circle_contour(center, radius)
        measurement = _build_hole_measurement(contour, outer)
        if measurement is not None:
            holes.append(measurement)
    return holes


def detect_holes(
    gray: np.ndarray,
    outer: OuterCircleResult,
    expected_hole_count: int | None = None,
    hole_diameter_range: tuple[int, int] | None = None,
) -> list[HoleMeasurement]:
    """Detect dark connected components inside the disk body."""
    # Prefer contour-based detection first to capture irregular and multi-diameter holes
    holes = _detect_holes_from_contours(gray, outer)
    if expected_hole_count is None:
        expected_hole_count = 0

    # If contours found fewer holes than expected, complement with Hough circles
    if len(holes) < expected_hole_count:
        additional = _parse_hough_circles(
            gray,
            outer,
            existing_centers=[hole.center for hole in holes],
            hole_diameter_range=hole_diameter_range,
        )
        holes.extend(additional)

    # Merge/dedupe using adaptive separation threshold; prefer contour measurements
    min_sep = max(int(outer.radius * 0.06), 14)
    unique_holes: list[HoleMeasurement] = []
    for hole in sorted(holes, key=lambda h: h.angle_deg):
        replaced = False
        for i, existing in enumerate(unique_holes):
            if np.hypot(hole.center[0] - existing.center[0], hole.center[1] - existing.center[1]) < min_sep:
                # prefer the contour-derived measurement if it looks irregular or multi-diameter
                if hole.circularity < existing.circularity or hole.diameter_variation_ratio > existing.diameter_variation_ratio:
                    unique_holes[i] = hole
                replaced = True
                break
        if not replaced:
            unique_holes.append(hole)

    return sorted(unique_holes, key=lambda hole: hole.angle_deg)


def angular_spacing_deviation(holes: list[HoleMeasurement]) -> float:
    """Return the largest angular spacing deviation from an even pattern."""
    if len(holes) < 2:
        return 360.0
    angles = [hole.angle_deg for hole in holes]
    spacings = np.diff(angles + [angles[0] + 360]).tolist()
    expected = 360.0 / len(holes)
    return float(max(abs(spacing - expected) for spacing in spacings))


def hole_pattern_circle_metrics(holes: list[HoleMeasurement]) -> tuple[float, float, tuple[float, float] | None]:
    """Measure how closely all hole centers lie on one circular bolt pattern.

    The residual ratio catches general off-circle placement. When at least five
    holes are available, the fitted ellipse axis ratio additionally catches an
    oval pattern that could still look evenly spaced to simpler checks.
    """
    if len(holes) < 3:
        return 1.0, 0.0, None

    points = np.array([hole.center for hole in holes], dtype=np.float64)
    x_values = points[:, 0]
    y_values = points[:, 1]
    design_matrix = np.column_stack((2 * x_values, 2 * y_values, np.ones(len(points))))
    rhs = x_values**2 + y_values**2
    center_x, center_y, radius_term = np.linalg.lstsq(design_matrix, rhs, rcond=None)[0]
    fitted_radius = float(np.sqrt(max(radius_term + center_x**2 + center_y**2, 0.0)))
    distances = np.sqrt((x_values - center_x) ** 2 + (y_values - center_y) ** 2)
    rms_residual = float(np.sqrt(np.mean((distances - fitted_radius) ** 2)))
    residual_ratio = rms_residual / fitted_radius if fitted_radius else 1.0

    ellipse_axis_ratio = 1.0
    if len(points) >= 5:
        ellipse = cv2.fitEllipse(points.astype(np.float32))
        major_axis, minor_axis = sorted(ellipse[1], reverse=True)
        ellipse_axis_ratio = float(minor_axis / major_axis) if major_axis else 0.0

    return residual_ratio, ellipse_axis_ratio, (float(center_x), float(center_y))
