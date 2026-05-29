-- Migration 004: Add optional audit table for human-in-the-loop labels.
-- The image dataset remains filesystem-backed under dataset/, while this table
-- gives production deployments a database-visible label trail.

BEGIN;

CREATE TABLE IF NOT EXISTS public.dataset_label_records (
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
    ON public.dataset_label_records (physical_part_id, labeled_at DESC);

COMMIT;
