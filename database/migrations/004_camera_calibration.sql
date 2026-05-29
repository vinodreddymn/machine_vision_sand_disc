-- Migration 004: Camera Calibration Schema

BEGIN;

CREATE TABLE IF NOT EXISTS public.camera_calibration (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) NOT NULL,
    calibration_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    mm_per_pixel FLOAT NOT NULL,
    reference_od_mm FLOAT NOT NULL,
    reference_hole_mm FLOAT NOT NULL,
    active BOOLEAN DEFAULT TRUE
);

-- Index for quick active calibration lookup
CREATE INDEX IF NOT EXISTS idx_camera_calibration_active
    ON public.camera_calibration (camera_id, active);

COMMIT;
