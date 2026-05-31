// ─── PLC & Status Types ──────────────────────────────────────────────────────

export interface PlcStatus {
  run_status: string;
  mode: string;
  conveyor_status: string;
  reject_actuator: string;
  accept_gate: string;
}

export interface Status {
  running: boolean;
  mode: string;
  part_id: string;
  plc: PlcStatus;
  storage: string;
  pending_label: boolean;
  log_count: number;
  camera_name?: string;
}

// ─── Station Type ─────────────────────────────────────────────────────────────

export interface Station {
  station: string;
  name: string;
  active: boolean;
  part_id: string | null;
  serial_number: string | null;
  decision: string;
  disposition: string;
  source_name: string | null;
  system_prediction: string | null;
  anomaly_score: number | null;
  pending_label: boolean;
  defects: string[];
  measurements: Record<string, number | string>;
  stream_url: string;
  captured_image_url: string;
  cycle_time_ms: number | null;
}

// ─── Dataset Metrics sub-type ─────────────────────────────────────────────────

export interface DatasetStats {
  total_good: number;
  total_defective: number;
  operator_corrections: number;
  system_accuracy_estimate: number;
}

// ─── Metrics Type ─────────────────────────────────────────────────────────────

export interface Metrics {
  total_parts: number;
  passed_parts: number;
  rejected_parts: number;
  station1_passed: number;
  station1_rejected: number;
  dataset: DatasetStats;
}

// ─── Snapshot (combined poll result) ─────────────────────────────────────────

export interface Snapshot {
  status: Status | null;
  station1: Station | null;
  metrics: Metrics | null;
  logs: string[];
}

export const emptySnapshot: Snapshot = {
  status: null,
  station1: null,
  metrics: null,
  logs: [],
};
