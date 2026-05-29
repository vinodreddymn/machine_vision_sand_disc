-- Migration 003: Convert persistence to the single-station inspection schema.
-- Target database: machine_vision / diskvision
--
-- Run during a controlled maintenance window after taking a backup. Existing
-- stage1/stage2 tables are preserved; optional backfill copies stage1 rows
-- into the new single-station table.

BEGIN;

CREATE TABLE IF NOT EXISTS public.inspection_serial_registry (
    serial_number TEXT PRIMARY KEY,
    physical_part_id TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'S1',
    station_code TEXT NOT NULL DEFAULT 'SINGLE',
    first_seen_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE IF EXISTS public.inspection_serial_registry
    ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT 'S1';

ALTER TABLE IF EXISTS public.inspection_serial_registry
    ALTER COLUMN stage SET DEFAULT 'S1';

ALTER TABLE IF EXISTS public.inspection_serial_registry
    ADD COLUMN IF NOT EXISTS station_code TEXT NOT NULL DEFAULT 'SINGLE';

CREATE TABLE IF NOT EXISTS public.inspection_records (
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
    CONSTRAINT inspection_records_pkey PRIMARY KEY (id, inspected_at)
) PARTITION BY RANGE (inspected_at);

ALTER TABLE IF EXISTS public.inspection_records
    ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT 'S1';

ALTER TABLE IF EXISTS public.inspection_records
    ALTER COLUMN stage SET DEFAULT 'S1';

ALTER TABLE IF EXISTS public.inspection_records
    ADD COLUMN IF NOT EXISTS station_code TEXT NOT NULL DEFAULT 'SINGLE';

CREATE INDEX IF NOT EXISTS idx_inspection_records_part
    ON public.inspection_records (physical_part_id, inspected_at);

CREATE INDEX IF NOT EXISTS idx_inspection_records_station_time
    ON public.inspection_records (station_code, inspected_at DESC);

CREATE INDEX IF NOT EXISTS idx_inspection_records_serial_lookup
    ON public.inspection_records (serial_number, inspected_at DESC);

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

DO $$
DECLARE
    partition_day DATE;
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

-- Optional backfill from the previous Stage 1 table. Uncomment after reviewing
-- row counts and deciding whether the old top-side history should become the
-- single-station history.
--
-- INSERT INTO public.inspection_serial_registry (
--     serial_number,
--     physical_part_id,
--     station_code,
--     first_seen_at
-- )
-- SELECT DISTINCT ON (serial_number)
--     serial_number,
--     physical_part_id,
--     'SINGLE',
--     first_seen_at
-- FROM public.stage1_serial_registry
-- ORDER BY serial_number, first_seen_at ASC
-- ON CONFLICT (serial_number) DO NOTHING;
--
-- INSERT INTO public.inspection_records (
--     physical_part_id,
--     station_code,
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
--     physical_part_id,
--     'SINGLE',
--     serial_number,
--     inspected_at,
--     decision,
--     CASE
--         WHEN final_disposition = 'REJECTED AT STATION 1' THEN 'REJECTED'
--         ELSE final_disposition
--     END,
--     source_name,
--     reject_requested,
--     measurements,
--     defects,
--     overlay_path
-- FROM public.stage1_inspection_records;

COMMIT;
