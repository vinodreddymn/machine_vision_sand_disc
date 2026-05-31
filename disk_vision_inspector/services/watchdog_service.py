from __future__ import annotations

import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from http.client import HTTPConnection

from disk_vision_inspector.config_service.settings import RuntimeSettings
from disk_vision_inspector.shared.logging import configure_service_logging


log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ManagedService:
    name: str
    args: list[str]


class WatchdogService:
    """Simple multi-process supervisor for modular services.

    Design goals:
    - Headless operation: services keep running without any UI.
    - Crash recovery: restart services on unexpected exit.
    - Backward compatible: uses the existing code by invoking service entrypoints.
    """

    def __init__(self, *, settings: RuntimeSettings, services: list[ManagedService]) -> None:
        self.settings = settings
        self.services = services
        self._procs: dict[str, subprocess.Popen] = {}

    def run_forever(self) -> int:
        self._start_all()
        try:
            while True:
                self._poll_once()
                time.sleep(1.0)
        except KeyboardInterrupt:
            log.info("Watchdog stopping...")
        finally:
            self._stop_all()
        return 0

    def _start_all(self) -> None:
        for svc in self.services:
            self._start_one(svc)

    def _start_one(self, svc: ManagedService) -> None:
        cmd = [sys.executable, "-m", "disk_vision_inspector.run", *svc.args]
        log.info("Starting %s: %s", svc.name, " ".join(cmd))
        self._procs[svc.name] = subprocess.Popen(cmd)

    def _poll_once(self) -> None:
        for svc in list(self.services):
            proc = self._procs.get(svc.name)
            if proc is None:
                continue
            code = proc.poll()
            if code is None:
                # Process is alive: ensure health endpoint responds when available.
                if self._service_unhealthy(svc.name):
                    log.warning("%s failed health check. Restarting.", svc.name)
                    proc.terminate()
                    time.sleep(self.settings.restart_backoff_seconds)
                    self._start_one(svc)
                continue
            log.warning("%s exited with code %s. Restarting after %.1fs backoff.", svc.name, code, self.settings.restart_backoff_seconds)
            time.sleep(self.settings.restart_backoff_seconds)
            self._start_one(svc)

    def _service_unhealthy(self, name: str) -> bool:
        port = self._service_port(name)
        if port is None:
            return False
        try:
            conn = HTTPConnection("127.0.0.1", port, timeout=1.0)
            conn.request("GET", "/health")
            resp = conn.getresponse()
            ok = 200 <= resp.status < 300
            conn.close()
            return not ok
        except Exception:
            return True

    def _service_port(self, name: str) -> int | None:
        if name == "dashboard_service":
            return self.settings.dashboard_port
        if name == "health_service":
            return self.settings.health_port
        if name == "camera_service":
            return self.settings.camera_port
        if name == "ai_service":
            return self.settings.ai_port
        if name == "database_service":
            return self.settings.database_port
        if name == "notification_service":
            return self.settings.notifications_port
        return None

    def _stop_all(self) -> None:
        for name, proc in self._procs.items():
            if proc.poll() is None:
                log.info("Stopping %s (pid=%s)", name, proc.pid)
                proc.terminate()
        deadline = time.time() + 5.0
        for proc in self._procs.values():
            while proc.poll() is None and time.time() < deadline:
                time.sleep(0.1)
            if proc.poll() is None:
                proc.kill()


def run_watchdog(*, settings: RuntimeSettings) -> int:
    configure_service_logging(service_name="watchdog_service")
    services = [
        ManagedService(name="dashboard_service", args=["dashboard"]),
        ManagedService(name="health_service", args=["health"]),
        ManagedService(name="camera_service", args=["camera"]),
        ManagedService(name="ai_service", args=["ai"]),
        ManagedService(name="database_service", args=["database"]),
        ManagedService(name="notification_service", args=["notifications"]),
    ]
    return WatchdogService(settings=settings, services=services).run_forever()
