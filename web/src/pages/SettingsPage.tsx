import { useCallback } from 'react';
import { SettingsProvider } from '../contexts/SettingsContext';
import { ModeSelector } from '../components/settings/ModeSelector';
import { ToleranceForm } from '../components/settings/ToleranceForm';
import { CalibrationSettings } from '../components/settings/CalibrationSettings';
import { ConfigurationManager } from '../components/config/ConfigurationManager';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { useSnapshotContext } from '../contexts/SnapshotContext';
import { setInspectionMode } from '../services/toleranceService';
import type { InspectionMode } from '../types/settings';

type SettingsTab = 'calibration' | 'tolerances' | 'configurations';

interface SettingsPageProps {
  active: boolean;
  settingsTab: SettingsTab;
  onSettingsTabChange: (tab: SettingsTab) => void;
}

export function SettingsPage({
  active,
  settingsTab,
  onSettingsTabChange,
}: SettingsPageProps) {
  const { snapshot, refresh } = useSnapshotContext();

  const handleModeChange = useCallback(
    async (mode: InspectionMode) => {
      try {
        await setInspectionMode(mode);
        await refresh();
      } catch {
        // Error is surfaced by snapshot context
      }
    },
    [refresh],
  );

  return (
    <SettingsProvider active={active && settingsTab === 'tolerances'}>
      <div className="settings-page">
        {/* Sub-tab switcher for calibration vs tolerances */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '16px',
            borderBottom: '1px solid #232a36',
            paddingBottom: '12px',
          }}
        >
          <button
            id="settings-tab-calibration"
            className={`sidebar-button ${settingsTab === 'calibration' ? 'active' : ''}`}
            style={{ fontSize: '13px', padding: '6px 14px' }}
            onClick={() => onSettingsTabChange('calibration')}
          >
            Camera Calibration
          </button>
          <button
            id="settings-tab-tolerances"
            className={`sidebar-button ${settingsTab === 'tolerances' ? 'active' : ''}`}
            style={{ fontSize: '13px', padding: '6px 14px' }}
            onClick={() => onSettingsTabChange('tolerances')}
          >
            Tolerances &amp; Mode
          </button>
          <button
            id="settings-tab-configurations"
            className={`sidebar-button ${settingsTab === 'configurations' ? 'active' : ''}`}
            style={{ fontSize: '13px', padding: '6px 14px' }}
            onClick={() => onSettingsTabChange('configurations')}
          >
            System Configurations
          </button>
        </div>

        {settingsTab === 'tolerances' && (
          <>
            <ErrorBoundary>
              <ModeSelector
                currentMode={snapshot.status?.mode}
                onModeChange={handleModeChange}
              />
            </ErrorBoundary>
            <ErrorBoundary>
              <ToleranceForm />
            </ErrorBoundary>
          </>
        )}

        {settingsTab === 'calibration' && (
          <ErrorBoundary>
            <CalibrationSettings />
          </ErrorBoundary>
        )}

        {settingsTab === 'configurations' && (
          <ErrorBoundary>
            <div style={{ height: '100%', overflow: 'hidden' }}>
              <ConfigurationManager />
            </div>
          </ErrorBoundary>
        )}
      </div>
    </SettingsProvider>
  );
}
