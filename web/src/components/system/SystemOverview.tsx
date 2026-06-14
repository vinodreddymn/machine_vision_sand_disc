import type {
  Alarm,
  ServiceStatus,
  SystemHealth
} from '../../types/systemHealth';

interface Props {
  health: SystemHealth | null;
  alarms: Alarm[];
  services: Record<string, ServiceStatus>;
}

function calculateHealthScore(
  health: SystemHealth | null
) {
  if (!health) return 0;

  let score = 100;

  if (!health.camera_online) score -= 15;
  if (!health.plc_online) score -= 15;
  if (!health.database_online) score -= 15;
  if (!health.network_online) score -= 10;

  if ((health.temperature ?? 0) > 75) {
    score -= 10;
  }

  if ((health.free_disk_gb ?? 100) < 10) {
    score -= 10;
  }

  return Math.max(0, score);
}

export function SystemOverview({
  health,
  alarms,
  services
}: Props) {

  const score =
    calculateHealthScore(health);

  const onlineServices =
    Object.values(services)
      .filter(
        s =>
          String(s.status)
            .toUpperCase() === 'ONLINE'
      ).length;

  const totalServices =
    Object.keys(services).length;

  return (
    <section className="sys-overview">

      <div className="sys-health-score">

        <div className="sys-score-value">
          {score}%
        </div>

        <div className="sys-score-label">
          SYSTEM HEALTH
        </div>

      </div>

      <div className="sys-overview-kpis">

        <div className="sys-kpi-card">
          <span>Status</span>
          <strong>
            {score >= 90
              ? 'HEALTHY'
              : score >= 70
              ? 'WARNING'
              : 'CRITICAL'}
          </strong>
        </div>

        <div className="sys-kpi-card">
          <span>Uptime</span>
          <strong>
            {health?.uptime ?? '--'}
          </strong>
        </div>

        <div className="sys-kpi-card">
          <span>Active Alarms</span>
          <strong>
            {alarms.length}
          </strong>
        </div>

        <div className="sys-kpi-card">
          <span>Services</span>
          <strong>
            {onlineServices}/{totalServices}
          </strong>
        </div>

      </div>

    </section>
  );
}