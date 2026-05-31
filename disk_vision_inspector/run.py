from __future__ import annotations

import argparse

from disk_vision_inspector.config_service.settings import RuntimeSettings
from disk_vision_inspector.services.dashboard_service import run_dashboard
from disk_vision_inspector.services.health_service import run_health_service
from disk_vision_inspector.services.watchdog_service import run_watchdog
from disk_vision_inspector.services.ai_service.runtime import run_ai_service
from disk_vision_inspector.services.camera_service.runtime import run_camera_service
from disk_vision_inspector.services.database_service.runtime import run_database_service
from disk_vision_inspector.services.notification_service.runtime import run_notification_service


def main() -> int:
    parser = argparse.ArgumentParser(description="DiskVisionInspector modular runtime")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dashboard", help="Run dashboard service (FastAPI + web UI).")
    sub.add_parser("health", help="Run health service scaffold.")
    sub.add_parser("camera", help="Run camera service scaffold.")
    sub.add_parser("ai", help="Run AI/vision service scaffold.")
    sub.add_parser("database", help="Run database service scaffold.")
    sub.add_parser("notifications", help="Run notification service scaffold.")
    sub.add_parser("watchdog", help="Run watchdog supervisor (starts other services).")
    args = parser.parse_args()

    settings = RuntimeSettings()
    if args.cmd == "dashboard":
        return run_dashboard(settings=settings)
    if args.cmd == "health":
        return run_health_service()
    if args.cmd == "camera":
        return run_camera_service()
    if args.cmd == "ai":
        return run_ai_service()
    if args.cmd == "database":
        return run_database_service()
    if args.cmd == "notifications":
        return run_notification_service()
    if args.cmd == "watchdog":
        return run_watchdog(settings=settings)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
