import { useSnapshotContext } from '../contexts/SnapshotContext';
import { CameraViewer } from '../components/production/CameraViewer';
import { LabelPanel } from '../components/training/LabelPanel';
import { DatasetActions } from '../components/training/DatasetActions';
import { DatasetMetrics } from '../components/training/DatasetMetrics';
import { DefectReport } from '../components/training/DefectReport';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { API, DEFAULT_CAMERA_NAME } from '../utils/constants';

export function TrainingPage() {
  const { snapshot, runAction } = useSnapshotContext();
  const { status, station1, metrics } = snapshot;

  return (
    <div className="grid-training">
      <div>
        <ErrorBoundary>
          <CameraViewer
            station={station1}
            cameraName={status?.camera_name ?? DEFAULT_CAMERA_NAME}
            partId={status?.part_id ?? null}
            streamUrl={API.STREAM_STATION1}
            showPrediction
          />
          <LabelPanel
            pendingLabel={status?.pending_label ?? false}
            runAction={runAction}
          />
        </ErrorBoundary>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <ErrorBoundary>
          <DatasetActions
            cameraName={status?.camera_name ?? DEFAULT_CAMERA_NAME}
            runAction={runAction}
          />
        </ErrorBoundary>
        <ErrorBoundary>
          <DatasetMetrics dataset={metrics?.dataset} />
        </ErrorBoundary>
        <ErrorBoundary>
          <DefectReport defects={station1?.defects ?? []} />
        </ErrorBoundary>
      </div>
    </div>
  );
}
