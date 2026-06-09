import type { AuditLog } from '../../services/adminService';

interface AdminSystemAuditTabProps {
  audit: AuditLog[];
}

export function AdminSystemAuditTab({ audit }: AdminSystemAuditTabProps) {
  return (
    <div className="settings-group">
      <h3 style={{ margin: 0 }}>System Audit Logs</h3>
      <div className="history-table-container">
        <table className="inspection-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {audit.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleString()}</td>
                <td>{a.actor ?? '--'}</td>
                <td>{a.action}</td>
                <td>{a.resource ?? '--'}</td>
                <td>{a.message}</td>
            </tr>
          ))}
          {audit.length === 0 && (
            <tr><td colSpan={5} style={{ color: '#64748b' }}>No audit logs found.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  </div>
  );
}
