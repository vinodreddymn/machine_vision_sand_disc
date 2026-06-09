import type { UnifiedAuditEvent } from '../../services/adminService';

interface AdminTimelineTabProps {
  timeline: UnifiedAuditEvent[];
}

export function AdminTimelineTab({ timeline }: AdminTimelineTabProps) {
  return (
    <div className="settings-group">
      <h3 style={{ margin: 0 }}>Unified Audit Timeline</h3>
      <div className="history-table-container">
        <table className="inspection-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Source</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {timeline.map((entry, idx) => (
              <tr key={`${entry.timestamp}-${idx}`}>
                <td>{new Date(entry.timestamp).toLocaleString()}</td>
                <td>{entry.source}</td>
                <td>{entry.actor ?? '--'}</td>
                <td>{entry.action}</td>
                <td>{entry.resource ?? '--'}</td>
                <td>{entry.message}</td>
              </tr>
            ))}
            {timeline.length === 0 && (
              <tr><td colSpan={6} style={{ color: '#64748b' }}>No unified audit events found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
