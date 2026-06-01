import React, { useEffect, useState } from 'react';
import { Trash2, AlertTriangle, CheckCircle, XCircle, Database, Images } from 'lucide-react';
import { getCleanupStatus, executeCleanup, formatSize, type DatasetStatus, type CleanupResult } from '../../services/cleanupService';
import '../../styles/cleanup-manager.css';

interface CleanupManagerProps {
  onCleanupComplete?: (result: CleanupResult) => void;
}

export const CleanupManager = React.memo(function CleanupManager({ onCleanupComplete }: CleanupManagerProps) {
  const [status, setStatus] = useState<DatasetStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [cleanupOptions, setCleanupOptions] = useState({
    cleanDataset: true,
    cleanOutputs: false,
    cleanDatabase: false,
  });
  const [result, setResult] = useState<CleanupResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load status on mount
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const data = await getCleanupStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cleanup status');
    } finally {
      setLoading(false);
    }
  };

  const handleCleanup = async () => {
    if (!showConfirmation) {
      setShowConfirmation(true);
      return;
    }

    try {
      setExecuting(true);
      setError(null);
      const cleanupResult = await executeCleanup(cleanupOptions);
      setResult(cleanupResult);
      onCleanupComplete?.(cleanupResult);

      // Refresh status after cleanup completes
      setTimeout(() => fetchStatus(), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cleanup failed');
    } finally {
      setExecuting(false);
      setShowConfirmation(false);
    }
  };

  if (loading && !status) {
    return <div className="cleanup-panel loading">Loading data status...</div>;
  }

  if (!status) {
    return <div className="cleanup-panel error">Failed to load data status</div>;
  }

  const totalSize = status.training_data.size_mb + status.inspection_outputs.size_mb;
  const cleanupSize =
    (cleanupOptions.cleanDataset ? status.training_data.size_mb : 0) +
    (cleanupOptions.cleanOutputs ? status.inspection_outputs.size_mb : 0);

  return (
    <div className="cleanup-panel">
      <div className="cleanup-header">
        <Trash2 size={20} />
        <h3>AI Training Data Cleanup</h3>
      </div>

      {error && (
        <div className="cleanup-error">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className={`cleanup-result ${result.status}`}>
          <div className="result-header">
            {result.status === 'success' ? (
              <>
                <CheckCircle size={20} />
                <span>Cleanup Completed Successfully</span>
              </>
            ) : (
              <>
                <XCircle size={20} />
                <span>Cleanup Failed</span>
              </>
            )}
          </div>
          <div className="result-output">
            <pre>{result.output}</pre>
          </div>
          <button
            className="result-close-btn"
            onClick={() => setResult(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {!result && (
        <>
          {/* Data Status Cards */}
          <div className="status-cards">
            <div className="status-card">
              <div className="card-icon training">
                <Images size={24} />
              </div>
              <div className="card-content">
                <div className="card-label">Training Dataset</div>
                <div className="card-value">{status.training_data.total_images} images</div>
                <div className="card-size">{formatSize(status.training_data.size_mb)}</div>
                <div className="card-breakdown">
                  <span>Good: {status.training_data.good_images}</span>
                  <span>Defect: {status.training_data.defect_images}</span>
                </div>
              </div>
            </div>

            <div className="status-card">
              <div className="card-icon outputs">
                <Images size={24} />
              </div>
              <div className="card-content">
                <div className="card-label">Inspection Outputs</div>
                <div className="card-value">{status.inspection_outputs.total_images} images</div>
                <div className="card-size">{formatSize(status.inspection_outputs.size_mb)}</div>
                <div className="card-breakdown">
                  <span>Passed: {status.inspection_outputs.passed_images}</span>
                  <span>Failed: {status.inspection_outputs.failed_images}</span>
                </div>
              </div>
            </div>

            <div className="status-card">
              <div className="card-icon database">
                <Database size={24} />
              </div>
              <div className="card-content">
                <div className="card-label">Database Records</div>
                <div className="card-value">{status.database.inspection_records} records</div>
                <div className="card-size">Inspection History</div>
              </div>
            </div>
          </div>

          {/* Cleanup Options */}
          {!showConfirmation && (
            <div className="cleanup-options">
              <div className="options-header">
                <h4>Select items to delete:</h4>
              </div>

              <div className="option-item">
                <input
                  type="checkbox"
                  id="cleanDataset"
                  checked={cleanupOptions.cleanDataset}
                  onChange={(e) =>
                    setCleanupOptions({ ...cleanupOptions, cleanDataset: e.target.checked })
                  }
                />
                <label htmlFor="cleanDataset">
                  <span className="option-title">Training Dataset</span>
                  <span className="option-desc">
                    Delete {status.training_data.total_images} training images ({formatSize(status.training_data.size_mb)})
                  </span>
                </label>
              </div>

              <div className="option-item">
                <input
                  type="checkbox"
                  id="cleanOutputs"
                  checked={cleanupOptions.cleanOutputs}
                  onChange={(e) =>
                    setCleanupOptions({ ...cleanupOptions, cleanOutputs: e.target.checked })
                  }
                />
                <label htmlFor="cleanOutputs">
                  <span className="option-title">Inspection Outputs</span>
                  <span className="option-desc">
                    Delete {status.inspection_outputs.total_images} output images ({formatSize(status.inspection_outputs.size_mb)})
                  </span>
                </label>
              </div>

              <div className="option-item">
                <input
                  type="checkbox"
                  id="cleanDatabase"
                  checked={cleanupOptions.cleanDatabase}
                  onChange={(e) =>
                    setCleanupOptions({ ...cleanupOptions, cleanDatabase: e.target.checked })
                  }
                />
                <label htmlFor="cleanDatabase">
                  <span className="option-title">Inspection History (Database)</span>
                  <span className="option-desc">
                    Delete {status.database.inspection_records} inspection records (⚠️  Cannot be undone)
                  </span>
                </label>
              </div>

              {/* Summary */}
              <div className="cleanup-summary">
                <div className="summary-item">
                  <span>Storage to free:</span>
                  <span className="summary-value">{formatSize(cleanupSize)}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="cleanup-actions">
                <button
                  className="btn-cleanup"
                  onClick={handleCleanup}
                  disabled={!cleanupOptions.cleanDataset && !cleanupOptions.cleanOutputs && !cleanupOptions.cleanDatabase}
                >
                  <Trash2 size={18} />
                  Delete Selected Data
                </button>
              </div>
            </div>
          )}

          {/* Confirmation Dialog */}
          {showConfirmation && (
            <div className="confirmation-dialog">
              <div className="confirmation-header">
                <AlertTriangle size={24} />
                <h3>Confirm Data Deletion</h3>
              </div>

              <div className="confirmation-message">
                <p>⚠️  This action cannot be undone.</p>
                <p>You will delete:</p>
                <ul>
                  {cleanupOptions.cleanDataset && (
                    <li>Training dataset ({formatSize(status.training_data.size_mb)})</li>
                  )}
                  {cleanupOptions.cleanOutputs && (
                    <li>Inspection outputs ({formatSize(status.inspection_outputs.size_mb)})</li>
                  )}
                  {cleanupOptions.cleanDatabase && (
                    <li>{status.database.inspection_records} inspection records from database</li>
                  )}
                </ul>
              </div>

              <div className="confirmation-actions">
                <button
                  className="btn-cancel"
                  onClick={() => setShowConfirmation(false)}
                  disabled={executing}
                >
                  Cancel
                </button>
                <button
                  className="btn-confirm"
                  onClick={handleCleanup}
                  disabled={executing}
                >
                  {executing ? 'Deleting...' : 'Yes, Delete All'}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
});
