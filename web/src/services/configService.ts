/**
 * Configuration Management Service
 * Handles all API calls for configuration management, versioning, and audit logs
 */

const API_BASE = '/api/config';

export interface ConfigMetadata {
  id: number;
  config_key: string;
  version: number;
  created_at: string;
  updated_at: string;
  updated_by?: string;
  description?: string;
  is_active: boolean;
}

export interface RuntimeReloadResult {
  config_key?: string;
  version?: number;
  data?: Record<string, any>;
  configs?: ConfigData[];
}

export interface AuditLogEntry {
  id: number;
  config_key: string;
  action: string;
  old_value?: Record<string, any>;
  new_value?: Record<string, any>;
  version_number: number;
  changed_by: string;
  changed_at: string;
  reason?: string;
  ip_address?: string;
}

export interface ConfigData {
  config_key: string;
  data: Record<string, any>;
  versions: ConfigMetadata[];
}

/**
 * Get all active configurations
 */
export async function getAllConfigs(): Promise<ConfigData[]> {
  const response = await fetch(`${API_BASE}/all`);
  if (!response.ok) {
    throw new Error(`Failed to fetch configurations: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get a specific configuration by key
 */
export async function getConfig(configKey: string): Promise<Record<string, any>> {
  const response = await fetch(`${API_BASE}/${configKey}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch configuration ${configKey}: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Save a configuration (creates new version automatically)
 */
export async function saveConfig(
  configKey: string,
  configData: Record<string, any>,
  description?: string,
  reason?: string
): Promise<ConfigMetadata> {
  const response = await fetch(`${API_BASE}/${configKey}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('diskvision_token') || ''}`,
    },
    body: JSON.stringify({
      ...configData,
      description,
      reason,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to save configuration: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get version history for a configuration
 */
export async function getConfigVersions(
  configKey: string,
  limit: number = 10
): Promise<ConfigMetadata[]> {
  const response = await fetch(`${API_BASE}/${configKey}/versions?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch configuration versions: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Rollback configuration to a previous version
 */
export async function rollbackConfig(
  configKey: string,
  version: number,
  reason?: string
): Promise<ConfigMetadata> {
  const response = await fetch(`${API_BASE}/${configKey}/rollback/${version}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('diskvision_token') || ''}`,
    },
    body: JSON.stringify({ reason }),
  });

  if (!response.ok) {
    throw new Error(`Failed to rollback configuration: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Reload configuration data without restarting the application
 */
export async function reloadConfig(configKey?: string): Promise<RuntimeReloadResult> {
  const query = new URLSearchParams();
  if (configKey) {
    query.append('config_key', configKey);
  }

  const response = await fetch(`${API_BASE}/reload${query.toString() ? `?${query.toString()}` : ''}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('diskvision_token') || ''}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to reload configuration: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get the current version number for a configuration
 */
export async function getConfigVersion(configKey: string): Promise<number> {
  const response = await fetch(`${API_BASE}/${configKey}/version`);
  if (!response.ok) {
    throw new Error(`Failed to fetch configuration version: ${response.statusText}`);
  }
  const data = await response.json();
  return data.version;
}

/**
 * Get audit log for configurations
 */
export async function getConfigAuditLog(
  configKey?: string,
  limit: number = 100
): Promise<AuditLogEntry[]> {
  const query = new URLSearchParams();

  if (configKey) {
    query.append('config_key', configKey);
  }

  query.append('limit', limit.toString());

  const token = localStorage.getItem('diskvision_token');

  const response = await fetch(`${API_BASE}/audit-log?${query.toString()}`, {
    headers: {
      Authorization: `Bearer ${token || ''}`,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Failed to fetch audit log: ${response.status}`);
  }

  return response.json();
}
