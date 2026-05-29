"""Lightweight rule-based anomaly score for assisted labeling."""

from __future__ import annotations

from config.settings import load_tolerances
from vision.defect_analysis import InspectionResult


def anomaly_score(result: InspectionResult) -> float:
    """Return a 0-100 score where higher means more likely defective."""
    if result.outer_circle is None:
        return 100.0
    tolerances = load_tolerances()
    score = 0.0
    measurements = result.measurements
    expected_holes = tolerances["expected_hole_count"]

    score += min(25.0, abs(int(measurements.get("hole_count", 0)) - expected_holes) * 8.0)
    score += min(18.0, float(measurements.get("surface_defect_count", 0)) * 6.0)
    score += min(18.0, float(measurements.get("surface_defect_area_ratio", 0.0)) * 200.0)
    score += min(14.0, float(measurements.get("hole_diameter_spread_ratio", 0.0)) * 60.0)
    score += min(12.0, float(measurements.get("outer_radial_deviation_ratio", 0.0)) * 200.0)
    score += min(8.0, max(0.0, 1.0 - float(measurements.get("outer_circularity", 1.0))) * 40.0)
    score += min(10.0, len(result.defects) * 4.0)
    if not result.passed:
        score = max(score, 55.0)
    return round(min(100.0, score), 2)


def assisted_prediction(result: InspectionResult) -> str:
    """Return GOOD/DEFECT from the classical result and anomaly score."""
    if result.passed and anomaly_score(result) < 50.0:
        return "GOOD"
    return "DEFECT"
