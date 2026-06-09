import React, { useCallback } from 'react';
import { Play, CircleStop, Power, Check, Wifi, WifiOff } from 'lucide-react';
import { Clock } from './Clock';
import { useClock } from '../../hooks/useClock';
import { useSnapshotContext } from '../../contexts/SnapshotContext';
import { postJson } from '../../services/apiService';
import { computeYieldRate } from '../../utils/calculations';
import { API } from '../../utils/constants';

type Tab = 'production' | 'training' | 'history' | 'system' | 'admin' | 'settings';
type SettingsTab = 'calibration' | 'tolerances' | 'configurations' | 'camera';

interface HeaderProps {
  activeTab: Tab;
  settingsTab: SettingsTab;
}

function getSubtitle(activeTab: Tab, settingsTab: SettingsTab): string {
  switch (activeTab) {
    case 'production': return 'Real-time Production Inspection HMI';
    case 'training': return 'Ground-Truth Dataset Collector & Labeling';
    case 'history': return 'Industry 4.0 SQL History Database Browser';
    case 'system': return 'Industrial System Health, Alarms, and Diagnostics';
    case 'admin': return 'User Management and System Administration';
    case 'settings':
      return settingsTab === 'calibration'
        ? 'One-Time Camera Calibration — px → mm'
        : settingsTab === 'camera'
        ? 'Camera Hardware Configuration & Live Feed'
        : 'Inspection Tolerances & Mode Control';
  }
}

export const Header = React.memo(function Header({
  activeTab,
  settingsTab,
}: HeaderProps) {
  const { snapshot, wsConnected, runAction } = useSnapshotContext();
  const clock = useClock();
  const yieldRate = computeYieldRate(snapshot.metrics);

  const handleStart = useCallback(
    () => runAction(() => postJson(API.START)),
    [runAction],
  );
  const handleStop = useCallback(
    () => runAction(() => postJson(API.STOP)),
    [runAction],
  );
  const handleShutdown = useCallback(
    () => runAction(() => postJson(API.SHUTDOWN)),
    [runAction],
  );

  return (
    <header className="workspace-header">
      <div>
        <h1 style={{ margin: 0, fontSize: '20px', color: '#f8fafc' }}>
          DiskVisionInspector{' '}
          <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 'normal' }}>
            v2.0
          </span>
        </h1>
        <span style={{ fontSize: '13px', color: '#94a3b8' }}>
          {getSubtitle(activeTab, settingsTab)}
        </span>
      </div>

      <div className="header-meta">
        {/* WebSocket connection badge */}
        <div
          className={`oee-badge ${wsConnected ? '' : 'disconnected'}`}
          title={wsConnected ? 'Live feed connected' : 'Live feed disconnected'}
          style={{ gap: '6px' }}
        >
          {wsConnected ? <Wifi size={13} /> : <WifiOff size={13} />}
          {wsConnected ? 'Live' : 'Reconnecting'}
        </div>

        {/* Yield badge */}
        <div className="oee-badge">
          <Check size={14} />
          Yield: {yieldRate}
        </div>

        <Clock date={clock} />

        <div className="header-actions">
          <button
            id="btn-start-line"
            className="button good"
            onClick={handleStart}
            disabled={snapshot.status?.running}
            style={{ height: '36px', minHeight: '36px' }}
          >
            <Play size={14} />
            Start Line
          </button>
          <button
            id="btn-stop-line"
            className="button"
            onClick={handleStop}
            disabled={!snapshot.status?.running}
            style={{ height: '36px', minHeight: '36px' }}
          >
            <CircleStop size={14} />
            Stop
          </button>
       
        </div>
      </div>
    </header>
  );
});
