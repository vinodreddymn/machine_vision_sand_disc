import { getJson, postJson } from './apiService';
import type { Alarm, DeviceStatus, HealthHistory, StartupDiagnostics, SystemHealth, ServiceStatus } from '../types/systemHealth';
import { API } from '../utils/constants';

export function getSystemHealth(): Promise<SystemHealth> {
  return getJson<SystemHealth>(API.SYSTEM_HEALTH);
}

export function getDeviceStatus(): Promise<DeviceStatus> {
  return getJson<DeviceStatus>(API.SYSTEM_DEVICES);
}

export function getActiveAlarms(): Promise<Alarm[]> {
  return getJson<Alarm[]>(API.SYSTEM_ALARMS);
}

export function getAlarmHistory(): Promise<Alarm[]> {
  return getJson<Alarm[]>(API.SYSTEM_ALARM_HISTORY);
}

export function acknowledgeAlarm(alarmId: number): Promise<{ status: string; id: number }> {
  return postJson<{ status: string; id: number }>(`${API.SYSTEM_ALARM_ACK_PREFIX}/${alarmId}/ack`);
}

export function getSystemHistory(hours = 24, limit = 500): Promise<HealthHistory[]> {
  return getJson<HealthHistory[]>(`${API.SYSTEM_HISTORY}?hours=${hours}&limit=${limit}`);
}

export function getServiceStatus(): Promise<Record<string, ServiceStatus>> {
  return getJson<Record<string, ServiceStatus>>(API.SYSTEM_SERVICES);
}

export function getStartupDiagnostics(): Promise<StartupDiagnostics> {
  return getJson<StartupDiagnostics>('/api/system/diagnostics');
}
