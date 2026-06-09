import { CheckCircle, AlertTriangle, Download, ShieldCheck, RefreshCcw } from 'lucide-react';
import type { CalibrationStatus } from '../../types/calibration';

interface CalibrationStatusBannerProps {
  status: CalibrationStatus | null;
  cameraId: string;
  onDownloadReport: () => void;
  onToggleValidate: () => void;
  onRefresh: () => void;
}

export function CalibrationStatusBanner({
  status,
  cameraId,
  onDownloadReport,
  onToggleValidate,
  onRefresh,
}: CalibrationStatusBannerProps) {
  return (
    <div className={`cal-status-banner ${status?.calibrated ? 'calibrated' : 'uncalibrated'}`}>
      <div className="cal-status-icon">
        {status?.calibrated ? <CheckCircle size={28} /> : <AlertTriangle size={28} />}
      </div>
      <div className="cal-status-text">
        <strong>
          {status?.calibrated ? '✓ Camera Calibrated' : '⚠ Calibration Required'}
        </strong>
        {status?.calibrated && (
          <span>
            Scale: <b>{status.mm_per_pixel?.toFixed(6)} mm/pixel</b>
            &nbsp;·&nbsp;Last: {status.calibration_date ? new Date(status.calibration_date).toLocaleString() : 'N/A'}
            &nbsp;·&nbsp;Ref OD: {status.reference_od_mm} mm
          </span>
        )}
        {!status?.calibrated && (
          <span>
            Place a certified reference disc under the camera and run the calibration wizard below.
          </span>
        )}
      </div>
      <div className="cal-status-actions">
        <button className="button" onClick={onDownloadReport} title="Download PDF Report">
          <Download size={14} /> PDF Report
        </button>
        <button className="button" onClick={onToggleValidate} title="Validate Calibration">
          <ShieldCheck size={14} /> Validate
        </button>
        <button className="button" onClick={onRefresh} title="Refresh Status">
          <RefreshCcw size={14} />
        </button>
      </div>
    </div>
  );
}
