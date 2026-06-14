import type {
  SystemHealth
} from '../../types/systemHealth';

interface Props {
  health: SystemHealth | null;
}

export function VisionHealthPanel({
  health
}: Props) {
  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>Vision Engine</h3>
      </div>

      <div className="sys-vision-grid">

        <div className="sys-stat">
          <span>Inference Time</span>
          <strong>
            {health?.inference_time_ms ?? '--'} ms
          </strong>
        </div>

        <div className="sys-stat">
          <span>Inspection Latency</span>
          <strong>
            {health?.inspection_latency_ms ?? '--'} ms
          </strong>
        </div>

        <div className="sys-stat">
          <span>FPS</span>
          <strong>
            {health?.camera_fps ?? '--'}
          </strong>
        </div>

        <div className="sys-stat">
          <span>Queue Backlog</span>
          <strong>
            {health?.queue_backlog ?? '--'}
          </strong>
        </div>

        <div className="sys-stat">
          <span>Frame Drops</span>
          <strong>
            {health?.camera_frame_drops ?? '--'}
          </strong>
        </div>

        <div className="sys-stat">
          <span>Thread Status</span>
          <strong>
            {health?.thread_status ?? '--'}
          </strong>
        </div>

      </div>

    </section>
  );
}