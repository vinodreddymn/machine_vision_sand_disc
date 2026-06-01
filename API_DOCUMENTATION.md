# API Documentation (Baseline)

The system exposes a REST API (FastAPI) plus WebSocket logs.

## Core APIs

- `GET /api/status`
- `GET /api/station1`
- `GET /api/metrics`
- `GET /api/history`
- `GET /api/logs`

## System / Health

- `GET /api/system/health`
- `GET /api/system/devices`
- `GET /api/system/alarms`
- `GET /api/system/alarm-history`
- `POST /api/system/alarm/{id}/ack`
- `GET /api/system/history`
- `GET /api/system/services`

## Auth (Optional)

Controlled by `config/security.json`:
- `GET /api/auth/config`
- `POST /api/auth/login`

