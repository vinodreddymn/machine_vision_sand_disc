"""Tests for serial assignment and storage-service behavior."""

from __future__ import annotations

from datetime import datetime, timezone

from automation.workflow import FinalDisposition, StationDecision, StationRecord
from storage.service import InspectionStorageService
from tests.test_pipeline import build_synthetic_disk
from vision.defect_analysis import inspect_disk


class FakeRepository:
    """Small in-memory repository used to test storage orchestration."""

    def __init__(self) -> None:
        self.saved: list[dict] = []
        self.counters: dict[tuple[str, str], int] = {}
        self.part_counter = 0

    def initialize_schema(self) -> None:
        return None

    def next_serial(self, stage: str, inspected_at: datetime) -> str:
        key = (stage, inspected_at.strftime("%Y%m%d"))
        self.counters[key] = self.counters.get(key, 0) + 1
        return f"{stage}-{inspected_at:%Y%m%d-%H%M%S}-{self.counters[key]:06d}"

    def next_part_id(self, prefix: str = "PART") -> str:
        self.part_counter += 1
        return f"{prefix}-{self.part_counter:06d}"

    def save_inspection(self, **kwargs) -> int:
        self.saved.append(kwargs)
        return len(self.saved)

    def get_recent_inspections(self, limit: int = 100):
        return []

    def get_part_history(self, physical_part_id: str):
        return []

    def get_stage_history(self, stage: str, limit: int = 100):
        return []


def test_storage_service_assigns_stage_serial_and_persists_payload() -> None:
    repository = FakeRepository()
    service = InspectionStorageService(repository)
    result = inspect_disk(build_synthetic_disk())
    record = StationRecord(
        name="Station 1",
        decision=StationDecision.PASS,
        source_name="top.png",
        inspection_result=result,
    )
    inspected_at = datetime(2026, 5, 17, 14, 35, 22, tzinfo=timezone.utc)

    serial = service.persist_station_record(
        physical_part_id="PART001",
        stage="S1",
        record=record,
        final_disposition=FinalDisposition.IN_PROGRESS,
        overlay_path="outputs/passed/station_1_top.png",
        inspected_at=inspected_at,
    )

    assert serial == "S1-20260517-143522-000001"
    assert record.serial_number == serial
    assert record.inspected_at == inspected_at
    assert repository.saved[0]["physical_part_id"] == "PART001"
    assert repository.saved[0]["measurements"]["hole_count"] == 5


def test_storage_service_serials_increment_per_stage_per_day() -> None:
    repository = FakeRepository()
    service = InspectionStorageService(repository)
    result = inspect_disk(build_synthetic_disk())
    timestamp = datetime(2026, 5, 17, 9, 0, 0, tzinfo=timezone.utc)

    first = service.persist_station_record(
        physical_part_id="P1",
        stage="S1",
        record=StationRecord("Station 1", StationDecision.PASS, inspection_result=result),
        final_disposition=FinalDisposition.IN_PROGRESS,
        overlay_path=None,
        inspected_at=timestamp,
    )
    second = service.persist_station_record(
        physical_part_id="P1",
        stage="S2",
        record=StationRecord("Station 2", StationDecision.PASS, inspection_result=result),
        final_disposition=FinalDisposition.ACCEPTED,
        overlay_path=None,
        inspected_at=timestamp,
    )
    third = service.persist_station_record(
        physical_part_id="P2",
        stage="S1",
        record=StationRecord("Station 1", StationDecision.PASS, inspection_result=result),
        final_disposition=FinalDisposition.IN_PROGRESS,
        overlay_path=None,
        inspected_at=timestamp,
    )

    assert first.endswith("000001")
    assert second.endswith("000001")
    assert third.endswith("000002")


def test_storage_service_returns_sequential_part_ids() -> None:
    service = InspectionStorageService(FakeRepository())

    assert service.next_part_id() == "PART-000001"
    assert service.next_part_id() == "PART-000002"
