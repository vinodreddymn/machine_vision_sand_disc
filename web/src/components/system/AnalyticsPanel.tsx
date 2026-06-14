import type { HealthHistory } from '../../types/systemHealth';

interface AnalyticsPanelProps {
  history: HealthHistory[];
}

function getStats(values: Array<number | null>) {
  const valid = values.filter(
    (v): v is number => v !== null
  );

  if (!valid.length) {
    return {
      current: '--',
      min: '--',
      max: '--',
      avg: '--'
    };
  }

  return {
    current: valid[valid.length - 1].toFixed(1),
    min: Math.min(...valid).toFixed(1),
    max: Math.max(...valid).toFixed(1),
    avg:
      (
        valid.reduce((a, b) => a + b, 0) /
        valid.length
      ).toFixed(1)
  };
}

export function AnalyticsPanel({
  history
}: AnalyticsPanelProps) {

  const cpu = getStats(
    history.map((h) => h.cpu_usage)
  );

  const ram = getStats(
    history.map((h) => h.memory_usage)
  );

  const temp = getStats(
    history.map((h) => h.temperature)
  );

  const disk = getStats(
    history.map((h) => h.disk_usage)
  );

  const cards = [
    {
      title: 'CPU Usage',
      unit: '%',
      data: cpu
    },
    {
      title: 'Memory Usage',
      unit: '%',
      data: ram
    },
    {
      title: 'Temperature',
      unit: '°C',
      data: temp
    },
    {
      title: 'Disk Usage',
      unit: '%',
      data: disk
    }
  ];

  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>System Analytics</h3>
      </div>

      <div className="sys-analytics-grid">

        {cards.map((card) => (
          <div
            key={card.title}
            className="sys-analytics-card"
          >

            <div className="sys-analytics-title">
              {card.title}
            </div>

            <div className="sys-analytics-current">
              {card.data.current}
              {card.unit}
            </div>

            <div className="sys-analytics-stats">

              <div>
                <span>Min</span>
                <strong>
                  {card.data.min}
                  {card.unit}
                </strong>
              </div>

              <div>
                <span>Max</span>
                <strong>
                  {card.data.max}
                  {card.unit}
                </strong>
              </div>

              <div>
                <span>Avg</span>
                <strong>
                  {card.data.avg}
                  {card.unit}
                </strong>
              </div>

            </div>

          </div>
        ))}

      </div>

    </section>
  );
}