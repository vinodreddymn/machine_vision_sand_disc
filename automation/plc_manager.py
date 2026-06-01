"""PLC integration framework for future industrial deployments.

This module is intentionally additive. The current system uses `PLCController`
directly; Phase 12 introduces `PLCManager` as an abstraction layer so new PLC
protocols can be integrated with minimal churn.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from automation.plc import PLCController, PLCStatus, SimulatedPLCController


class PLCProvider(str, Enum):
    """Supported PLC protocol families (future)."""

    SIMULATED = "SIMULATED"
    SNAP7 = "SNAP7"
    MODBUS_TCP = "MODBUS_TCP"
    ETHERNET_IP = "ETHERNET_IP"
    OPC_UA = "OPC_UA"
    DIGITAL_IO = "DIGITAL_IO"


@dataclass(slots=True)
class PLCConnectionStatus:
    provider: PLCProvider
    online: bool
    last_success_ts: float | None
    latency_ms: float | None
    error_count: int
    message: str | None = None


class PLCAdapter(ABC):
    """Protocol-agnostic PLC adapter contract."""

    provider: PLCProvider

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def read_status(self) -> PLCStatus: ...

    @abstractmethod
    def reject_part(self, station_name: str) -> None: ...

    @abstractmethod
    def release_to_good_bin(self) -> None: ...

    def heartbeat(self) -> bool:
        """Optional periodic connectivity check."""
        try:
            _ = self.read_status()
            return True
        except Exception:
            return False


class SimulatedPLCAdapter(PLCAdapter):
    provider = PLCProvider.SIMULATED

    def __init__(self, controller: PLCController | None = None) -> None:
        self.controller = controller or SimulatedPLCController()

    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def read_status(self) -> PLCStatus:
        return self.controller.read_status()

    def reject_part(self, station_name: str) -> None:
        return self.controller.reject_part(station_name)

    def release_to_good_bin(self) -> None:
        return self.controller.release_to_good_bin()


class PLCManager:
    """Own PLC connectivity and expose a stable API to the rest of the system."""

    def __init__(self, adapter: PLCAdapter | None = None) -> None:
        self.adapter = adapter or SimulatedPLCAdapter()
        self._last_success_ts: float | None = None
        self._error_count = 0
        self._last_latency_ms: float | None = None
        self._message: str | None = None

    def connect(self) -> None:
        self.adapter.connect()

    def disconnect(self) -> None:
        self.adapter.disconnect()

    def status(self) -> PLCConnectionStatus:
        return PLCConnectionStatus(
            provider=self.adapter.provider,
            online=self._last_success_ts is not None and (time.time() - self._last_success_ts) < 10.0,
            last_success_ts=self._last_success_ts,
            latency_ms=self._last_latency_ms,
            error_count=self._error_count,
            message=self._message,
        )

    def read_status(self) -> PLCStatus:
        started = time.perf_counter()
        try:
            status = self.adapter.read_status()
            self._last_latency_ms = (time.perf_counter() - started) * 1000.0
            self._last_success_ts = time.time()
            self._message = None
            return status
        except Exception as error:
            self._error_count += 1
            self._message = str(error)
            raise

    def reject_part(self, station_name: str) -> None:
        try:
            self.adapter.reject_part(station_name)
            self._last_success_ts = time.time()
        except Exception as error:
            self._error_count += 1
            self._message = str(error)
            raise

    def release_to_good_bin(self) -> None:
        try:
            self.adapter.release_to_good_bin()
            self._last_success_ts = time.time()
        except Exception as error:
            self._error_count += 1
            self._message = str(error)
            raise

    def diagnostics(self) -> dict[str, Any]:
        s = self.status()
        return {
            "provider": s.provider.value,
            "online": s.online,
            "last_success_ts": s.last_success_ts,
            "latency_ms": s.latency_ms,
            "error_count": s.error_count,
            "message": s.message,
        }

