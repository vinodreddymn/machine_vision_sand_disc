import React, { useRef, useEffect } from 'react';

interface EventLogProps {
  logs: string[];
}

export const EventLog = React.memo(function EventLog({ logs }: EventLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs.length]);

  return (
    <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ marginBottom: '10px' }}>Operational Events log</h2>
      <div
        className="log-terminal"
        style={{ flex: 1, minHeight: '280px' }}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
      >
        {logs.length > 0 ? (
          <>
            {logs.map((log, idx) => (
              <p key={idx}>{log}</p>
            ))}
            <div ref={bottomRef} />
          </>
        ) : (
          <p style={{ color: '#64748b' }}>Waiting for system events...</p>
        )}
      </div>
    </div>
  );
});
