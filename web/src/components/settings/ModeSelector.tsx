import React from 'react';
import type { InspectionMode } from '../../types/settings';

interface ModeSelectorProps {
  currentMode: string | undefined;
  onModeChange: (mode: InspectionMode) => Promise<void>;
}

const MODES: { id: InspectionMode; title: string; description: string }[] = [
  {
    id: 'PRODUCTION',
    title: 'PRODUCTION',
    description:
      'Fully automated runs, signals PLC actuators automatically, hides labeling actions.',
  },
  {
    id: 'DATA_COLLECTION',
    title: 'DATA COLLECTION (TRAINING)',
    description:
      'Enables operator ground-truth labeling, captures and persists training samples.',
  },
];

export const ModeSelector = React.memo(function ModeSelector({
  currentMode,
  onModeChange,
}: ModeSelectorProps) {
  return (
    <div className="settings-group">
      <h2 style={{ margin: 0, fontSize: '16px', color: '#f8fafc' }}>
        System Operations Mode
      </h2>
      <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
        Toggle the active operation mode of the single station disc inspection
        camera loop.
      </p>
      <div className="mode-selectors">
        {MODES.map(({ id, title, description }) => (
          <div
            key={id}
            id={`mode-card-${id.toLowerCase()}`}
            className={`mode-card ${currentMode === id ? 'selected' : ''}`}
            onClick={() => { void onModeChange(id); }}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') void onModeChange(id);
            }}
            aria-pressed={currentMode === id}
          >
            <h3>{title}</h3>
            <p>{description}</p>
          </div>
        ))}
      </div>
    </div>
  );
});
