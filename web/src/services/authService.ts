import { getJson, postJson } from './apiService';

export interface AuthConfig {
  auth_enabled: boolean;
}

export interface LoginResponse {
  token: string | null;
  auth_enabled: boolean;
  role?: string;
}

export function getAuthConfig(): Promise<AuthConfig> {
  return getJson<AuthConfig>('/api/auth/config');
}

export function login(username: string, password: string): Promise<LoginResponse> {
  return postJson<LoginResponse>('/api/auth/login', { username, password });
}

