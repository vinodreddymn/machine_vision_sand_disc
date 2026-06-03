import { useCallback, useEffect, useMemo, useState } from 'react';
import { Shield, UserPlus, Database, AlertCircle, CheckCircle, Clock, Trash2 } from 'lucide-react';
import type { AppUser, UserRole } from '../types/admin';
import {
  activateModel,
  createBackup,
  createModel,
  createUser,
  deactivateModel,
  listAuditLogs,
  listModels,
  listUnifiedAuditEvents,
  listUsers,
  rollbackModel,
  type AuditLog,
  type ModelRegistryEntry,
  type UnifiedAuditEvent,
} from '../services/adminService';
import { getConfigAuditLog } from '../services/configService';
import type { AuditLogEntry } from '../services/configService';
import { CleanupManager } from '../components/admin/CleanupManager';

const ROLES: UserRole[] = ['OPERATOR', 'SUPERVISOR', 'ADMIN'];

export function AdminPage() {
  const [users, setUsers] = useState<AppUser[]>([]);
  const [audit, setAudit] = useState<AuditLog[]>([]);
  const [configAudit, setConfigAudit] = useState<AuditLogEntry[]>([]);
  const [timeline, setTimeline] = useState<UnifiedAuditEvent[]>([]);
  const [models, setModels] = useState<ModelRegistryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('OPERATOR');
  const [backupResult, setBackupResult] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'users' | 'audit' | 'compliance' | 'config' | 'cleanup' | 'timeline' | 'models'>('users');
  const [modelVersion, setModelVersion] = useState('');
  const [modelPath, setModelPath] = useState('models/active');
  const [modelNotes, setModelNotes] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [data, logs, configLogs, timelineLogs, modelRows] = await Promise.all([
        listUsers(),
        listAuditLogs(),
        getConfigAuditLog(undefined, 50).catch(() => []),
        listUnifiedAuditEvents(100).catch(() => []),
        listModels(50).catch(() => []),
      ]);
      setUsers(data);
      setAudit(logs);
      setConfigAudit(configLogs);
      setTimeline(timelineLogs);
      setModels(modelRows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const canCreate = useMemo(() => newUsername.trim().length > 2 && newPassword.trim().length >= 6, [newUsername, newPassword]);

  const handleCreate = useCallback(async () => {
    setBusy(true);
    try {
      await createUser({ username: newUsername.trim(), password: newPassword, role: newRole, active: true });
      setNewUsername('');
      setNewPassword('');
      setNewRole('OPERATOR');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, [newUsername, newPassword, newRole, refresh]);

  const handleBackup = useCallback(async () => {
    setBusy(true);
    try {
      const res = await createBackup();
      setBackupResult(JSON.stringify(res, null, 2));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, [refresh]);

  const handleCreateModel = useCallback(async () => {
    if (!modelVersion.trim() || !modelPath.trim()) return;
    setBusy(true);
    try {
      await createModel({
        version: modelVersion.trim(),
        model_path: modelPath.trim(),
        notes: modelNotes.trim() || null,
        active: false,
      });
      setModelVersion('');
      setModelPath('models/active');
      setModelNotes('');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, [modelVersion, modelPath, modelNotes, refresh]);

  const handleModelAction = useCallback(async (action: 'activate' | 'deactivate' | 'rollback', version: string) => {
    setBusy(true);
    try {
      if (action === 'activate') {
        await activateModel(version);
      } else if (action === 'deactivate') {
        await deactivateModel(version);
      } else {
        await rollbackModel(version);
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, [refresh]);

  return (
    <div className="settings-page">
      <div className="settings-group">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Shield size={18} />
          <h2 style={{ margin: 0, fontSize: '16px' }}>Administration & Compliance</h2>
        </div>
        <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#8b949e' }}>Industry 4.0 Compliant System Management</p>
        {error && <div className="alert">{error}</div>}
      </div>

      {/* Tab Navigation */}
      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          <UserPlus size={16} />
          Users &amp; Access
        </button>
        <button
          className={`admin-tab ${activeTab === 'compliance' ? 'active' : ''}`}
          onClick={() => setActiveTab('compliance')}
        >
          <CheckCircle size={16} />
          Compliance
        </button>
        <button
          className={`admin-tab ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          <Database size={16} />
          Configuration Audit
        </button>
        <button
          className={`admin-tab ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          <Clock size={16} />
          System Audit
        </button>
        <button
          className={`admin-tab ${activeTab === 'cleanup' ? 'active' : ''}`}
          onClick={() => setActiveTab('cleanup')}
        >
          <Trash2 size={16} />
          Data Management
        </button>
        <button
          className={`admin-tab ${activeTab === 'timeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          <Clock size={16} />
          Unified Timeline
        </button>
        <button
          className={`admin-tab ${activeTab === 'models' ? 'active' : ''}`}
          onClick={() => setActiveTab('models')}
        >
          <Database size={16} />
          Model Registry
        </button>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <>
          <div className="settings-group">
            <h3 style={{ margin: 0 }}>Create User</h3>
            <div className="settings-grid">
              <div className="settings-field">
                <label>Username</label>
                <input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} />
              </div>
              <div className="settings-field">
                <label>Password</label>
                <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              </div>
              <div className="settings-field">
                <label>Role</label>
                <select value={newRole} onChange={(e) => setNewRole(e.target.value as UserRole)}>
                  {ROLES.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="button good" onClick={handleCreate} disabled={!canCreate || busy}>
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
              <button className="button" onClick={handleBackup} disabled={busy}>
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
      )}

      {/* Compliance Tab */}
      {activeTab === 'compliance' && (
        <div className="compliance-dashboard">
          <div className="compliance-header">
            <h3>System Compliance Status</h3>
            <p className="compliance-subtitle">Industry 4.0 Standards Compliance Monitoring</p>
          </div>

          <div className="compliance-metrics">
            <div className="compliance-metric">
              <div className="metric-icon compliance-ok">
                <CheckCircle size={24} />
              </div>
              <div className="metric-info">
                <h4>Data Traceability</h4>
                <p>Full audit trail maintained for all configuration changes</p>
                <span className="metric-status">COMPLIANT</span>
              </div>
            </div>

            <div className="compliance-metric">
              <div className="metric-icon compliance-ok">
                <CheckCircle size={24} />
              </div>
              <div className="metric-info">
                <h4>Version Control</h4>
                <p>All system configurations versioned and rollback capable</p>
                <span className="metric-status">ENABLED</span>
              </div>
            </div>

            <div className="compliance-metric">
              <div className="metric-icon compliance-ok">
                <CheckCircle size={24} />
              </div>
              <div className="metric-info">
                <h4>User Access Control</h4>
                <p>Role-based access control with audit logging</p>
                <span className="metric-status">ACTIVE</span>
              </div>
            </div>

            <div className="compliance-metric">
              <div className="metric-icon compliance-ok">
                <CheckCircle size={24} />
              </div>
              <div className="metric-info">
                <h4>Change Tracking</h4>
                <p>All system changes logged with timestamp and user attribution</p>
                <span className="metric-status">VERIFIED</span>
              </div>
            </div>
          </div>

          <div className="compliance-info">
            <h4>Compliance Features</h4>
            <ul>
              <li>✓ Complete audit trail of all system modifications</li>
              <li>✓ User attribution for all changes</li>
              <li>✓ Configuration versioning with rollback capability</li>
              <li>✓ Role-based access control (RBAC)</li>
              <li>✓ Time-stamped change records</li>
              <li>✓ Change reason documentation</li>
              <li>✓ IP address logging for remote access</li>
              <li>✓ Immutable audit log storage</li>
            </ul>
          </div>
        </div>
      )}

      {/* Configuration Audit Tab */}
      {activeTab === 'config' && (
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
      )}

      {/* System Audit Tab */}
      {activeTab === 'audit' && (
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
      )}

      {/* Data Management Tab */}
      {activeTab === 'cleanup' && (
        <div className="settings-group">
          <CleanupManager />
        </div>
      )}

      {activeTab === 'timeline' && (
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
      )}

      {activeTab === 'models' && (
        <>
          <div className="settings-group">
            <h3 style={{ margin: 0 }}>Create Model Version</h3>
            <div className="settings-grid">
              <div className="settings-field">
                <label>Version</label>
                <input value={modelVersion} onChange={(e) => setModelVersion(e.target.value)} placeholder="v1.0.0" />
              </div>
              <div className="settings-field">
                <label>Model Path</label>
                <input value={modelPath} onChange={(e) => setModelPath(e.target.value)} placeholder="models/v1/model.onnx" />
              </div>
              <div className="settings-field">
                <label>Notes</label>
                <input value={modelNotes} onChange={(e) => setModelNotes(e.target.value)} placeholder="Training notes or run id" />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="button good" onClick={handleCreateModel} disabled={busy || !modelVersion.trim() || !modelPath.trim()}>
                {busy ? 'Saving...' : 'Create Model'}
              </button>
            </div>
          </div>

          <div className="settings-group">
            <h3 style={{ margin: 0 }}>Registered Models</h3>
            <div className="history-table-container">
              <table className="inspection-table">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Active</th>
                    <th>Dataset</th>
                    <th>Accuracy</th>
                    <th>Path</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model) => (
                    <tr key={model.id}>
                      <td>{model.version}</td>
                      <td>{model.active ? 'Yes' : 'No'}</td>
                      <td>{model.dataset_size ?? '--'}</td>
                      <td>{model.accuracy != null ? `${(model.accuracy * 100).toFixed(2)}%` : '--'}</td>
                      <td>{model.model_path}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          <button className="button" onClick={() => handleModelAction('activate', model.version)} disabled={busy || model.active}>Activate</button>
                          <button className="button" onClick={() => handleModelAction('deactivate', model.version)} disabled={busy || !model.active}>Deactivate</button>
                          <button className="button" onClick={() => handleModelAction('rollback', model.version)} disabled={busy}>Rollback</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {models.length === 0 && (
                    <tr><td colSpan={6} style={{ color: '#64748b' }}>No model versions found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
