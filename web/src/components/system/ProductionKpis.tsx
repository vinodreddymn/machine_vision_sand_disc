import type {
  SystemHealth
} from '../../types/systemHealth';

interface Props {
  health: SystemHealth | null;
}

export function ProductionKpis({
  health
}: Props) {
  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>Production KPIs</h3>
      </div>

      <div className="sys-vision-grid">

        <div className="sys-stat">
          <span>Parts / Min</span>
          <strong>
            {health?.parts_per_minute ?? '--'}
          </strong>
        </div>

        <div className="sys-stat">
          <span>Cycle Time</span>
          <strong>
            {health?.average_cycle_time_ms ?? '--'} ms
          </strong>
        </div>

        <div className="sys-stat">
          <span>Inspection</span>
          <strong>
            {health?.inspection_running
              ? 'RUNNING'
              : 'STOPPED'}
          </strong>
        </div>

        <div className="sys-stat">
          <span>Mode</span>
          <strong>
            {health?.current_mode ?? '--'}
          </strong>
        </div>

      </div>

    </section>
  );
}