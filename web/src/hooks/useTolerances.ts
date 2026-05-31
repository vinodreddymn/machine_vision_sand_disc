import { useState, useEffect, useCallback } from 'react';
import {
  getTolerances,
  saveTolerances,
} from '../services/toleranceService';
import type {
  ToleranceSettings,
  ToleranceValidationErrors,
} from '../types/settings';

export interface UseTolerancesReturn {
  tolerances: ToleranceSettings | null;
  setTolerances: React.Dispatch<React.SetStateAction<ToleranceSettings | null>>;
  saving: boolean;
  success: boolean;
  error: string | null;
  validationErrors: ToleranceValidationErrors;
  save: (e: React.FormEvent) => Promise<void>;
  reload: () => Promise<void>;
}

function validate(t: ToleranceSettings): ToleranceValidationErrors {
  const errors: ToleranceValidationErrors = {};

  if (!t.expected_hole_count || t.expected_hole_count < 1) {
    errors.expected_hole_count = 'Hole count must be ≥ 1';
  }
  if (t.hole_circularity_min <= 0 || t.hole_circularity_min > 1) {
    errors.hole_circularity_min = 'Circularity must be between 0 and 1';
  }
  if (t.outer_radius_px.min < 0) {
    errors.outer_radius_px_min = 'Min radius must be ≥ 0';
  }
  if (t.outer_radius_px.max <= t.outer_radius_px.min) {
    errors.outer_radius_px_max = 'Max radius must be greater than min radius';
  }
  if (t.surface.min_defect_area_px <= 0) {
    errors.surface_min_defect_area_px = 'Defect area must be > 0';
  }
  if (
    t.surface.max_total_defect_area_ratio <= 0 ||
    t.surface.max_total_defect_area_ratio > 1
  ) {
    errors.surface_max_total_defect_area_ratio =
      'Defect area ratio must be between 0 and 1';
  }

  return errors;
}

/**
 * Manages tolerance settings: loading, editing, validation, saving.
 * @param active - only fetches when true
 */
export function useTolerances(active: boolean): UseTolerancesReturn {
  const [tolerances, setTolerances] = useState<ToleranceSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] =
    useState<ToleranceValidationErrors>({});

  const reload = useCallback(async () => {
    try {
      const data = await getTolerances();
      setTolerances(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    if (active) {
      void reload();
    }
  }, [active, reload]);

  const save = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!tolerances) return;

      const errors = validate(tolerances);
      setValidationErrors(errors);
      if (Object.keys(errors).length > 0) return;

      setSaving(true);
      setSuccess(false);
      try {
        await saveTolerances(tolerances);
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setSaving(false);
      }
    },
    [tolerances],
  );

  return {
    tolerances,
    setTolerances,
    saving,
    success,
    error,
    validationErrors,
    save,
    reload,
  };
}
