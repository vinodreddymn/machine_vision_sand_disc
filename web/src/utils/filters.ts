import type { StoredInspection, HistoryFilters } from '../types/history';

/**
 * Pure filter + sort function for inspection history.
 * Used inside useHistory hook via useMemo.
 */
export function filterAndSortHistory(
  list: StoredInspection[],
  filters: HistoryFilters,
): StoredInspection[] {
  const {
    searchQuery,
    filterDecision,
    filterMode,
    filterDateFrom,
    filterDateTo,
    sortKey,
    sortDir,
  } = filters;

  const q = searchQuery.toLowerCase();

  const filtered = list.filter((item) => {
    const matchesSearch =
      item.physical_part_id.toLowerCase().includes(q) ||
      (item.serial_number && item.serial_number.toLowerCase().includes(q));

    const matchesDecision =
      filterDecision === 'ALL' || item.decision === filterDecision;

    const matchesMode =
      filterMode === 'ALL' || item.inspection_mode === filterMode;

    const itemDate = new Date(item.inspected_at).getTime();
    const matchesDateFrom =
      !filterDateFrom || itemDate >= new Date(filterDateFrom).getTime();
    const matchesDateTo =
      !filterDateTo || itemDate <= new Date(filterDateTo).getTime();

    return (
      matchesSearch &&
      matchesDecision &&
      matchesMode &&
      matchesDateFrom &&
      matchesDateTo
    );
  });

  return [...filtered].sort((a, b) => {
    let valA: number | string;
    let valB: number | string;

    switch (sortKey) {
      case 'cycle_time_ms':
        valA = a.cycle_time_ms ?? 0;
        valB = b.cycle_time_ms ?? 0;
        break;
      case 'decision':
        valA = a.decision;
        valB = b.decision;
        break;
      case 'inspected_at':
      default:
        valA = new Date(a.inspected_at).getTime();
        valB = new Date(b.inspected_at).getTime();
        break;
    }

    if (valA < valB) return sortDir === 'asc' ? -1 : 1;
    if (valA > valB) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * Convert StoredInspection[] to a downloadable CSV string.
 */
export function toCSV(list: StoredInspection[]): string {
  const headers = [
    'ID',
    'Part ID',
    'Serial Number',
    'Timestamp',
    'Mode',
    'Decision',
    'Cycle Time (ms)',
    'Disposition',
    'Source',
  ];

  const rows = list.map((item) => [
    item.id,
    item.physical_part_id,
    item.serial_number || '',
    item.inspected_at,
    item.inspection_mode,
    item.decision,
    item.cycle_time_ms ?? '',
    item.final_disposition,
    item.source_name || '',
  ]);

  const escape = (v: string | number) =>
    typeof v === 'string' && v.includes(',') ? `"${v}"` : String(v);

  return [headers, ...rows].map((r) => r.map(escape).join(',')).join('\n');
}
