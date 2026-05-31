// ─── Global Constants ─────────────────────────────────────────────────────────

/** Polling interval for snapshot refresh (ms) */
export const POLL_INTERVAL_MS = 1500;

/** Maximum log lines retained in memory */
export const MAX_LOG_LINES = 150;

/** Default camera name when none is provided */
export const DEFAULT_CAMERA_NAME = 'USB Camera 0';

/** WebSocket reconnect delay (ms) */
export const WS_RECONNECT_DELAY_MS = 3000;

/** API base paths */
export const API = {
  STATUS: '/api/status',
  STATION1: '/api/station1',
  METRICS: '/api/metrics',
  LOGS: '/api/logs',
  START: '/api/start-inspection',
  STOP: '/api/stop-inspection',
  SHUTDOWN: '/api/shutdown',
  START_PART: '/api/start-part',
  RESET: '/api/reset',
  OPERATOR_LABEL: '/api/operator-label',
  UPLOAD: '/api/upload',
  UPLOAD_VIDEO: '/api/upload-video',
  RESET_CAMERA: '/api/reset-camera',
  TOLERANCES: '/api/config/tolerances',
  MODE: '/api/config/mode',
  HISTORY: '/api/history',
  STREAM_STATION1: '/stream/station1',
  IMAGE_OVERLAY: '/image/station1/overlay',
  SYSTEM_HEALTH: '/api/system/health',
  SYSTEM_DEVICES: '/api/system/devices',
  SYSTEM_ALARMS: '/api/system/alarms',
  SYSTEM_ALARM_HISTORY: '/api/system/alarm-history',
  SYSTEM_ALARM_ACK_PREFIX: '/api/system/alarm',
  SYSTEM_HISTORY: '/api/system/history',
  SYSTEM_SERVICES: '/api/system/services',
} as const;
