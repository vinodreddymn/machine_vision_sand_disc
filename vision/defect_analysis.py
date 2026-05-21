"""Inspection orchestration and structured pass/fail decisions."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import cv2

from config.settings import load_tolerances
from vision.circle_detection import OuterCircleResult, detect_outer_circle
from vision.hole_detection import (
    HoleMeasurement,
    angular_spacing_deviation,
    detect_holes,
    hole_pattern_circle_metrics,
)
from vision.preprocessing import create_foreground_mask, preprocess_image
from vision.surface_inspection import SurfaceDefect, detect_surface_defects


@dataclass(slots=True)
class InspectionResult:
    passed: bool
    outer_circle: OuterCircleResult | None
    holes: list[HoleMeasurement] = field(default_factory=list)
    surface_defects: list[SurfaceDefect] = field(default_factory=list)
    measurements: dict[str, float | int | str] = field(default_factory=dict)
    defects: list[str] = field(default_factory=list)


def inspect_disk(image: np.ndarray) -> InspectionResult:
    """Run the complete phase-one inspection pipeline."""
    tolerances = load_tolerances()
    # Use CLAHE-equalized gray for geometry/hole detection but original grayscale for surface defect contrast
    equalized_gray, blurred = preprocess_image(image)
    orig_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = create_foreground_mask(blurred)
    outer = detect_outer_circle(mask, blurred)
    if outer is None:
        return InspectionResult(
            passed=False,
            outer_circle=None,
            defects=["Outer disk profile was not detected."],
            measurements={"status": "No disk detected"},
        )

    radius_limits = tolerances["outer_radius_px"]
    outer_defects: list[str] = []
    if not radius_limits["min"] <= outer.radius <= radius_limits["max"]:
        outer_defects.append("Outer radius is outside configured tolerance.")
    if outer.circularity < tolerances["outer_edge"]["circularity_min"]:
        outer_defects.append("Outer edge circularity is below tolerance.")
    if outer.area_loss_ratio > tolerances["outer_edge"]["max_area_loss_ratio"]:
        outer_defects.append("Outer edge appears cut or incomplete.")
    if outer.radial_deviation_ratio > 0.035 or outer.solidity < 0.965:
        outer_defects.append("Outer edge is irregular or torn.")

    measurements: dict[str, float | int | str] = {
        "outer_radius_px": outer.radius,
        "outer_diameter_px": outer.radius * 2,
        "outer_circularity": round(outer.circularity, 3),
        "edge_area_loss_ratio": round(outer.area_loss_ratio, 3),
        "outer_radial_deviation_ratio": round(outer.radial_deviation_ratio, 4),
        "outer_solidity": round(outer.solidity, 4),
        "hole_count": 0,
        "avg_hole_diameter_px": 0.0,
        "hole_diameter_spread_ratio": 0.0,
        "irregular_hole_count": 0,
        "multi_diameter_hole_count": 0,
        "torn_hole_count": 0,
        "max_hole_spacing_deviation_deg": 0.0,
        "hole_pattern_circle_residual_ratio": 0.0,
        "hole_pattern_ellipse_axis_ratio": 0.0,
        "surface_defect_count": 0,
        "surface_defect_area_ratio": 0.0,
    }

    if outer_defects and not (radius_limits["min"] <= outer.radius <= radius_limits["max"]):
        return InspectionResult(
            passed=False,
            outer_circle=outer,
            holes=[],
            surface_defects=[],
            measurements=measurements,
            defects=outer_defects,
        )

    holes = detect_holes(
        equalized_gray,
        outer,
        expected_hole_count=tolerances["expected_hole_count"],
        hole_diameter_range=(
            tolerances["hole_diameter_px"]["min"],
            tolerances["hole_diameter_px"]["max"],
        ),
    )

    hole_defects: list[str] = []
    expected_holes = tolerances["expected_hole_count"]
    if len(holes) != expected_holes:
        hole_defects.append(f"Hole count mismatch: expected {expected_holes}, found {len(holes)}.")

    diameter_limits = tolerances["hole_diameter_px"]
    invalid_diameters = [
        hole for hole in holes if not diameter_limits["min"] <= hole.diameter <= diameter_limits["max"]
    ]
    if invalid_diameters:
        hole_defects.append(f"{len(invalid_diameters)} hole(s) have diameter outside tolerance.")

    invalid_shapes = [hole for hole in holes if hole.circularity < tolerances["hole_circularity_min"]]
    if invalid_shapes:
        hole_defects.append(f"{len(invalid_shapes)} hole(s) are not circular enough.")

    irregular_holes = [hole for hole in holes if hole.is_irregular]
    if irregular_holes:
        hole_defects.append(f"{len(irregular_holes)} hole(s) are irregular.")

    multi_diameter_holes = [hole for hole in holes if hole.is_multi_diameter]
    if multi_diameter_holes:
        hole_defects.append(f"{len(multi_diameter_holes)} hole(s) show multiple diameters.")

    hole_diameters = [hole.equivalent_diameter for hole in holes]
    hole_diameter_spread_ratio = (
        float(np.ptp(hole_diameters) / np.median(hole_diameters)) if hole_diameters else 0.0
    )
    if len(holes) == expected_holes and hole_diameter_spread_ratio > 0.18:
        hole_defects.append("Hole diameters are inconsistent across the pattern.")

    torn_holes = [hole for hole in holes if hole.is_torn]
    if torn_holes:
        hole_defects.append(f"{len(torn_holes)} hole(s) appear torn or cracked.")

    radial_values = [hole.radial_ratio for hole in holes]
    radial_spread = float(np.ptp(radial_values)) if radial_values else 0.0
    if radial_spread > tolerances["hole_position"]["radial_tolerance_ratio"]:
        hole_defects.append("Hole radial positions are inconsistent.")

    spacing_deviation = angular_spacing_deviation(holes)
    if len(holes) == expected_holes and spacing_deviation > tolerances["hole_position"]["angular_spacing_tolerance_deg"]:
        hole_defects.append("Hole angular spacing is outside tolerance.")

    pattern_residual_ratio, pattern_ellipse_axis_ratio, _ = hole_pattern_circle_metrics(holes)
    if len(holes) == expected_holes:
        if pattern_residual_ratio > tolerances["hole_position"]["max_pattern_circle_residual_ratio"]:
            hole_defects.append("Hole centers do not lie on a uniform circular pattern.")
        if pattern_ellipse_axis_ratio < tolerances["hole_position"]["min_pattern_ellipse_axis_ratio"]:
            hole_defects.append("Hole-center pattern is oval instead of circular.")

    surface_defects = detect_surface_defects(
        orig_gray,
        outer,
        holes,
        min_area=tolerances["surface"]["min_defect_area_px"],
    )

    surface_issue_defects: list[str] = []
    total_surface_area = sum(defect.area for defect in surface_defects)
    surface_ratio = total_surface_area / outer.area if outer.area else 1.0
    if surface_defects:
        surface_issue_defects.append(f"{len(surface_defects)} surface defect(s) detected.")
    if surface_ratio > tolerances["surface"]["max_total_defect_area_ratio"]:
        surface_issue_defects.append("Surface peel or texture damage exceeds tolerance.")
    if any(defect.severity == "crack" for defect in surface_defects):
        surface_issue_defects.append("Crack-like surface defect detected.")

    defects = outer_defects + hole_defects + surface_issue_defects
    measurements.update(
        {
            "hole_count": len(holes),
            "avg_hole_diameter_px": round(float(np.mean([hole.diameter for hole in holes])), 2) if holes else 0.0,
            "hole_diameter_spread_ratio": round(hole_diameter_spread_ratio, 4),
            "irregular_hole_count": len(irregular_holes),
            "multi_diameter_hole_count": len(multi_diameter_holes),
            "torn_hole_count": len(torn_holes),
            "max_hole_spacing_deviation_deg": round(spacing_deviation, 2),
            "hole_pattern_circle_residual_ratio": round(pattern_residual_ratio, 4),
            "hole_pattern_ellipse_axis_ratio": round(pattern_ellipse_axis_ratio, 4),
            "surface_defect_count": len(surface_defects),
            "surface_defect_area_ratio": round(surface_ratio, 4),
        }
    )
    return InspectionResult(
        passed=not defects,
        outer_circle=outer,
        holes=holes,
        surface_defects=surface_defects,
        measurements=measurements,
        defects=defects,
    )
