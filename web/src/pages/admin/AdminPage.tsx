import { useCallback, useEffect, useMemo, useState } from 'react';
import { Shield } from 'lucide-react';
import type { AppUser, UserRole } from '../../types/admin';
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
} from '../../services/adminService';
import { getConfigAuditLog, type AuditLogEntry } from '../../services/configService';
import { CleanupManager } from '../../components/admin/CleanupManager';

import { AdminTabs, type AdminTab } from './AdminTabs';
import { AdminUsersTab } from './AdminUsersTab';
import { AdminComplianceTab } from './AdminComplianceTab';
import { AdminConfigAuditTab } from './AdminConfigAuditTab';
import { AdminSystemAuditTab } from './AdminSystemAuditTab';
import { AdminTimelineTab } from './AdminTimelineTab';
import { AdminModelsTab } from './AdminModelsTab';

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
  const [activeTab, setActiveTab] = useState<AdminTab>('users');
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

      <AdminTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === 'users' && (
        <AdminUsersTab
          users={users}
          newUsername={newUsername}
          newPassword={newPassword}
          newRole={newRole}
          canCreate={canCreate}
          busy={busy}
          backupResult={backupResult}
          onUsernameChange={setNewUsername}
          onPasswordChange={setNewPassword}
          onRoleChange={setNewRole}
          onCreate={handleCreate}
          onBackup={handleBackup}
          roles={ROLES}
        />
      )}

      {activeTab === 'compliance' && <AdminComplianceTab />}

      {activeTab === 'config' && <AdminConfigAuditTab configAudit={configAudit} />}

      {activeTab === 'audit' && <AdminSystemAuditTab audit={audit} />}

      {activeTab === 'cleanup' && (
        <div className="settings-group">
          <CleanupManager />
        </div>
      )}

      {activeTab === 'timeline' && <AdminTimelineTab timeline={timeline} />}

      {activeTab === 'models' && (
        <AdminModelsTab
          models={models}
          modelVersion={modelVersion}
          modelPath={modelPath}
          modelNotes={modelNotes}
          busy={busy}
          onVersionChange={setModelVersion}
          onPathChange={setModelPath}
          onNotesChange={setModelNotes}
          onCreateModel={handleCreateModel}
          onModelAction={handleModelAction}
        />
      )}
    </div>
  );
}
