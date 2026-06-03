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

export interface UnifiedAuditEvent {
  source: 'SYSTEM' | 'CONFIG';
  timestamp: string;
  actor: string | null;
  action: string;
  resource: string | null;
  message: string;
  details: unknown;
}

export interface ModelRegistryEntry {
  id: number;
  version: string;
  training_date: string | null;
  dataset_size: number | null;
  accuracy: number | null;
  active: boolean;
  notes: string | null;
  model_path: string;
  created_at: string;
  updated_at: string;
}

export interface CreateModelRequest {
  version: string;
  training_date?: string | null;
  dataset_size?: number | null;
  accuracy?: number | null;
  active?: boolean;
  notes?: string | null;
  model_path: string;
}

export function listAuditLogs(limit = 200): Promise<AuditLog[]> {
  return getJson<AuditLog[]>(`/api/admin/audit-logs?limit=${limit}`);
}

export function createBackup(): Promise<unknown> {
  return postJson<unknown>('/api/admin/backup/create');
}

export function listUnifiedAuditEvents(limit = 200): Promise<UnifiedAuditEvent[]> {
  return getJson<UnifiedAuditEvent[]>(`/api/audit/events?limit=${limit}`);
}

export function listModels(limit = 200): Promise<ModelRegistryEntry[]> {
  return getJson<ModelRegistryEntry[]>(`/api/models?limit=${limit}`);
}

export function createModel(req: CreateModelRequest): Promise<{ status: string; id: number }> {
  return postJson<{ status: string; id: number }>('/api/models', req);
}

export function activateModel(version: string): Promise<{ status: string; version: string; active: boolean }> {
  return postJson<{ status: string; version: string; active: boolean }>(`/api/models/${encodeURIComponent(version)}/activate`);
}

export function deactivateModel(version: string): Promise<{ status: string; version: string; active: boolean }> {
  return postJson<{ status: string; version: string; active: boolean }>(`/api/models/${encodeURIComponent(version)}/deactivate`);
}

export function rollbackModel(version: string): Promise<{ status: string; version: string }> {
  return postJson<{ status: string; version: string }>(`/api/models/${encodeURIComponent(version)}/rollback`);
}
