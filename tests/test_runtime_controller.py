from __future__ import annotations

from automation.inspection_controller import InspectionController, InspectionState
from automation.plc import DeviceState, SimulatedPLCController


def test_inspection_controller_state_transitions() -> None:
    controller = InspectionController(config_version=7)

    assert controller.snapshot().state is InspectionState.IDLE

    controller.ready(requested_by="unit-test")
    assert controller.snapshot().state is InspectionState.READY

    controller.start(requested_by="unit-test")
    snapshot = controller.snapshot()
    assert snapshot.state is InspectionState.RUNNING
    assert snapshot.config_version == 7

    controller.request_reload_config(requested_by="unit-test")
    assert controller.snapshot().reload_requested is True

    controller.acknowledge_reload_config(requested_by="unit-test")
    assert controller.snapshot().reload_requested is False

    controller.stop(requested_by="unit-test")
    assert controller.snapshot().state is InspectionState.STOPPED

    controller.fault("camera offline", requested_by="unit-test")
    assert controller.snapshot().state is InspectionState.FAULT


def test_simulated_plc_edge_commands_and_heartbeat() -> None:
    plc = SimulatedPLCController()

    plc.start_request()
    plc.reset_request()
    plc.reload_config_request()
    plc.confirm_label_request()
    plc.override_label_request()
    plc.stop_request()

    status = plc.read_status()

    assert plc.command_pulses == [
        "Start Request",
        "Reset Request",
        "Reload Config Request",
        "Confirm Label Request",
        "Override Label Request",
        "Stop Request",
    ]
    assert status.run_status is DeviceState.STOPPED
    assert isinstance(status.heartbeat_bit, bool)
    assert status.watchdog_timeout_seconds == 5.0
