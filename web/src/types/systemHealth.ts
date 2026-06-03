export type AlarmSeverity = 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY';

export interface SystemHealth {
  cpu_usage: number | null;
  memory_usage: number | null;
  temperature: number | null;
  disk_usage: number | null;
  uptime: string | null;
  cpu_frequency_mhz: number | null;
  load_average: Record<string, number> | null;
  free_disk_gb: number | null;
  network_online: boolean;
  lan_ip: string | null;
  wifi_online: boolean;
  camera_online: boolean;
  camera_fps: number | null;
  camera_frame_drops: number | null;
  last_frame_timestamp: string | null;
  camera_source_name: string | null;
  camera_recovery_attempts: number | null;
  inspection_running: boolean;
  current_mode: string | null;
  parts_per_minute: number | null;
  average_cycle_time_ms: number | null;
  inspection_latency_ms: number | null;
  inference_time_ms: number | null;
  queue_backlog: number | null;
  thread_status: string | null;
  plc_online: boolean;
  plc_latency_ms: number | null;
  plc_heartbeat_ok: boolean;
  plc_last_success: string | null;
  plc_error_count: number | null;
  database_online: boolean;
  database_connection: string | null;
  database_last_success: string | null;
  database_size_bytes: number | null;
  database_write_failures: number | null;
  storage_status: string | null;
  timestamp: string | null;
}

export interface DeviceStatus {
  camera: 'ONLINE' | 'OFFLINE';
  plc: 'ONLINE' | 'OFFLINE';
  database: 'ONLINE' | 'OFFLINE';
  network: 'ONLINE' | 'OFFLINE';
}

export interface ServiceStatus {
  name?: string;
  status: 'ONLINE' | 'OFFLINE' | string;
  version?: string | null;
  timestamp?: number | null;
}

export interface StartupDiagnostics {
  database: string;
  camera: string;
  plc: string;
  storage: string;
  model: string;
  model_version?: string | null;
  config_version?: number | null;
  inspection_runtime?: Record<string, unknown> | null;
}

export interface Alarm {
  id: number;
  timestamp: string;
  category: string;
  severity: AlarmSeverity;
  message: string;
  source: string;
  acknowledged: boolean;
}

export interface HealthHistory {
  timestamp: string;
  cpu_usage: number | null;
  memory_usage: number | null;
  temperature: number | null;
  disk_usage: number | null;
  free_disk_gb: number | null;
}
