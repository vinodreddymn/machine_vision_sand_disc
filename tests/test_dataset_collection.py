"""Dataset collection regression tests."""

from __future__ import annotations

from dataset.collector import DatasetCollector
from dataset.exporter import DatasetExporter
from dataset.label_manager import LabelManager
from tests.test_pipeline import build_synthetic_disk
from vision.anomaly_scoring import anomaly_score, assisted_prediction
from vision.defect_analysis import inspect_disk
from vision.overlay_renderer import render_overlay


def test_dataset_collector_saves_full_roi_overlay_and_metadata(tmp_path) -> None:
    image = build_synthetic_disk()
    result = inspect_disk(image)
    collector = DatasetCollector(tmp_path)

    saved = collector.save_labeled_inspection(
        part_id="PART-000001",
        station="S1",
        source_name="synthetic.png",
        original_image=image,
        overlay_image=render_overlay(image, result),
        inspection_result=result,
        system_prediction=assisted_prediction(result),
        operator_label="GOOD",
        label_source="WEB_CONFIRM",
        anomaly_score=anomaly_score(result),
    )

    assert saved.full_path.exists()
    assert saved.roi_path is not None and saved.roi_path.exists()
    assert saved.overlay_path is not None and saved.overlay_path.exists()
    assert saved.metadata_path.exists()

    metadata = saved.metadata_path.read_text(encoding="utf-8")
    assert '"label_source": "WEB_CONFIRM"' in metadata
    assert '"prediction": "GOOD"' in metadata

    stats = LabelManager(tmp_path).stats()
    assert stats.total_good == 1
    assert stats.station1_good == 1
    assert stats.operator_corrections == 0


def test_operator_override_counts_as_correction(tmp_path) -> None:
    image = build_synthetic_disk()
    result = inspect_disk(image)
    collector = DatasetCollector(tmp_path)

    collector.save_labeled_inspection(
        part_id="PART-000002",
        station="station1",
        source_name="override.png",
        original_image=image,
        overlay_image=None,
        inspection_result=result,
        system_prediction="GOOD",
        operator_label="DEFECTIVE",
        label_source="WEB_OVERRIDE",
        override_reason="FALSE_SCRATCH",
        confidence=0.2,
    )

    stats = LabelManager(tmp_path).stats()
    assert stats.total_defective == 1
    assert stats.operator_corrections == 1
    assert stats.system_accuracy_estimate == 0.0


def test_dataset_exporter_writes_csv_and_labels(tmp_path) -> None:
    image = build_synthetic_disk()
    result = inspect_disk(image)
    collector = DatasetCollector(tmp_path / "dataset")
    collector.save_labeled_inspection(
        part_id="PART-000003",
        station="S1",
        source_name="export.png",
        original_image=image,
        overlay_image=render_overlay(image, result),
        inspection_result=result,
        system_prediction="GOOD",
        operator_label="GOOD",
        label_source="WEB_CONFIRM",
    )

    export_root = DatasetExporter(tmp_path / "dataset", tmp_path / "export").export_generic()

    assert (export_root / "metadata.csv").exists()
    assert list((export_root / "labels").glob("*.txt"))
    assert "label_source" in (export_root / "metadata.csv").read_text(encoding="utf-8")
