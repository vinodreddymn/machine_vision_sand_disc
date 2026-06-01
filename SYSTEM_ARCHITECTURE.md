# System Architecture (Baseline)

This document describes the evolving architecture of DiskVisionInspector as it transitions from a single-process prototype to a modular industrial platform.

## Current Runtime Modes

- Legacy Desktop GUI: `python main.py --gui`
- Legacy Web/Headless: `python main.py --web` (FastAPI + serves `web/dist`)
- Modular (supervised): `python -m disk_vision_inspector.run watchdog`

## Modular Services (Current)

- `dashboard_service`: wraps existing FastAPI app (`services/api.py`)
- `health_service`: provides `/health` + runs retention loop
- `camera_service`, `ai_service`, `database_service`, `notification_service`: scaffolds with `/health`
- `backup_service`: exposes `POST /backup/create` on `127.0.0.1:8115`

Next phases will progressively move ownership of camera capture, inference, and DB maintenance into their respective services.

