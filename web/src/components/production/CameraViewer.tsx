import React from 'react';
import type { Station } from '../../types/snapshot';

interface CameraViewerProps {
  station: Station | null;
  cameraName: string;
  partId: string | null;
  streamUrl: string;
  showPrediction?: boolean;
}

function getDecisionClass(decision: string | null | undefined): string {
  if (!decision) return '';
  const d = decision.toUpperCase();
  if (d === 'PASS') return 'decision-pass';
  if (d === 'FAIL' || d === 'REJECT') return 'decision-fail';
  return '';
}

export const CameraViewer = React.memo(
  function CameraViewer({
    station,
    cameraName,
    partId,
    streamUrl,
    showPrediction = false,
  }: CameraViewerProps) {
    const decisionClass = getDecisionClass(station?.decision);

    return (
      <div className="camera-viewer">

        <div className="camera-header">

          <div>
            <h2 className="camera-title">
              {showPrediction
                ? 'Calibration Mode'
                : 'Inspection Camera'}
            </h2>

            <span className="camera-meta">
              Camera: {cameraName}
            </span>
          </div>



        </div>

        <div className="camera-grid">

          <div className="camera-card">
            <div className="camera-card-title">
              Live Feed
            </div>
            <img
              src={streamUrl}
              alt="Inspection Stream"
            />
          </div>

          <div className={`camera-card ${decisionClass}`}>
            <div className="camera-card-title">
              Latest Inspection
              {decisionClass === 'decision-pass' && (
                <span className="decision-badge pass">PASS</span>
              )}
              {decisionClass === 'decision-fail' && (
                <span className="decision-badge fail">
                  {station?.decision?.toUpperCase()}
                </span>
              )}
            </div>

            {station?.captured_image_url ? (
              <img
                src={`${station.captured_image_url}?t=${Date.now()}`}
                alt="Inspection Result"
              />
            ) : (
              <div className="camera-placeholder">
                Waiting for inspection image...
              </div>
            )}
          </div>

        </div>

      </div>
    );
  }
);