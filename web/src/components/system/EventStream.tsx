import {
  Activity,
  AlertTriangle,
  ShieldAlert
} from 'lucide-react';

import type {
  Alarm,
  SystemHealth
} from '../../types/systemHealth';

interface EventStreamProps {
  alarms: Alarm[];
  health: SystemHealth | null;
}

export function EventStream({
  alarms,
  health
}: EventStreamProps) {

  const events = [
    ...(health
      ? [
          {
            type: 'SYSTEM',
            text:
              health.inspection_running
                ? 'Inspection Running'
                : 'Inspection Stopped',
            timestamp:
              health.timestamp ??
              new Date().toISOString()
          }
        ]
      : []),

    ...alarms.map((alarm) => ({
      type: alarm.severity,
      text: `${alarm.category}: ${alarm.message}`,
      timestamp: alarm.timestamp
    }))
  ]
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() -
        new Date(a.timestamp).getTime()
    )
    .slice(0, 20);

  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>Live Event Stream</h3>
      </div>

      <div className="sys-event-stream">

        {events.length === 0 && (
          <div className="sys-empty-state">
            No recent events
          </div>
        )}

        {events.map((event, index) => (

          <div
            key={`${event.timestamp}-${index}`}
            className="sys-event-row"
          >

            <div className="sys-event-icon">

              {event.type ===
                'CRITICAL' ||
              event.type ===
                'EMERGENCY' ? (
                <ShieldAlert size={16} />
              ) : event.type ===
                'WARNING' ? (
                <AlertTriangle size={16} />
              ) : (
                <Activity size={16} />
              )}

            </div>

            <div className="sys-event-content">

              <div className="sys-event-message">
                {event.text}
              </div>

              <div className="sys-event-time">
                {new Date(
                  event.timestamp
                ).toLocaleString()}
              </div>

            </div>

          </div>

        ))}

      </div>

    </section>
  );
}