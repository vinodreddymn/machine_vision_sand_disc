import { getJson, postJson } from './apiService';
import type { ToleranceSettings } from '../types/settings';
import type { InspectionMode } from '../types/settings';

export async function getTolerances(): Promise<ToleranceSettings> {
  return getJson<ToleranceSettings>('/api/config/tolerances');
}

export async function saveTolerances(
  tolerances: ToleranceSettings,
): Promise<{ status: string }> {
  return postJson<{ status: string }>('/api/config/tolerances', tolerances);
}

export async function setInspectionMode(
  mode: InspectionMode | string,
): Promise<{ mode: string }> {
  return postJson<{ mode: string }>('/api/config/mode', { mode });
}
