import { getJson, postJson } from './apiService';
import type { AppUser, CreateUserRequest } from '../types/admin';

export function listUsers(limit = 200): Promise<AppUser[]> {
  return getJson<AppUser[]>(`/api/admin/users?limit=${limit}`);
}

export function createUser(req: CreateUserRequest): Promise<{ status: string; id: number }> {
  return postJson<{ status: string; id: number }>('/api/admin/users', req);
}

export interface AuditLog {
  id: number;
  created_at: string;
  actor: string | null;
  action: string;
  resource: string | null;
  message: string;
  details: unknown;
}

export function listAuditLogs(limit = 200): Promise<AuditLog[]> {
  return getJson<AuditLog[]>(`/api/admin/audit-logs?limit=${limit}`);
}

export function createBackup(): Promise<unknown> {
  return postJson<unknown>('/api/admin/backup/create');
}
