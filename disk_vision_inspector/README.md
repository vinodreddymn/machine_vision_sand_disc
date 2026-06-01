# Modular Runtime (Scaffold)

This folder introduces a modular, multi-service runtime alongside the existing DiskVisionInspector codebase.

Goals:
- Preserve legacy behavior (`python main.py --web` / `--gui`)
- Provide service-style entrypoints that can be supervised/restarted independently
- Prepare the codebase for Phase 3+ health, watchdog, retention, and security work

## Run (New)

```powershell
.\.venv\Scripts\python -m disk_vision_inspector.run dashboard
```

Supervisor (starts dashboard + health services, restarts on crash):

```powershell
.\.venv\Scripts\python -m disk_vision_inspector.run watchdog
```

Additional scaffolds (independently runnable):

```powershell
.\.venv\Scripts\python -m disk_vision_inspector.run camera
.\.venv\Scripts\python -m disk_vision_inspector.run ai
.\.venv\Scripts\python -m disk_vision_inspector.run database
.\.venv\Scripts\python -m disk_vision_inspector.run notifications
.\.venv\Scripts\python -m disk_vision_inspector.run backup
```

## Logging

New modular services log to rotating files:

```text
outputs/logs/dashboard_service.log
outputs/logs/watchdog_service.log
outputs/logs/health_service.log
outputs/logs/camera_service.log
outputs/logs/ai_service.log
outputs/logs/database_service.log
outputs/logs/notification_service.log
outputs/logs/backup_service.log
```

Legacy runtime continues using `outputs/logs/inspection.log`.
