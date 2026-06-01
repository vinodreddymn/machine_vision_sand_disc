# Migration Notes

This file records noteworthy changes to project structure and runtime behavior as the system evolves toward an industrial multi-service architecture.

## 2026-05-31 - Phase 2 Scaffold (Modular Runtime Package)

Added a new package `disk_vision_inspector/` that introduces service-style entrypoints without removing or changing the legacy runtime.

Files added:
- `disk_vision_inspector/run.py`: CLI entrypoint (`python -m disk_vision_inspector.run ...`)
- `disk_vision_inspector/services/dashboard_service.py`: runs existing FastAPI app as a managed service
- `disk_vision_inspector/services/watchdog_service.py`: simple supervisor that restarts services on crash
- `disk_vision_inspector/services/health_service.py`: health service scaffold (Phase 3 expands this)
- `disk_vision_inspector/config_service/settings.py`: modular runtime settings (separate from legacy `config/settings.py`)
- `disk_vision_inspector/shared/logging.py`: per-service rotating logs (`outputs/logs/{service}.log`)
- `disk_vision_inspector/shared/constants.py`, `disk_vision_inspector/shared/models.py`
- `disk_vision_inspector/services/camera_service/runtime.py`: camera service scaffold
- `disk_vision_inspector/services/ai_service/runtime.py`: AI service scaffold
- `disk_vision_inspector/services/database_service/runtime.py`: database service scaffold
- `disk_vision_inspector/services/notification_service/runtime.py`: notification service scaffold

Backward compatibility:
- Existing commands remain unchanged: `python main.py --gui`, `python main.py --web`
- New modular runner is additive:
  - `python -m disk_vision_inspector.run dashboard`
  - `python -m disk_vision_inspector.run watchdog`

## 2026-05-31 - Phase 3/4 Foundations (Service Health + Watchdog Checks)

Added per-service `/health` endpoints (FastAPI) for modular services and upgraded watchdog to restart services if health checks fail.

Additive APIs:
- `GET /api/system/services` (dashboard probes modular services on localhost ports)

Config:
- Service ports configurable via env vars:
  - `DISK_VISION_HEALTH_PORT` (default 8110)
  - `DISK_VISION_CAMERA_PORT` (default 8111)
  - `DISK_VISION_AI_PORT` (default 8112)
  - `DISK_VISION_DATABASE_PORT` (default 8113)
  - `DISK_VISION_NOTIFICATIONS_PORT` (default 8114)

## 2026-05-31 - Phase 7/8 Foundations (Industrial Tables + Image Retention)

Added new database tables (created via `storage/postgres.py` schema initialization):
- `service_events`, `camera_events`, `production_stats`, `audit_logs`

Added configurable retention policy:
- `config/image_retention.json`
- loader: `config/settings.py`

Added retention executor:
- `services/image_manager.py` (deletes/moves old files under `outputs/` according to config)

## 2026-05-31 - Phase 9/10 Foundations (Optional Auth + RBAC + Rate Limit)

Added optional security layer (disabled by default):
- Config: `config/security.json`
- JWT + password hashing utilities: `services/security.py`
- DB users table: `app_users` (created during `storage.initialize_schema()`)
- Auth endpoints:
  - `GET /api/auth/config`
  - `POST /api/auth/login`

Added RBAC enforcement (only when auth is enabled) on critical endpoints:
- `/api/config/tolerances` (ADMIN)
- `/api/config/mode` (SUPERVISOR)
- `/api/start-inspection`, `/api/stop-inspection`, `/api/reset*`, `/api/start-part`, `/api/upload-video` (OPERATOR)
- `/api/reset-camera` (SUPERVISOR)
- `/api/shutdown` (ADMIN)

Added optional in-memory rate limiting middleware (disabled by default):
- `rate_limit_enabled`, `rate_limit_per_minute` in `config/security.json`

Dashboard login UX:
- Adds a login modal when auth is enabled and no token is present.
- Stores token in `localStorage` and attaches `Authorization: Bearer` automatically.

## 2026-06-01 - Phase 12/14/15 Foundations (PLC Manager + Backup/Diagnostics)

PLC integration preparation:
- Added `automation/plc_manager.py` defining `PLCManager` + `PLCAdapter` interfaces and provider enums for Snap7/Modbus/OPC UA/etc.

Backup/restore foundation:
- Added modular `backup_service` (`disk_vision_inspector/services/backup_service/runtime.py`) exposing `POST /backup/create`
- Added CLI helper `scripts/backup_create.py` (calls backup service)

Diagnostics:
- Added `scripts/health_check.py` and `scripts/diagnostics.py`

## 2026-06-01 - Phase 11/16 Foundations (Admin UI + Reliability Runner)

Admin (user management):
- Added admin endpoints (RBAC ADMIN):
  - `GET /api/admin/users`
  - `POST /api/admin/users`
- Added dashboard page/tab:
  - `web/src/pages/AdminPage.tsx`

Reliability testing (baseline):
- Added soak runner `scripts/run_reliability.py` which generates `RELIABILITY_REPORT.md`

## 2026-06-01 - Phase 13 Foundations (Email + Telegram Notifications)

Added notification delivery config:
- `config/notifications.json`

Implemented optional delivery channels (disabled by default):
- SMTP email: `services/notifications.py`
- Telegram bot: `services/notifications.py`

Wiring:
- `services/api.py` loads `config/notifications.json` and enables channels in `NotificationDispatcher`
- Added admin test endpoint: `POST /api/admin/notification-test`
- System Health page shows configured channels and can trigger a test (requires ADMIN when auth enabled)

## 2026-06-01 - Phase 10/11/14 Enhancements (Audit Logs + Backup Proxy + HTTPS Templates)

Audit logs:
- Added `GET /api/admin/audit-logs` (ADMIN)
- Added Audit Logs table on `Administration` page

Backups:
- Added dashboard proxy endpoint `POST /api/admin/backup/create` which calls backup service on `127.0.0.1:8115`
- Added UI button on `Administration` page to create and display backup bundle result

HTTPS:
- Added reverse-proxy templates:
  - `deploy/caddy/Caddyfile`
  - `deploy/nginx/diskvision.conf`
