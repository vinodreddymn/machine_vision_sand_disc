"""Regression tests for the GUI-independent inspection engine."""

from __future__ import annotations

from dataset.collector import DatasetCollector
from services.inspection_engine import InspectionEngine
from tests.test_pipeline import build_synthetic_disk


def test_engine_inspects_and_confirms_label(tmp_path) -> None:
    engine = InspectionEngine(dataset_collector=DatasetCollector(tmp_path))

    engine.inspect_image(build_synthetic_disk(), "engine.png")
    latest = engine.latest_inspection()

    assert latest["system_prediction"] == "GOOD"
    saved = engine.confirm_label("GOOD")
    assert saved.metadata_path.exists()
    assert engine.dataset_stats()["total_good"] == 1
