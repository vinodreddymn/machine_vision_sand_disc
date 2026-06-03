import { useCallback, useEffect, useState } from 'react';
import { Camera, Database, HardDrive, Network, Thermometer, Workflow } from 'lucide-react';
import type { Alarm, DeviceStatus, HealthHistory, StartupDiagnostics, SystemHealth, ServiceStatus } from '../types/systemHealth';
import { acknowledgeAlarm, getActiveAlarms, getDeviceStatus, getServiceStatus, getStartupDiagnostics, getSystemHealth, getSystemHistory } from '../services/systemHealthService';
import { postJson } from '../services/apiService';
import { StatusBadge } from '../components/system/StatusBadge';
import { HealthMetricGrid } from '../components/system/HealthMetricGrid';
import { AlarmPanel } from '../components/system/AlarmPanel';
import { TrendPanel } from '../components/system/TrendPanel';

function levelFromOnline(online: boolean): 'normal' | 'critical' {
  return online ? 'normal' : 'critical';
}

function levelFromTemp(temp: number | null): 'normal' | 'warning' | 'critical' | 'emergency' {
  if (temp === null) return 'warning';
  if (temp >= 85) return 'emergency';
  if (temp >= 80) return 'critical';
  if (temp >= 75) return 'warning';
  return 'normal';
}

function levelFromDisk(freeDiskGb: number | null): 'normal' | 'warning' | 'critical' | 'emergency' {
  if (freeDiskGb === null) return 'warning';
  if (freeDiskGb < 1) return 'emergency';
  if (freeDiskGb < 5) return 'critical';
  if (freeDiskGb < 10) return 'warning';
  return 'normal';
}

export function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [devices, setDevices] = useState<DeviceStatus | null>(null);
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [history, setHistory] = useState<HealthHistory[]>([]);
  const [services, setServices] = useState<Record<string, ServiceStatus>>({});
  const [diagnostics, setDiagnostics] = useState<StartupDiagnostics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notifStatus, setNotifStatus] = useState<{ channels: Array<{ type: string }> } | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [nextHealth, nextDevices, nextAlarms, nextHistory, nextDiagnostics] = await Promise.all([
        getSystemHealth(),
        getDeviceStatus(),
        getActiveAlarms(),
        getSystemHistory(24, 200),
        getStartupDiagnostics().catch(() => null),
      ]);
      const nextServices = await getServiceStatus();
      try {
        const n = await fetch('/api/system/notifications').then((r) => r.json() as Promise<{ channels: Array<{ type: string }> }>);
        setNotifStatus(n);
      } catch {
        setNotifStatus(null);
      }
      setHealth(nextHealth);
      setDevices(nextDevices);
      setAlarms(nextAlarms);
      setHistory(nextHistory);
      setDiagnostics(nextDiagnostics);
      setServices(nextServices);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => { void refresh(); }, 3000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const handleAcknowledge = useCallback(async (alarmId: number) => {
    await acknowledgeAlarm(alarmId);
    await refresh();
  }, [refresh]);

  return (
    <div className="settings-page">
      {error && <div className="alert">{error}</div>}

      <HealthMetricGrid health={health} />

      <div className="sys-badge-grid">
        <StatusBadge label="Camera" value={devices?.camera ?? 'UNKNOWN'} level={levelFromOnline(devices?.camera === 'ONLINE')} icon={<Camera size={14} />} />
        <StatusBadge label="PLC" value={devices?.plc ?? 'UNKNOWN'} level={levelFromOnline(devices?.plc === 'ONLINE')} icon={<Workflow size={14} />} />
        <StatusBadge label="Database" value={devices?.database ?? 'UNKNOWN'} level={levelFromOnline(devices?.database === 'ONLINE')} icon={<Database size={14} />} />
        <StatusBadge label="Network" value={devices?.network ?? 'UNKNOWN'} level={levelFromOnline(devices?.network === 'ONLINE')} icon={<Network size={14} />} />
        <StatusBadge label="Storage" value={`${health?.free_disk_gb ?? '--'} GB free`} level={levelFromDisk(health?.free_disk_gb ?? null)} icon={<HardDrive size={14} />} />
        <StatusBadge label="Temperature" value={`${health?.temperature ?? '--'} C`} level={levelFromTemp(health?.temperature ?? null)} icon={<Thermometer size={14} />} />
      </div>

      <AlarmPanel alarms={alarms} onAcknowledge={handleAcknowledge} />

      <div className="settings-group">
        <h3 style={{ margin: 0 }}>Service Status</h3>
        <div className="sys-badge-grid" style={{ marginTop: '12px' }}>
          {Object.entries(services).map(([name, svc]) => (
            <StatusBadge
              key={name}
              label={name}
              value={String(svc.status ?? 'UNKNOWN')}
              level={levelFromOnline(String(svc.status).toUpperCase() === 'ONLINE')}
            />
          ))}
        </div>
      </div>

      <div className="settings-group">
        <h3 style={{ margin: 0 }}>Startup Diagnostics</h3>
        <div className="sys-badge-grid" style={{ marginTop: '12px' }}>
          <StatusBadge label="Database" value={diagnostics?.database ?? 'UNKNOWN'} level={levelFromOnline((diagnostics?.database ?? 'OFFLINE') === 'ONLINE')} />
          <StatusBadge label="Camera" value={diagnostics?.camera ?? 'UNKNOWN'} level={levelFromOnline((diagnostics?.camera ?? 'OFFLINE') !== 'OFFLINE')} />
          <StatusBadge label="PLC" value={diagnostics?.plc ?? 'UNKNOWN'} level={levelFromOnline((diagnostics?.plc ?? 'OFFLINE') === 'ONLINE')} />
          <StatusBadge label="Storage" value={diagnostics?.storage ?? 'UNKNOWN'} level={levelFromOnline((diagnostics?.storage ?? 'OFFLINE') === 'ONLINE')} />
          <StatusBadge label="Model" value={diagnostics?.model ?? 'UNKNOWN'} level={levelFromOnline((diagnostics?.model ?? 'OFFLINE') === 'ONLINE')} />
        </div>
      </div>

      <div className="settings-group">
        <h3 style={{ margin: 0 }}>Notifications</h3>
        <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {(notifStatus?.channels ?? []).map((c) => (
            <div key={c.type} className="oee-badge">{c.type}</div>
          ))}
          {(!notifStatus || (notifStatus.channels ?? []).length === 0) && (
            <div style={{ color: '#64748b', fontSize: '13px' }}>No channels configured.</div>
          )}
          <button
            className="button"
            onClick={() => postJson('/api/admin/notification-test')}
            style={{ marginLeft: 'auto' }}
          >
            Send Test
          </button>
        </div>
      </div>

      <TrendPanel history={history} />
    </div>
  );
}
