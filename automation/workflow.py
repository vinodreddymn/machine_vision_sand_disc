"""Single-station inspection state machine for one conveyed part."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

import numpy as np

from automation.plc import PLCController, SimulatedPLCController
from vision.defect_analysis import InspectionResult, inspect_disk
from vision.overlay_renderer import render_overlay


class StationDecision(str, Enum):
    """Operator-facing station decision values."""

    WAITING = "WAITING"
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class FinalDisposition(str, Enum):
    """Final outcome for one physical part."""

    IN_PROGRESS = "IN PROGRESS"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"


@dataclass(slots=True)
class StationRecord:
    """Inspection evidence and decision for one station."""

    name: str
    decision: StationDecision = StationDecision.WAITING
    source_name: str | None = None
    raw_image: np.ndarray | None = None
    overlay_image: np.ndarray | None = None
    inspection_result: InspectionResult | None = None
    reject_requested: bool = False
    serial_number: str | None = None
    inspected_at: datetime | None = None
    cycle_time_ms: int | None = None


@dataclass(slots=True)
class PartRecord:
    """Current line record for one product at the inspection station."""

    part_id: str
    station: StationRecord
    final_disposition: FinalDisposition = FinalDisposition.IN_PROGRESS

    @property
    def station_1(self) -> StationRecord:
        """Compatibility alias for older callers."""
        return self.station


@dataclass(slots=True)
class ProductionCounters:
    """Cumulative line totals for the current application session."""

    total_parts_detected: int = 0
    passed: int = 0
    rejected: int = 0

    @property
    def station_1_passed(self) -> int:
        """Compatibility alias for older dashboard code."""
        return self.passed

    @property
    def station_1_rejected(self) -> int:
        """Compatibility alias for older dashboard code."""
        return self.rejected


class SingleStationInspectionController:
    """Coordinate one inspection station and PLC requests."""

    station_name = "Inspection Station"

    def __init__(
        self,
        plc: PLCController | None = None,
        part_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.plc = plc or SimulatedPLCController()
        self.part_id_factory = part_id_factory or self._fallback_part_id
        self._fallback_part_counter = 0
        self.counters = ProductionCounters()
        self.current_part = self._new_part()

    def start_new_part(self) -> PartRecord:
        """Reset workflow state for the next part."""
        reset = getattr(self.plc, "reset", None)
        if callable(reset):
            reset()
        self.current_part = self._new_part()
        return self.current_part

    def inspect_current_part(self, image: np.ndarray, source_name: str) -> StationRecord:
        """Inspect the current part and issue the final single-station action."""
        record = self._inspect(self.station_name, image, source_name)
        self.current_part.station = record
        self.counters.total_parts_detected += 1
        if record.decision is StationDecision.FAIL:
            record.reject_requested = True
            self.plc.reject_part(self.station_name)
            self.current_part.final_disposition = FinalDisposition.REJECTED
            self.counters.rejected += 1
        else:
            self.plc.release_to_good_bin()
            self.current_part.final_disposition = FinalDisposition.ACCEPTED
            self.counters.passed += 1
        return record

    def inspect_station_1(self, image: np.ndarray, source_name: str) -> StationRecord:
        """Compatibility alias for older tests and scripts."""
        return self.inspect_current_part(image, source_name)

    @staticmethod
    def _inspect(name: str, image: np.ndarray, source_name: str) -> StationRecord:
        import time
        start_time = time.perf_counter()
        result = inspect_disk(image)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return StationRecord(
            name=name,
            decision=StationDecision.PASS if result.passed else StationDecision.FAIL,
            source_name=source_name,
            raw_image=image,
            overlay_image=render_overlay(image, result),
            inspection_result=result,
            inspected_at=datetime.now().astimezone(),
            cycle_time_ms=duration_ms,
        )

    def _new_part(self) -> PartRecord:
        return PartRecord(
            part_id=self.part_id_factory(),
            station=StationRecord(self.station_name),
        )

    def _fallback_part_id(self) -> str:
        """Generate deterministic in-memory ids when no database factory is supplied."""
        self._fallback_part_counter += 1
        return f"PART-{self._fallback_part_counter:06d}"


TwoStageInspectionController = SingleStationInspectionController
