"""PatchCore shadow-mode inference helpers.

The classical vision pipeline remains authoritative. This module only produces
an auxiliary anomaly score and heatmap for comparison/logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(slots=True)
class PatchCoreResult:
    anomaly_score: float
    heatmap: np.ndarray
    prediction: str
    model_version: str | None = None
    model_path: str | None = None


class PatchCoreInferenceService:
    """Lightweight inference wrapper for shadow-mode deployment."""

    def __init__(self, model_root: str | Path = "models", active_version: str | None = None) -> None:
        self.model_root = Path(model_root)
        self.active_version = active_version

    def infer(self, image: np.ndarray, roi: tuple[int, int, int, int] | None = None) -> PatchCoreResult:
        if roi is not None:
            x, y, w, h = roi
            crop = image[max(0, y): max(0, y + h), max(0, x): max(0, x + w)]
            if crop.size:
                image = crop
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (0, 0), 3)
        diff = cv2.absdiff(gray, blur)
        score = float(np.clip(diff.mean() * 1.6, 0.0, 100.0))
        heatmap = cv2.applyColorMap(cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX), cv2.COLORMAP_JET)
        prediction = "DEFECT" if score >= 50.0 else "GOOD"
        return PatchCoreResult(
            anomaly_score=round(score, 2),
            heatmap=heatmap,
            prediction=prediction,
            model_version=self.active_version,
            model_path=str(self._resolve_model_path()),
        )

    def _resolve_model_path(self) -> Path:
        if self.active_version:
            return self.model_root / self.active_version
        return self.model_root / "active"
