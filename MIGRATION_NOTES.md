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
