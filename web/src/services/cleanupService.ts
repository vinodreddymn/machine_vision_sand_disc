/**
 * Service for managing AI training data cleanup operations.
 * Communicates with backend cleanup endpoints.
 */

export interface DatasetStatus {
  training_data: {
    good_images: number;
    defect_images: number;
    total_images: number;
    size_mb: number;
  };
  inspection_outputs: {
    passed_images: number;
    failed_images: number;
    total_images: number;
    size_mb: number;
  };
  database: {
    inspection_records: number;
  };
}

export interface CleanupRequest {
  clean_dataset: boolean;
  clean_outputs: boolean;
  clean_database: boolean;
}

export interface CleanupResult {
  status: 'success' | 'error';
  output: string;
  return_code: number;
}

const API_BASE = 'http://localhost:8010';

/**
 * Get current size and count of AI training data
 */
export async function getCleanupStatus(): Promise<DatasetStatus> {
  const token = localStorage.getItem('authToken');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/api/admin/cleanup/status`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to get cleanup status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Execute cleanup of specified data types
 */
export async function executeCleanup(options: {
  cleanDataset?: boolean;
  cleanOutputs?: boolean;
  cleanDatabase?: boolean;
}): Promise<CleanupResult> {
  const token = localStorage.getItem('authToken');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const request: CleanupRequest = {
    clean_dataset: options.cleanDataset ?? true,
    clean_outputs: options.cleanOutputs ?? false,
    clean_database: options.cleanDatabase ?? false,
  };

  const response = await fetch(`${API_BASE}/api/admin/cleanup/execute`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to execute cleanup: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Format bytes to human readable size
 */
export function formatSize(mb: number): string {
  if (mb < 1) {
    return (mb * 1024).toFixed(0) + ' KB';
  }
  if (mb < 1024) {
    return mb.toFixed(2) + ' MB';
  }
  return (mb / 1024).toFixed(2) + ' GB';
}
