import { getJson } from './apiService';
import type { StoredInspection } from '../types/history';

export async function getHistory(): Promise<StoredInspection[]> {
  return getJson<StoredInspection[]>('/api/history');
}
