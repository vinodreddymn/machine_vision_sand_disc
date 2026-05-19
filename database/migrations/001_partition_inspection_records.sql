-- Partition inspection_records by day for high-volume industrial workloads.
-- PostgreSQL 15+ compatible.
--
-- Target database: machine_vision
-- Partition key: inspected_at
-- Partition cadence: daily
--
-- Run during a controlled maintenance window after taking a backup.

BEGIN;

-- Preserve the current non-partitioned table exactly once.
DO $$
DECLARE
    relation_kind "char";
    legacy_exists BOOLEAN;
BEGIN
    SELECT c.relkind
    INTO relation_kind
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname = 'inspection_records';

    SELECT EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relname = 'inspection_records_legacy'
    )
    INTO legacy_exists;

    IF relation_kind = 'r' AND NOT legacy_exists THEN
        ALTER TABLE public.inspection_records
            RENAME TO inspection_records_legacy;

        -- Free canonical index names for the new partitioned parent while
        -- preserving the old table for rollback or optional backfill.
        ALTER INDEX IF EXISTS public.inspection_records_pkey
            RENAME TO inspection_records_legacy_pkey;
        ALTER INDEX IF EXISTS public.inspection_records_serial_number_key
            RENAME TO inspection_records_legacy_serial_number_key;
        ALTER INDEX IF EXISTS public.idx_inspection_records_part
            RENAME TO idx_inspection_records_legacy_part;
        ALTER INDEX IF EXISTS public.idx_inspection_records_stage_time
            RENAME TO idx_inspection_records_legacy_stage_time;
    END IF;
END
$$;

-- Global serial-number registry.
-- PostgreSQL cannot enforce UNIQUE(serial_number) across a RANGE-partitioned table
-- unless inspected_at is part of that constraint. This small companion table keeps
-- serial-number uniqueness global and cheap to check.
CREATE TABLE IF NOT EXISTS public.inspection_serial_registry (
    serial_number TEXT PRIMARY KEY,
    physical_part_id TEXT NOT NULL,
    stage TEXT NOT NULL CHECK (stage IN ('S1', 'S2')),
    first_seen_at TIMESTAMPTZ NOT NULL
);

-- New partitioned parent table.
CREATE TABLE IF NOT EXISTS public.inspection_records (
    id BIGSERIAL NOT NULL,
    physical_part_id TEXT NOT NULL,
    stage TEXT NOT NULL CHECK (stage IN ('S1', 'S2')),
    serial_number TEXT NOT NULL,
    inspected_at TIMESTAMPTZ NOT NULL,
    decision TEXT NOT NULL,
    final_disposition TEXT NOT NULL,
    source_name TEXT,
    reject_requested BOOLEAN NOT NULL DEFAULT FALSE,
    measurements JSONB NOT NULL,
    defects JSONB NOT NULL,
    overlay_path TEXT,
    CONSTRAINT inspection_records_pkey PRIMARY KEY (id, inspected_at)
) PARTITION BY RANGE (inspected_at);

-- Parent-level indexes automatically create matching indexes on partitions.
CREATE INDEX IF NOT EXISTS idx_inspection_records_part
    ON public.inspection_records (physical_part_id, inspected_at);

CREATE INDEX IF NOT EXISTS idx_inspection_records_stage_time
    ON public.inspection_records (stage, inspected_at DESC);

CREATE INDEX IF NOT EXISTS idx_inspection_records_serial_lookup
    ON public.inspection_records (serial_number, inspected_at DESC);

-- Reusable helper for scheduler jobs and one-off maintenance.
CREATE OR REPLACE FUNCTION public.ensure_inspection_records_partition(partition_day DATE)
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

-- Create a practical initial partition window around the migration date.
-- Adjust the lower/upper offsets if you need a larger historical preload window.
DO $$
DECLARE
    partition_day DATE;
    partition_name TEXT;
BEGIN
    FOR partition_day IN
        SELECT generate_series(
            CURRENT_DATE - INTERVAL '7 days',
            CURRENT_DATE + INTERVAL '7 days',
            INTERVAL '1 day'
        )::DATE
    LOOP
        PERFORM public.ensure_inspection_records_partition(partition_day);
    END LOOP;
END
$$;

-- Optional historical migration.
-- Leave commented until you have reviewed row count, timing, and downtime.
--
-- 1) Backfill the global serial registry.
-- INSERT INTO public.inspection_serial_registry (
--     serial_number,
--     physical_part_id,
--     stage,
--     first_seen_at
-- )
-- SELECT DISTINCT ON (serial_number)
--     serial_number,
--     physical_part_id,
--     stage,
--     inspected_at
-- FROM public.inspection_records_legacy
-- ORDER BY serial_number, inspected_at ASC;
--
-- 2) Copy old inspection rows into the partitioned parent.
-- INSERT INTO public.inspection_records (
--     id,
--     physical_part_id,
--     stage,
--     serial_number,
--     inspected_at,
--     decision,
--     final_disposition,
--     source_name,
--     reject_requested,
--     measurements,
--     defects,
--     overlay_path
-- )
-- SELECT
--     id,
--     physical_part_id,
--     stage,
--     serial_number,
--     inspected_at,
--     decision,
--     final_disposition,
--     source_name,
--     reject_requested,
--     measurements,
--     defects,
--     overlay_path
-- FROM public.inspection_records_legacy;
--
-- 3) Advance the sequence after preserving old ids.
-- SELECT setval(
--     pg_get_serial_sequence('public.inspection_records', 'id'),
--     COALESCE((SELECT MAX(id) FROM public.inspection_records), 1),
--     TRUE
-- );

COMMIT;
