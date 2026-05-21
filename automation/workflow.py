"""Two-station inspection state machine for one conveyed part."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
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
    REJECTED_AT_STATION_1 = "REJECTED AT STATION 1"
    REJECTED_AT_STATION_2 = "REJECTED AT STATION 2"
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


@dataclass(slots=True)
class PartRecord:
    """Current line record for one product traversing both stations."""

    part_id: str
    station_1: StationRecord
    station_2: StationRecord
    final_disposition: FinalDisposition = FinalDisposition.IN_PROGRESS
    flipper_ready: bool = False


@dataclass(slots=True)
class ProductionCounters:
    """Cumulative line totals for the current application session."""

    total_parts_detected: int = 0
    station_1_passed: int = 0
    station_1_rejected: int = 0
    station_2_received: int = 0
    station_2_passed: int = 0
    station_2_rejected: int = 0


class TwoStageInspectionController:
    """Coordinate station decisions and PLC requests for two independent inspection stations."""

    def __init__(
        self,
        plc: PLCController | None = None,
        part_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.plc = plc or SimulatedPLCController()
        self.part_id_factory = part_id_factory or self._fallback_part_id
        self._fallback_part_counter = 0
        self.counters = ProductionCounters()
        self.current_part_s1 = self._new_part()
        self.current_part_s2 = self._new_part()

    @property
    def current_part(self) -> PartRecord:
        """Return Station 1 part record for backwards compatibility."""
        return self.current_part_s1

    def start_new_part(self) -> PartRecord:
        """Reset workflow state for both stations."""
        reset = getattr(self.plc, "reset", None)
        if callable(reset):
            reset()
        self.current_part_s1 = self._new_part()
        self.current_part_s2 = self._new_part()
        return self.current_part_s1

    def start_new_part_s1(self) -> PartRecord:
        """Reset workflow state for Station 1."""
        self.current_part_s1 = self._new_part()
        return self.current_part_s1

    def start_new_part_s2(self) -> PartRecord:
        """Reset workflow state for Station 2."""
        self.current_part_s2 = self._new_part()
        return self.current_part_s2

    def inspect_station_1(self, image: np.ndarray, source_name: str) -> StationRecord:
        """Inspect top side independently and reject or release."""
        record = self._inspect("Station 1", image, source_name)
        self.current_part_s1.station_1 = record
        self.counters.total_parts_detected += 1
        if record.decision is StationDecision.FAIL:
            record.reject_requested = True
            self.plc.reject_part("Station 1")
            self.current_part_s1.final_disposition = FinalDisposition.REJECTED_AT_STATION_1
            self.current_part_s1.flipper_ready = False
            self.counters.station_1_rejected += 1
        else:
            self.plc.release_to_flipper()
            self.current_part_s1.final_disposition = FinalDisposition.ACCEPTED
            self.current_part_s1.flipper_ready = True
            self.counters.station_1_passed += 1
        return record

    def inspect_station_2(self, image: np.ndarray, source_name: str) -> StationRecord:
        """Inspect flipped side independently and reject or release."""
        record = self._inspect("Station 2", image, source_name)
        self.current_part_s2.station_2 = record
        self.counters.station_2_received += 1
        if record.decision is StationDecision.FAIL:
            record.reject_requested = True
            self.plc.reject_part("Station 2")
            self.current_part_s2.final_disposition = FinalDisposition.REJECTED_AT_STATION_2
            self.counters.station_2_rejected += 1
        else:
            self.plc.release_to_good_bin()
            self.current_part_s2.final_disposition = FinalDisposition.ACCEPTED
            self.counters.station_2_passed += 1
        return record

    @staticmethod
    def _inspect(name: str, image: np.ndarray, source_name: str) -> StationRecord:
        result = inspect_disk(image)
        record = StationRecord(
            name=name,
            decision=StationDecision.PASS if result.passed else StationDecision.FAIL,
            source_name=source_name,
            raw_image=image,
            overlay_image=render_overlay(image, result),
            inspection_result=result,
            inspected_at=datetime.now().astimezone(),
        )
        return record

    def _new_part(self) -> PartRecord:
        return PartRecord(
            part_id=self.part_id_factory(),
            station_1=StationRecord("Station 1"),
            station_2=StationRecord("Station 2"),
        )

    def _fallback_part_id(self) -> str:
        """Generate deterministic in-memory ids when no database factory is supplied."""
        self._fallback_part_counter += 1
        return f"PART-{self._fallback_part_counter:06d}"
