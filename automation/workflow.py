"""
Single Station Inspection Workflow

Hardware-independent inspection controller.

Supports:
- Simulated PLC
- Arduino Nano Controller
- Siemens PLC (future)
- Modbus PLC (future)

The vision system is responsible for:
1. Detecting a new part
2. Capturing the image
3. Calling inspect_current_part()

The PLC layer is responsible only for:
- Good part release
- Reject actuation
- Machine status indication
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

import numpy as np

from automation.plc import PLCController, SimulatedPLCController
from vision.defect_analysis import InspectionResult, inspect_disk
from vision.overlay_renderer import render_overlay


# ============================================================
# ENUMS
# ============================================================

class StationDecision(str, Enum):
    WAITING = "WAITING"
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class FinalDisposition(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass(slots=True)
class StationRecord:
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
    part_id: str

    station: StationRecord

    final_disposition: FinalDisposition = (
        FinalDisposition.IN_PROGRESS
    )

    @property
    def station_1(self) -> StationRecord:
        return self.station


@dataclass(slots=True)
class ProductionCounters:
    total_parts_detected: int = 0

    passed: int = 0

    rejected: int = 0

    @property
    def yield_percent(self) -> float:

        if self.total_parts_detected == 0:
            return 0.0

        return round(
            (self.passed / self.total_parts_detected) * 100,
            2
        )

    @property
    def station_1_passed(self) -> int:
        return self.passed

    @property
    def station_1_rejected(self) -> int:
        return self.rejected


# ============================================================
# INSPECTION CONTROLLER
# ============================================================

class SingleStationInspectionController:

    station_name = "Inspection Station"

    def __init__(
        self,
        plc: PLCController | None = None,
        part_id_factory: Callable[[], str] | None = None,
    ) -> None:

        self.plc = plc or SimulatedPLCController()

        self.part_id_factory = (
            part_id_factory
            or self._generate_part_id
        )

        self._part_counter = 0

        self.counters = ProductionCounters()

        self.current_part = self._create_new_part()

    # ========================================================
    # PART MANAGEMENT
    # ========================================================

    def start_new_part(self) -> PartRecord:

        reset_method = getattr(
            self.plc,
            "reset",
            None
        )

        if callable(reset_method):
            reset_method()

        self.current_part = self._create_new_part()

        return self.current_part

    # ========================================================
    # MAIN INSPECTION
    # ========================================================

    def inspect_current_part(
        self,
        image: np.ndarray,
        source_name: str
    ) -> StationRecord:

        station_record = self._run_inspection(
            image=image,
            source_name=source_name
        )

        self.current_part.station = station_record

        self.counters.total_parts_detected += 1

        if station_record.decision == StationDecision.FAIL:

            station_record.reject_requested = True

            self.plc.reject_part(
                self.station_name
            )

            self.current_part.final_disposition = (
                FinalDisposition.REJECTED
            )

            self.counters.rejected += 1

        else:

            self.plc.release_to_good_bin()

            self.current_part.final_disposition = (
                FinalDisposition.ACCEPTED
            )

            self.counters.passed += 1

        return station_record

    # Backward compatibility
    def inspect_station_1(
        self,
        image: np.ndarray,
        source_name: str
    ) -> StationRecord:

        return self.inspect_current_part(
            image,
            source_name
        )

    # ========================================================
    # INTERNAL METHODS
    # ========================================================

    def _run_inspection(
        self,
        image: np.ndarray,
        source_name: str
    ) -> StationRecord:

        start_time = time.perf_counter()

        result = inspect_disk(image)

        cycle_time_ms = int(
            (time.perf_counter() - start_time)
            * 1000
        )

        return StationRecord(
            name=self.station_name,

            decision=(
                StationDecision.PASS
                if result.passed
                else StationDecision.FAIL
            ),

            source_name=source_name,

            raw_image=image,

            overlay_image=render_overlay(
                image,
                result
            ),

            inspection_result=result,

            inspected_at=datetime.now().astimezone(),

            cycle_time_ms=cycle_time_ms,
        )

    def _create_new_part(self) -> PartRecord:

        return PartRecord(
            part_id=self.part_id_factory(),
            station=StationRecord(
                self.station_name
            ),
        )

    def _generate_part_id(self) -> str:

        self._part_counter += 1

        return (
            f"PART-{self._part_counter:06d}"
        )

    # ========================================================
    # DASHBOARD HELPERS
    # ========================================================

    def get_statistics(self) -> dict:

        return {
            "total_parts":
                self.counters.total_parts_detected,

            "passed":
                self.counters.passed,

            "rejected":
                self.counters.rejected,

            "yield_percent":
                self.counters.yield_percent,
        }


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

TwoStageInspectionController = (
    SingleStationInspectionController
)