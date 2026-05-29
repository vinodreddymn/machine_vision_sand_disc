"""Regression tests for the single-station automation workflow."""

from __future__ import annotations

from automation.plc import DeviceState, SimulatedPLCController
from automation.workflow import FinalDisposition, SingleStationInspectionController, StationDecision
from tests.test_pipeline import build_synthetic_disk


def test_failure_rejects_current_part() -> None:
    plc = SimulatedPLCController()
    controller = SingleStationInspectionController(plc)

    record = controller.inspect_current_part(build_synthetic_disk(with_surface_defect=True), "bad_disc.png")

    assert record.decision is StationDecision.FAIL
    assert record.reject_requested is True
    assert controller.current_part.final_disposition is FinalDisposition.REJECTED
    assert plc.reject_requests == ["Inspection Station"]
    assert controller.counters.total_parts_detected == 1
    assert controller.counters.passed == 0
    assert controller.counters.rejected == 1
    assert plc.read_status().reject_actuator is DeviceState.IDLE


def test_pass_releases_to_good_product_path() -> None:
    plc = SimulatedPLCController()
    controller = SingleStationInspectionController(plc)

    record = controller.inspect_current_part(build_synthetic_disk(), "good_disc.png")

    assert record.decision is StationDecision.PASS
    assert controller.current_part.final_disposition is FinalDisposition.ACCEPTED
    assert plc.good_bin_released is True
    assert controller.counters.total_parts_detected == 1
    assert controller.counters.passed == 1


def test_counters_accumulate_across_multiple_parts() -> None:
    controller = SingleStationInspectionController()

    controller.inspect_current_part(build_synthetic_disk(), "good_disc.png")
    controller.start_new_part()
    controller.inspect_current_part(build_synthetic_disk(with_surface_defect=True), "bad_disc.png")

    assert controller.counters.total_parts_detected == 2
    assert controller.counters.passed == 1
    assert controller.counters.rejected == 1


def test_default_part_ids_are_sequential() -> None:
    controller = SingleStationInspectionController()

    first = controller.current_part.part_id
    second = controller.start_new_part().part_id

    assert first == "PART-000001"
    assert second == "PART-000002"
