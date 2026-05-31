import type { SystemHealth } from '../../types/systemHealth';

interface HealthMetricGridProps {
  health: SystemHealth | null;
}

function fmtNum(value: number | null, unit = ''): string {
  if (value === null || Number.isNaN(value)) {
    return '--';
  }
  return `${value.toFixed(1)}${unit}`;
}

export function HealthMetricGrid({ health }: HealthMetricGridProps) {
  if (!health) {
    return <div className="settings-group">No health snapshot available yet.</div>;
  }

  return (
    <div className="sys-metric-grid">
      <div className="sys-metric-card"><span>CPU Usage</span><strong>{fmtNum(health.cpu_usage, '%')}</strong></div>
      <div className="sys-metric-card"><span>RAM Usage</span><strong>{fmtNum(health.memory_usage, '%')}</strong></div>
      <div className="sys-metric-card"><span>Temperature</span><strong>{fmtNum(health.temperature, ' C')}</strong></div>
      <div className="sys-metric-card"><span>Disk Usage</span><strong>{fmtNum(health.disk_usage, '%')}</strong></div>
      <div className="sys-metric-card"><span>Uptime</span><strong>{health.uptime ?? '--'}</strong></div>
      <div className="sys-metric-card"><span>Inspection FPS</span><strong>{fmtNum(health.camera_fps)}</strong></div>
      <div className="sys-metric-card"><span>Inspection Rate</span><strong>{fmtNum(health.parts_per_minute, ' ppm')}</strong></div>
      <div className="sys-metric-card"><span>Avg Cycle Time</span><strong>{fmtNum(health.average_cycle_time_ms, ' ms')}</strong></div>
    </div>
  );
}
