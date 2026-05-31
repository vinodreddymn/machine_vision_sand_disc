import { getJson, postJson, uploadFile } from './apiService';
import type {
  CalibrationStatus,
  CalibrationCaptureResult,
  CalibrationRecord,
  ValidationResult,
  CalibrationSaveResult,
} from '../types/calibration';

export async function getCalibrationStatus(
  cameraId = 'CAM01',
): Promise<CalibrationStatus> {
  return getJson<CalibrationStatus>(
    `/api/calibration/status?camera_id=${cameraId}`,
  );
}

export async function captureLiveCalibration(): Promise<CalibrationCaptureResult> {
  const response = await fetch('/api/calibration/capture-live', {
    method: 'POST',
  });
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try {
      detail = (JSON.parse(text) as { detail?: string }).detail ?? text;
    } catch {
      // Use raw text
    }
    throw new Error(detail);
  }
  return response.json() as Promise<CalibrationCaptureResult>;
}

export async function uploadCalibrationImage(
  file: File,
): Promise<CalibrationCaptureResult> {
  const data = new FormData();
  data.append('file', file);
  const response = await fetch('/api/calibration/capture', {
    method: 'POST',
    body: data,
  });
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try {
      detail = (JSON.parse(text) as { detail?: string }).detail ?? text;
    } catch {
      // Use raw text
    }
    throw new Error(detail);
  }
  return response.json() as Promise<CalibrationCaptureResult>;
}

export async function saveCalibration(
  cameraId: string,
  outerDiameterPx: number,
  referenceOdMm: number,
  referenceHoleMm: number,
): Promise<CalibrationSaveResult> {
  return postJson<CalibrationSaveResult>('/api/calibration/save', {
    camera_id: cameraId,
    outer_diameter_px: outerDiameterPx,
    reference_od_mm: referenceOdMm,
    reference_hole_mm: referenceHoleMm,
  });
}

export async function getCalibrationHistory(
  cameraId = 'CAM01',
): Promise<CalibrationRecord[]> {
  return getJson<CalibrationRecord[]>(
    `/api/calibration/history?camera_id=${cameraId}`,
  );
}

export async function deleteCalibration(id: number): Promise<void> {
  const response = await fetch(`/api/calibration/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete calibration record ${id}`);
  }
}

export async function validateCalibration(
  cameraId: string,
  referenceOdMm: number,
  tolerance = 0.1,
): Promise<ValidationResult> {
  return postJson<ValidationResult>('/api/calibration/validate', {
    camera_id: cameraId,
    reference_od_mm: referenceOdMm,
    tolerance,
  });
}

export function downloadCalibrationReport(cameraId = 'CAM01'): void {
  window.open(
    `/api/calibration/report?camera_id=${encodeURIComponent(cameraId)}`,
    '_blank',
  );
}

// Keep uploadFile export for any consumers that need it
export { uploadFile };
