// ─── Production Metrics (derived/computed) ───────────────────────────────────

export interface ProductionMetrics {
  yieldRate: string;
  totalParts: number;
  passedParts: number;
  rejectedParts: number;
  cycleTimeMs: number | null;
}

// ─── Telemetry Data ───────────────────────────────────────────────────────────

export interface TelemetryData {
  systemState: 'RUNNING' | 'STOPPED' | string;
  lineMode: string;
  conveyorStatus: string;
  rejectGate: string;
}
