import React, { useCallback } from 'react';
import { Download, RotateCcw } from 'lucide-react';
import { useSettingsContext } from '../../contexts/SettingsContext';
import type { ToleranceSettings } from '../../types/settings';
import { defaultTolerances } from '../../types/settings';

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <span style={{ color: '#ef4444', fontSize: '11px', marginTop: '2px' }}>
      {message}
    </span>
  );
}

export const ToleranceForm = React.memo(function ToleranceForm() {
  const {
    tolerances,
    setTolerances,
    saving,
    success,
    validationErrors,
    save,
    reload,
  } = useSettingsContext();

  const patch = useCallback(
    (partial: Partial<ToleranceSettings>) => {
      setTolerances((prev) => (prev ? { ...prev, ...partial } : prev));
    },
    [setTolerances],
  );

  const handleRestoreDefaults = useCallback(() => {
    setTolerances(defaultTolerances);
  }, [setTolerances]);

  const handleBackupSettings = useCallback(() => {
    if (!tolerances) return;
    const json = JSON.stringify(tolerances, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tolerances_backup.json';
    a.click();
    URL.revokeObjectURL(url);
  }, [tolerances]);

  if (!tolerances) {
    return (
      <div
        className="settings-group"
        style={{ alignItems: 'center', padding: '40px', color: '#64748b' }}
      >
        Loading tolerance parameters from tolerances.json...
      </div>
    );
  }

  return (
    <form className="settings-group" onSubmit={(e) => { void save(e); }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: '16px', color: '#f8fafc' }}>
            Inspection Tolerances Tuning
          </h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
            Tune geometric parameters and defect detection limits on the
            shop-floor.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="button"
            onClick={handleBackupSettings}
            title="Backup current settings as JSON"
            style={{ fontSize: '12px', padding: '4px 10px' }}
          >
            <Download size={13} /> Backup
          </button>
          <button
            type="button"
            id="btn-restore-defaults"
            className="button"
            onClick={handleRestoreDefaults}
            title="Restore factory defaults"
            style={{ fontSize: '12px', padding: '4px 10px' }}
          >
            <RotateCcw size={13} /> Restore Defaults
          </button>
          <button
            type="button"
            className="button"
            onClick={() => { void reload(); }}
            title="Reload from server"
            style={{ fontSize: '12px', padding: '4px 10px' }}
          >
            Reload
          </button>
        </div>
      </div>

      {success && (
        <div
          className="alert"
          style={{
            background: '#10b981',
            borderColor: '#34d399',
            color: '#e7fff5',
          }}
        >
          Tolerances settings saved successfully.
        </div>
      )}

      <div className="settings-grid">
        {/* Expected Hole Count */}
        <div className="settings-field">
          <label htmlFor="tol-hole-count">Expected Hole Count</label>
          <input
            id="tol-hole-count"
            type="number"
            min={1}
            value={tolerances.expected_hole_count}
            onChange={(e) =>
              patch({ expected_hole_count: parseInt(e.target.value) || 0 })
            }
          />
          <FieldError message={validationErrors.expected_hole_count} />
        </div>

        {/* Hole Circularity Min */}
        <div className="settings-field">
          <label htmlFor="tol-circularity">Hole Circularity Limit (min)</label>
          <input
            id="tol-circularity"
            type="number"
            step="0.01"
            min={0}
            max={1}
            value={tolerances.hole_circularity_min}
            onChange={(e) =>
              patch({ hole_circularity_min: parseFloat(e.target.value) || 0 })
            }
          />
          <FieldError message={validationErrors.hole_circularity_min} />
        </div>

        {/* Outer Radius Min */}
        <div className="settings-field">
          <label htmlFor="tol-radius-min">Outer Radius Min (px)</label>
          <input
            id="tol-radius-min"
            type="number"
            min={0}
            value={tolerances.outer_radius_px.min}
            onChange={(e) =>
              patch({
                outer_radius_px: {
                  ...tolerances.outer_radius_px,
                  min: parseInt(e.target.value) || 0,
                },
              })
            }
          />
          <FieldError message={validationErrors.outer_radius_px_min} />
        </div>

        {/* Outer Radius Max */}
        <div className="settings-field">
          <label htmlFor="tol-radius-max">Outer Radius Max (px)</label>
          <input
            id="tol-radius-max"
            type="number"
            min={0}
            value={tolerances.outer_radius_px.max}
            onChange={(e) =>
              patch({
                outer_radius_px: {
                  ...tolerances.outer_radius_px,
                  max: parseInt(e.target.value) || 0,
                },
              })
            }
          />
          <FieldError message={validationErrors.outer_radius_px_max} />
        </div>

        {/* Min Surface Defect Area */}
        <div className="settings-field">
          <label htmlFor="tol-defect-area">Min Surface Defect Area (px)</label>
          <input
            id="tol-defect-area"
            type="number"
            min={1}
            value={tolerances.surface.min_defect_area_px}
            onChange={(e) =>
              patch({
                surface: {
                  ...tolerances.surface,
                  min_defect_area_px: parseInt(e.target.value) || 0,
                },
              })
            }
          />
          <FieldError message={validationErrors.surface_min_defect_area_px} />
        </div>

        {/* Max Defect Area Ratio */}
        <div className="settings-field">
          <label htmlFor="tol-defect-ratio">Max Defect Area Ratio</label>
          <input
            id="tol-defect-ratio"
            type="number"
            step="0.01"
            min={0}
            max={1}
            value={tolerances.surface.max_total_defect_area_ratio}
            onChange={(e) =>
              patch({
                surface: {
                  ...tolerances.surface,
                  max_total_defect_area_ratio: parseFloat(e.target.value) || 0,
                },
              })
            }
          />
          <FieldError
            message={validationErrors.surface_max_total_defect_area_ratio}
          />
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
        <button
          id="btn-save-tolerances"
          type="submit"
          className="button good"
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </form>
  );
});
