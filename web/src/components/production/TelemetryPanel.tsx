import React from 'react';
import type { Status } from '../../types/snapshot';

interface TelemetryPanelProps {
  status: Status | null;
}

interface TelemetryRowProps {
  label: string;
  value: string;
  valueClass: string;
}

const TelemetryRow = React.memo(function TelemetryRow({
  label,
  value,
  valueClass,
}: TelemetryRowProps) {
  return (
    <div className="plc-telemetry-item">
      <span>{label}</span>
      <strong className={valueClass}>{value}</strong>
    </div>
  );
});

export const TelemetryPanel = React.memo(function TelemetryPanel({
  status,
}: TelemetryPanelProps) {
  const isRunning = status?.running ?? false;
  const conveyorRunning = status?.plc.conveyor_status === 'RUNNING';
  const rejectActive = status?.plc.reject_actuator === 'ACTIVE';

  return (
    <div className="plc-telemetry-panel">
      <h2 style={{ margin: 0, fontSize: '15px', color: '#f8fafc' }}>
        PLC &amp; Conveyor Telemetry
      </h2>
      <div className="plc-telemetry-grid">
        <TelemetryRow
          label="System State"
          value={isRunning ? 'RUNNING' : 'STOPPED'}
          valueClass={isRunning ? 'plc-val-running' : 'plc-val-idle'}
        />
        <TelemetryRow
          label="Line Mode"
          value={status?.mode ?? 'MANUAL'}
          valueClass="plc-val-active"
        />
        <TelemetryRow
          label="Conveyor"
          value={status?.plc.conveyor_status ?? 'STOPPED'}
          valueClass={conveyorRunning ? 'plc-val-running' : 'plc-val-idle'}
        />
        <TelemetryRow
          label="Reject Gate"
          value={status?.plc.reject_actuator ?? 'IDLE'}
          valueClass={rejectActive ? 'plc-val-fault' : 'plc-val-idle'}
        />
      </div>
    </div>
  );
});
