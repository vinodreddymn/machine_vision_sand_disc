from __future__ import annotations

import logging
import time

from fastapi import FastAPI

from disk_vision_inspector.config_service.settings import RuntimeSettings
from disk_vision_inspector.shared.logging import configure_service_logging


log = logging.getLogger(__name__)


def run_ai_service() -> int:
    configure_service_logging(service_name="ai_service")
    settings = RuntimeSettings()
    app = FastAPI(title="DiskVisionInspector AI Service")

    @app.get("/health")
    def health() -> dict:
        return {"name": "ai_service", "status": "ONLINE", "timestamp": time.time()}

    @app.get("/metrics")
    def metrics() -> dict:
        return {"timestamp": time.time(), "ai": {"model_version": None}}

    import uvicorn

    log.info("AI service listening on 127.0.0.1:%s", settings.ai_port)
    uvicorn.run(app, host="127.0.0.1", port=settings.ai_port)
    return 0
