from __future__ import annotations

import logging
import time

from disk_vision_inspector.shared.logging import configure_service_logging


log = logging.getLogger(__name__)


def run_database_maintenance_loop(*, interval_seconds: int = 3600) -> int:
    """Run periodic DB maintenance tasks (best-effort).

    Current tasks:
    - Ensure schema exists
    - Prune system health history older than 30 days (already used by health monitor too)
    """
    configure_service_logging(service_name="database_maintenance")
    try:
        from config.settings import POSTGRES_DSN
        from storage.postgres import PostgresInspectionRepository
        from storage.service import InspectionStorageService

        storage = InspectionStorageService(PostgresInspectionRepository(POSTGRES_DSN))
    except Exception as error:
        log.warning("Database maintenance disabled (storage init failed): %s", error)
        storage = None

    while True:
        if storage is not None:
            try:
                storage.initialize()
                pruned = storage.prune_health_history(days=30)
                log.info("DB maintenance ok. Pruned %s health rows.", pruned)
            except Exception as error:
                log.warning("DB maintenance failed: %s", error)
        time.sleep(interval_seconds)

