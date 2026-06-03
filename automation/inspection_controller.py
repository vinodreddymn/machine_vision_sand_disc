"""Central inspection runtime state manager.

This keeps the application state machine in one place so the GUI, API, and CLI
can observe and transition the same runtime state without duplicating logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any


class InspectionState(str, Enum):
    """High-level operating states for the inspection runtime."""

    IDLE = "IDLE"
    READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAULT = "FAULT"
    MAINTENANCE = "MAINTENANCE"


@dataclass(slots=True)
class InspectionRuntimeSnapshot:
    """Serialized state for API responses and UI telemetry."""

    state: InspectionState
    updated_at: datetime
    last_command: str | None = None
    requested_by: str | None = None
    fault_reason: str | None = None
    config_version: int | None = None
    reload_requested: bool = False


class InspectionController:
    """Single source of truth for line runtime state."""

    def __init__(self, *, config_version: int | None = None) -> None:
        self._lock = RLock()
        self._state = InspectionState.IDLE
        self._updated_at = datetime.now(timezone.utc)
        self._last_command: str | None = None
        self._requested_by: str | None = None
        self._fault_reason: str | None = None
        self._config_version = config_version
        self._reload_requested = False

    def start(self, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        return self._transition(InspectionState.RUNNING, "START", requested_by=requested_by)

    def stop(self, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        self._transition(InspectionState.STOPPING, "STOP_REQUEST", requested_by=requested_by)
        return self._transition(InspectionState.STOPPED, "STOP", requested_by=requested_by)

    def reset(self, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        target = InspectionState.READY if self._state in {InspectionState.RUNNING, InspectionState.STOPPED} else InspectionState.IDLE
        return self._transition(target, "RESET", requested_by=requested_by)

    def fault(self, reason: str, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        with self._lock:
            self._state = InspectionState.FAULT
            self._updated_at = datetime.now(timezone.utc)
            self._last_command = "FAULT"
            self._requested_by = requested_by
            self._fault_reason = reason
            self._reload_requested = False
            return self._snapshot_unlocked()

    def maintenance(self, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        return self._transition(InspectionState.MAINTENANCE, "MAINTENANCE", requested_by=requested_by)

    def ready(self, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        return self._transition(InspectionState.READY, "READY", requested_by=requested_by)

    def request_reload_config(self, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        with self._lock:
            self._reload_requested = True
            self._last_command = "RELOAD_CONFIG_REQUEST"
            self._requested_by = requested_by
            self._updated_at = datetime.now(timezone.utc)
            return self._snapshot_unlocked()

    def acknowledge_reload_config(self, *, requested_by: str | None = None) -> InspectionRuntimeSnapshot:
        with self._lock:
            self._reload_requested = False
            self._last_command = "RELOAD_CONFIG"
            self._requested_by = requested_by
            self._updated_at = datetime.now(timezone.utc)
            return self._snapshot_unlocked()

    def set_config_version(self, version: int | None) -> None:
        with self._lock:
            self._config_version = version
            self._updated_at = datetime.now(timezone.utc)

    def snapshot(self) -> InspectionRuntimeSnapshot:
        with self._lock:
            return self._snapshot_unlocked()

    def _snapshot_unlocked(self) -> InspectionRuntimeSnapshot:
        return InspectionRuntimeSnapshot(
            state=self._state,
            updated_at=self._updated_at,
            last_command=self._last_command,
            requested_by=self._requested_by,
            fault_reason=self._fault_reason,
            config_version=self._config_version,
            reload_requested=self._reload_requested,
        )

    def as_dict(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        return {
            "state": snapshot.state.value,
            "updated_at": snapshot.updated_at.isoformat(),
            "last_command": snapshot.last_command,
            "requested_by": snapshot.requested_by,
            "fault_reason": snapshot.fault_reason,
            "config_version": snapshot.config_version,
            "reload_requested": snapshot.reload_requested,
        }

    def _transition(
        self,
        state: InspectionState,
        command: str,
        *,
        requested_by: str | None = None,
    ) -> InspectionRuntimeSnapshot:
        with self._lock:
            self._state = state
            self._updated_at = datetime.now(timezone.utc)
            self._last_command = command
            self._requested_by = requested_by
            if state is not InspectionState.FAULT:
                self._fault_reason = None
            if state is not InspectionState.READY and command != "RELOAD_CONFIG_REQUEST":
                self._reload_requested = False
            return self.snapshot()
