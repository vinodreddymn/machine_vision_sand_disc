import type { HealthHistory } from '../../types/systemHealth';

interface TrendPanelProps {
  history: HealthHistory[];
}

export function TrendPanel({ history }: TrendPanelProps) {
  return (
    <div className="settings-group">
      <h3 style={{ margin: 0 }}>Health Trends (24h)</h3>
      <div className="history-table-container">
        <table className="inspection-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Temp (C)</th>
              <th>CPU (%)</th>
              <th>RAM (%)</th>
              <th>Disk (%)</th>
            </tr>
          </thead>
          <tbody>
            {history.map((row) => (
              <tr key={row.timestamp}>
                <td>{new Date(row.timestamp).toLocaleString()}</td>
                <td>{row.temperature ?? '--'}</td>
                <td>{row.cpu_usage ?? '--'}</td>
                <td>{row.memory_usage ?? '--'}</td>
                <td>{row.disk_usage ?? '--'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
