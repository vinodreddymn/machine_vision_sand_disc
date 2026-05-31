from __future__ import annotations

import logging

import uvicorn

from disk_vision_inspector.shared.logging import configure_service_logging
from disk_vision_inspector.config_service.settings import RuntimeSettings


log = logging.getLogger(__name__)


def run_dashboard(*, settings: RuntimeSettings) -> int:
    """Run the existing FastAPI app as an independently managed service."""
    configure_service_logging(service_name="dashboard_service")
    from services.api import create_app  # legacy API module

    app = create_app()
    log.info("Starting dashboard service on %s:%s", settings.dashboard_host, settings.dashboard_port)
    uvicorn.run(app, host=settings.dashboard_host, port=settings.dashboard_port)
    return 0

