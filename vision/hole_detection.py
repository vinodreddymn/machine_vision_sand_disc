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


def detect_holes(gray: np.ndarray, outer: OuterCircleResult) -> list[HoleMeasurement]:
    """Detect dark connected components inside the disk body."""
    disk_mask = np.zeros_like(gray)
    cv2.circle(disk_mask, outer.center, max(outer.radius - 4, 1), 255, -1)
    _, dark_regions = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    candidates = cv2.bitwise_and(dark_regions, disk_mask)
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    contours, _ = cv2.findContours(candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    holes: list[HoleMeasurement] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 30:
            continue
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
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
        if not 0.35 <= radial_ratio <= 0.92:
            continue
        angle = float(np.degrees(np.arctan2(-(y - outer.center[1]), x - outer.center[0])) % 360)
        holes.append(
            HoleMeasurement(
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
        )
    return sorted(holes, key=lambda hole: hole.angle_deg)


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
