import React, { useRef, useEffect } from 'react';
import { AlertCircle, Info, CheckCircle, Clock } from 'lucide-react';

interface EventLogProps {
  logs: string[];
  maxLines?: number;
}

// Helper to parse log level from message
function getLogLevel(log: string): 'error' | 'warning' | 'info' | 'success' {
  const lower = log.toLowerCase();
  if (lower.includes('error') || lower.includes('failed')) return 'error';
  if (lower.includes('warning') || lower.includes('warn')) return 'warning';
  if (lower.includes('success') || lower.includes('passed') || lower.includes('completed')) return 'success';
  if (lower.includes('info') || lower.includes('started')) return 'info';
  return 'info';
}

function getLogIcon(level: 'error' | 'warning' | 'info' | 'success') {
  switch (level) {
    case 'error':
      return <AlertCircle size={14} />;
    case 'warning':
      return <AlertCircle size={14} />;
    case 'success':
      return <CheckCircle size={14} />;
    default:
      return <Info size={14} />;
  }
}

export const EventLog = React.memo(function EventLog({ logs, maxLines = 100 }: EventLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // Keep only the latest logs
  const displayLogs = logs.slice(-maxLines);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs.length]);

  return (
    <div className="panel event-log-panel">
      <div className="event-log-header">
        <h2>Operational Events Log</h2>
        <span className="log-count">{logs.length} events</span>
      </div>
      
      <div
        className="event-log-container"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
      >
        {displayLogs.length > 0 ? (
          <>
            {displayLogs.map((log, idx) => {
              const level = getLogLevel(log);
              return (
                <div key={idx} className={`log-entry log-${level}`}>
                  <div className={`log-icon log-icon-${level}`}>
                    {getLogIcon(level)}
                  </div>
                  <div className="log-content">
                    <p className="log-message">{log}</p>
                  </div>
                  <div className="log-timestamp">
                    <Clock size={12} />
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </>
        ) : (
          <p className="log-placeholder">Waiting for system events...</p>
        )}
      </div>
      
      <div className="event-log-footer">
        <span className="footer-text">Latest {displayLogs.length} of {logs.length} events · Auto-scrolling enabled</span>
      </div>
    </div>
  );
});
