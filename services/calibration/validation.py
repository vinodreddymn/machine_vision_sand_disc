"""Calibration validation logic."""

from __future__ import annotations

def validate_calibration(measured_px: float, active_mm_per_pixel: float, expected_mm: float, tolerance: float = 0.1) -> dict:
    """Validate if the measured pixels match the expected physical dimensions."""
    measured_mm = measured_px * active_mm_per_pixel
    error = abs(expected_mm - measured_mm)
    passed = error <= tolerance
    
    return {
        "expected_mm": expected_mm,
        "measured_mm": round(measured_mm, 3),
        "error_mm": round(error, 3),
        "passed": passed,
        "tolerance": tolerance
    }
