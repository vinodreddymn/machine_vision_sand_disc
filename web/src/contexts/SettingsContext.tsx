import { createContext, useContext, type ReactNode } from 'react';
import { useTolerances, type UseTolerancesReturn } from '../hooks/useTolerances';

// ─── Context ──────────────────────────────────────────────────────────────────

const SettingsContext = createContext<UseTolerancesReturn | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

interface SettingsProviderProps {
  children: ReactNode;
  active: boolean;
}

export function SettingsProvider({ children, active }: SettingsProviderProps) {
  const value = useTolerances(active);
  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

// ─── Consumer Hook ────────────────────────────────────────────────────────────

export function useSettingsContext(): UseTolerancesReturn {
  const ctx = useContext(SettingsContext);
  if (!ctx) {
    throw new Error('useSettingsContext must be used within SettingsProvider');
  }
  return ctx;
}
