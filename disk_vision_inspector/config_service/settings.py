from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Settings for the modular multi-service runtime.

    These are intentionally separate from `config/settings.py` (legacy) so that
    Phase 2+ can evolve without breaking existing workflows.
    """

    dashboard_host: str = os.getenv("DISK_VISION_API_HOST", "0.0.0.0")
    dashboard_port: int = int(os.getenv("DISK_VISION_API_PORT", "8010"))
    restart_backoff_seconds: float = float(os.getenv("DISK_VISION_RESTART_BACKOFF_SECONDS", "2.0"))

    # Modular service ports (local-only by default). These are additive and do not
    # change the legacy `main.py --web` behavior.
    health_port: int = int(os.getenv("DISK_VISION_HEALTH_PORT", "8110"))
    camera_port: int = int(os.getenv("DISK_VISION_CAMERA_PORT", "8111"))
    ai_port: int = int(os.getenv("DISK_VISION_AI_PORT", "8112"))
    database_port: int = int(os.getenv("DISK_VISION_DATABASE_PORT", "8113"))
    notifications_port: int = int(os.getenv("DISK_VISION_NOTIFICATIONS_PORT", "8114"))
