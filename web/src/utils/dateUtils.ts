/**
 * Format a Date object to a human-readable locale string.
 */
export function formatDateTime(date: Date): string {
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

/**
 * Format an ISO timestamp string to locale string.
 */
export function formatIsoDate(iso: string): string {
  return new Date(iso).toLocaleString();
}
