"""
PLC Abstraction Layer

Defines:

- PLCController interface
- PLCStatus model
- SimulatedPLCController

Concrete implementations live in separate files:

- arduino_plc.py
- snap7_plc.py
- modbus_plc.py
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class PLCMode(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class DeviceState(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    READY = "READY"
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    FAULT = "FAULT"


# ============================================================
# STATUS MODEL
# ============================================================

@dataclass(slots=True)
class PLCStatus:

    run_status: DeviceState = DeviceState.STOPPED

    mode: PLCMode = PLCMode.MANUAL

    conveyor_status: DeviceState = DeviceState.IDLE

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


# ============================================================
# ABSTRACT PLC INTERFACE
# ============================================================

class PLCController(ABC):

    @abstractmethod
    def reject_part(self, station_name: str) -> None:
        pass

    @abstractmethod
    def release_to_flipper(self) -> None:
        pass

    @abstractmethod
    def release_to_good_bin(self) -> None:
        pass

    @abstractmethod
    def read_status(self) -> PLCStatus:
        pass

    def start_request(self) -> None:
        pass

    def stop_request(self) -> None:
        pass

    def reset_request(self) -> None:
        pass

    def reload_config_request(self) -> None:
        pass

    def confirm_label_request(self) -> None:
        pass

    def override_label_request(self) -> None:
        pass


# ============================================================
# SIMULATED PLC
# ============================================================

@dataclass(slots=True)
class SimulatedPLCController(PLCController):

    reject_requests: list[str] = field(default_factory=list)

    transfer_released: bool = False

    good_bin_released: bool = False

    last_action: str = "Idle"

    status: PLCStatus = field(default_factory=PLCStatus)

    command_history: list[str] = field(default_factory=list)

    watchdog_timeout_seconds: float = 5.0

    _last_heartbeat_toggle: float = field(
        default_factory=time.monotonic,
        init=False,
        repr=False,
    )

    # --------------------------------------------------------
    # PART ROUTING
    # --------------------------------------------------------

    def reject_part(self, station_name: str) -> None:

        self.reject_requests.append(station_name)

        self.last_action = "Reject Part"

        self.status.reject_actuator = DeviceState.ACTIVE

        self.status.reject_actuator = DeviceState.IDLE

    def release_to_flipper(self) -> None:

        self.transfer_released = True

        self.release_to_good_bin()

    def release_to_good_bin(self) -> None:

        self.good_bin_released = True

        self.last_action = "Release Good Part"

        self.status.accept_gate = DeviceState.ACTIVE

        self.status.accept_gate = DeviceState.READY

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def read_status(self) -> PLCStatus:

        now = time.monotonic()

        if now - self._last_heartbeat_toggle >= 1:

            self.status.heartbeat_bit = (
                not self.status.heartbeat_bit
            )

            self._last_heartbeat_toggle = now

        self.status.last_heartbeat_at = now

        self.status.watchdog_timeout_seconds = (
            self.watchdog_timeout_seconds
        )

        self.status.inspection_running = (
            self.status.run_status ==
            DeviceState.RUNNING
        )

        return self.status

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    def _record_command(
        self,
        command: str
    ) -> None:

        self.command_history.append(command)

        self.last_action = command

    def start_request(self) -> None:

        self._record_command("START")

        self.status.run_status = DeviceState.RUNNING

        self.status.conveyor_status = DeviceState.RUNNING

    def stop_request(self) -> None:

        self._record_command("STOP")

        self.status.run_status = DeviceState.STOPPED

        self.status.conveyor_status = DeviceState.STOPPED

    def reset_request(self) -> None:

        self._record_command("RESET")

        self.status.run_status = DeviceState.READY

        self.status.conveyor_status = DeviceState.IDLE

        self.status.fault_active = False

    def reload_config_request(self) -> None:

        self._record_command("RELOAD_CONFIG")

    def confirm_label_request(self) -> None:

        self._record_command("CONFIRM_LABEL")

    def override_label_request(self) -> None:

        self._record_command("OVERRIDE_LABEL")

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    def reset(self) -> None:

        self.reject_requests.clear()

        self.transfer_released = False

        self.good_bin_released = False

        self.last_action = "Idle"

        self.status.reject_actuator = DeviceState.IDLE

        self.status.accept_gate = DeviceState.READY