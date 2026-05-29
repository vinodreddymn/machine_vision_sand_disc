export type PlcStatus = {
  run_status: string;
  mode: string;
  conveyor_status: string;
  reject_actuator: string;
  accept_gate: string;
};

export type Status = {
  running: boolean;
  mode: string;
  part_id: string;
  plc: PlcStatus;
  storage: string;
  pending_label: boolean;
  log_count: number;
  camera_name?: string;
};

export type Station = {
  station: string;
  name: string;
  active: boolean;
  part_id: string | null;
  serial_number: string | null;
  decision: string;
  disposition: string;
  source_name: string | null;
  system_prediction: string | null;
  anomaly_score: number | null;
  pending_label: boolean;
  defects: string[];
  measurements: Record<string, number | string>;
  stream_url: string;
  captured_image_url: string;
  cycle_time_ms: number | null;
};

export type Metrics = {
  total_parts: number;
  passed_parts: number;
  rejected_parts: number;
  station1_passed: number;
  station1_rejected: number;
  dataset: Record<string, number>;
};

export type StoredInspection = {
  id: number;
  physical_part_id: string;
  stage: string;
  serial_number: string;
  inspected_at: string;
  decision: string;
  final_disposition: string;
  source_name: string | null;
  reject_requested: boolean;
  measurements: Record<string, number | string>;
  defects: string[];
  overlay_path: string | null;
  inspection_mode: string;
  cycle_time_ms: number | null;
};

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadImage(station: string, file: File): Promise<unknown> {
  const data = new FormData();
  data.append('file', file);
  const response = await fetch(`/api/upload?station=${encodeURIComponent(station)}`, {
    method: 'POST',
    body: data
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function getTolerances(): Promise<Record<string, any>> {
  return getJson<Record<string, any>>('/api/config/tolerances');
}

export async function saveTolerances(tolerances: Record<string, any>): Promise<{ status: string }> {
  return postJson<{ status: string }>('/api/config/tolerances', tolerances);
}

export async function setInspectionMode(mode: string): Promise<{ mode: string }> {
  return postJson<{ mode: string }>('/api/config/mode', { mode });
}

export async function getHistory(): Promise<StoredInspection[]> {
  return getJson<StoredInspection[]>('/api/history');
}

export async function uploadVideo(station: string, file: File): Promise<unknown> {
  const data = new FormData();
  data.append('file', file);
  const response = await fetch(`/api/upload-video?station=${encodeURIComponent(station)}`, {
    method: 'POST',
    body: data
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function resetCamera(station: string): Promise<unknown> {
  return postJson(`/api/reset-camera?station=${encodeURIComponent(station)}`);
}

// ─── Calibration Types ────────────────────────────────────────────────────────

export type CalibrationStatus = {
  calibrated: boolean;
  camera_id?: string;
  calibration_date?: string;
  mm_per_pixel?: number;
  reference_od_mm?: number;
  reference_hole_mm?: number;
  storage?: string;
};

export type CalibrationCaptureResult = {
  outer_diameter_px: number;
  hole_diameter_px: number;
  overlay_image: string;
};

export type CalibrationRecord = {
  id: number;
  camera_id: string;
  calibration_date: string;
  mm_per_pixel: number;
  reference_od_mm: number;
  reference_hole_mm: number;
  active: boolean;
};

export type ValidationResult = {
  expected_mm: number;
  measured_mm: number;
  error_mm: number;
  passed: boolean;
  tolerance: number;
  overlay_image?: string;
};

// ─── Calibration API Functions ────────────────────────────────────────────────

export async function getCalibrationStatus(cameraId = 'CAM01'): Promise<CalibrationStatus> {
  return getJson<CalibrationStatus>(`/api/calibration/status?camera_id=${cameraId}`);
}

export async function captureLiveCalibration(): Promise<CalibrationCaptureResult> {
  const response = await fetch('/api/calibration/capture-live', { method: 'POST' });
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try { detail = JSON.parse(text).detail ?? text; } catch (_) {}
    throw new Error(detail);
  }
  return response.json();
}

export async function uploadCalibrationImage(file: File): Promise<CalibrationCaptureResult> {
  const data = new FormData();
  data.append('file', file);
  const response = await fetch('/api/calibration/capture', { method: 'POST', body: data });
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try { detail = JSON.parse(text).detail ?? text; } catch (_) {}
    throw new Error(detail);
  }
  return response.json();
}

export async function saveCalibration(
  cameraId: string,
  outerDiameterPx: number,
  referenceOdMm: number,
  referenceHoleMm: number,
): Promise<{ status: string; record_id: number; mm_per_pixel: number }> {
  return postJson('/api/calibration/save', {
    camera_id: cameraId,
    outer_diameter_px: outerDiameterPx,
    reference_od_mm: referenceOdMm,
    reference_hole_mm: referenceHoleMm,
  });
}

export async function getCalibrationHistory(cameraId = 'CAM01'): Promise<CalibrationRecord[]> {
  return getJson<CalibrationRecord[]>(`/api/calibration/history?camera_id=${cameraId}`);
}

export async function deleteCalibration(id: number): Promise<void> {
  const response = await fetch(`/api/calibration/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`Failed to delete calibration record ${id}`);
}

export async function validateCalibration(
  cameraId: string,
  referenceOdMm: number,
  tolerance = 0.1,
): Promise<ValidationResult> {
  return postJson('/api/calibration/validate', {
    camera_id: cameraId,
    reference_od_mm: referenceOdMm,
    tolerance,
  });
}

export function downloadCalibrationReport(cameraId = 'CAM01') {
  window.open(`/api/calibration/report?camera_id=${encodeURIComponent(cameraId)}`, '_blank');
}
