import React from 'react';
import { RefreshCcw } from 'lucide-react';
import { useHistoryContext } from '../../contexts/HistoryContext';
import type { DecisionFilter, ModeFilter, SortKey } from '../../types/history';

export const HistoryFilters = React.memo(function HistoryFilters() {
  const { filters, setFilters, reload } = useHistoryContext();

  return (
    <div className="table-header-filters">
      <h2 style={{ margin: 0, fontSize: '16px' }}>Inspection Database Logs</h2>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          id="history-search"
          className="search-input"
          placeholder="Search Part ID or Serial..."
          value={filters.searchQuery}
          onChange={(e) => setFilters({ searchQuery: e.target.value })}
        />

        <select
          id="filter-decision"
          className="select-input"
          value={filters.filterDecision}
          onChange={(e) =>
            setFilters({ filterDecision: e.target.value as DecisionFilter })
          }
        >
          <option value="ALL">All Decisions</option>
          <option value="PASS">PASS Only</option>
          <option value="FAIL">FAIL Only</option>
        </select>

        <select
          id="filter-mode"
          className="select-input"
          value={filters.filterMode}
          onChange={(e) =>
            setFilters({ filterMode: e.target.value as ModeFilter })
          }
        >
          <option value="ALL">All Modes</option>
          <option value="PRODUCTION">PRODUCTION</option>
          <option value="DATA_COLLECTION">DATA_COLLECTION</option>
        </select>

        <select
          id="filter-sort"
          className="select-input"
          value={`${filters.sortKey}:${filters.sortDir}`}
          onChange={(e) => {
            const [sortKey, sortDir] = e.target.value.split(':') as [
              SortKey,
              'asc' | 'desc',
            ];
            setFilters({ sortKey, sortDir });
          }}
        >
          <option value="inspected_at:desc">Newest First</option>
          <option value="inspected_at:asc">Oldest First</option>
          <option value="cycle_time_ms:asc">Fastest Cycle</option>
          <option value="cycle_time_ms:desc">Slowest Cycle</option>
          <option value="decision:asc">Decision A→Z</option>
        </select>

        <input
          type="date"
          id="filter-date-from"
          className="select-input"
          title="From date"
          value={filters.filterDateFrom}
          onChange={(e) => setFilters({ filterDateFrom: e.target.value })}
        />
        <input
          type="date"
          id="filter-date-to"
          className="select-input"
          title="To date"
          value={filters.filterDateTo}
          onChange={(e) => setFilters({ filterDateTo: e.target.value })}
        />

        <button
          id="btn-reload-history"
          className="button"
          onClick={() => { void reload(); }}
          title="Refresh history"
          style={{ padding: '0 10px', height: '34px' }}
        >
          <RefreshCcw size={14} />
        </button>
      </div>
    </div>
  );
});
