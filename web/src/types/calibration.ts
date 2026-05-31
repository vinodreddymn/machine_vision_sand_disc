// ─── Calibration Types ────────────────────────────────────────────────────────

export interface CalibrationStatus {
  calibrated: boolean;
  camera_id?: string;
  calibration_date?: string;
  mm_per_pixel?: number;
  reference_od_mm?: number;
  reference_hole_mm?: number;
  storage?: string;
}

export interface CalibrationCaptureResult {
  outer_diameter_px: number;
  hole_diameter_px: number;
  overlay_image: string;
}

export interface CalibrationRecord {
  id: number;
  camera_id: string;
  calibration_date: string;
  mm_per_pixel: number;
  reference_od_mm: number;
  reference_hole_mm: number;
  active: boolean;
}

export interface ValidationResult {
  expected_mm: number;
  measured_mm: number;
  error_mm: number;
  passed: boolean;
  tolerance: number;
  overlay_image?: string;
}

export interface CalibrationSaveResult {
  status: string;
  record_id: number;
  mm_per_pixel: number;
}
