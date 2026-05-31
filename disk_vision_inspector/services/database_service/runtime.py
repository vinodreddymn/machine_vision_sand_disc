from __future__ import annotations

import logging
import time

from fastapi import FastAPI

from disk_vision_inspector.config_service.settings import RuntimeSettings
from disk_vision_inspector.shared.logging import configure_service_logging


log = logging.getLogger(__name__)


def run_database_service() -> int:
    configure_service_logging(service_name="database_service")
    settings = RuntimeSettings()
    app = FastAPI(title="DiskVisionInspector Database Service")

    # Best-effort schema ensure (safe if DB is offline).
    try:
        from config.settings import POSTGRES_DSN
        from storage.postgres import PostgresInspectionRepository
        from storage.service import InspectionStorageService

        storage = InspectionStorageService(PostgresInspectionRepository(POSTGRES_DSN))
        storage.initialize()
    except Exception:
        storage = None

    @app.get("/health")
    def health() -> dict:
        online = False
        if storage is not None:
            try:
                online = storage.health_query()
            except Exception:
                online = False
        return {"name": "database_service", "status": "ONLINE" if online else "OFFLINE", "timestamp": time.time()}

    @app.get("/metrics")
    def metrics() -> dict:
        size = None
        if storage is not None:
            try:
                size = storage.database_size_bytes()
            except Exception:
                size = None
        return {"timestamp": time.time(), "database": {"connected": storage is not None, "size_bytes": size}}

    import uvicorn

    log.info("Database service listening on 127.0.0.1:%s", settings.database_port)
    uvicorn.run(app, host="127.0.0.1", port=settings.database_port)
    return 0
