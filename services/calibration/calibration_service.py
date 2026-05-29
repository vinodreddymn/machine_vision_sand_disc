"""Calibration service to manage calibration state and business logic."""

from __future__ import annotations

from typing import Any

from services.calibration.circle_detector import detect_calibration_circles
from storage.postgres import PostgresInspectionRepository

class CalibrationService:
    def __init__(self, db: PostgresInspectionRepository):
        self.db = db

    def get_status(self, camera_id: str) -> dict[str, Any]:
        """Get the current active calibration status."""
        active = self.db.get_active_calibration(camera_id)
        if active:
            # We must convert datetime to ISO string for JSON serialization
            cal_date = active["calibration_date"]
            if hasattr(cal_date, "isoformat"):
                cal_date = cal_date.isoformat()
                
            return {
                "calibrated": True,
                "calibration_date": cal_date,
                "mm_per_pixel": active["mm_per_pixel"],
                "reference_od_mm": active["reference_od_mm"],
                "reference_hole_mm": active["reference_hole_mm"],
            }
        return {"calibrated": False}

    def process_calibration_frame(self, image) -> dict[str, Any] | None:
        """Process an image to detect calibration circles and return pixel dimensions."""
        result = detect_calibration_circles(image)
        if result:
            return {
                "outer_diameter_px": result["outer_diameter_px"],
                "hole_diameter_px": result["hole_diameter_px"],
                "overlay": result["overlay"]
            }
        return None

    def save_calibration(
        self,
        camera_id: str,
        outer_diameter_px: float,
        reference_od_mm: float,
        reference_hole_mm: float
    ) -> dict[str, Any]:
        """Calculate mm_per_pixel and save to database."""
        mm_per_pixel = reference_od_mm / outer_diameter_px
        record_id = self.db.save_calibration(
            camera_id=camera_id,
            mm_per_pixel=mm_per_pixel,
            reference_od_mm=reference_od_mm,
            reference_hole_mm=reference_hole_mm
        )
        return {
            "status": "success",
            "record_id": record_id,
            "mm_per_pixel": mm_per_pixel
        }

    def get_history(self, camera_id: str) -> list[dict[str, Any]]:
        """Retrieve calibration history."""
        records = self.db.get_calibration_history(camera_id)
        # Convert datetimes
        for rec in records:
            if hasattr(rec["calibration_date"], "isoformat"):
                rec["calibration_date"] = rec["calibration_date"].isoformat()
        return records
