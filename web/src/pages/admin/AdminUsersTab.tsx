import { UserPlus, CheckCircle, AlertCircle } from 'lucide-react';
import type { AppUser, UserRole } from '../../types/admin';

interface AdminUsersTabProps {
  users: AppUser[];
  newUsername: string;
  newPassword: string;
  newRole: UserRole;
  canCreate: boolean;
  busy: boolean;
  backupResult: string | null;
  onUsernameChange: (val: string) => void;
  onPasswordChange: (val: string) => void;
  onRoleChange: (val: UserRole) => void;
  onCreate: () => void;
  onBackup: () => void;
  roles: UserRole[];
}

export function AdminUsersTab({
  users,
  newUsername,
  newPassword,
  newRole,
  canCreate,
  busy,
  backupResult,
  onUsernameChange,
  onPasswordChange,
  onRoleChange,
  onCreate,
  onBackup,
  roles,
}: AdminUsersTabProps) {
  return (
    <>
      <div className="settings-group">
        <h3 style={{ margin: 0 }}>Create User</h3>
        <div className="settings-grid">
          <div className="settings-field">
            <label>Username</label>
            <input value={newUsername} onChange={(e) => onUsernameChange(e.target.value)} />
          </div>
          <div className="settings-field">
            <label>Password</label>
            <input type="password" value={newPassword} onChange={(e) => onPasswordChange(e.target.value)} />
          </div>
          <div className="settings-field">
            <label>Role</label>
            <select value={newRole} onChange={(e) => onRoleChange(e.target.value as UserRole)}>
              {roles.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="button good" onClick={onCreate} disabled={!canCreate || busy}>
            <UserPlus size={14} />
            {busy ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>

      <div className="settings-group">
        <h3 style={{ margin: 0 }}>Users</h3>
        <div className="history-table-container">
          <table className="inspection-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Role</th>
                <th>Active</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td><span className={`role-badge role-${u.role.toLowerCase()}`}>{u.role}</span></td>
                  <td>{u.active ? <CheckCircle size={14} color="#3fb950" /> : <AlertCircle size={14} color="#f85149" />}</td>
                  <td>{new Date(u.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={4} style={{ color: '#64748b' }}>No users found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="settings-group">
        <h3 style={{ margin: 0 }}>Backups</h3>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="button" onClick={onBackup} disabled={busy}>
            {busy ? 'Running...' : 'Create Backup Bundle'}
          </button>
        </div>
        {backupResult && (
          <div className="log-terminal" style={{ marginTop: '12px', height: '220px' }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{backupResult}</pre>
          </div>
        )}
      </div>
    </>
  );
}
