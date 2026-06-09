import { useState, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';
import {
  getCalibrationStatus,
  captureLiveCalibration,
  uploadCalibrationImage,
  saveCalibration,
  getCalibrationHistory,
  deleteCalibration,
  validateCalibration,
  downloadCalibrationReport,
} from '../../services/calibrationService';
import type {
  CalibrationStatus,
  CalibrationCaptureResult,
  CalibrationRecord,
  ValidationResult,
  CalibrationSaveResult,
} from '../../types/calibration';

import { CalibrationStatusBanner } from './CalibrationStatusBanner';
import { CalibrationValidateWidget } from './CalibrationValidateWidget';
import { CalibrationWizard } from './CalibrationWizard';
import { CalibrationHistoryTable } from './CalibrationHistoryTable';

type Step = 1 | 2 | 3 | 4;

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
  const [saveResult, setSaveResult] = useState<CalibrationSaveResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [valTolerance, setValTolerance] = useState('0.10');
  const [valRefOd, setValRefOd] = useState('100.00');
  const [valResult, setValResult] = useState<ValidationResult | null>(null);
  const [showValidate, setShowValidate] = useState(false);

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

  useEffect(() => {
    void reload();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCaptureLive = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await captureLiveCalibration();
      setCaptureResult(result);
      setStep(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleUploadImage = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const result = await uploadCalibrationImage(file);
      setCaptureResult(result);
      setStep(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    if (!captureResult) return;
    const od = parseFloat(refOd);
    const hole = parseFloat(refHole);
    if (!od || !hole || od <= 0 || hole <= 0) {
      setError('Please enter valid positive dimensions.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await saveCalibration(cameraId, captureResult.outer_diameter_px, od, hole);
      setSaveResult(res);
      setStep(4);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
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
    setValidating(true);
    setError(null);
    setValResult(null);
    try {
      const res = await validateCalibration(cameraId, parseFloat(valRefOd), parseFloat(valTolerance));
      setValResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setValidating(false);
    }
  };

  const resetWizard = () => {
    setStep(1);
    setCaptureResult(null);
    setSaveResult(null);
    setError(null);
  };

  return (
    <div className="calibration-page">
      <CalibrationStatusBanner
        status={status}
        cameraId={cameraId}
        onDownloadReport={() => downloadCalibrationReport(cameraId)}
        onToggleValidate={() => setShowValidate((v) => !v)}
        onRefresh={() => { void reload(); }}
      />

      {error && (
        <div className="cal-error">
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      {showValidate && (
        <CalibrationValidateWidget
          valRefOd={valRefOd}
          valTolerance={valTolerance}
          validating={validating}
          valResult={valResult}
          onValRefOdChange={setValRefOd}
          onValToleranceChange={setValTolerance}
          onValidate={() => { void handleValidate(); }}
        />
      )}

      <div className="cal-main-grid">
        <CalibrationWizard
          step={step}
          captureResult={captureResult}
          saveResult={saveResult}
          refOd={refOd}
          refHole={refHole}
          busy={busy}
          cameraId={cameraId}
          onSetStep={setStep}
          onCaptureLive={() => { void handleCaptureLive(); }}
          onUploadImage={(f) => { void handleUploadImage(f); }}
          onRefOdChange={setRefOd}
          onRefHoleChange={setRefHole}
          onSave={() => { void handleSave(); }}
          onReset={resetWizard}
        />

        <CalibrationHistoryTable
          history={history}
          cameraId={cameraId}
          onReload={() => { void reload(); }}
          onDelete={(id) => { void handleDelete(id); }}
          onDownloadReport={() => downloadCalibrationReport(cameraId)}
        />
      </div>
    </div>
  );
}
