import { createContext, useContext, type ReactNode } from 'react';
import { useSnapshot, type UseSnapshotReturn } from '../hooks/useSnapshot';

// ─── Context ──────────────────────────────────────────────────────────────────

const SnapshotContext = createContext<UseSnapshotReturn | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

interface SnapshotProviderProps {
  children: ReactNode;
}

export function SnapshotProvider({ children }: SnapshotProviderProps) {
  const value = useSnapshot();
  return (
    <SnapshotContext.Provider value={value}>
      {children}
    </SnapshotContext.Provider>
  );
}

// ─── Consumer Hook ────────────────────────────────────────────────────────────

export function useSnapshotContext(): UseSnapshotReturn {
  const ctx = useContext(SnapshotContext);
  if (!ctx) {
    throw new Error('useSnapshotContext must be used within SnapshotProvider');
  }
  return ctx;
}
