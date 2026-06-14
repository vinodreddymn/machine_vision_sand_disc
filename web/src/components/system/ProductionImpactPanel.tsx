import {
  Gauge,
  Package,
  Timer,
  Play
} from 'lucide-react';

import type {
  SystemHealth
} from '../../types/systemHealth';

interface Props {
  health: SystemHealth | null;
}

export function ProductionImpactPanel({
  health
}: Props) {

  const throughput =
    (health?.parts_per_minute ?? 0) * 60;

  const availability =
    health?.inspection_running
      ? 99.5
      : 0;

  const efficiency =
    health?.average_cycle_time_ms
      ? Math.max(
          0,
          Math.min(
            100,
            100 -
              health.average_cycle_time_ms /
                2
          )
        )
      : 0;

  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>
          Production Impact
        </h3>
      </div>

      <div className="sys-production-grid">

        <div className="sys-impact-card">

          <Gauge size={22} />

          <span>
            Availability
          </span>

          <strong>
            {availability.toFixed(1)}%
          </strong>

        </div>

        <div className="sys-impact-card">

          <Package size={22} />

          <span>
            Throughput / Hr
          </span>

          <strong>
            {throughput.toFixed(0)}
          </strong>

        </div>

        <div className="sys-impact-card">

          <Timer size={22} />

          <span>
            Cycle Efficiency
          </span>

          <strong>
            {efficiency.toFixed(1)}%
          </strong>

        </div>

        <div className="sys-impact-card">

          <Play size={22} />

          <span>
            Inspection State
          </span>

          <strong>
            {health?.inspection_running
              ? 'RUNNING'
              : 'STOPPED'}
          </strong>

        </div>

      </div>

    </section>
  );
}