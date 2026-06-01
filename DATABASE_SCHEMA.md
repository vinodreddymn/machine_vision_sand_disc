# Database Schema (Baseline)

PostgreSQL schema is created/updated by `storage/postgres.py` during initialization.

Key tables:
- `inspection_records` (partitioned by day)
- `serial_counters`, `part_counters`
- `dataset_label_records`
- `camera_calibration`
- `system_alarms`
- `system_health_history`
- `service_events`, `camera_events`, `production_stats`, `audit_logs`
- `app_users`

