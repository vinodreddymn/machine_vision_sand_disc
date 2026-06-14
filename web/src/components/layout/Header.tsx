import React, { useCallback, useState, useRef, useEffect } from 'react';
import {
  Activity,
  Camera,
  Package,
  Wifi,
  WifiOff,
  Check,
  Play,
  CircleStop,
  Factory,
  Database,
  Settings,
  HeartPulse,
  Shield,
  LogOut,
  X,
  Gauge,
  Clock as ClockIcon
} from 'lucide-react';

import ashtechLogo from '../../assets/ashtech_logo.png';
import { Clock } from './Clock';
import { useClock } from '../../hooks/useClock';
import { useSnapshotContext } from '../../contexts/SnapshotContext';

import { postJson } from '../../services/apiService';
import { computeYieldRate } from '../../utils/calculations';
import { API } from '../../utils/constants';
import { canAccess } from '../../utils/permissions';

type Tab =
  | 'production'
  | 'training'
  | 'history'
  | 'system'
  | 'admin'
  | 'settings';

type SettingsTab =
  | 'calibration'
  | 'tolerances'
  | 'configurations'
  | 'camera';

interface HeaderProps {
  activeTab: Tab;
  settingsTab: SettingsTab;
  onTabChange: (tab: Tab) => void;
}

const NAV_ITEMS: {
  id: Tab;
  label: string;
  Icon: React.ElementType;
}[] = [
  { id: 'production', label: 'Production Run', Icon: Factory },
  { id: 'training', label: 'Training & Datasets', Icon: Activity },
  { id: 'history', label: 'Analytics & Logs', Icon: Database },
  { id: 'system', label: 'System Health', Icon: HeartPulse },
  { id: 'admin', label: 'Administration', Icon: Shield },
  { id: 'settings', label: 'Settings', Icon: Settings },
];

function getSubtitle(
  activeTab: Tab,
  settingsTab: SettingsTab
): string {
  switch (activeTab) {
    case 'production':
      return 'Real-Time Production Inspection HMI';

    case 'training':
      return 'Ground Truth Dataset Collection & Validation';

    case 'history':
      return 'Production History & SQL Analytics';

    case 'system':
      return 'Industrial Diagnostics & System Health';

    case 'admin':
      return 'Administration & User Management';

    case 'settings':
      return settingsTab === 'camera'
        ? 'Camera Hardware Configuration'
        : 'Inspection Configuration';

    default:
      return '';
  }
}

