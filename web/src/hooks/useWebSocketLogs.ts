import { useEffect } from 'react';
import { createWebSocketConnection } from '../services/websocketService';

/**
 * Opens a WebSocket connection to /ws/logs and calls onMessage for
 * each received log line. Handles reconnect and cleanup automatically.
 */
export function useWebSocketLogs(
  onMessage: (message: string) => void,
  onStatusChange?: (connected: boolean) => void,
): void {
  useEffect(() => {
    const cleanup = createWebSocketConnection(onMessage, onStatusChange);
    return cleanup;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally empty — callbacks are stable refs from useSnapshot
}
