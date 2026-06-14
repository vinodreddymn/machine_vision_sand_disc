import { AlertTriangle, ShieldAlert, Bell } from 'lucide-react';
import type { Alarm } from '../../types/systemHealth';

interface Props {
  alarms: Alarm[];
  onAcknowledge: (alarmId: number) => void;
}

export function AlarmCommandCenter({
  alarms,
  onAcknowledge
}: Props) {

  const critical =
    alarms.filter(
      a =>
        a.severity === 'CRITICAL' ||
        a.severity === 'EMERGENCY'
    ).length;

  const warning =
    alarms.filter(
      a =>
        a.severity === 'WARNING'
    ).length;

  const info =
    alarms.filter(
      a =>
        a.severity === 'INFO'
    ).length;

  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>Alarm Command Center</h3>
      </div>

      <div className="sys-alarm-summary">

        <div className="sys-alarm-stat critical">
          <ShieldAlert size={18} />
          <strong>{critical}</strong>
          <span>Critical</span>
        </div>

        <div className="sys-alarm-stat warning">
          <AlertTriangle size={18} />
          <strong>{warning}</strong>
          <span>Warning</span>
        </div>

        <div className="sys-alarm-stat info">
          <Bell size={18} />
          <strong>{info}</strong>
          <span>Info</span>
        </div>

        <div className="sys-alarm-stat">
          <strong>{alarms.length}</strong>
          <span>Total</span>
        </div>

      </div>

      <div className="sys-alarm-list">

        {alarms.length === 0 && (
          <div className="sys-empty-state">
            No active alarms
          </div>
        )}

        {alarms.map((alarm) => (
          <div
            key={alarm.id}
            className={`sys-alarm-card severity-${alarm.severity.toLowerCase()}`}
          >

            <div className="sys-alarm-main">

              <div className="sys-alarm-title">
                {alarm.category}
              </div>

              <div className="sys-alarm-message">
                {alarm.message}
              </div>

              <div className="sys-alarm-meta">
                {alarm.source}
                {' • '}
                {new Date(
                  alarm.timestamp
                ).toLocaleString()}
              </div>

            </div>

            <button
              className="button"
              onClick={() =>
                onAcknowledge(alarm.id)
              }
            >
              Acknowledge
            </button>

          </div>
        ))}

      </div>

    </section>
  );
}