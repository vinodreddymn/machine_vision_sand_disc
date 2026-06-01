"""PostgreSQL persistence for single-station inspection history."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from storage.models import StoredInspection


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS inspection_serial_registry (
    serial_number TEXT PRIMARY KEY,
    physical_part_id TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'S1',
    station_code TEXT NOT NULL DEFAULT 'SINGLE',
    first_seen_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE IF EXISTS inspection_serial_registry
    ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT 'S1';

ALTER TABLE IF EXISTS inspection_serial_registry
    ALTER COLUMN stage SET DEFAULT 'S1';

ALTER TABLE IF EXISTS inspection_serial_registry
    ADD COLUMN IF NOT EXISTS station_code TEXT NOT NULL DEFAULT 'SINGLE';

CREATE TABLE IF NOT EXISTS inspection_records (
    id BIGSERIAL NOT NULL,
    physical_part_id TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'S1',
    station_code TEXT NOT NULL DEFAULT 'SINGLE',
    serial_number TEXT NOT NULL,
    inspected_at TIMESTAMPTZ NOT NULL,
    decision TEXT NOT NULL,
    final_disposition TEXT NOT NULL,
    source_name TEXT,
    reject_requested BOOLEAN NOT NULL DEFAULT FALSE,
    measurements JSONB NOT NULL,
    defects JSONB NOT NULL,
    overlay_path TEXT,
    inspection_mode TEXT NOT NULL DEFAULT 'PRODUCTION',
    cycle_time_ms INTEGER,
    CONSTRAINT inspection_records_pkey PRIMARY KEY (id, inspected_at)
) PARTITION BY RANGE (inspected_at);

ALTER TABLE IF EXISTS inspection_records
    ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT 'S1';

ALTER TABLE IF EXISTS inspection_records
    ALTER COLUMN stage SET DEFAULT 'S1';

ALTER TABLE IF EXISTS inspection_records
    ADD COLUMN IF NOT EXISTS station_code TEXT NOT NULL DEFAULT 'SINGLE';

ALTER TABLE IF EXISTS inspection_records
    ADD COLUMN IF NOT EXISTS inspection_mode TEXT NOT NULL DEFAULT 'PRODUCTION';

ALTER TABLE IF EXISTS inspection_records
    ADD COLUMN IF NOT EXISTS cycle_time_ms INTEGER;

CREATE INDEX IF NOT EXISTS idx_inspection_records_part
    ON inspection_records (physical_part_id, inspected_at);

CREATE INDEX IF NOT EXISTS idx_inspection_records_station_time
    ON inspection_records (station_code, inspected_at DESC);

CREATE INDEX IF NOT EXISTS idx_inspection_records_serial_lookup
    ON inspection_records (serial_number, inspected_at DESC);

CREATE TABLE IF NOT EXISTS serial_counters (
    stage TEXT NOT NULL,
    production_date DATE NOT NULL,
    last_value INTEGER NOT NULL,
    PRIMARY KEY (stage, production_date)
);

CREATE TABLE IF NOT EXISTS part_counters (
    counter_key TEXT PRIMARY KEY,
    last_value BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS dataset_label_records (
    id BIGSERIAL PRIMARY KEY,
    physical_part_id TEXT NOT NULL,
    station_code TEXT NOT NULL,
    serial_number TEXT,
    labeled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    system_prediction TEXT NOT NULL,
    operator_label TEXT NOT NULL,
    anomaly_score NUMERIC(6, 2),
    metadata_path TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dataset_label_records_part
    ON dataset_label_records (physical_part_id, labeled_at DESC);

CREATE OR REPLACE FUNCTION ensure_inspection_records_partition(partition_day DATE)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_name TEXT := format('inspection_records_%s', to_char(partition_day, 'YYYY_MM_DD'));
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS public.%I PARTITION OF public.inspection_records
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        partition_day::TIMESTAMPTZ,
        (partition_day + 1)::TIMESTAMPTZ
    );
    RETURN partition_name;
END
$$;

CREATE TABLE IF NOT EXISTS public.camera_calibration (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) NOT NULL,
    calibration_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    mm_per_pixel FLOAT NOT NULL,
    reference_od_mm FLOAT NOT NULL,
    reference_hole_mm FLOAT NOT NULL,
    active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_camera_calibration_active
    ON public.camera_calibration (camera_id, active);

CREATE TABLE IF NOT EXISTS system_alarms (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT NOT NULL,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_system_alarms_created_at
    ON system_alarms (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_system_alarms_ack
    ON system_alarms (acknowledged, created_at DESC);

CREATE TABLE IF NOT EXISTS system_health_history (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    cpu_usage_percent DOUBLE PRECISION,
    memory_usage_percent DOUBLE PRECISION,
    cpu_temperature_c DOUBLE PRECISION,
    disk_usage_percent DOUBLE PRECISION,
    free_disk_gb DOUBLE PRECISION,
    inspection_fps DOUBLE PRECISION,
    parts_per_minute DOUBLE PRECISION,
    avg_cycle_time_ms DOUBLE PRECISION,
    network_online BOOLEAN,
    camera_online BOOLEAN,
    plc_online BOOLEAN,
    database_online BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_system_health_history_time
    ON system_health_history (captured_at DESC);

CREATE TABLE IF NOT EXISTS service_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    service_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_service_events_time
    ON service_events (created_at DESC);

CREATE TABLE IF NOT EXISTS camera_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    camera_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_camera_events_time
    ON camera_events (created_at DESC);

CREATE TABLE IF NOT EXISTS production_stats (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    stage TEXT NOT NULL DEFAULT 'S1',
    total_parts BIGINT NOT NULL,
    passed_parts BIGINT NOT NULL,
    rejected_parts BIGINT NOT NULL,
    yield_percent DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_production_stats_time
    ON production_stats (captured_at DESC);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor TEXT,
    action TEXT NOT NULL,
    resource TEXT,
    message TEXT NOT NULL,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_time
    ON audit_logs (created_at DESC);

CREATE TABLE IF NOT EXISTS app_users (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'OPERATOR',
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_app_users_active
    ON app_users (active, username);
"""


