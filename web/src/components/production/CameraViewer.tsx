import React from 'react';
import type { Station } from '../../types/snapshot';

interface CameraViewerProps {
  station: Station | null;
  cameraName: string;
  partId: string | null;
  streamUrl: string;
  showPrediction?: boolean;
}

export const CameraViewer = React.memo(function CameraViewer({
  station,
  cameraName,
  partId,
  streamUrl,
  showPrediction = false,
}: CameraViewerProps) {
  return (
    <div className="production-feed-viewer">
      <div
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <h2 style={{ margin: 0, fontSize: '15px', color: '#f8fafc' }}>
          {showPrediction ? 'Calibration & Sample Test' : 'Real-time Camera Inspector'}
        </h2>
        <span style={{ fontSize: '12px', color: '#64748b' }}>
          Source:{' '}
          <span style={{ color: '#38bdf8', fontWeight: 600 }}>
            {cameraName}
          </span>{' '}
          {showPrediction ? (
            <>
              | Prediction: {station?.system_prediction ?? 'N/A'} (Score:{' '}
              {station?.anomaly_score ?? 'N/A'})
            </>
          ) : (
            <>| Active Part: {partId ?? 'None'}</>
          )}
        </span>
      </div>

      <div className="production-feed-layout">
        <div className="feed-box">
          <span>
            {showPrediction ? 'Target Sample Video / Camera' : 'Live Camera Stream'}
          </span>
          <img src={streamUrl} alt="Inspection Stream" />
        </div>
        <div className="feed-box">
          <span>
            {showPrediction ? 'Captured Image Overlay' : 'Latest Overlay Inspection Result'}
          </span>
          {station?.captured_image_url ? (
            <img
              src={`${station.captured_image_url}?t=${Date.now()}`}
              alt="Captured Result Overlay"
            />
          ) : (
            <div className="no-img">No inspection image captured yet.</div>
          )}
        </div>
      </div>
    </div>
  );
});
