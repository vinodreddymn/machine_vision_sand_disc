"""PLC boundary and in-memory implementation for local development."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class PLCMode(str, Enum):
    """Machine operating modes reported by the PLC."""

    AUTO = "AUTO"
    MANUAL = "MANUAL"


class DeviceState(str, Enum):
    """Simple readable machine-state values for the operator UI."""

    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    READY = "READY"
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    FAULT = "FAULT"


@dataclass(slots=True)
class PLCStatus:
    """Snapshot of machine telemetry read from the PLC."""

    run_status: DeviceState = DeviceState.RUNNING
    mode: PLCMode = PLCMode.MANUAL
    conveyor_status: DeviceState = DeviceState.RUNNING
    reject_actuator: DeviceState = DeviceState.IDLE
    accept_gate: DeviceState = DeviceState.READY
    python_running: bool = True
    inspection_running: bool = False
    camera_healthy: bool = True
    database_healthy: bool = True
    plc_connected: bool = True
    fault_active: bool = False
    heartbeat_bit: bool = False
    watchdog_timeout_seconds: float = 5.0
    last_heartbeat_at: float | None = None


class PLCController(ABC):
    """Minimal PLC contract needed by the single-station line workflow."""

    @abstractmethod
    def reject_part(self, station_name: str) -> None:
        """Pulse the station reject actuator."""

    @abstractmethod
    def release_to_flipper(self) -> None:
        """Compatibility alias for older two-stage callers."""

    @abstractmethod
    def release_to_good_bin(self) -> None:
        """Allow a pass part to continue as an accepted product."""

    @abstractmethod
    def read_status(self) -> PLCStatus:
        """Return the latest machine status snapshot from the PLC."""

    def start_request(self) -> None:
        """Edge-trigger the start request output."""

    def stop_request(self) -> None:
        """Edge-trigger the stop request output."""

    def reset_request(self) -> None:
        """Edge-trigger the reset request output."""

    def reload_config_request(self) -> None:
        """Edge-trigger the configuration reload request output."""

    def confirm_label_request(self) -> None:
        """Edge-trigger the label confirmation request output."""

    def override_label_request(self) -> None:
        """Edge-trigger the label override request output."""


@dataclass(slots=True)
class SimulatedPLCController(PLCController):
    """Record requested PLC actions while hardware integration is pending."""

    reject_requests: list[str] = field(default_factory=list)
    transfer_released: bool = False
    good_bin_released: bool = False
    last_action: str = "Idle"
    status: PLCStatus = field(default_factory=PLCStatus)
    command_pulses: list[str] = field(default_factory=list)
    watchdog_timeout_seconds: float = 5.0
    _last_heartbeat_toggle: float = field(default_factory=time.monotonic, init=False, repr=False)

    def reject_part(self, station_name: str) -> None:
        # Record the reject request and pulse the actuator (ACTIVE then IDLE)
        self.reject_requests.append(station_name)
        self.last_action = "Reject actuator fired"
        self.status.reject_actuator = DeviceState.ACTIVE
        # Simulate a short pulse by releasing immediately in the simulated controller.
        self.status.reject_actuator = DeviceState.IDLE
        self.status.accept_gate = DeviceState.READY

    def release_to_flipper(self) -> None:
        self.transfer_released = True
        self.release_to_good_bin()

    def release_to_good_bin(self) -> None:
        self.good_bin_released = True
        self.last_action = "Released to good-product path"
        self.status.accept_gate = DeviceState.ACTIVE
        self.status.accept_gate = DeviceState.READY

    def read_status(self) -> PLCStatus:
        """Return the current simulated PLC state."""
        now = time.monotonic()
        if now - self._last_heartbeat_toggle >= 1.0:
            self.status.heartbeat_bit = not self.status.heartbeat_bit
            self._last_heartbeat_toggle = now
        self.status.last_heartbeat_at = now
        self.status.watchdog_timeout_seconds = self.watchdog_timeout_seconds
        self.status.inspection_running = self.status.run_status is DeviceState.RUNNING
        self.status.plc_connected = True
        self.status.fault_active = False
        return self.status

    def reset(self) -> None:
        """Reset transient outputs when a new part enters the line."""
        self.reject_requests.clear()
        self.transfer_released = False
        self.good_bin_released = False
        self.last_action = "Idle"
        self.status.reject_actuator = DeviceState.IDLE
        self.status.accept_gate = DeviceState.READY

    def _pulse_command(self, name: str) -> None:
        self.command_pulses.append(name)
        self.last_action = name

    def start_request(self) -> None:
        self._pulse_command("Start Request")
        self.status.run_status = DeviceState.RUNNING
        self.status.conveyor_status = DeviceState.RUNNING
        self.status.inspection_running = True

    def stop_request(self) -> None:
        self._pulse_command("Stop Request")
        self.status.run_status = DeviceState.STOPPED
        self.status.conveyor_status = DeviceState.STOPPED
        self.status.inspection_running = False

    def reset_request(self) -> None:
        self._pulse_command("Reset Request")
        self.status.run_status = DeviceState.READY
        self.status.conveyor_status = DeviceState.IDLE
        self.status.fault_active = False

    def reload_config_request(self) -> None:
        self._pulse_command("Reload Config Request")

    def confirm_label_request(self) -> None:
        self._pulse_command("Confirm Label Request")

    def override_label_request(self) -> None:
        self._pulse_command("Override Label Request")
