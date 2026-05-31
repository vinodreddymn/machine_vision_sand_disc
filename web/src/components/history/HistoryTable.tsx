import React, { useCallback } from 'react';
import { Download } from 'lucide-react';
import { useHistoryContext } from '../../contexts/HistoryContext';
import { toCSV } from '../../utils/filters';
import { formatIsoDate } from '../../utils/dateUtils';

function downloadBlob(content: string, filename: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export const HistoryTable = React.memo(function HistoryTable() {
  const { filteredHistory, selectedInspection, setSelectedInspection } =
    useHistoryContext();

  const handleExportCSV = useCallback(() => {
    const csv = toCSV(filteredHistory);
    downloadBlob(csv, 'inspection_history.csv', 'text/csv');
  }, [filteredHistory]);

  const handleExportJSON = useCallback(() => {
    const json = JSON.stringify(filteredHistory, null, 2);
    downloadBlob(json, 'inspection_history.json', 'application/json');
  }, [filteredHistory]);

  return (
    <div className="history-table-container">
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '8px',
          padding: '8px 0',
        }}
      >
        <button
          id="btn-export-csv"
          className="button"
          onClick={handleExportCSV}
          title="Export to CSV"
          style={{ fontSize: '12px', padding: '4px 10px' }}
        >
          <Download size={13} /> CSV
        </button>
        <button
          id="btn-export-json"
          className="button"
          onClick={handleExportJSON}
          title="Export to JSON"
          style={{ fontSize: '12px', padding: '4px 10px' }}
        >
          <Download size={13} /> JSON
        </button>
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
                style={{ cursor: 'pointer' }}
              >
                <td>
                  <strong>{item.physical_part_id}</strong>
                </td>
                <td>{item.serial_number || '--'}</td>
                <td>{formatIsoDate(item.inspected_at)}</td>
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
                <td>
                  {item.cycle_time_ms != null
                    ? `${item.cycle_time_ms} ms`
                    : '--'}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan={6}
                style={{
                  textAlign: 'center',
                  color: '#64748b',
                  padding: '24px',
                }}
              >
                No matching inspection logs found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
});
