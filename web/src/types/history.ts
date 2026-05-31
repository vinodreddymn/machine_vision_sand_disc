// ─── Stored Inspection Record ─────────────────────────────────────────────────

export interface StoredInspection {
  id: number;
  physical_part_id: string;
  stage: string;
  serial_number: string;
  inspected_at: string;
  decision: string;
  final_disposition: string;
  source_name: string | null;
  reject_requested: boolean;
  measurements: Record<string, number | string>;
  defects: string[];
  overlay_path: string | null;
  inspection_mode: string;
  cycle_time_ms: number | null;
}

// ─── Filter Types ─────────────────────────────────────────────────────────────

export type DecisionFilter = 'ALL' | 'PASS' | 'FAIL';
export type ModeFilter = 'ALL' | 'PRODUCTION' | 'DATA_COLLECTION';
export type SortKey = 'inspected_at' | 'cycle_time_ms' | 'decision';
export type SortDir = 'asc' | 'desc';

export interface HistoryFilters {
  searchQuery: string;
  filterDecision: DecisionFilter;
  filterMode: ModeFilter;
  filterDateFrom: string;
  filterDateTo: string;
  sortKey: SortKey;
  sortDir: SortDir;
}

export const defaultHistoryFilters: HistoryFilters = {
  searchQuery: '',
  filterDecision: 'ALL',
  filterMode: 'ALL',
  filterDateFrom: '',
  filterDateTo: '',
  sortKey: 'inspected_at',
  sortDir: 'desc',
};
