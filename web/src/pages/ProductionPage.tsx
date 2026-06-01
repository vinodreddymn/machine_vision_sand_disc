import { useSnapshotContext } from '../contexts/SnapshotContext';
import { KPICards } from '../components/production/KPICards';
import { CameraViewer } from '../components/production/CameraViewer';
import { DecisionDisplay } from '../components/production/DecisionDisplay';
import { TelemetryPanel } from '../components/production/TelemetryPanel';
import { EventLog } from '../components/production/EventLog';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { API, DEFAULT_CAMERA_NAME } from '../utils/constants';
import { Zap, AlertTriangle, Clock, Gauge } from 'lucide-react';

export function ProductionPage() {
  const { snapshot } = useSnapshotContext();
  const { status, station1, metrics, logs } = snapshot;
  
  // Calculate OEE (Overall Equipment Effectiveness)
  const totalParts = metrics?.total_parts ?? 0;
  const passedParts = metrics?.passed_parts ?? 0;
  const effectiveness = totalParts > 0 ? ((passedParts / totalParts) * 100).toFixed(1) : '0.0';
  const cycleTime = station1?.cycle_time_ms ?? 0;
  const partsPerMinute = cycleTime > 0 ? (60000 / cycleTime).toFixed(1) : '0.0';

  return (
    <div className="production-page-container">
      {/* Header Section */}
      <div className="production-header">
        <div className="header-title">
          <h1>PRODUCTION DASHBOARD</h1>
          <p className="subtitle">Real-time Manufacturing Intelligence System</p>
        </div>
        
        <div className="header-status">
          <div className={`status-badge ${status?.running ? 'running' : 'stopped'}`}>
            <Zap size={14} />
            <span>{status?.running ? 'RUNNING' : 'STOPPED'}</span>
          </div>
          <div className="status-mode">
            <span className="mode-label">MODE:</span>
            <span className="mode-value">{status?.mode ?? 'MANUAL'}</span>
          </div>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="production-grid">
        {/* Left Column: Camera & Decision */}
        <div className="production-column-main">
          <ErrorBoundary>
            <div className="camera-section">
              <CameraViewer
                station={station1}
                cameraName={status?.camera_name ?? DEFAULT_CAMERA_NAME}
                partId={status?.part_id ?? null}
                streamUrl={API.STREAM_STATION1}
              />
            </div>
          </ErrorBoundary>

          <ErrorBoundary>
            <DecisionDisplay decision={station1?.decision ?? null} />
          </ErrorBoundary>
        </div>

        {/* Right Column: Metrics & Telemetry */}
        <div className="production-column-side">
          {/* KPI Dashboard */}
          <div className="kpi-section">
            <h2 className="section-title">KEY PERFORMANCE INDICATORS</h2>
            <ErrorBoundary>
              <KPICards
                metrics={metrics}
                cycleTimeMs={station1?.cycle_time_ms ?? null}
              />
            </ErrorBoundary>
          </div>

          {/* Additional Metrics */}
          <div className="metrics-grid">
            <div className="metric-card industry40">
              <div className="metric-icon">
                <Gauge size={18} />
              </div>
              <div className="metric-info">
                <span className="metric-label">Equipment Efficiency</span>
                <span className="metric-value">{effectiveness}%</span>
              </div>
            </div>
            
            <div className="metric-card industry40">
              <div className="metric-icon">
                <Clock size={18} />
              </div>
              <div className="metric-info">
                <span className="metric-label">Parts per Minute</span>
                <span className="metric-value">{partsPerMinute}</span>
              </div>
            </div>

            {metrics?.rejected_parts ? (
              <div className="metric-card industry40 warning">
                <div className="metric-icon">
                  <AlertTriangle size={18} />
                </div>
                <div className="metric-info">
                  <span className="metric-label">Rejected</span>
                  <span className="metric-value">{metrics.rejected_parts}</span>
                </div>
              </div>
            ) : null}
          </div>

          {/* Telemetry */}
          <ErrorBoundary>
            <TelemetryPanel status={status} />
          </ErrorBoundary>

          {/* Event Log */}
          <ErrorBoundary>
            <EventLog logs={logs} maxLines={10} />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}
