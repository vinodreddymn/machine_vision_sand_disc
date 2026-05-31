// ─── Tolerance Settings ───────────────────────────────────────────────────────

export interface RadiusRange {
  min: number;
  max: number;
}

export interface SurfaceSettings {
  min_defect_area_px: number;
  max_total_defect_area_ratio: number;
}

export interface ToleranceSettings {
  expected_hole_count: number;
  hole_circularity_min: number;
  outer_radius_px: RadiusRange;
  surface: SurfaceSettings;
}

export const defaultTolerances: ToleranceSettings = {
  expected_hole_count: 1,
  hole_circularity_min: 0.7,
  outer_radius_px: { min: 50, max: 300 },
  surface: { min_defect_area_px: 50, max_total_defect_area_ratio: 0.05 },
};

// ─── Tolerance Validation Errors ──────────────────────────────────────────────

export type ToleranceValidationErrors = Partial<{
  expected_hole_count: string;
  hole_circularity_min: string;
  outer_radius_px_min: string;
  outer_radius_px_max: string;
  surface_min_defect_area_px: string;
  surface_max_total_defect_area_ratio: string;
}>;

// ─── Inspection Mode ──────────────────────────────────────────────────────────

export type InspectionMode = 'PRODUCTION' | 'DATA_COLLECTION';
