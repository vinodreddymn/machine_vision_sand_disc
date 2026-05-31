import { createContext, useContext, type ReactNode } from 'react';
import { useHistory, type UseHistoryReturn } from '../hooks/useHistory';

// ─── Context ──────────────────────────────────────────────────────────────────

const HistoryContext = createContext<UseHistoryReturn | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

interface HistoryProviderProps {
  children: ReactNode;
  active: boolean;
}

export function HistoryProvider({ children, active }: HistoryProviderProps) {
  const value = useHistory(active);
  return (
    <HistoryContext.Provider value={value}>
      {children}
    </HistoryContext.Provider>
  );
}

// ─── Consumer Hook ────────────────────────────────────────────────────────────

export function useHistoryContext(): UseHistoryReturn {
  const ctx = useContext(HistoryContext);
  if (!ctx) {
    throw new Error('useHistoryContext must be used within HistoryProvider');
  }
  return ctx;
}
