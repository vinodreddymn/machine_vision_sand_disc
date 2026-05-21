-- Migration 002: Split inspection records and serial registry into separate tables per stage for independent operation.
-- Target database: machine_vision

BEGIN;

-- Stage 1 registries and partitioned records
CREATE TABLE IF NOT EXISTS public.stage1_serial_registry (
    serial_number TEXT PRIMARY KEY,
    physical_part_id TEXT NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.stage1_inspection_records (
    id BIGSERIAL NOT NULL,
    physical_part_id TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    inspected_at TIMESTAMPTZ NOT NULL,
    decision TEXT NOT NULL,
    final_disposition TEXT NOT NULL,
    source_name TEXT,
    reject_requested BOOLEAN NOT NULL DEFAULT FALSE,
    measurements JSONB NOT NULL,
    defects JSONB NOT NULL,
    overlay_path TEXT,
    CONSTRAINT stage1_inspection_records_pkey PRIMARY KEY (id, inspected_at)
) PARTITION BY RANGE (inspected_at);

CREATE INDEX IF NOT EXISTS idx_stage1_inspection_records_part
    ON public.stage1_inspection_records (physical_part_id, inspected_at);

CREATE INDEX IF NOT EXISTS idx_stage1_inspection_records_stage_time
    ON public.stage1_inspection_records (inspected_at DESC);

CREATE INDEX IF NOT EXISTS idx_stage1_inspection_records_serial_lookup
    ON public.stage1_inspection_records (serial_number, inspected_at DESC);

-- Stage 2 registries and partitioned records
CREATE TABLE IF NOT EXISTS public.stage2_serial_registry (
    serial_number TEXT PRIMARY KEY,
    physical_part_id TEXT NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.stage2_inspection_records (
    id BIGSERIAL NOT NULL,
    physical_part_id TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    inspected_at TIMESTAMPTZ NOT NULL,
    decision TEXT NOT NULL,
    final_disposition TEXT NOT NULL,
    source_name TEXT,
    reject_requested BOOLEAN NOT NULL DEFAULT FALSE,
    measurements JSONB NOT NULL,
    defects JSONB NOT NULL,
    overlay_path TEXT,
    CONSTRAINT stage2_inspection_records_pkey PRIMARY KEY (id, inspected_at)
) PARTITION BY RANGE (inspected_at);

CREATE INDEX IF NOT EXISTS idx_stage2_inspection_records_part
    ON public.stage2_inspection_records (physical_part_id, inspected_at);

CREATE INDEX IF NOT EXISTS idx_stage2_inspection_records_stage_time
    ON public.stage2_inspection_records (inspected_at DESC);

CREATE INDEX IF NOT EXISTS idx_stage2_inspection_records_serial_lookup
    ON public.stage2_inspection_records (serial_number, inspected_at DESC);

-- Helper functions for daily partitions
CREATE OR REPLACE FUNCTION public.ensure_stage1_partition(partition_day DATE)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_name TEXT := format('stage1_inspection_records_%s', to_char(partition_day, 'YYYY_MM_DD'));
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS public.%I PARTITION OF public.stage1_inspection_records
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        partition_day::TIMESTAMPTZ,
        (partition_day + 1)::TIMESTAMPTZ
    );
    RETURN partition_name;
END
$$;

CREATE OR REPLACE FUNCTION public.ensure_stage2_partition(partition_day DATE)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_name TEXT := format('stage2_inspection_records_%s', to_char(partition_day, 'YYYY_MM_DD'));
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS public.%I PARTITION OF public.stage2_inspection_records
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        partition_day::TIMESTAMPTZ,
        (partition_day + 1)::TIMESTAMPTZ
    );
    RETURN partition_name;
END
$$;

-- Create practical initial partitions window
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
        PERFORM public.ensure_stage1_partition(partition_day);
        PERFORM public.ensure_stage2_partition(partition_day);
    END LOOP;
END
$$;

COMMIT;
