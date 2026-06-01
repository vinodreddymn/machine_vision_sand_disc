-- Migration 005: Add configuration store for JSON-based system settings.
-- Stores all JSON configuration files (tolerances, health_thresholds, etc.) in the database
-- with versioning and audit trail support for Industry 4.0 compliance.

BEGIN;

CREATE TABLE IF NOT EXISTS public.config_store (
    id BIGSERIAL PRIMARY KEY,
    config_key TEXT NOT NULL,
    config_type TEXT NOT NULL DEFAULT 'json',
    config_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by TEXT,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(config_key, version)
);

CREATE INDEX IF NOT EXISTS idx_config_store_key
    ON public.config_store (config_key);

CREATE INDEX IF NOT EXISTS idx_config_store_active
    ON public.config_store (config_key, is_active);

CREATE INDEX IF NOT EXISTS idx_config_store_updated_at
    ON public.config_store (updated_at DESC);

-- Configuration versioning and rollback tracking
CREATE TABLE IF NOT EXISTS public.config_audit_log (
    id BIGSERIAL PRIMARY KEY,
    config_key TEXT NOT NULL,
    action TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    version_number INTEGER,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason TEXT,
    ip_address TEXT
);

CREATE INDEX IF NOT EXISTS idx_config_audit_log_key
    ON public.config_audit_log (config_key);

CREATE INDEX IF NOT EXISTS idx_config_audit_log_changed_at
    ON public.config_audit_log (changed_at DESC);

COMMIT;
