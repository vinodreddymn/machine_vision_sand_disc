import type { AuditLogEntry } from '../../services/configService';

interface AdminConfigAuditTabProps {
  configAudit: AuditLogEntry[];
}

export function AdminConfigAuditTab({ configAudit }: AdminConfigAuditTabProps) {
  return (
    <div className="settings-group">
      <h3 style={{ margin: 0 }}>Configuration Changes Audit Trail</h3>
      <p style={{ color: '#8b949e', fontSize: '12px', marginTop: '4px' }}>Track all system configuration modifications for compliance</p>
      <div className="history-table-container">
        <table className="inspection-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Configuration</th>
              <th>Action</th>
              <th>Changed By</th>
              <th>Reason</th>
              <th>Version</th>
            </tr>
          </thead>
          <tbody>
            {configAudit.map((entry, idx) => (
              <tr key={entry.id || idx}>
                <td style={{ fontSize: '12px' }}>{new Date(entry.changed_at).toLocaleString()}</td>
                <td><span className="config-key-badge">{entry.config_key}</span></td>
                <td>
                  <span className={`action-badge action-${entry.action.toLowerCase()}`}>
                    {entry.action}
                  </span>
                </td>
                <td>{entry.changed_by}</td>
                <td style={{ fontSize: '12px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {entry.reason || '--'}
                </td>
                <td style={{ textAlign: 'center' }}>v{entry.version_number}</td>
              </tr>
            ))}
            {configAudit.length === 0 && (
              <tr><td colSpan={6} style={{ color: '#64748b' }}>No configuration changes recorded.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
