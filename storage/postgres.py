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

