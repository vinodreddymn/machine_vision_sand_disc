import React, { useCallback } from 'react';
import { RefreshCcw, ShieldCheck, Upload, Video, Camera } from 'lucide-react';
import { postJson, uploadFile } from '../../services/apiService';
import { API } from '../../utils/constants';

interface DatasetActionsProps {
  cameraName: string;
  runAction: (fn: () => Promise<unknown>) => Promise<void>;
}

export const DatasetActions = React.memo(function DatasetActions({
  cameraName,
  runAction,
}: DatasetActionsProps) {
  const handleStartPart = useCallback(
    () => runAction(() => postJson(API.START_PART)),
    [runAction],
  );
  const handleReset = useCallback(
    () => runAction(() => postJson(API.RESET)),
    [runAction],
  );
  const handleResetCamera = useCallback(
    () => runAction(() => postJson(`${API.RESET_CAMERA}?station=S1`)),
    [runAction],
  );

  const handleImageUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        void runAction(() =>
          uploadFile(`${API.UPLOAD}?station=${encodeURIComponent('S1')}`, file),
        );
      }
      e.currentTarget.value = '';
    },
    [runAction],
  );

  const handleVideoUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        void runAction(() =>
          uploadFile(
            `${API.UPLOAD_VIDEO}?station=${encodeURIComponent('S1')}`,
            file,
          ),
        );
      }
      e.currentTarget.value = '';
    },
    [runAction],
  );

  const isLiveCamera = cameraName === 'USB Camera 0';

  return (
    <div className="panel actions-panel" style={{ minHeight: 'auto' }}>
      <h2>Training Calibration Actions</h2>
      <div
        className="action-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '10px',
          marginTop: '12px',
        }}
      >
        <button id="btn-start-part" className="button" onClick={handleStartPart}>
          <RefreshCcw size={16} />
          Start New Part
        </button>
        <button id="btn-reset-pipeline" className="button" onClick={handleReset}>
          <ShieldCheck size={16} />
          Reset Pipeline
        </button>

        <label
          className="button upload-button"
          style={{ display: 'flex', justifyContent: 'center' }}
          htmlFor="upload-image-input"
        >
          <Upload size={16} />
          Upload Image
          <input
            id="upload-image-input"
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
          />
        </label>

        <label
          className="button upload-button"
          style={{ display: 'flex', justifyContent: 'center' }}
          htmlFor="upload-video-input"
        >
          <Video size={16} />
          Upload Video
          <input
            id="upload-video-input"
            type="file"
            accept="video/*"
            onChange={handleVideoUpload}
          />
        </label>

        <button
          id="btn-reset-camera"
          className="button"
          onClick={handleResetCamera}
          disabled={isLiveCamera}
          style={{ gridColumn: 'span 2', justifyContent: 'center' }}
        >
          <Camera size={16} />
          Reset to Live USB Camera
        </button>
      </div>
    </div>
  );
});
