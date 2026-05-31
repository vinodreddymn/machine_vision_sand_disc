import { useSnapshotContext } from '../contexts/SnapshotContext';
import { KPICards } from '../components/production/KPICards';
import { CameraViewer } from '../components/production/CameraViewer';
import { DecisionDisplay } from '../components/production/DecisionDisplay';
import { TelemetryPanel } from '../components/production/TelemetryPanel';
import { EventLog } from '../components/production/EventLog';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { API, DEFAULT_CAMERA_NAME } from '../utils/constants';

export function ProductionPage() {
  const { snapshot } = useSnapshotContext();
  const { status, station1, metrics, logs } = snapshot;

  return (
    <div className="grid-production">
      <div>
        <ErrorBoundary>
          <KPICards
            metrics={metrics}
            cycleTimeMs={station1?.cycle_time_ms ?? null}
          />
        </ErrorBoundary>

        <ErrorBoundary>
          <CameraViewer
            station={station1}
            cameraName={status?.camera_name ?? DEFAULT_CAMERA_NAME}
            partId={status?.part_id ?? null}
            streamUrl={API.STREAM_STATION1}
          />
          <DecisionDisplay decision={station1?.decision ?? null} />
        </ErrorBoundary>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <ErrorBoundary>
          <TelemetryPanel status={status} />
        </ErrorBoundary>
        <ErrorBoundary>
          <EventLog logs={logs} />
        </ErrorBoundary>
      </div>
    </div>
  );
}
