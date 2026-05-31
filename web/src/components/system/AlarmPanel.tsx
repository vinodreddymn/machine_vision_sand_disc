import type { Alarm } from '../../types/systemHealth';

interface AlarmPanelProps {
  alarms: Alarm[];
  onAcknowledge: (alarmId: number) => void;
}

export function AlarmPanel({ alarms, onAcknowledge }: AlarmPanelProps) {
  return (
    <div className="settings-group">
      <h3 style={{ margin: 0 }}>Active Alarms</h3>
      <div className="log-terminal" style={{ height: '280px' }}>
        {alarms.length === 0 && <p>No active alarms.</p>}
        {alarms.map((alarm) => (
          <div key={alarm.id} className={`sys-alarm-row sys-alarm-${alarm.severity.toLowerCase()}`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <strong>{alarm.severity} - {alarm.category}</strong>
              <span>{alarm.message}</span>
              <small>{new Date(alarm.timestamp).toLocaleString()}</small>
            </div>
            <button className="button" onClick={() => onAcknowledge(alarm.id)}>Ack</button>
          </div>
        ))}
      </div>
    </div>
  );
}
