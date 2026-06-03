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
    assert latest["confirmation_mode"] == "AUTO_ACCEPT"
    assert latest["patchcore_result"] is not None
    assert engine.status()["pending_label"] is False
    assert engine.dataset_stats()["total_good"] == 1


def test_engine_confidence_mode_changes_for_defect(tmp_path) -> None:
    engine = InspectionEngine(dataset_collector=DatasetCollector(tmp_path))

    engine.inspect_image(build_synthetic_disk(with_surface_defect=True), "defect.png")
    latest = engine.latest_inspection()

    assert latest["system_prediction"] == "DEFECT"
    assert latest["confirmation_mode"] in {"REQUEST_CONFIRMATION", "REQUIRE_CONFIRMATION"}
    assert engine.status()["pending_label"] is True
