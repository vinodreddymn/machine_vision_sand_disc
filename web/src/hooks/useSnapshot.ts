import { useState, useEffect, useCallback, useRef } from 'react';
import { getJson, postJson } from '../services/apiService';
import { useWebSocketLogs } from './useWebSocketLogs';
import type { Snapshot, Status, Station, Metrics } from '../types/snapshot';
import { emptySnapshot } from '../types/snapshot';
import { POLL_INTERVAL_MS, MAX_LOG_LINES, API } from '../utils/constants';

export interface UseSnapshotReturn {
  snapshot: Snapshot;
  loading: boolean;
  wsConnected: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  runAction: (fn: () => Promise<unknown>) => Promise<void>;
}

export function useSnapshot(): UseSnapshotReturn {
  const [snapshot, setSnapshot] = useState<Snapshot>(emptySnapshot);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stable ref so WS callback never stale-closes over snapshot
  const snapshotRef = useRef(snapshot);
  snapshotRef.current = snapshot;

  const refresh = useCallback(async () => {
    try {
      const [status, station1, metrics, logs] = await Promise.all([
        getJson<Status>(API.STATUS),
        getJson<Station>(API.STATION1),
        getJson<Metrics>(API.METRICS),
        getJson<string[]>(API.LOGS),
      ]);
      setSnapshot({ status, station1, metrics, logs });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const runAction = useCallback(
    async (fn: () => Promise<unknown>) => {
      try {
        await fn();
        await refresh();
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    },
    [refresh],
  );

  // Stable WS message handler — appends to current logs via ref
  const handleWsMessage = useCallback((message: string) => {
    setSnapshot((prev) => ({
      ...prev,
      logs: [...prev.logs, message].slice(-MAX_LOG_LINES),
    }));
  }, []);

  const handleWsStatus = useCallback((connected: boolean) => {
    setWsConnected(connected);
  }, []);

  // Polling
  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => { void refresh(); }, POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [refresh]);

  // WebSocket
  useWebSocketLogs(handleWsMessage, handleWsStatus);

  return { snapshot, loading, wsConnected, error, refresh, runAction };
}

// Re-export postJson for runAction consumers that need it
export { postJson };
