/**
 * Backward-compatibility barrel re-export.
 *
 * All imports that previously used `from './api'` continue to work.
 * New code should import directly from the appropriate module:
 *   - Types   → `../types/snapshot`, `../types/history`, etc.
 *   - Services → `../services/apiService`, `../services/calibrationService`, etc.
 */

// ─── Types ────────────────────────────────────────────────────────────────────
export type { PlcStatus, Status, Station, Metrics, Snapshot } from './types/snapshot';
export type { StoredInspection } from './types/history';
export type {
  CalibrationStatus,
  CalibrationCaptureResult,
  CalibrationRecord,
  ValidationResult,
  CalibrationSaveResult,
} from './types/calibration';
export type { SystemHealth, Alarm, DeviceStatus, HealthHistory } from './types/systemHealth';

// ─── API helpers ──────────────────────────────────────────────────────────────
export { getJson, postJson, uploadFile as uploadImage } from './services/apiService';

// ─── Inspection services ──────────────────────────────────────────────────────
export { getTolerances, saveTolerances, setInspectionMode } from './services/toleranceService';
export { getHistory } from './services/historyService';

// ─── Calibration services ─────────────────────────────────────────────────────
export {
  getCalibrationStatus,
  captureLiveCalibration,
  uploadCalibrationImage,
  saveCalibration,
  getCalibrationHistory,
  deleteCalibration,
  validateCalibration,
  downloadCalibrationReport,
} from './services/calibrationService';
export {
  getSystemHealth,
  getDeviceStatus,
  getActiveAlarms,
  getAlarmHistory,
  acknowledgeAlarm,
  getSystemHistory,
} from './services/systemHealthService';

// ─── Legacy upload helpers ────────────────────────────────────────────────────
import { uploadFile } from './services/apiService';

export async function uploadVideo(station: string, file: File): Promise<unknown> {
  return uploadFile(`/api/upload-video?station=${encodeURIComponent(station)}`, file);
}

export async function resetCamera(station: string): Promise<unknown> {
  const { postJson } = await import('./services/apiService');
  return postJson(`/api/reset-camera?station=${encodeURIComponent(station)}`);
}
