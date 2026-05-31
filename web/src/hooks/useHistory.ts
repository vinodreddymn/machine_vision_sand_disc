import { useState, useEffect, useMemo, useCallback } from 'react';
import { getHistory } from '../services/historyService';
import { filterAndSortHistory } from '../utils/filters';
import type { StoredInspection, HistoryFilters } from '../types/history';
import { defaultHistoryFilters } from '../types/history';

export interface UseHistoryReturn {
  historyList: StoredInspection[];
  filteredHistory: StoredInspection[];
  selectedInspection: StoredInspection | null;
  setSelectedInspection: (item: StoredInspection | null) => void;
  filters: HistoryFilters;
  setFilters: (partial: Partial<HistoryFilters>) => void;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

/**
 * Manages inspection history: fetching, filtering, sorting, selection.
 * @param active - only fetches data when true (avoids unnecessary API calls)
 */
export function useHistory(active: boolean): UseHistoryReturn {
  const [historyList, setHistoryList] = useState<StoredInspection[]>([]);
  const [selectedInspection, setSelectedInspection] =
    useState<StoredInspection | null>(null);
  const [filters, setFiltersState] =
    useState<HistoryFilters>(defaultHistoryFilters);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getHistory();
      setHistoryList(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (active) {
      void reload();
    }
  }, [active, reload]);

  const setFilters = useCallback((partial: Partial<HistoryFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...partial }));
  }, []);

  const filteredHistory = useMemo(
    () => filterAndSortHistory(historyList, filters),
    [historyList, filters],
  );

  return {
    historyList,
    filteredHistory,
    selectedInspection,
    setSelectedInspection,
    filters,
    setFilters,
    loading,
    error,
    reload,
  };
}