class PostgresInspectionRepository:
    """Store and retrieve inspection history from PostgreSQL."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize_schema(self) -> None:
        """Create required tables and indexes if they do not yet exist."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(SCHEMA_SQL)
                cursor.execute("SELECT ensure_inspection_records_partition(CURRENT_DATE)")
                cursor.execute(
                    "SELECT ensure_inspection_records_partition((CURRENT_DATE + INTERVAL '1 day')::DATE)"
                )

    def next_serial(self, stage: str, inspected_at: datetime) -> str:
        """Reserve the next per-station/per-day serial number."""
        production_date = inspected_at.date()
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO serial_counters (stage, production_date, last_value)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (stage, production_date)
                    DO UPDATE SET last_value = serial_counters.last_value + 1
                    RETURNING last_value
                    """,
                    (stage, production_date),
                )
                next_value = cursor.fetchone()[0]
        return f"{stage}-{inspected_at:%Y%m%d-%H%M%S}-{next_value:06d}"

    def next_part_id(self, prefix: str = "PART") -> str:
        """Reserve the next globally sequential physical part id."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO part_counters (counter_key, last_value)
                    VALUES (%s, 1)
                    ON CONFLICT (counter_key)
                    DO UPDATE SET last_value = part_counters.last_value + 1
                    RETURNING last_value
                    """,
                    (prefix,),
                )
                next_value = cursor.fetchone()[0]
        return f"{prefix}-{next_value:06d}"

    def save_inspection(
        self,
        *,
        physical_part_id: str,
        stage: str,
        serial_number: str,
        inspected_at: datetime,
        decision: str,
        final_disposition: str,
        source_name: str | None,
        reject_requested: bool,
        measurements: dict[str, Any],
        defects: list[str],
        overlay_path: str | None,
        inspection_mode: str = "PRODUCTION",
        cycle_time_ms: int | None = None,
    ) -> int:
        """Persist one inspection and return its database id."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO inspection_serial_registry (
                        serial_number,
                        physical_part_id,
                        stage,
                        station_code,
                        first_seen_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (serial_number, physical_part_id, "S1", stage, inspected_at),
                )
                cursor.execute(
                    """
                    INSERT INTO inspection_records (
                        physical_part_id,
                        stage,
                        station_code,
                        serial_number,
                        inspected_at,
                        decision,
                        final_disposition,
                        source_name,
                        reject_requested,
                        measurements,
                        defects,
                        overlay_path,
                        inspection_mode,
                        cycle_time_ms
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        physical_part_id,
                        "S1",
                        stage,
                        serial_number,
                        inspected_at,
                        decision,
                        final_disposition,
                        source_name,
                        reject_requested,
                        Jsonb(measurements),
                        Jsonb(defects),
                        overlay_path,
                        inspection_mode,
                        cycle_time_ms,
                    ),
                )
                return int(cursor.fetchone()[0])

    def get_recent_inspections(self, limit: int = 100) -> list[StoredInspection]:
        """Return the newest stored inspections first."""
        return self._fetch_many(
            """
            SELECT id, physical_part_id, station_code AS stage, serial_number, inspected_at, decision,
                   final_disposition, source_name, reject_requested, measurements, defects, overlay_path,
                   inspection_mode, cycle_time_ms
            FROM inspection_records
            ORDER BY inspected_at DESC, id DESC
            LIMIT %s
            """,
            (limit,),
        )

    def get_part_history(self, physical_part_id: str) -> list[StoredInspection]:
        """Return all records for one physical part."""
        return self._fetch_many(
            """
            SELECT id, physical_part_id, station_code AS stage, serial_number, inspected_at, decision,
                   final_disposition, source_name, reject_requested, measurements, defects, overlay_path,
                   inspection_mode, cycle_time_ms
            FROM inspection_records
            WHERE physical_part_id = %s
            ORDER BY inspected_at ASC, id ASC
            """,
            (physical_part_id,),
        )

    def get_stage_history(self, stage: str, limit: int = 100) -> list[StoredInspection]:
        """Return newest records for one station code."""
        return self._fetch_many(
            """
            SELECT id, physical_part_id, station_code AS stage, serial_number, inspected_at, decision,
                   final_disposition, source_name, reject_requested, measurements, defects, overlay_path,
                   inspection_mode, cycle_time_ms
            FROM inspection_records
            WHERE station_code = %s
            ORDER BY inspected_at DESC, id DESC
            LIMIT %s
            """,
            (stage, limit),
        )

    def _fetch_many(self, query: str, params: tuple[Any, ...]) -> list[StoredInspection]:
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return [StoredInspection(**row) for row in cursor.fetchall()]

    @contextmanager
    def _connect(self, **kwargs: Any) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self.dsn, **kwargs) as connection:
            yield connection

    def save_calibration(self, camera_id: str, mm_per_pixel: float, reference_od_mm: float, reference_hole_mm: float) -> int:
        """Save a new active camera calibration."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE camera_calibration SET active = FALSE WHERE camera_id = %s",
                    (camera_id,)
                )
                cursor.execute(
                    """
                    INSERT INTO camera_calibration (camera_id, mm_per_pixel, reference_od_mm, reference_hole_mm, active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (camera_id, mm_per_pixel, reference_od_mm, reference_hole_mm)
                )
                return int(cursor.fetchone()[0])

    def get_active_calibration(self, camera_id: str) -> dict[str, Any] | None:
        """Get the current active calibration for a camera."""
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, camera_id, calibration_date, mm_per_pixel, reference_od_mm, reference_hole_mm
                    FROM camera_calibration
                    WHERE camera_id = %s AND active = TRUE
                    ORDER BY calibration_date DESC
                    LIMIT 1
                    """,
                    (camera_id,)
                )
                return cursor.fetchone()

    def get_calibration_history(self, camera_id: str) -> list[dict[str, Any]]:
        """Get all calibration history for a camera."""
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, camera_id, calibration_date, mm_per_pixel, reference_od_mm, reference_hole_mm, active
                    FROM camera_calibration
                    WHERE camera_id = %s
                    ORDER BY calibration_date DESC
                    """,
                    (camera_id,)
                )
                return cursor.fetchall()

    def save_alarm(
        self,
        *,
        category: str,
        severity: str,
        message: str,
        source: str,
        acknowledged: bool = False,
    ) -> int:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO system_alarms (category, severity, message, source, acknowledged)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (category, severity, message, source, acknowledged),
                )
                return int(cursor.fetchone()[0])

    def list_alarms(self, *, active_only: bool = False, limit: int = 100) -> list[dict[str, Any]]:
        where_clause = "WHERE acknowledged = FALSE" if active_only else ""
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, created_at, category, severity, message, source, acknowledged, acknowledged_at
                    FROM system_alarms
                    {where_clause}
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return cursor.fetchall()

    def acknowledge_alarm(self, alarm_id: int) -> bool:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE system_alarms
                    SET acknowledged = TRUE, acknowledged_at = now()
                    WHERE id = %s
                    """,
                    (alarm_id,),
                )
                return cursor.rowcount > 0

    def save_health_snapshot(self, snapshot: dict[str, Any]) -> int:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO system_health_history (
                        cpu_usage_percent,
                        memory_usage_percent,
                        cpu_temperature_c,
                        disk_usage_percent,
                        free_disk_gb,
                        inspection_fps,
                        parts_per_minute,
                        avg_cycle_time_ms,
                        network_online,
                        camera_online,
                        plc_online,
                        database_online
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        snapshot.get("cpu_usage"),
                        snapshot.get("memory_usage"),
                        snapshot.get("temperature"),
                        snapshot.get("disk_usage"),
                        snapshot.get("free_disk_gb"),
                        snapshot.get("inspection_fps"),
                        snapshot.get("parts_per_minute"),
                        snapshot.get("average_cycle_time_ms"),
                        snapshot.get("network_online"),
                        snapshot.get("camera_online"),
                        snapshot.get("plc_online"),
                        snapshot.get("database_online"),
                    ),
                )
                return int(cursor.fetchone()[0])

    def get_health_history(self, *, hours: int = 24, limit: int = 500) -> list[dict[str, Any]]:
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, captured_at, cpu_usage_percent, memory_usage_percent, cpu_temperature_c,
                           disk_usage_percent, free_disk_gb, inspection_fps, parts_per_minute,
                           avg_cycle_time_ms, network_online, camera_online, plc_online, database_online
                    FROM system_health_history
                    WHERE captured_at >= now() - make_interval(hours => %s)
                    ORDER BY captured_at DESC
                    LIMIT %s
                    """,
                    (hours, limit),
                )
                return cursor.fetchall()

    def prune_health_history(self, *, days: int = 30) -> int:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM system_health_history
                    WHERE captured_at < now() - make_interval(days => %s)
                    """,
                    (days,),
                )
                return cursor.rowcount

    def database_size_bytes(self) -> int:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_database_size(current_database())")
                value = cursor.fetchone()
                return int(value[0]) if value else 0

    def health_query(self) -> bool:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                value = cursor.fetchone()
                return bool(value and value[0] == 1)

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, username, password_hash, role, active, created_at
                    FROM app_users
                    WHERE username = %s
                    LIMIT 1
                    """,
                    (username,),
                )
                return cursor.fetchone()

    def create_user(self, *, username: str, password_hash: str, role: str) -> int:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO app_users (username, password_hash, role, active)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (username, password_hash, role),
                )
                return int(cursor.fetchone()[0])

    def ensure_default_admin(self, *, username: str, password_hash: str) -> int | None:
        existing = self.get_user_by_username(username)
        if existing:
            return int(existing["id"])
        try:
            return self.create_user(username=username, password_hash=password_hash, role="ADMIN")
        except Exception:
            return None

    def write_audit_log(self, *, actor: str | None, action: str, resource: str | None, message: str, details: dict[str, Any] | None) -> int:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_logs (actor, action, resource, message, details)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (actor, action, resource, message, Jsonb(details or {})),
                )
                return int(cursor.fetchone()[0])

    def list_users(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, created_at, username, role, active
                    FROM app_users
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return cursor.fetchall()

    def list_audit_logs(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, created_at, actor, action, resource, message, details
                    FROM audit_logs
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return cursor.fetchall()
