"""Application-facing inspection storage service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

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

    def get_active_calibration(self, camera_id: str) -> dict | None: ...
    
    def save_calibration(self, camera_id: str, mm_per_pixel: float, reference_od_mm: float, reference_hole_mm: float) -> int: ...
    def save_alarm(self, *, category: str, severity: str, message: str, source: str, acknowledged: bool = False) -> int: ...
    def list_alarms(self, *, active_only: bool = False, limit: int = 100) -> list[dict]: ...
    def acknowledge_alarm(self, alarm_id: int) -> bool: ...
    def save_health_snapshot(self, snapshot: dict[str, Any]) -> int: ...
    def get_health_history(self, *, hours: int = 24, limit: int = 500) -> list[dict]: ...
    def prune_health_history(self, *, days: int = 30) -> int: ...
    def database_size_bytes(self) -> int: ...
    def health_query(self) -> bool: ...
    def get_user_by_username(self, username: str) -> dict | None: ...
    def create_user(self, *, username: str, password_hash: str, role: str) -> int: ...
    def ensure_default_admin(self, *, username: str, password_hash: str) -> int | None: ...
    def write_audit_log(self, *, actor: str | None, action: str, resource: str | None, message: str, details: dict[str, Any] | None) -> int: ...


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
        
    def get_active_calibration(self, camera_id: str) -> dict | None:
        """Return the active camera calibration."""
        return self.repository.get_active_calibration(camera_id)

    def save_alarm(
        self,
        *,
        category: str,
        severity: str,
        message: str,
        source: str,
        acknowledged: bool = False,
    ) -> int:
        return self.repository.save_alarm(
            category=category,
            severity=severity,
            message=message,
            source=source,
            acknowledged=acknowledged,
        )

    def list_alarms(self, *, active_only: bool = False, limit: int = 100) -> list[dict]:
        return self.repository.list_alarms(active_only=active_only, limit=limit)

    def acknowledge_alarm(self, alarm_id: int) -> bool:
        return self.repository.acknowledge_alarm(alarm_id)

    def save_health_snapshot(self, snapshot: dict[str, Any]) -> int:
        return self.repository.save_health_snapshot(snapshot)

    def get_health_history(self, *, hours: int = 24, limit: int = 500) -> list[dict]:
        return self.repository.get_health_history(hours=hours, limit=limit)

    def prune_health_history(self, *, days: int = 30) -> int:
        return self.repository.prune_health_history(days=days)

    def database_size_bytes(self) -> int:
        return self.repository.database_size_bytes()

    def health_query(self) -> bool:
        return self.repository.health_query()

    def get_user_by_username(self, username: str) -> dict | None:
        return self.repository.get_user_by_username(username)

    def create_user(self, *, username: str, password_hash: str, role: str) -> int:
        return self.repository.create_user(username=username, password_hash=password_hash, role=role)

    def ensure_default_admin(self, *, username: str, password_hash: str) -> int | None:
        return self.repository.ensure_default_admin(username=username, password_hash=password_hash)

    def write_audit_log(
        self,
        *,
        actor: str | None,
        action: str,
        resource: str | None,
        message: str,
        details: dict[str, Any] | None,
    ) -> int:
        return self.repository.write_audit_log(actor=actor, action=action, resource=resource, message=message, details=details)
