"""Save original, ROI, overlay, and metadata for labeled inspections."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from config.settings import DATASET_DIR, MODE_DATA_COLLECTION
from dataset.label_manager import DEFECT_LABEL, GOOD_LABEL, LabelManager
from vision.defect_analysis import InspectionResult


@dataclass(slots=True)
class DatasetSaveResult:
    """Paths written for one labeled inspection."""

    full_path: Path
    roi_path: Path | None
    overlay_path: Path | None
    metadata_path: Path


class DatasetCollector:
    """Filesystem-backed dataset collector."""

    def __init__(self, dataset_root: str | Path = DATASET_DIR) -> None:
        self.dataset_root = Path(dataset_root)
        self.label_manager = LabelManager(self.dataset_root)
        self.ensure_structure()

    def ensure_structure(self) -> None:
        for label_dir in ("good", "defect"):
            for station in ("station1", "station2"):
                for image_type in ("full", "roi", "overlay"):
                    (self.dataset_root / label_dir / station / image_type).mkdir(parents=True, exist_ok=True)
        (self.dataset_root / "metadata").mkdir(parents=True, exist_ok=True)

    def save_labeled_inspection(
        self,
        *,
        part_id: str,
        station: str,
        source_name: str | None,
        original_image: np.ndarray,
        overlay_image: np.ndarray | None,
        inspection_result: InspectionResult,
        system_prediction: str,
        operator_label: str,
        label_source: str | None = None,
        override_reason: str | None = None,
        serial_number: str | None = None,
        camera_source: str | None = None,
        inspected_at: datetime | None = None,
        anomaly_score: float | None = None,
        confidence: float | None = None,
        inspection_mode: str = MODE_DATA_COLLECTION,
        extra_metadata: dict[str, Any] | None = None,
    ) -> DatasetSaveResult:
        label = self.label_manager.normalize_operator_label(operator_label)
        normalized_label_source = self.label_manager.normalize_label_source(label_source)
        normalized_override_reason = self.label_manager.normalize_override_reason(override_reason)
        label_dir = "good" if label == GOOD_LABEL else "defect"
        station_dir = self._station_dir_name(station)
        timestamp = inspected_at or datetime.now().astimezone()
        safe_part_id = self._safe_name(part_id)
        stem = f"{safe_part_id}_{timestamp:%Y%m%d_%H%M%S_%f}"

        full_path = self.dataset_root / label_dir / station_dir / "full" / f"{stem}.png"
        roi_path = self.dataset_root / label_dir / station_dir / "roi" / f"{stem}.png"
        overlay_path = self.dataset_root / label_dir / station_dir / "overlay" / f"{stem}.png"
        metadata_path = self.dataset_root / "metadata" / f"{stem}.json"

        cv2.imwrite(str(full_path), original_image)
        roi = self._crop_roi(original_image, inspection_result)
        saved_roi_path: Path | None = None
        if roi is not None:
            cv2.imwrite(str(roi_path), roi)
            saved_roi_path = roi_path
        saved_overlay_path: Path | None = None
        if overlay_image is not None:
            cv2.imwrite(str(overlay_path), overlay_image)
            saved_overlay_path = overlay_path

        metadata: dict[str, Any] = {
            "part_id": part_id,
            "station": self._station_code(station),
            "timestamp": timestamp.isoformat(),
            "prediction": system_prediction,
            "system_prediction": system_prediction,
            "operator_label": label,
            "label_source": normalized_label_source,
            "override_reason": normalized_override_reason,
            "serial_number": serial_number,
            "camera_source": camera_source or source_name,
            "source_name": source_name,
            "inspection_mode": inspection_mode,
            "anomaly_score": anomaly_score,
            "confidence": confidence,
            "measurements": inspection_result.measurements,
            "defects": inspection_result.defects,
            "full_image_path": str(full_path),
            "roi_image_path": str(saved_roi_path) if saved_roi_path else None,
            "overlay_image_path": str(saved_overlay_path) if saved_overlay_path else None,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return DatasetSaveResult(full_path, saved_roi_path, saved_overlay_path, metadata_path)

    @staticmethod
    def _crop_roi(image: np.ndarray, result: InspectionResult) -> np.ndarray | None:
        outer = result.outer_circle
        if outer is None:
            return None
        x, y = outer.center
        radius = int(outer.radius * 1.08)
        left = max(0, x - radius)
        right = min(image.shape[1], x + radius)
        top = max(0, y - radius)
        bottom = min(image.shape[0], y + radius)
        if left >= right or top >= bottom:
            return None
        return image[top:bottom, left:right].copy()

    @staticmethod
    def _station_dir_name(station: str) -> str:
        value = station.strip().lower()
        if value in {"s2", "station2", "station 2"}:
            return "station2"
        return "station1"

    @staticmethod
    def _station_code(station: str) -> str:
        return "S2" if DatasetCollector._station_dir_name(station) == "station2" else "S1"

    @staticmethod
    def _safe_name(value: str) -> str:
        return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