export const Header = React.memo(function Header({
  activeTab,
  settingsTab,
  onTabChange,
}: HeaderProps) {
  const {
    snapshot,
    wsConnected,
    runAction,
  } = useSnapshotContext();

  const clock = useClock();

  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const { status, station1, metrics } = snapshot;

  const yieldRate = computeYieldRate(metrics);
  const isRunning = status?.running ?? false;
  const mode = status?.mode ?? 'MANUAL';
  const cameraName = status?.camera_name ?? 'CAM01';
  const partId = status?.part_id ?? 'WAITING';

  const conveyor = status?.plc?.conveyor_status ?? 'STOPPED';
  const rejectGate = status?.plc?.reject_actuator ?? 'IDLE';
  const cycleTimeMs = station1?.cycle_time_ms ?? null;

  const totalParts = metrics?.total_parts ?? 0;
  const passedParts = metrics?.passed_parts ?? 0;
  const rejectedParts = metrics?.rejected_parts ?? 0;

  const calculatedYieldRate = totalParts > 0
    ? ((passedParts / totalParts) * 100).toFixed(1)
    : '0.0';

  const rejectRate = totalParts > 0
    ? ((rejectedParts / totalParts) * 100).toFixed(1)
    : '0.0';

  const partsPerMinute = cycleTimeMs && cycleTimeMs > 0
    ? (60000 / cycleTimeMs).toFixed(1)
    : '0.0';

  const role = localStorage.getItem('diskvision_role') ?? 'OPERATOR';
  const username = localStorage.getItem('diskvision_username') ?? '';

  const [actionPending, setActionPending] = useState<'starting' | 'stopping' | null>(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleStart = useCallback(async () => {
    setActionPending('starting');
    try {
      await runAction(() => postJson(API.START));
    } finally {
      setActionPending(null);
    }
  }, [runAction]);

  const handleStop = useCallback(async () => {
    setActionPending('stopping');
    try {
      await runAction(() => postJson(API.STOP));
    } finally {
      setActionPending(null);
    }
  }, [runAction]);

  const getStatusBadge = () => {
    if (actionPending === 'starting') {
      return {
        text: 'STARTING...',
        className: 'starting',
        Icon: Activity,
      };
    }
    if (actionPending === 'stopping') {
      return {
        text: 'STOPPING...',
        className: 'stopping',
        Icon: Activity,
      };
    }
    if (isRunning) {
      return {
        text: 'STARTED',
        className: 'started',
        Icon: Play,
      };
    }
    return {
      text: 'STOPPED',
      className: 'stopped',
      Icon: CircleStop,
    };
  };

  const statusBadge = getStatusBadge();

  const handleLogout = useCallback(() => {
    localStorage.removeItem('diskvision_token');
    localStorage.removeItem('diskvision_role');
    localStorage.removeItem('diskvision_username');
    window.location.reload();
  }, []);

  const visibleNavItems = NAV_ITEMS.filter(({ id }) =>
    canAccess(role, id)
  );

  return (
    <header className="workspace-header">
      {/* Row 1: Brand, Navigation, Controls */}
      <div className="header-top-row">
        <div className="header-brand-group" ref={menuRef}>
          <button
            className={`header-logo-badge-btn ${menuOpen ? 'menu-active' : ''}`}
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle Navigation Menu"
          >
            <img src={ashtechLogo} alt="ASHTECH Logo" className="header-logo-img" />
          </button>
          <div className="header-brand-text">
            <div className="header-title-row">
              <h1 className="app-title">
                DiskVisionInspector
              </h1>
              <span className="app-version">v2.0</span>
            </div>
            <div className="app-subtitle">
              {getSubtitle(activeTab, settingsTab)}
            </div>
          </div>

          {/* Dropdown Menu */}
          {menuOpen && (
            <div className="header-dropdown-menu">
              <div className="dropdown-header">
                <span className="dropdown-header-title">Navigation Menu</span>
              </div>

              <nav className="dropdown-nav">
                {visibleNavItems.map(({ id, label, Icon }) => (
                  <button
                    key={id}
                    className={`dropdown-item ${
                      activeTab === id ? 'active' : ''
                    }`}
                    onClick={() => {
                      onTabChange(id);
                      setMenuOpen(false);
                    }}
                  >
                    <Icon size={16} />
                    <span>{label}</span>
                  </button>
                ))}
              </nav>

              <div className="dropdown-footer">
                <div className="system-status-indicator">
                  <div className="status-indicator online" />
                  <span>System Online</span>
                </div>

                <div className="user-profile-card">
                  {username && (
                    <div className="profile-username">{username}</div>
                  )}
                  <div className="profile-role">Role: {role}</div>
                </div>

                <button
                  className="dropdown-logout-btn"
                  onClick={handleLogout}
                >
                  <LogOut size={16} />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="header-metrics-group">
          <div className="header-group production-status-group">
            <div
              className={`status-chip ${statusBadge.className} ${actionPending ? 'pulse-active' : ''}`}
            >
              <statusBadge.Icon size={14} className={actionPending ? 'animate-spin' : ''} />
              {statusBadge.text}
            </div>

            <div className="status-chip mode">{mode}</div>

            <div className="status-chip" title="Camera Name">
              <Camera size={14} />
              {cameraName}
            </div>


          </div>

          <div className="header-divider" />

          <div className="header-group system-status-group">
            <div
              className={`oee-badge ${
                wsConnected ? '' : 'disconnected'
              }`}
              title="Connection Status"
            >
              {wsConnected ? (
                <Wifi size={13} />
              ) : (
                <WifiOff size={13} />
              )}
              {wsConnected ? 'LIVE' : 'OFFLINE'}
            </div>
          </div>

          <div className="header-divider" />

          <div className="header-group controls-group">
            <Clock date={clock} />

            <div className="header-actions">
              <button
                className="button good"
                onClick={handleStart}
                disabled={isRunning || actionPending !== null}
              >
                <Play size={14} />
                {actionPending === 'starting' ? 'Starting...' : 'Start'}
              </button>

              <button
                className="button"
                onClick={handleStop}
                disabled={!isRunning || actionPending !== null}
              >
                <CircleStop size={14} />
                {actionPending === 'stopping' ? 'Stopping...' : 'Stop'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Real-time Telemetry & KPI Deck (Industry 4.0 Standard) */}
      <div className="header-bottom-deck">
        <div className="header-telemetry-panel">
          <div className={`header-telemetry-tile telemetry-${conveyor === 'RUNNING' ? 'success' : 'neutral'} ${conveyor === 'RUNNING' ? 'pulse-active' : ''}`}>
            <div className="tile-glow" />
            <div className="tile-header-row">
              <span>Conveyor</span>
              {conveyor === 'RUNNING' && <span className="pulse-dot" />}
            </div>
            <strong>{conveyor}</strong>
          </div>

          <div className={`header-telemetry-tile telemetry-${rejectGate === 'ACTIVE' ? 'danger' : 'neutral'} ${rejectGate === 'ACTIVE' ? 'pulse-active' : ''}`}>
            <div className="tile-glow" />
            <div className="tile-header-row">
              <span>Reject Gate</span>
              {rejectGate === 'ACTIVE' && <span className="pulse-dot" />}
            </div>
            <strong>{rejectGate}</strong>
          </div>
        </div>

        <div className="header-deck-divider" />

        <div className="header-kpi-grid">
          <div className="header-kpi-card blue">
            <div className="kpi-card-glow" />
            <div className="kpi-icon-wrapper"><Factory size={16} /></div>
            <div className="kpi-info">
              <span className="kpi-label">Total Inspected</span>
              <strong className="kpi-value">{totalParts.toLocaleString()}</strong>
            </div>
          </div>

          <div className="header-kpi-card green">
            <div className="kpi-card-glow" />
            <div className="kpi-icon-wrapper"><Check size={16} /></div>
            <div className="kpi-info">
              <span className="kpi-label">Passed</span>
              <div className="kpi-value-row">
                <strong className="kpi-value">{passedParts.toLocaleString()}</strong>
                <span className="kpi-badge badge-success">{calculatedYieldRate}%</span>
              </div>
            </div>
          </div>

          <div className="header-kpi-card red">
            <div className="kpi-card-glow" />
            <div className="kpi-icon-wrapper"><X size={16} /></div>
            <div className="kpi-info">
              <span className="kpi-label">Rejected</span>
              <div className="kpi-value-row">
                <strong className="kpi-value">{rejectedParts.toLocaleString()}</strong>
                <span className="kpi-badge badge-danger">{rejectRate}%</span>
              </div>
            </div>
          </div>

          <div className="header-kpi-card yellow">
            <div className="kpi-card-glow" />
            <div className="kpi-icon-wrapper"><ClockIcon size={16} /></div>
            <div className="kpi-info">
              <span className="kpi-label">Cycle Time</span>
              <strong className="kpi-value">{cycleTimeMs != null ? `${cycleTimeMs} ms` : '--'}</strong>
            </div>
          </div>

          <div className="header-kpi-card cyan">
            <div className="kpi-card-glow" />
            <div className="kpi-icon-wrapper"><Gauge size={16} /></div>
            <div className="kpi-info">
              <span className="kpi-label">Throughput</span>
              <strong className="kpi-value">{partsPerMinute} PPM</strong>
            </div>
          </div>

          <div className="header-kpi-card purple">
            <div className="kpi-card-glow" />
            <div className="kpi-icon-wrapper"><Activity size={16} /></div>
            <div className="kpi-info">
              <span className="kpi-label">Yield / OEE</span>
              <strong className="kpi-value">{yieldRate}</strong>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
});
