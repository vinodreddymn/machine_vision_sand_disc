"""PLC boundary and in-memory implementation for local development."""

from __future__ import annotations

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
    station_1_reject_actuator: DeviceState = DeviceState.IDLE
    flipper_status: DeviceState = DeviceState.READY
    station_2_reject_actuator: DeviceState = DeviceState.IDLE


class PLCController(ABC):
    """Minimal PLC contract needed by the two-station line workflow."""

    @abstractmethod
    def reject_part(self, station_name: str) -> None:
        """Pulse the reject actuator associated with one station."""

    @abstractmethod
    def release_to_flipper(self) -> None:
        """Allow a station-one pass part to continue toward the flipper."""

    @abstractmethod
    def release_to_good_bin(self) -> None:
        """Allow a station-two pass part to continue as an accepted product."""

    @abstractmethod
    def read_status(self) -> PLCStatus:
        """Return the latest machine status snapshot from the PLC."""


@dataclass(slots=True)
class SimulatedPLCController(PLCController):
    """Record requested PLC actions while hardware integration is pending."""

    reject_requests: list[str] = field(default_factory=list)
    transfer_released: bool = False
    good_bin_released: bool = False
    last_action: str = "Idle"
    status: PLCStatus = field(default_factory=PLCStatus)

    def reject_part(self, station_name: str) -> None:
        # Record the reject request and pulse the actuator (ACTIVE then IDLE)
        self.reject_requests.append(station_name)
        self.last_action = f"{station_name} reject actuator fired"
        if station_name == "Station 1":
            self.status.station_1_reject_actuator = DeviceState.ACTIVE
            # Simulate a short pulse by releasing immediately in the simulated controller
            self.status.station_1_reject_actuator = DeviceState.IDLE
        else:
            self.status.station_2_reject_actuator = DeviceState.ACTIVE
            # Simulate a short pulse by releasing immediately in the simulated controller
            self.status.station_2_reject_actuator = DeviceState.IDLE
            self.status.flipper_status = DeviceState.READY

    def release_to_flipper(self) -> None:
        self.transfer_released = True
        self.last_action = "Released to mechanical flipper"
        self.status.flipper_status = DeviceState.ACTIVE

    def release_to_good_bin(self) -> None:
        self.good_bin_released = True
        self.last_action = "Released to good-product path"
        self.status.flipper_status = DeviceState.READY

    def read_status(self) -> PLCStatus:
        """Return the current simulated PLC state."""
        return self.status

    def reset(self) -> None:
        """Reset transient outputs when a new part enters the line."""
        self.reject_requests.clear()
        self.transfer_released = False
        self.good_bin_released = False
        self.last_action = "Idle"
        self.status.station_1_reject_actuator = DeviceState.IDLE
        self.status.station_2_reject_actuator = DeviceState.IDLE
        self.status.flipper_status = DeviceState.READY
