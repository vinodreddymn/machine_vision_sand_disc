import { ShieldCheck } from 'lucide-react';
import type { ValidationResult } from '../../types/calibration';

interface CalibrationValidateWidgetProps {
  valRefOd: string;
  valTolerance: string;
  validating: boolean;
  valResult: ValidationResult | null;
  onValRefOdChange: (val: string) => void;
  onValToleranceChange: (val: string) => void;
  onValidate: () => void;
}

export function CalibrationValidateWidget({
  valRefOd,
  valTolerance,
  validating,
  valResult,
  onValRefOdChange,
  onValToleranceChange,
  onValidate,
}: CalibrationValidateWidgetProps) {
  return (
    <div className="cal-panel">
      <h3 className="cal-panel-title">
        <ShieldCheck size={16} /> Validate Active Calibration
      </h3>
      <div className="cal-validate-form">
        <div className="cal-field">
          <label>Reference OD (mm)</label>
          <input
            type="number"
            step="0.01"
            value={valRefOd}
            onChange={(e) => onValRefOdChange(e.target.value)}
          />
        </div>
        <div className="cal-field">
          <label>Tolerance ± (mm)</label>
          <input
            type="number"
            step="0.01"
            value={valTolerance}
            onChange={(e) => onValToleranceChange(e.target.value)}
          />
        </div>
        <button className="button good" onClick={onValidate} disabled={validating}>
          {validating ? 'Running...' : 'Run Validation'}
        </button>
      </div>
      {valResult && (
        <div className={`cal-validation-result ${valResult.passed ? 'pass' : 'fail'}`}>
          <div className="val-row">
            <span>Expected OD</span>
            <strong>{valResult.expected_mm} mm</strong>
          </div>
          <div className="val-row">
            <span>Measured OD</span>
            <strong>{valResult.measured_mm} mm</strong>
          </div>
          <div className="val-row">
            <span>Error</span>
            <strong>{valResult.error_mm} mm</strong>
          </div>
          <div className="val-row">
            <span>Tolerance</span>
            <strong>± {valResult.tolerance} mm</strong>
          </div>
          <div className={`val-verdict ${valResult.passed ? 'pass' : 'fail'}`}>
            {valResult.passed ? '✓ PASS' : '✗ FAIL'}
          </div>
          {valResult.overlay_image && (
            <img
              src={valResult.overlay_image}
              alt="Validation Overlay"
              className="cal-overlay-img"
            />
          )}
        </div>
      )}
    </div>
  );
}
