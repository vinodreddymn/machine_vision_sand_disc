from __future__ import annotations

from pathlib import Path

from dataset.exporter import DatasetExporter
from storage.service import InspectionStorageService


class RegistryFakeRepository:
    def __init__(self) -> None:
        self.models: list[dict] = []

    def initialize_schema(self) -> None:
        return None

    def next_serial(self, stage, inspected_at):
        raise NotImplementedError

    def next_part_id(self, prefix="PART"):
        return "PART-000001"

    def save_inspection(self, **kwargs):
        raise NotImplementedError

    def get_recent_inspections(self, limit=100):
        return []

    def get_part_history(self, physical_part_id):
        return []

    def get_stage_history(self, stage, limit=100):
        return []

    def get_active_calibration(self, camera_id):
        return None

    def save_calibration(self, camera_id, mm_per_pixel, reference_od_mm, reference_hole_mm):
        return 1

    def save_alarm(self, *, category, severity, message, source, acknowledged=False):
        return 1

    def list_alarms(self, *, active_only=False, limit=100):
        return []

    def acknowledge_alarm(self, alarm_id):
        return True

    def save_health_snapshot(self, snapshot):
        return 1

    def get_health_history(self, *, hours=24, limit=500):
        return []

    def prune_health_history(self, *, days=30):
        return 0

    def database_size_bytes(self):
        return 0

    def health_query(self):
        return True

    def get_user_by_username(self, username):
        return None

    def create_user(self, *, username, password_hash, role):
        return 1

    def ensure_default_admin(self, *, username, password_hash):
        return 1

    def write_audit_log(self, *, actor, action, resource, message, details):
        return 1

    def list_users(self, limit=200):
        return []

    def list_audit_logs(self, limit=200):
        return []

    def save_dataset_label(self, *, payload):
        self.models.append(payload)
        return 1

    def list_dataset_labels(self, limit=200):
        return []

    def create_model(self, *, payload):
        self.models.append(payload)
        return 99

    def list_models(self, limit=200):
        return self.models

    def activate_model(self, version):
        return True

    def deactivate_model(self, version):
        return True

    def rollback_model(self, version):
        return True


def test_storage_service_model_registry_hooks() -> None:
    service = InspectionStorageService(RegistryFakeRepository())
    model_id = service.create_model(payload={"version": "v1", "model_path": "models/v1/model.onnx"})

    assert model_id == 99
    assert service.list_models() == [{"version": "v1", "model_path": "models/v1/model.onnx"}]
    assert service.activate_model("v1") is True
    assert service.deactivate_model("v1") is True
    assert service.rollback_model("v1") is True


def test_dataset_exporter_writes_expected_structure(tmp_path) -> None:
    dataset_root = tmp_path / "dataset"
    export_root = tmp_path / "dataset_export"
    (dataset_root / "metadata").mkdir(parents=True)
    (dataset_root / "metadata" / "sample.json").write_text(
        '{"part_id":"P-1","station":"S1","operator_label":"GOOD","system_prediction":"GOOD","prediction":"GOOD","confidence":0.9,"anomaly_score":1.2,"timestamp":"2026-06-03T00:00:00Z","full_image_path":"","roi_image_path":"","overlay_image_path":""}',
        encoding="utf-8",
    )

    result = DatasetExporter(dataset_root=dataset_root, export_root=export_root).export_generic()

    assert (result / "images").exists()
    assert (result / "labels").exists()
    assert (result / "metadata").exists()
    assert (result / "metadata.csv").exists()
