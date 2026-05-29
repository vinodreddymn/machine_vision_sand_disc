"""Application-facing inspection storage service."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from automation.workflow import FinalDisposition, StationRecord
from storage.models import StoredInspection


class InspectionRepository(Protocol):
    """Repository shape used by the workflow and GUI."""

    def initialize_schema(self) -> None: ...

    def next_serial(self, stage: str, inspected_at: datetime) -> str: ...

    def next_part_id(self, prefix: str = "PART") -> str: ...

    def save_inspection(self, **kwargs) -> int: ...

    def get_recent_inspections(self, limit: int = 100) -> list[StoredInspection]: ...

    def get_part_history(self, physical_part_id: str) -> list[StoredInspection]: ...

    def get_stage_history(self, stage: str, limit: int = 100) -> list[StoredInspection]: ...


class InspectionStorageService:
    """Generate serials and persist station records."""

    def __init__(self, repository: InspectionRepository) -> None:
        self.repository = repository

    def initialize(self) -> None:
        """Ensure persistent schema exists before use."""
        self.repository.initialize_schema()

    def next_part_id(self, prefix: str = "PART") -> str:
        """Return the next database-backed physical part id."""
        return self.repository.next_part_id(prefix)

    def persist_station_record(
        self,
        *,
        physical_part_id: str | None,
        stage: str,
        record: StationRecord,
        final_disposition: FinalDisposition,
        overlay_path: str | None,
        inspected_at: datetime | None = None,
        inspection_mode: str = "PRODUCTION",
        cycle_time_ms: int | None = None,
    ) -> str:
        """Assign a stage serial and save one completed inspection."""
        if record.inspection_result is None:
            raise ValueError("Only completed station inspections can be persisted.")
        inspected_at = inspected_at or datetime.now().astimezone()
        if physical_part_id is None:
            physical_part_id = f"{stage}-{inspected_at:%Y%m%d-%H%M%S}"
        serial_number = self.repository.next_serial(stage, inspected_at)
        self.repository.save_inspection(
            physical_part_id=physical_part_id,
            stage=stage,
            serial_number=serial_number,
            inspected_at=inspected_at,
            decision=record.decision.value,
            final_disposition=final_disposition.value,
            source_name=record.source_name,
            reject_requested=record.reject_requested,
            measurements=record.inspection_result.measurements,
            defects=record.inspection_result.defects,
            overlay_path=overlay_path,
            inspection_mode=inspection_mode,
            cycle_time_ms=cycle_time_ms,
        )
        record.serial_number = serial_number
        record.inspected_at = inspected_at
        return serial_number

    def recent(self, limit: int = 100) -> list[StoredInspection]:
        """Return recent inspection history."""
        return self.repository.get_recent_inspections(limit)

    def for_part(self, physical_part_id: str) -> list[StoredInspection]:
        """Return all stored records for one physical part."""
        return self.repository.get_part_history(physical_part_id)

    def for_stage(self, stage: str, limit: int = 100) -> list[StoredInspection]:
        """Return recent stored records for one stage."""
        return self.repository.get_stage_history(stage, limit)
