-- Migration 006: Runtime controller, richer dataset labels, and model registry groundwork.

BEGIN;

CREATE TABLE IF NOT EXISTS public.inspection_runtime_state (
    id BIGSERIAL PRIMARY KEY,
    state TEXT NOT NULL,
    last_command TEXT,
    requested_by TEXT,
    fault_reason TEXT,
    config_version INTEGER,
    reload_requested BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_inspection_runtime_state_updated_at
    ON public.inspection_runtime_state (updated_at DESC);

ALTER TABLE IF EXISTS public.dataset_label_records
    ADD COLUMN IF NOT EXISTS prediction TEXT;

ALTER TABLE IF EXISTS public.dataset_label_records
    ADD COLUMN IF NOT EXISTS label_source TEXT;

ALTER TABLE IF EXISTS public.dataset_label_records
    ADD COLUMN IF NOT EXISTS override_reason TEXT;

ALTER TABLE IF EXISTS public.dataset_label_records
    ADD COLUMN IF NOT EXISTS confidence NUMERIC(6, 4);

CREATE INDEX IF NOT EXISTS idx_dataset_label_records_label_source
    ON public.dataset_label_records (label_source);

CREATE TABLE IF NOT EXISTS public.model_registry (
    id BIGSERIAL PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    training_date TIMESTAMPTZ,
    dataset_size BIGINT,
    accuracy NUMERIC(6, 4),
    active BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    model_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_model_registry_active
    ON public.model_registry (active, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.plc_command_log (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    command TEXT NOT NULL,
    source TEXT,
    requested_by TEXT,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_plc_command_log_created_at
    ON public.plc_command_log (created_at DESC);

COMMIT;
