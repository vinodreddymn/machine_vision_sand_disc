"""Regression tests for the first-pass classical inspection pipeline."""

from __future__ import annotations

import cv2
import numpy as np

from config.settings import load_tolerances
from vision.defect_analysis import inspect_disk
from vision.overlay_renderer import render_overlay


def build_synthetic_disk(
    with_surface_defect: bool = False,
    oval_pattern: bool = False,
    irregular_hole: bool = False,
    multi_diameter_hole: bool = False,
    crack: bool = False,
) -> np.ndarray:
    """Create a controlled disk image matching default tolerances."""
    image = np.zeros((600, 600, 3), dtype=np.uint8)
    center = (300, 300)
    cv2.circle(image, center, 220, (190, 190, 190), -1)
    expected_holes = load_tolerances()["expected_hole_count"]
    for angle in np.linspace(0, 360, expected_holes, endpoint=False):
        radians = np.radians(angle)
        radius_x = 150 if oval_pattern else 130
        radius_y = 105 if oval_pattern else 130
        hole_center = (
            round(center[0] + radius_x * np.cos(radians)),
            round(center[1] - radius_y * np.sin(radians)),
        )
        radius = 26 if multi_diameter_hole and angle == 72 else 18
        cv2.circle(image, hole_center, radius, (0, 0, 0), -1)
        if irregular_hole and angle == 0:
            cv2.rectangle(image, (hole_center[0] + 10, hole_center[1] - 5), (hole_center[0] + 27, hole_center[1] + 5), (0, 0, 0), -1)
    if with_surface_defect:
        cv2.rectangle(image, (280, 210), (330, 250), (70, 70, 70), -1)
    if crack:
        cv2.line(image, (220, 255), (370, 265), (40, 40, 40), 4)
    return image


def test_nominal_disk_passes() -> None:
    result = inspect_disk(build_synthetic_disk())
    assert result.passed is True
    assert result.measurements["hole_count"] == load_tolerances()["expected_hole_count"]


def test_surface_defect_fails_and_overlay_renders() -> None:
    image = build_synthetic_disk(with_surface_defect=True)
    result = inspect_disk(image)
    overlay = render_overlay(image, result)
    assert result.passed is False
    assert result.measurements["surface_defect_count"] >= 1
    assert overlay.shape == image.shape


def test_overlay_draws_circle_for_valid_hole_pattern() -> None:
    image = build_synthetic_disk()
    result = inspect_disk(image)
    overlay = render_overlay(image, result)

    top_of_pattern = (300, 170)

    assert tuple(overlay[top_of_pattern[1], top_of_pattern[0]]) == (0, 220, 0)


def test_oval_hole_pattern_fails() -> None:
    image = build_synthetic_disk(oval_pattern=True)
    result = inspect_disk(image)
    overlay = render_overlay(image, result)

    assert result.passed is False
    assert result.measurements["hole_pattern_ellipse_axis_ratio"] < 0.92
    assert "Hole-center pattern is oval instead of circular." in result.defects
    assert np.any(np.all(overlay == (0, 0, 255), axis=2))


def test_irregular_hole_fails() -> None:
    result = inspect_disk(build_synthetic_disk(irregular_hole=True))

    assert result.passed is False
    assert result.measurements["irregular_hole_count"] >= 1
    assert any("irregular" in defect.lower() for defect in result.defects)


def test_multi_diameter_hole_fails() -> None:
    result = inspect_disk(build_synthetic_disk(multi_diameter_hole=True))

    assert result.passed is False
    assert result.measurements["hole_diameter_spread_ratio"] > 0.18
    assert "Hole diameters are inconsistent across the pattern." in result.defects


def test_crack_like_surface_defect_fails() -> None:
    result = inspect_disk(build_synthetic_disk(crack=True))

    assert result.passed is False
    assert any(defect.severity == "crack" for defect in result.surface_defects)
    assert "Crack-like surface defect detected." in result.defects
