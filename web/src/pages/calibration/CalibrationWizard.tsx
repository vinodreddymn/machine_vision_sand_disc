import { useRef } from 'react';
import { Camera, ZoomIn, Ruler, CheckCircle, ChevronRight, Target, Upload, RefreshCcw } from 'lucide-react';
import type { CalibrationCaptureResult, CalibrationSaveResult } from '../../types/calibration';

type Step = 1 | 2 | 3 | 4;

const STEPS = [
  { id: 1 as Step, label: 'Capture', icon: Camera },
  { id: 2 as Step, label: 'Detect', icon: ZoomIn },
  { id: 3 as Step, label: 'Dimensions', icon: Ruler },
  { id: 4 as Step, label: 'Save', icon: CheckCircle },
];

interface CalibrationWizardProps {
  step: Step;
  captureResult: CalibrationCaptureResult | null;
  saveResult: CalibrationSaveResult | null;
  refOd: string;
  refHole: string;
  busy: boolean;
  cameraId: string;
  onSetStep: (step: Step) => void;
  onCaptureLive: () => void;
  onUploadImage: (file: File) => void;
  onRefOdChange: (val: string) => void;
  onRefHoleChange: (val: string) => void;
  onSave: () => void;
  onReset: () => void;
}

export function CalibrationWizard({
  step,
  captureResult,
  saveResult,
  refOd,
  refHole,
  busy,
  cameraId,
  onSetStep,
  onCaptureLive,
  onUploadImage,
  onRefOdChange,
  onRefHoleChange,
  onSave,
  onReset,
}: CalibrationWizardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
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
            Place a certified reference disc under the camera. Then capture the live frame or upload a pre-recorded image.
          </p>
          <div className="cal-ref-example">
            <div className="cal-ref-badge"><Target size={14} /> Reference Disc Example</div>
            <div className="cal-ref-specs">
              <span>Outer Diameter: <b>100.00 mm</b></span>
              <span>Center Hole: <b>20.00 mm</b></span>
            </div>
          </div>
          <div className="cal-capture-actions">
            <button className="button good cal-big-btn" onClick={onCaptureLive} disabled={busy}>
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
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  onUploadImage(e.target.files[0]);
                }
              }}
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
            <button className="button" onClick={onReset}>← Re-capture</button>
            <button className="button good" onClick={() => onSetStep(3)}>
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
              <input type="number" step="0.01" min="1" value={refOd} onChange={(e) => onRefOdChange(e.target.value)} />
            </div>
            <div className="cal-field">
              <label>Actual Center Hole Diameter (mm)</label>
              <input type="number" step="0.01" min="1" value={refHole} onChange={(e) => onRefHoleChange(e.target.value)} />
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
            <button className="button" onClick={() => onSetStep(2)}>← Back</button>
            <button className="button good" onClick={onSave} disabled={busy}>
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
          <button className="button good" onClick={onReset}><RefreshCcw size={14} /> Recalibrate</button>
        </div>
      )}
    </div>
  );
}
