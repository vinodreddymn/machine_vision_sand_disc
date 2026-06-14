import { useSnapshotContext } from '../contexts/SnapshotContext';

import { CameraViewer } from '../components/production/CameraViewer';
import { EventLog } from '../components/production/EventLog';

import { ErrorBoundary } from '../components/common/ErrorBoundary';

import { API, DEFAULT_CAMERA_NAME } from '../utils/constants';

export function ProductionPage() {
  const { snapshot } = useSnapshotContext();

  const {
    status,
    station1,
    metrics,
    logs
  } = snapshot;

  return (
    <div className="production-page">
      {/* Main Workspace Layout: Camera Inspection & Operations Log */}
      <section className="production-main-layout">
        <div className="production-inspection-pane">
          <ErrorBoundary>
            <CameraViewer
              station={station1}
              cameraName={status?.camera_name ?? DEFAULT_CAMERA_NAME}
              partId={status?.part_id ?? null}
              streamUrl={API.STREAM_STATION1}
            />
          </ErrorBoundary>
        </div>

        <div className="production-log-pane">
          <ErrorBoundary>
            <EventLog logs={logs} maxLines={100} />
          </ErrorBoundary>
        </div>
      </section>
    </div>
  );
}