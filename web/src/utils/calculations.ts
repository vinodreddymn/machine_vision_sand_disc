import type { Metrics } from '../types/snapshot';

/**
 * Compute production yield percentage from metrics.
 */
export function computeYieldRate(metrics: Metrics | null): string {
  const total = metrics?.total_parts ?? 0;
  const passed = metrics?.passed_parts ?? 0;
  if (total === 0) return '100.00%';
  return `${((passed / total) * 100).toFixed(2)}%`;
}

/**
 * Clamp a number between min and max.
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
