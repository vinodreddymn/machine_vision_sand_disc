"""Export labeled samples into a flat training-friendly dataset."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from config.settings import DATASET_DIR, DATASET_EXPORT_DIR
from dataset.label_manager import LabelManager


class DatasetExporter:
    """Create generic image/label/metadata exports for future AI training."""

    def __init__(
        self,
        dataset_root: str | Path = DATASET_DIR,
        export_root: str | Path = DATASET_EXPORT_DIR,
    ) -> None:
        self.dataset_root = Path(dataset_root)
        self.export_root = Path(export_root)
        self.label_manager = LabelManager(self.dataset_root)

    def export_generic(self) -> Path:
        images_dir = self.export_root / "images"
        labels_dir = self.export_root / "labels"
        metadata_dir = self.export_root / "metadata"
        for directory in (images_dir, labels_dir, metadata_dir):
            directory.mkdir(parents=True, exist_ok=True)

        csv_path = self.export_root / "metadata.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "part_id",
                    "station",
                    "operator_label",
                    "label_source",
                    "override_reason",
                    "system_prediction",
                    "prediction",
                    "confidence",
                    "anomaly_score",
                    "timestamp",
                    "image",
                    "roi",
                    "overlay",
                    "metadata",
                ],
            )
            writer.writeheader()
            for metadata_path in sorted((self.dataset_root / "metadata").glob("*.json")):
                record = json.loads(metadata_path.read_text(encoding="utf-8"))
                export_id = metadata_path.stem
                copied = self._copy_images(record, images_dir, export_id)
                label_path = labels_dir / f"{export_id}.txt"
                label_path.write_text(str(record.get("operator_label", "")), encoding="utf-8")
                copied_metadata = metadata_dir / metadata_path.name
                shutil.copy2(metadata_path, copied_metadata)
                writer.writerow(
                    {
                        "part_id": record.get("part_id"),
                        "station": record.get("station"),
                        "operator_label": record.get("operator_label"),
                        "label_source": record.get("label_source"),
                        "override_reason": record.get("override_reason"),
                        "system_prediction": record.get("system_prediction"),
                        "prediction": record.get("prediction"),
                        "confidence": record.get("confidence"),
                        "anomaly_score": record.get("anomaly_score"),
                        "timestamp": record.get("timestamp"),
                        "image": str(copied.get("full", "")),
                        "roi": str(copied.get("roi", "")),
                        "overlay": str(copied.get("overlay", "")),
                        "metadata": str(copied_metadata),
                    }
                )
        return self.export_root

    @staticmethod
    def _copy_images(record: dict, images_dir: Path, export_id: str) -> dict[str, Path]:
        copied: dict[str, Path] = {}
        for key, suffix in (
            ("full_image_path", "full"),
            ("roi_image_path", "roi"),
            ("overlay_image_path", "overlay"),
        ):
            raw_path = str(record.get(key) or "").strip()
            if not raw_path:
                continue
            source = Path(raw_path)
            if not source.exists() or not source.is_file():
                continue
            destination = images_dir / f"{export_id}_{suffix}{source.suffix}"
            shutil.copy2(source, destination)
            copied[suffix] = destination
        return copied
