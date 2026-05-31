// ─── Core HTTP Helpers ────────────────────────────────────────────────────────

export async function getJson<T>(path: string): Promise<T> {
  const token = window.localStorage.getItem('diskvision_token');
  const response = await fetch(path, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) {
    throw new Error(`${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const token = window.localStorage.getItem('diskvision_token');
  const response = await fetch(path, {
    method: 'POST',
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadFile(
  url: string,
  file: File,
): Promise<unknown> {
  const data = new FormData();
  data.append('file', file);
  const token = window.localStorage.getItem('diskvision_token');
  const response = await fetch(url, {
    method: 'POST',
    body: data,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}
