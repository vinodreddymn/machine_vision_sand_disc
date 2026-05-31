from __future__ import annotations

import logging
import time
from dataclasses import asdict

from fastapi import FastAPI

from disk_vision_inspector.shared.logging import configure_service_logging
from disk_vision_inspector.config_service.settings import RuntimeSettings
from disk_vision_inspector.shared.models import ServiceHealth


log = logging.getLogger(__name__)


class HealthService:
    """Local in-process health reporter scaffold.

    Phase 3 will expand this into a full metrics subsystem.
    """

    def __init__(self) -> None:
        self._health = ServiceHealth(name="health_service", status="ONLINE", version=None)
    def snapshot(self) -> dict:
        return asdict(self._health)


def run_health_service() -> int:
    configure_service_logging(service_name="health_service")
    settings = RuntimeSettings()
    svc = HealthService()
    # Best-effort retention loop (runs in-process here until Phase 8 moves it into a dedicated service).
    try:
        import threading
        from services.image_manager import run_retention_loop

        threading.Thread(target=run_retention_loop, kwargs={"interval_seconds": 3600}, daemon=True).start()
    except Exception:
        pass

    app = FastAPI(title="DiskVisionInspector Health Service")

    @app.get("/health")
    def health() -> dict:
        return svc.snapshot()

    @app.get("/metrics")
    def metrics() -> dict:
        return {
            "timestamp": time.time(),
            "service": svc.snapshot(),
        }

    import uvicorn

    log.info("Health service listening on 127.0.0.1:%s", settings.health_port)
    uvicorn.run(app, host="127.0.0.1", port=settings.health_port)
    return 0
