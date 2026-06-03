"""Ground-truth label handling and dataset statistics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config.settings import DATASET_DIR

GOOD_LABEL = "GOOD"
DEFECT_LABEL = "DEFECTIVE"
WEB_CONFIRM = "WEB_CONFIRM"
WEB_OVERRIDE = "WEB_OVERRIDE"
PLC_CONFIRM = "PLC_CONFIRM"
PLC_OVERRIDE = "PLC_OVERRIDE"

FALSE_SCRATCH = "FALSE_SCRATCH"
LIGHTING = "LIGHTING"
REFLECTION = "REFLECTION"
DUST = "DUST"
ROI_ERROR = "ROI_ERROR"
OTHER = "OTHER"

VALID_LABEL_SOURCES = {WEB_CONFIRM, WEB_OVERRIDE, PLC_CONFIRM, PLC_OVERRIDE}
VALID_OVERRIDE_REASONS = {FALSE_SCRATCH, LIGHTING, REFLECTION, DUST, ROI_ERROR, OTHER}


@dataclass(slots=True)
class DatasetStats:
    """Operator-facing dataset counters."""

    total_good: int = 0
    total_defective: int = 0
    station1_good: int = 0
    station1_defective: int = 0
    station2_good: int = 0
    station2_defective: int = 0
    operator_corrections: int = 0

    @property
    def total(self) -> int:
        return self.total_good + self.total_defective

    @property
    def system_accuracy_estimate(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.total - self.operator_corrections) / self.total * 100.0, 2)

    def as_dict(self) -> dict[str, float | int]:
        return {
            "total_good": self.total_good,
            "total_defective": self.total_defective,
            "station1_good": self.station1_good,
            "station1_defective": self.station1_defective,
            "station2_good": self.station2_good,
            "station2_defective": self.station2_defective,
            "operator_corrections": self.operator_corrections,
            "system_accuracy_estimate": self.system_accuracy_estimate,
        }


class LabelManager:
    """Read metadata and compute labeling quality statistics."""

    def __init__(self, dataset_root: str | Path = DATASET_DIR) -> None:
        self.dataset_root = Path(dataset_root)

    @staticmethod
    def normalize_operator_label(label: str) -> str:
        value = label.strip().upper()
        if value in {"GOOD", "PASS", "CONFIRM_GOOD"}:
            return GOOD_LABEL
        if value in {"DEFECT", "DEFECTIVE", "FAIL", "MARK_DEFECTIVE"}:
            return DEFECT_LABEL
        raise ValueError(f"Unsupported operator label: {label}")

    @staticmethod
    def prediction_to_label(prediction: str) -> str:
        value = prediction.strip().upper()
        if value in {"GOOD", "PASS"}:
            return GOOD_LABEL
        return DEFECT_LABEL

    @staticmethod
    def normalize_label_source(label_source: str | None) -> str:
        if not label_source:
            return WEB_CONFIRM
        value = label_source.strip().upper()
        if value not in VALID_LABEL_SOURCES:
            raise ValueError(f"Unsupported label source: {label_source}")
        return value

    @staticmethod
    def normalize_override_reason(reason: str | None) -> str | None:
        if reason is None or not str(reason).strip():
            return None
        value = str(reason).strip().upper()
        if value not in VALID_OVERRIDE_REASONS:
            raise ValueError(f"Unsupported override reason: {reason}")
        return value

    def read_metadata(self) -> list[dict[str, Any]]:
        metadata_dir = self.dataset_root / "metadata"
        if not metadata_dir.exists():
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(metadata_dir.glob("*.json")):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return records

    def stats(self) -> DatasetStats:
        stats = DatasetStats()
        for record in self.read_metadata():
            label = self.normalize_operator_label(str(record.get("operator_label", "")))
            station = str(record.get("station", "")).upper()
            prediction = self.prediction_to_label(str(record.get("system_prediction", "")))
            if label == GOOD_LABEL:
                stats.total_good += 1
                if station in {"S1", "STATION1", "SINGLE"}:
                    stats.station1_good += 1
                elif station in {"S2", "STATION2"}:
                    stats.station2_good += 1
            else:
                stats.total_defective += 1
                if station in {"S1", "STATION1", "SINGLE"}:
                    stats.station1_defective += 1
                elif station in {"S2", "STATION2"}:
                    stats.station2_defective += 1
            if prediction != label:
                stats.operator_corrections += 1
        return stats
