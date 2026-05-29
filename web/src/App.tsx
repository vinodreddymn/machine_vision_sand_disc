import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Check,
  CircleStop,
  Database,
  Factory,
  Play,
  Power,
  RefreshCcw,
  ShieldCheck,
  Upload,
  X,
  Settings,
  Video,
  Camera,
  SlidersHorizontal,
  Cpu
} from 'lucide-react';
import { CalibrationPage } from './CalibrationPage';
import {
  getJson,
  Metrics,
  postJson,
  Station,
  Status,
  uploadImage,
  uploadVideo,
  resetCamera,
  getTolerances,
  saveTolerances,
  setInspectionMode,
  getHistory,
  StoredInspection
} from './api';

type Snapshot = {
  status: Status | null;
  station1: Station | null;
  metrics: Metrics | null;
  logs: string[];
};

const emptySnapshot: Snapshot = {
  status: null,
  station1: null,
  metrics: null,
  logs: []
};

export function App() {
  const [activeTab, setActiveTab] = useState<'production' | 'training' | 'history' | 'settings'>('production');
  const [settingsTab, setSettingsTab] = useState<'calibration' | 'tolerances'>('calibration');
  const [snapshot, setSnapshot] = useState<Snapshot>(emptySnapshot);
  const [clock, setClock] = useState(new Date());
  const [error, setError] = useState<string | null>(null);

  // Settings state
  const [tolerances, setTolerances] = useState<any>(null);
  const [savingTolerances, setSavingTolerances] = useState(false);
  const [settingsSuccess, setSettingsSuccess] = useState(false);

  // History state
  const [historyList, setHistoryList] = useState<StoredInspection[]>([]);
  const [selectedInspection, setSelectedInspection] = useState<StoredInspection | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDecision, setFilterDecision] = useState<'ALL' | 'PASS' | 'FAIL'>('ALL');
  const [filterMode, setFilterMode] = useState<'ALL' | 'PRODUCTION' | 'DATA_COLLECTION'>('ALL');

  async function refresh() {
    try {
      const [status, station1, metrics, logs] = await Promise.all([
        getJson<Status>('/api/status'),
        getJson<Station>('/api/station1'),
        getJson<Metrics>('/api/metrics'),
        getJson<string[]>('/api/logs')
      ]);
      setSnapshot({ status, station1, metrics, logs });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 1500);
    const clockTimer = window.setInterval(() => setClock(new Date()), 1000);
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/logs`);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { message: string };
      setSnapshot((current) => ({ ...current, logs: [...current.logs, payload.message].slice(-150) }));
    };
    return () => {
      window.clearInterval(timer);
      window.clearInterval(clockTimer);
      socket.close();
    };
  }, []);

  // Fetch tolerances or history on tab change
  useEffect(() => {
    if (activeTab === 'settings') {
      getTolerances()
        .then((data) => {
          setTolerances(data);
          setError(null);
        })
        .catch((err) => setError(err.message));
    } else if (activeTab === 'history') {
      getHistory()
        .then((data) => {
          setHistoryList(data);
          setError(null);
        })
        .catch((err) => setError(err.message));
    }
  }, [activeTab]);

  async function runAction(action: () => Promise<unknown>) {
    try {
      await action();
      await refresh();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const handleSaveTolerances = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tolerances) return;
    setSavingTolerances(true);
    setSettingsSuccess(false);
    try {
      await saveTolerances(tolerances);
      setSettingsSuccess(true);
      setTimeout(() => setSettingsSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingTolerances(false);
    }
  };

  const handleModeChange = async (mode: string) => {
    try {
      await setInspectionMode(mode);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  // Filtered history list
  const filteredHistory = useMemo(() => {
    return historyList.filter((item) => {
      const matchesSearch =
        item.physical_part_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.serial_number && item.serial_number.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesDecision =
        filterDecision === 'ALL' || item.decision === filterDecision;
      const matchesMode =
        filterMode === 'ALL' || item.inspection_mode === filterMode;
      return matchesSearch && matchesDecision && matchesMode;
    });
  }, [historyList, searchQuery, filterDecision, filterMode]);

  // Production yield
  const yieldRate = useMemo(() => {
    const total = snapshot.metrics?.total_parts ?? 0;
    const passed = snapshot.metrics?.passed_parts ?? 0;
    if (total === 0) return '100.00%';
    return `${((passed / total) * 100).toFixed(2)}%`;
  }, [snapshot.metrics]);

  return (
    <div className="app-container">
      {/* Sidebar navigation */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Factory size={28} />
          <h1>ASHTECH SOLUTIONS</h1>
        </div>
        <nav className="sidebar-nav">
          <button
            className={`sidebar-button ${activeTab === 'production' ? 'active' : ''}`}
            onClick={() => setActiveTab('production')}
          >
            <Factory size={18} />
            Production Run
          </button>
          <button
            className={`sidebar-button ${activeTab === 'training' ? 'active' : ''}`}
            onClick={() => setActiveTab('training')}
          >
            <Activity size={18} />
            Training & Datasets
          </button>
          <button
            className={`sidebar-button ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <Database size={18} />
            Analytics & Logs
          </button>
          <button
            className={`sidebar-button ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={18} />
            Settings
          </button>
        </nav>
      </aside>

      {/* Main Content Pane */}
      <main className="main-content">
        <header className="workspace-header">
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', color: '#f8fafc' }}>
              DiskVisionInspector <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 'normal' }}>v2.0</span>
            </h1>
            <span style={{ fontSize: '13px', color: '#94a3b8' }}>
              {activeTab === 'production' && 'Real-time Production Inspection HMI'}
              {activeTab === 'training' && 'Ground-Truth Dataset Collector & Labeling'}
              {activeTab === 'history' && 'Industry 4.0 SQL History Database Browser'}
              {activeTab === 'settings' && settingsTab === 'calibration' && 'One-Time Camera Calibration — px → mm'}
              {activeTab === 'settings' && settingsTab === 'tolerances' && 'Inspection Tolerances & Mode Control'}
            </span>
          </div>

          <div className="header-meta">
            <div className="oee-badge">
              <Check size={14} />
              Yield: {yieldRate}
            </div>
            <div className="header-clock">
              {clock.toLocaleDateString()} {clock.toLocaleTimeString()}
            </div>
            <div className="header-actions">
              <button
                className="button good"
                onClick={() => runAction(() => postJson('/api/start-inspection'))}
                disabled={snapshot.status?.running}
                style={{ height: '36px', minHeight: '36px' }}
              >
                <Play size={14} />
                Start Line
              </button>
              <button
                className="button"
                onClick={() => runAction(() => postJson('/api/stop-inspection'))}
                disabled={!snapshot.status?.running}
                style={{ height: '36px', minHeight: '36px' }}
              >
                <CircleStop size={14} />
                Stop
              </button>
              <button
                className="button danger"
                onClick={() => runAction(() => postJson('/api/shutdown'))}
                style={{ height: '36px', minHeight: '36px' }}
              >
                <Power size={14} />
                Shutdown
              </button>
            </div>
          </div>
        </header>

        {error && (
          <div style={{ padding: '0 24px', marginTop: '16px' }}>
            <div className="alert">{error}</div>
          </div>
        )}

        {/* Dynamic Screen Panels */}
        {activeTab === 'production' && (
          <div className="grid-production">
            <div>
              {/* Production Yield/Counters */}
              <div className="kpi-container">
                <div className="kpi-card">
                  <div className="kpi-icon blue"><Factory size={22} /></div>
                  <div className="kpi-info">
                    <span>Total Inspected</span>
                    <strong>{snapshot.metrics?.total_parts ?? 0}</strong>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon green"><Check size={22} /></div>
                  <div className="kpi-info">
                    <span>Passed</span>
                    <strong>{snapshot.metrics?.passed_parts ?? 0}</strong>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon red"><X size={22} /></div>
                  <div className="kpi-info">
                    <span>Rejected</span>
                    <strong>{snapshot.metrics?.rejected_parts ?? 0}</strong>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon yellow"><Activity size={22} /></div>
                  <div className="kpi-info">
                    <span>Cycle Time</span>
                    <strong>{snapshot.station1?.cycle_time_ms ? `${snapshot.station1.cycle_time_ms} ms` : '--'}</strong>
                  </div>
                </div>
              </div>

              {/* Feed Viewer */}
              <div className="production-feed-viewer">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ margin: 0, fontSize: '15px', color: '#f8fafc' }}>Real-time Camera Inspector</h2>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>
                    Source: <span style={{ color: '#38bdf8', fontWeight: 600 }}>{snapshot.status?.camera_name ?? 'USB Camera 0'}</span> | Active Part: {snapshot.status?.part_id ?? 'None'}
                  </span>
                </div>
                <div className="production-feed-layout">
                  <div className="feed-box">
                    <span>Live Camera Stream</span>
                    <img src="/stream/station1" alt="Inspection Stream" />
                  </div>
                  <div className="feed-box">
                    <span>Latest Overlay Inspection Result</span>
                    {snapshot.station1?.captured_image_url ? (
                      <img
                        src={`${snapshot.station1.captured_image_url}?t=${Date.now()}`}
                        alt="Captured Result Overlay"
                      />
                    ) : (
                      <div className="no-img">No inspection image captured yet.</div>
                    )}
                  </div>
                </div>

                {/* Big Pass/Fail display */}
                <div
                  className={`large-decision-display ${
                    snapshot.station1?.decision ? snapshot.station1.decision.toLowerCase() : 'waiting'
                  }`}
                >
                  {snapshot.station1?.decision ?? 'WAITING FOR PART'}
                </div>
              </div>
            </div>

            {/* Sidebar Column: Telemetry, Logs */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="plc-telemetry-panel">
                <h2 style={{ margin: 0, fontSize: '15px', color: '#f8fafc' }}>PLC & Conveyor Telemetry</h2>
                <div className="plc-telemetry-grid">
                  <div className="plc-telemetry-item">
                    <span>System State</span>
                    <strong className={snapshot.status?.running ? 'plc-val-running' : 'plc-val-idle'}>
                      {snapshot.status?.running ? 'RUNNING' : 'STOPPED'}
                    </strong>
                  </div>
                  <div className="plc-telemetry-item">
                    <span>Line Mode</span>
                    <strong className="plc-val-active">
                      {snapshot.status?.mode ?? 'MANUAL'}
                    </strong>
                  </div>
                  <div className="plc-telemetry-item">
                    <span>Conveyor</span>
                    <strong
                      className={
                        snapshot.status?.plc.conveyor_status === 'RUNNING'
                          ? 'plc-val-running'
                          : 'plc-val-idle'
                      }
                    >
                      {snapshot.status?.plc.conveyor_status ?? 'STOPPED'}
                    </strong>
                  </div>
                  <div className="plc-telemetry-item">
                    <span>Reject Gate</span>
                    <strong
                      className={
                        snapshot.status?.plc.reject_actuator === 'ACTIVE'
                          ? 'plc-val-fault'
                          : 'plc-val-idle'
                      }
                    >
                      {snapshot.status?.plc.reject_actuator ?? 'IDLE'}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Event Logs */}
              <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <h2 style={{ marginBottom: '10px' }}>Operational Events log</h2>
                <div className="log-terminal" style={{ flex: 1, minHeight: '280px' }}>
                  {snapshot.logs.length > 0 ? (
                    snapshot.logs.map((log, idx) => <p key={idx}>{log}</p>)
                  ) : (
                    <p style={{ color: '#64748b' }}>Waiting for system events...</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'training' && (
          <div className="grid-training">
            <div>
              {/* Media viewer */}
              <div className="production-feed-viewer">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ margin: 0, fontSize: '15px', color: '#f8fafc' }}>Calibration & Sample Test</h2>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>
                    Source: <span style={{ color: '#38bdf8', fontWeight: 600 }}>{snapshot.status?.camera_name ?? 'USB Camera 0'}</span> | Prediction: {snapshot.station1?.system_prediction ?? 'N/A'} (Score:{' '}
                    {snapshot.station1?.anomaly_score ?? 'N/A'})
                  </span>
                </div>

                <div className="production-feed-layout">
                  <div className="feed-box">
                    <span>Target Sample Video / Camera</span>
                    <img src="/stream/station1" alt="Inspection Stream" />
                  </div>
                  <div className="feed-box">
                    <span>Captured Image Overlay</span>
                    {snapshot.station1?.captured_image_url ? (
                      <img
                        src={`${snapshot.station1.captured_image_url}?t=${Date.now()}`}
                        alt="Captured Result Overlay"
                      />
                    ) : (
                      <div className="no-img">No inspection image captured yet.</div>
                    )}
                  </div>
                </div>

                {/* Operator labeling confirmation buttons */}
                <div className="panel" style={{ background: '#11141b', border: '1px solid #232a36' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '12px'
                    }}
                  >
                    <span>Operator Dataset Label Assignment</span>
                    {snapshot.status?.pending_label ? (
                      <strong style={{ color: '#fbbf24', fontSize: '12px' }}>PENDING CONFIRMATION</strong>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '12px' }}>Idle</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button
                      className="button good"
                      style={{ flex: 1 }}
                      disabled={!snapshot.status?.pending_label}
                      onClick={() =>
                        runAction(() =>
                          postJson('/api/operator-label', { station: 'S1', operator_label: 'GOOD' })
                        )
                      }
                    >
                      <Check size={16} />
                      Confirm Good (PASS)
                    </button>
                    <button
                      className="button danger"
                      style={{ flex: 1 }}
                      disabled={!snapshot.status?.pending_label}
                      onClick={() =>
                        runAction(() =>
                          postJson('/api/operator-label', { station: 'S1', operator_label: 'DEFECTIVE' })
                        )
                      }
                    >
                      <X size={16} />
                      Mark Defective (FAIL)
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Operator dataset control panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="panel actions-panel" style={{ minHeight: 'auto' }}>
                <h2>Training Calibration Actions</h2>
                <div
                  className="action-grid"
                  style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '12px' }}
                >
                  <button className="button" onClick={() => runAction(() => postJson('/api/start-part'))}>
                    <RefreshCcw size={16} />
                    Start New Part
                  </button>
                  <button className="button" onClick={() => runAction(() => postJson('/api/reset'))}>
                    <ShieldCheck size={16} />
                    Reset Pipeline
                  </button>
                  <label className="button upload-button" style={{ display: 'flex', justifyContent: 'center' }}>
                    <Upload size={16} />
                    Upload Image
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) runAction(() => uploadImage('S1', file));
                        e.currentTarget.value = '';
                      }}
                    />
                  </label>
                  <label className="button upload-button" style={{ display: 'flex', justifyContent: 'center' }}>
                    <Video size={16} />
                    Upload Video
                    <input
                      type="file"
                      accept="video/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) runAction(() => uploadVideo('S1', file));
                        e.currentTarget.value = '';
                      }}
                    />
                  </label>
                  <button
                    className="button"
                    onClick={() => runAction(() => resetCamera('S1'))}
                    disabled={snapshot.status?.camera_name === 'USB Camera 0'}
                    style={{ gridColumn: 'span 2', justifyContent: 'center' }}
                  >
                    <Camera size={16} />
                    Reset to Live USB Camera
                  </button>
                </div>
              </div>

              {/* Dataset metrics */}
              <div className="plc-telemetry-panel">
                <h2 style={{ margin: 0, fontSize: '15px', color: '#f8fafc' }}>Dataset Collection Statistics</h2>
                <div className="plc-telemetry-grid">
                  <div className="plc-telemetry-item">
                    <span>Good Samples</span>
                    <strong>{snapshot.metrics?.dataset.total_good ?? 0}</strong>
                  </div>
                  <div className="plc-telemetry-item">
                    <span>Defect Samples</span>
                    <strong>{snapshot.metrics?.dataset.total_defective ?? 0}</strong>
                  </div>
                  <div className="plc-telemetry-item">
                    <span>Operator Corrections</span>
                    <strong style={{ color: '#fbbf24' }}>{snapshot.metrics?.dataset.operator_corrections ?? 0}</strong>
                  </div>
                  <div className="plc-telemetry-item">
                    <span>Accuracy Estimate</span>
                    <strong style={{ color: '#34d399' }}>
                      {snapshot.metrics?.dataset.system_accuracy_estimate
                        ? `${snapshot.metrics.dataset.system_accuracy_estimate}%`
                        : '0.00%'}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Defect report list */}
              <div className="panel" style={{ flex: 1 }}>
                <h2>Detected Defect Report</h2>
                <div className="defect-list" style={{ marginTop: '12px' }}>
                  {snapshot.station1?.defects && snapshot.station1.defects.length > 0 ? (
                    snapshot.station1.defects.map((defect, index) => <span key={index}>{defect}</span>)
                  ) : (
                    <span style={{ background: 'transparent', borderColor: 'transparent', color: '#64748b' }}>
                      No defects reported on latest run.
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="history-page">
            <div className="history-table-container">
              <div className="table-header-filters">
                <h2 style={{ margin: 0, fontSize: '16px' }}>Inspection Database Logs</h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search Part ID or Serial..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <select
                    className="select-input"
                    value={filterDecision}
                    onChange={(e: any) => setFilterDecision(e.target.value)}
                  >
                    <option value="ALL">All Decisions</option>
                    <option value="PASS">PASS Only</option>
                    <option value="FAIL">FAIL Only</option>
                  </select>
                  <select
                    className="select-input"
                    value={filterMode}
                    onChange={(e: any) => setFilterMode(e.target.value)}
                  >
                    <option value="ALL">All Modes</option>
                    <option value="PRODUCTION">PRODUCTION</option>
                    <option value="DATA_COLLECTION">DATA_COLLECTION</option>
                  </select>
                </div>
              </div>

              <table className="inspection-table">
                <thead>
                  <tr>
                    <th>Part ID</th>
                    <th>Serial Number</th>
                    <th>Timestamp</th>
                    <th>Mode</th>
                    <th>Decision</th>
                    <th>Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.length > 0 ? (
                    filteredHistory.map((item) => (
                      <tr
                        key={item.id}
                        className={selectedInspection?.id === item.id ? 'selected' : ''}
                        onClick={() => setSelectedInspection(item)}
                      >
                        <td><strong>{item.physical_part_id}</strong></td>
                        <td>{item.serial_number || '--'}</td>
                        <td>{new Date(item.inspected_at).toLocaleString()}</td>
                        <td>
                          <span
                            className={`table-badge ${
                              item.inspection_mode === 'PRODUCTION' ? 'prod' : 'train'
                            }`}
                          >
                            {item.inspection_mode}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`table-badge ${
                              item.decision === 'PASS' ? 'pass' : 'fail'
                            }`}
                          >
                            {item.decision}
                          </span>
                        </td>
                        <td>{item.cycle_time_ms ? `${item.cycle_time_ms} ms` : '--'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>
                        No matching inspection logs found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Selection details column */}
            <div>
              {selectedInspection ? (
                <div className="detail-inspector">
                  <div>
                    <h2 style={{ margin: 0, fontSize: '16px' }}>Part Details Inspector</h2>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      ID: {selectedInspection.physical_part_id}
                    </span>
                  </div>

                  {selectedInspection.overlay_path && (
                    <div>
                      <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Captured Image Overlay</span>
                      <img src={`/image/station1/overlay?t=${Date.now()}`} alt="Inspection Details" />
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #232a36', paddingBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Disposition</span>
                      <strong>{selectedInspection.final_disposition}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #232a36', paddingBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Source Name</span>
                      <strong>{selectedInspection.source_name || '--'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #232a36', paddingBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Hole Count</span>
                      <strong>{selectedInspection.measurements?.hole_count ?? '--'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #232a36', paddingBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Avg Hole Diam.</span>
                      <strong>{selectedInspection.measurements?.avg_hole_diameter_px ? `${selectedInspection.measurements.avg_hole_diameter_px} px` : '--'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #232a36', paddingBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Defect Area Ratio</span>
                      <strong>{selectedInspection.measurements?.surface_defect_area_ratio ? `${(Number(selectedInspection.measurements.surface_defect_area_ratio) * 100).toFixed(2)}%` : '--'}</strong>
                    </div>
                  </div>

                  <div>
                    <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
                      Inspection Defect Report
                    </span>
                    <div className="defect-list">
                      {selectedInspection.defects && selectedInspection.defects.length > 0 ? (
                        selectedInspection.defects.map((d, index) => <span key={index}>{d}</span>)
                      ) : (
                        <span style={{ background: 'transparent', borderColor: 'transparent', color: '#34d399' }}>
                          No defects detected.
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div
                  className="detail-inspector"
                  style={{ justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: '300px', color: '#64748b' }}
                >
                  <Database size={32} style={{ marginBottom: '10px' }} />
                  Select an inspection from the database log table to view details.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="settings-page">
            {/* Mode selection group */}
            <div className="settings-group">
              <h2 style={{ margin: 0, fontSize: '16px', color: '#f8fafc' }}>System Operations Mode</h2>
              <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
                Toggle the active operation mode of the single station disc inspection camera loop.
              </p>
              <div className="mode-selectors">
                <div
                  className={`mode-card ${
                    snapshot.status?.mode === 'PRODUCTION' ? 'selected' : ''
                  }`}
                  onClick={() => handleModeChange('PRODUCTION')}
                >
                  <h3>PRODUCTION</h3>
                  <p>Fully automated runs, signals PLC actuators automatically, hides labeling actions.</p>
                </div>
                <div
                  className={`mode-card ${
                    snapshot.status?.mode === 'DATA_COLLECTION' ? 'selected' : ''
                  }`}
                  onClick={() => handleModeChange('DATA_COLLECTION')}
                >
                  <h3>DATA COLLECTION (TRAINING)</h3>
                  <p>Enables operator ground-truth labeling, captures and persists training samples.</p>
                </div>
              </div>
            </div>

            {/* Tolerances tuning form */}
            {tolerances ? (
              <form className="settings-group" onSubmit={handleSaveTolerances}>
                <h2 style={{ margin: 0, fontSize: '16px', color: '#f8fafc' }}>Inspection Tolerances tuning</h2>
                <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
                  Tune geometric parameters and defect detection limits on the shop-floor.
                </p>

                {settingsSuccess && (
                  <div className="alert" style={{ background: '#10b981', borderColor: '#34d399', color: '#e7fff5' }}>
                    Tolerances settings saved successfully.
                  </div>
                )}

                <div className="settings-grid">
                  <div className="settings-field">
                    <label>Expected Hole Count</label>
                    <input
                      type="number"
                      value={tolerances.expected_hole_count}
                      onChange={(e) =>
                        setTolerances({ ...tolerances, expected_hole_count: parseInt(e.target.value) || 0 })
                      }
                    />
                  </div>
                  <div className="settings-field">
                    <label>Hole Circularity Limit (min)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={tolerances.hole_circularity_min}
                      onChange={(e) =>
                        setTolerances({ ...tolerances, hole_circularity_min: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </div>
                  <div className="settings-field">
                    <label>Outer Radius Min (px)</label>
                    <input
                      type="number"
                      value={tolerances.outer_radius_px?.min || 0}
                      onChange={(e) =>
                        setTolerances({
                          ...tolerances,
                          outer_radius_px: { ...tolerances.outer_radius_px, min: parseInt(e.target.value) || 0 }
                        })
                      }
                    />
                  </div>
                  <div className="settings-field">
                    <label>Outer Radius Max (px)</label>
                    <input
                      type="number"
                      value={tolerances.outer_radius_px?.max || 0}
                      onChange={(e) =>
                        setTolerances({
                          ...tolerances,
                          outer_radius_px: { ...tolerances.outer_radius_px, max: parseInt(e.target.value) || 0 }
                        })
                      }
                    />
                  </div>
                  <div className="settings-field">
                    <label>Min Surface Defect Area (px)</label>
                    <input
                      type="number"
                      value={tolerances.surface?.min_defect_area_px || 0}
                      onChange={(e) =>
                        setTolerances({
                          ...tolerances,
                          surface: { ...tolerances.surface, min_defect_area_px: parseInt(e.target.value) || 0 }
                        })
                      }
                    />
                  </div>
                  <div className="settings-field">
                    <label>Max Defect Area Ratio</label>
                    <input
                      type="number"
                      step="0.01"
                      value={tolerances.surface?.max_total_defect_area_ratio || 0}
                      onChange={(e) =>
                        setTolerances({
                          ...tolerances,
                          surface: { ...tolerances.surface, max_total_defect_area_ratio: parseFloat(e.target.value) || 0 }
                        })
                      }
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                  <button type="submit" className="button good" disabled={savingTolerances}>
                    {savingTolerances ? 'Saving...' : 'Save Settings'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="settings-group" style={{ alignItems: 'center', padding: '40px', color: '#64748b' }}>
                Loading tolerance parameters from tolerances.json...
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
