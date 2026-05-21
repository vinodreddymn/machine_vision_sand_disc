"""Regression tests for the two-station automation workflow."""

from __future__ import annotations

from automation.plc import DeviceState, SimulatedPLCController
from automation.workflow import FinalDisposition, StationDecision, TwoStageInspectionController
from tests.test_pipeline import build_synthetic_disk


def test_station_1_failure_rejects_and_leaves_station_2_waiting() -> None:
    plc = SimulatedPLCController()
    controller = TwoStageInspectionController(plc)

    record = controller.inspect_station_1(build_synthetic_disk(with_surface_defect=True), "bad_top.png")

    assert record.decision is StationDecision.FAIL
    assert record.reject_requested is True
    assert controller.current_part.station_2.decision is StationDecision.WAITING
    assert controller.current_part.final_disposition is FinalDisposition.REJECTED_AT_STATION_1
    assert plc.reject_requests == ["Station 1"]
    assert controller.counters.total_parts_detected == 1
    assert controller.counters.station_1_passed == 0
    assert controller.counters.station_1_rejected == 1
    assert controller.counters.station_2_received == 0
    # Simulated controller pulses the actuator and returns to IDLE after the pulse
    assert plc.read_status().station_1_reject_actuator is DeviceState.IDLE


def test_station_1_pass_releases_to_flipper_and_station_2_pass_accepts() -> None:
    plc = SimulatedPLCController()
    controller = TwoStageInspectionController(plc)

    station_1 = controller.inspect_station_1(build_synthetic_disk(), "good_top.png")
    station_2 = controller.inspect_station_2(build_synthetic_disk(), "good_bottom.png")

    assert station_1.decision is StationDecision.PASS
    assert station_2.decision is StationDecision.PASS
    assert controller.current_part.flipper_ready is True
    assert controller.current_part.final_disposition is FinalDisposition.ACCEPTED
    assert plc.transfer_released is True
    assert plc.good_bin_released is True
    assert plc.read_status().flipper_status is DeviceState.READY
    assert controller.counters.total_parts_detected == 1
    assert controller.counters.station_1_passed == 1
    assert controller.counters.station_2_received == 1
    assert controller.counters.station_2_passed == 1


def test_station_2_failure_rejects_after_station_1_pass() -> None:
    plc = SimulatedPLCController()
    controller = TwoStageInspectionController(plc)

    controller.inspect_station_1(build_synthetic_disk(), "good_top.png")
    record = controller.inspect_station_2(build_synthetic_disk(crack=True), "bad_bottom.png")

    assert record.decision is StationDecision.FAIL
    assert record.reject_requested is True
    assert controller.current_part_s2.final_disposition is FinalDisposition.REJECTED_AT_STATION_2
    assert plc.reject_requests == ["Station 2"]
    assert controller.counters.station_2_received == 1
    assert controller.counters.station_2_rejected == 1
    # Simulated controller pulses the actuator and returns to IDLE after the pulse
    assert plc.read_status().station_2_reject_actuator is DeviceState.IDLE


def test_station_2_can_run_without_station_1() -> None:
    controller = TwoStageInspectionController()

    record = controller.inspect_station_2(build_synthetic_disk(), "bottom.png")

    assert record.decision is StationDecision.PASS
    assert controller.current_part_s2.final_disposition is FinalDisposition.ACCEPTED
    assert controller.counters.station_2_received == 1
    assert controller.counters.station_2_passed == 1


def test_counters_accumulate_across_multiple_parts() -> None:
    controller = TwoStageInspectionController()

    controller.inspect_station_1(build_synthetic_disk(), "good_top.png")
    controller.inspect_station_2(build_synthetic_disk(), "good_bottom.png")
    controller.start_new_part()
    controller.inspect_station_1(build_synthetic_disk(with_surface_defect=True), "bad_top.png")

    assert controller.counters.total_parts_detected == 2
    assert controller.counters.station_1_passed == 1
    assert controller.counters.station_1_rejected == 1
    assert controller.counters.station_2_received == 1
    assert controller.counters.station_2_passed == 1
    assert controller.counters.station_2_rejected == 0


def test_default_part_ids_are_sequential() -> None:
    controller = TwoStageInspectionController()

    first = controller.current_part_s1.part_id
    second = controller.start_new_part_s1().part_id

    assert first == "PART-000001"
    assert second == "PART-000003"
