import { useState, useEffect, useRef } from 'react';
import {
  Camera,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
  RefreshCcw,
  Download,
  Trash2,
  Upload,
  ZoomIn,
  Target,
  Ruler,
  ShieldCheck,
} from 'lucide-react';
import {
  CalibrationStatus,
  CalibrationCaptureResult,
  CalibrationRecord,
  ValidationResult,
  getCalibrationStatus,
  captureLiveCalibration,
  uploadCalibrationImage,
  saveCalibration,
  getCalibrationHistory,
  deleteCalibration,
  validateCalibration,
  downloadCalibrationReport,
} from './api';

type Step = 1 | 2 | 3 | 4;

const STEPS = [
  { id: 1, label: 'Capture', icon: Camera },
  { id: 2, label: 'Detect', icon: ZoomIn },
  { id: 3, label: 'Dimensions', icon: Ruler },
  { id: 4, label: 'Save', icon: CheckCircle },
];

export function CalibrationPage() {
  const [status, setStatus] = useState<CalibrationStatus | null>(null);
  const [history, setHistory] = useState<CalibrationRecord[]>([]);
  const [step, setStep] = useState<Step>(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [captureResult, setCaptureResult] = useState<CalibrationCaptureResult | null>(null);
  const [refOd, setRefOd] = useState('100.00');
  const [refHole, setRefHole] = useState('20.00');
  const [cameraId] = useState('CAM01');
  const [saveResult, setSaveResult] = useState<{ mm_per_pixel: number } | null>(null);
  const [validating, setValidating] = useState(false);
  const [valTolerance, setValTolerance] = useState('0.10');
  const [valRefOd, setValRefOd] = useState('100.00');
  const [valResult, setValResult] = useState<ValidationResult | null>(null);
  const [showValidate, setShowValidate] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const reload = async () => {
    try {
      const [s, h] = await Promise.all([
        getCalibrationStatus(cameraId),
        getCalibrationHistory(cameraId),
      ]);
      setStatus(s);
      setHistory(h);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => { reload(); }, []);

  const handleCaptureLive = async () => {
    setBusy(true); setError(null);
    try {
      const result = await captureLiveCalibration();
      setCaptureResult(result);
      setStep(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setBusy(false); }
  };

  const handleUploadImage = async (file: File) => {
    setBusy(true); setError(null);
    try {
      const result = await uploadCalibrationImage(file);
      setCaptureResult(result);
      setStep(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setBusy(false); }
  };

  const handleProceedToDimensions = () => setStep(3);

  const handleSave = async () => {
    if (!captureResult) return;
    const od = parseFloat(refOd);
    const hole = parseFloat(refHole);
    if (!od || !hole || od <= 0 || hole <= 0) {
      setError('Please enter valid positive dimensions.');
      return;
    }
    setBusy(true); setError(null);
    try {
      const res = await saveCalibration(cameraId, captureResult.outer_diameter_px, od, hole);
      setSaveResult(res);
      setStep(4);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setBusy(false); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Deactivate this calibration record?')) return;
    try {
      await deleteCalibration(id);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleValidate = async () => {
    setValidating(true); setError(null); setValResult(null);
    try {
      const res = await validateCalibration(cameraId, parseFloat(valRefOd), parseFloat(valTolerance));
      setValResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setValidating(false); }
  };

  const resetWizard = () => {
    setStep(1); setCaptureResult(null); setSaveResult(null); setError(null);
  };

  return (
    <div className="calibration-page">
      {/* ── Status Banner ── */}
      <div className={`cal-status-banner ${status?.calibrated ? 'calibrated' : 'uncalibrated'}`}>
        <div className="cal-status-icon">
          {status?.calibrated ? <CheckCircle size={28} /> : <AlertTriangle size={28} />}
        </div>
        <div className="cal-status-text">
          <strong>{status?.calibrated ? '✓ Camera Calibrated' : '⚠ Calibration Required'}</strong>
          {status?.calibrated && (
            <span>
              Scale: <b>{status.mm_per_pixel?.toFixed(6)} mm/pixel</b>
              &nbsp;·&nbsp;Last: {status.calibration_date
                ? new Date(status.calibration_date).toLocaleString()
                : 'N/A'}
              &nbsp;·&nbsp;Ref OD: {status.reference_od_mm} mm
            </span>
          )}
          {!status?.calibrated && (
            <span>Place a certified reference disc under the camera and run the calibration wizard below.</span>
          )}
        </div>
        <div className="cal-status-actions">
          <button
            className="button"
            onClick={() => downloadCalibrationReport(cameraId)}
            title="Download PDF Report"
          >
            <Download size={14} /> PDF Report
          </button>
          <button
            className="button"
            onClick={() => setShowValidate(v => !v)}
            title="Validate Calibration"
          >
            <ShieldCheck size={14} /> Validate
          </button>
          <button className="button" onClick={reload} title="Refresh Status">
            <RefreshCcw size={14} />
          </button>
        </div>
      </div>

      {error && <div className="cal-error"><AlertTriangle size={14} /> {error}</div>}

      {/* ── Validation Widget ── */}
      {showValidate && (
        <div className="cal-panel">
          <h3 className="cal-panel-title"><ShieldCheck size={16} /> Validate Active Calibration</h3>
          <div className="cal-validate-form">
            <div className="cal-field">
              <label>Reference OD (mm)</label>
              <input type="number" step="0.01" value={valRefOd}
                onChange={e => setValRefOd(e.target.value)} />
            </div>
            <div className="cal-field">
              <label>Tolerance ± (mm)</label>
              <input type="number" step="0.01" value={valTolerance}
                onChange={e => setValTolerance(e.target.value)} />
            </div>
            <button className="button good" onClick={handleValidate} disabled={validating}>
              {validating ? 'Running...' : 'Run Validation'}
            </button>
          </div>
          {valResult && (
            <div className={`cal-validation-result ${valResult.passed ? 'pass' : 'fail'}`}>
              <div className="val-row"><span>Expected OD</span><strong>{valResult.expected_mm} mm</strong></div>
              <div className="val-row"><span>Measured OD</span><strong>{valResult.measured_mm} mm</strong></div>
              <div className="val-row"><span>Error</span><strong>{valResult.error_mm} mm</strong></div>
              <div className="val-row"><span>Tolerance</span><strong>± {valResult.tolerance} mm</strong></div>
              <div className={`val-verdict ${valResult.passed ? 'pass' : 'fail'}`}>
                {valResult.passed ? '✓ PASS' : '✗ FAIL'}
              </div>
              {valResult.overlay_image && (
                <img src={valResult.overlay_image} alt="Validation Overlay"
                  className="cal-overlay-img" />
              )}
            </div>
          )}
        </div>
      )}

      <div className="cal-main-grid">
        {/* ── Calibration Wizard ── */}
        <div className="cal-wizard-panel">
          {/* Stepper */}
          <div className="cal-stepper">
            {STEPS.map((s, idx) => (
              <div key={s.id} className="cal-step-wrapper">
                <div className={`cal-step ${step === s.id ? 'active' : step > s.id ? 'done' : ''}`}>
                  <div className="cal-step-circle">
                    {step > s.id ? <CheckCircle size={16} /> : <s.icon size={16} />}
                  </div>
                  <span>{s.label}</span>
                </div>
                {idx < STEPS.length - 1 && (
                  <ChevronRight size={16} className={`cal-step-arrow ${step > s.id ? 'done' : ''}`} />
                )}
              </div>
            ))}
          </div>

          {/* Step 1 – Capture */}
          {step === 1 && (
            <div className="cal-step-content">
              <h3 className="cal-step-heading"><Camera size={18} /> Step 1: Capture Calibration Image</h3>
              <p className="cal-step-desc">
                Place a certified reference disc under the camera. Then capture the live frame
                or upload a pre-recorded image.
              </p>
              <div className="cal-ref-example">
                <div className="cal-ref-badge"><Target size={14} /> Reference Disc Example</div>
                <div className="cal-ref-specs">
                  <span>Outer Diameter: <b>100.00 mm</b></span>
                  <span>Center Hole: <b>20.00 mm</b></span>
                </div>
              </div>
              <div className="cal-capture-actions">
                <button className="button good cal-big-btn" onClick={handleCaptureLive} disabled={busy}>
                  <Camera size={18} />
                  {busy ? 'Capturing...' : 'Capture Live Frame'}
                </button>
                <span className="cal-or">or</span>
                <button className="button cal-big-btn" onClick={() => fileInputRef.current?.click()} disabled={busy}>
                  <Upload size={18} /> Upload Image
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={e => { if (e.target.files?.[0]) handleUploadImage(e.target.files[0]); }}
                />
              </div>
              <div className="cal-live-preview">
                <span className="cal-feed-label">Live Camera Feed</span>
                <img src="/stream/station1" alt="Live Preview" className="cal-live-stream" />
              </div>
            </div>
          )}

          {/* Step 2 – Detect */}
          {step === 2 && captureResult && (
            <div className="cal-step-content">
              <h3 className="cal-step-heading"><ZoomIn size={18} /> Step 2: Circle Detection Results</h3>
              <p className="cal-step-desc">
                System detected the following pixel dimensions. Verify the overlay looks correct.
              </p>
              <div className="cal-detect-grid">
                <div className="cal-detect-card">
                  <span>Detected Outer Diameter</span>
                  <strong>{captureResult.outer_diameter_px.toFixed(1)} px</strong>
                </div>
                <div className="cal-detect-card">
                  <span>Detected Hole Diameter</span>
                  <strong>{captureResult.hole_diameter_px.toFixed(1)} px</strong>
                </div>
              </div>
              <img src={captureResult.overlay_image} alt="Detection Overlay" className="cal-overlay-img" />
              <div className="cal-step-actions">
                <button className="button" onClick={resetWizard}>← Re-capture</button>
                <button className="button good" onClick={handleProceedToDimensions}>
                  Proceed to Dimensions <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}

          {/* Step 3 – Enter Dimensions */}
          {step === 3 && captureResult && (
            <div className="cal-step-content">
              <h3 className="cal-step-heading"><Ruler size={18} /> Step 3: Enter Actual Dimensions</h3>
              <p className="cal-step-desc">
                Enter the certified physical dimensions of the reference disc.
              </p>
              <div className="cal-dim-grid">
                <div className="cal-field">
                  <label>Actual Outer Diameter (mm)</label>
                  <input type="number" step="0.01" min="1" value={refOd}
                    onChange={e => setRefOd(e.target.value)} />
                </div>
                <div className="cal-field">
                  <label>Actual Center Hole Diameter (mm)</label>
                  <input type="number" step="0.01" min="1" value={refHole}
                    onChange={e => setRefHole(e.target.value)} />
                </div>
              </div>
              <div className="cal-scale-preview">
                <span>Calculated Scale Factor:</span>
                <strong className="cal-scale-value">
                  {captureResult.outer_diameter_px > 0
                    ? (parseFloat(refOd) / captureResult.outer_diameter_px).toFixed(6)
                    : '--'} mm/pixel
                </strong>
                <span className="cal-scale-formula">
                  = {refOd} mm ÷ {captureResult.outer_diameter_px.toFixed(1)} px
                </span>
              </div>
              <div className="cal-step-actions">
                <button className="button" onClick={() => setStep(2)}>← Back</button>
                <button className="button good" onClick={handleSave} disabled={busy}>
                  {busy ? 'Saving...' : 'Save Calibration ✓'}
                </button>
              </div>
            </div>
          )}

          {/* Step 4 – Complete */}
          {step === 4 && saveResult && (
            <div className="cal-step-content cal-success-screen">
              <div className="cal-success-icon"><CheckCircle size={64} /></div>
              <h3>Calibration Saved Successfully!</h3>
              <p>Camera <b>{cameraId}</b> is now calibrated.</p>
              <div className="cal-success-metric">
                <span>Scale Factor</span>
                <strong>{saveResult.mm_per_pixel.toFixed(6)} mm/pixel</strong>
              </div>
              <p className="cal-success-note">
                All future inspections will report measurements in millimeters.
              </p>
              <button className="button good" onClick={resetWizard}>
                <RefreshCcw size={14} /> Recalibrate
              </button>
            </div>
          )}
        </div>

        {/* ── History Table ── */}
        <div className="cal-history-panel">
          <div className="cal-panel-header">
            <h3 className="cal-panel-title">Calibration History</h3>
            <button className="button" onClick={reload} title="Refresh">
              <RefreshCcw size={14} />
            </button>
          </div>
          {history.length === 0 ? (
            <div className="cal-empty">No calibration records found.</div>
          ) : (
            <div className="cal-history-table-wrap">
              <table className="cal-history-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>mm/pixel</th>
                    <th>Ref OD</th>
                    <th>Ref Hole</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(rec => (
                    <tr key={rec.id} className={rec.active ? 'cal-row-active' : ''}>
                      <td>{rec.id}</td>
                      <td>{new Date(rec.calibration_date).toLocaleString()}</td>
                      <td className="cal-mono">{rec.mm_per_pixel.toFixed(6)}</td>
                      <td>{rec.reference_od_mm} mm</td>
                      <td>{rec.reference_hole_mm} mm</td>
                      <td>
                        {rec.active
                          ? <span className="cal-badge active">ACTIVE</span>
                          : <span className="cal-badge inactive">inactive</span>
                        }
                      </td>
                      <td>
                        <button
                          className="cal-delete-btn"
                          onClick={() => handleDelete(rec.id)}
                          title="Deactivate"
                          disabled={!rec.active}
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="cal-history-footer">
            <button className="button" onClick={() => downloadCalibrationReport(cameraId)}>
              <Download size={14} /> Download PDF Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
