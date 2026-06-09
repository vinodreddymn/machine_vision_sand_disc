import { RefreshCcw, Download, Trash2 } from 'lucide-react';
import type { CalibrationRecord } from '../../types/calibration';

interface CalibrationHistoryTableProps {
  history: CalibrationRecord[];
  cameraId: string;
  onReload: () => void;
  onDelete: (id: number) => void;
  onDownloadReport: () => void;
}

export function CalibrationHistoryTable({
  history,
  cameraId,
  onReload,
  onDelete,
  onDownloadReport,
}: CalibrationHistoryTableProps) {
  return (
    <div className="cal-history-panel">
      <div className="cal-panel-header">
        <h3 className="cal-panel-title">Calibration History</h3>
        <button className="button" onClick={onReload} title="Refresh">
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
              {history.map((rec) => (
                <tr key={rec.id} className={rec.active ? 'cal-row-active' : ''}>
                  <td>{rec.id}</td>
                  <td>{new Date(rec.calibration_date).toLocaleString()}</td>
                  <td className="cal-mono">{rec.mm_per_pixel.toFixed(6)}</td>
                  <td>{rec.reference_od_mm} mm</td>
                  <td>{rec.reference_hole_mm} mm</td>
                  <td>
                    {rec.active ? (
                      <span className="cal-badge active">ACTIVE</span>
                    ) : (
                      <span className="cal-badge inactive">inactive</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="cal-delete-btn"
                      onClick={() => onDelete(rec.id)}
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
        <button className="button" onClick={onDownloadReport}>
          <Download size={14} /> Download PDF Report
        </button>
      </div>
    </div>
  );
}
