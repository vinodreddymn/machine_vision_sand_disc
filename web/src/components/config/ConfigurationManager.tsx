/**
 * Configuration Manager Component
 * Displays all configurations, allows editing, versioning, and audit log viewing
 * Industry 4.0 compliant with full traceability and change tracking
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getAllConfigs,
  getConfig,
  saveConfig,
  getConfigVersions,
  getConfigVersion,
  reloadConfig,
  rollbackConfig,
  getConfigAuditLog,
  ConfigData,
  ConfigMetadata,
  AuditLogEntry,
} from '../../services/configService';
import { JsonEditor } from './JsonEditor';
import '../../styles/config-manager.css';

type Tab = 'overview' | 'editor' | 'versions' | 'audit';

export function ConfigurationManager() {
  const [configs, setConfigs] = useState<ConfigData[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reloading, setReloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Editor state
  const [editData, setEditData] = useState<Record<string, any>>({});
  const [editDescription, setEditDescription] = useState('');
  const [editReason, setEditReason] = useState('');

  // Versions state
  const [versions, setVersions] = useState<ConfigMetadata[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);

  // Audit log state
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  // Load all configurations on mount
  useEffect(() => {
    const loadConfigs = async () => {
      try {
        setLoading(true);
        const data = await getAllConfigs();
        setConfigs(data);
        if (data.length > 0) {
          setSelectedConfig(data[0].config_key);
        }
        setError(null);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadConfigs();
  }, []);

  // Load selected configuration details
  useEffect(() => {
    if (!selectedConfig) return;

    const loadConfigDetails = async () => {
      try {
        const data = await getConfig(selectedConfig);
        setEditData(data);
        setEditDescription('');
        setEditReason('');
        setError(null);
      } catch (err) {
        setError((err as Error).message);
      }
    };

    loadConfigDetails();
  }, [selectedConfig]);

  // Load versions when tab changes
  useEffect(() => {
    if (currentTab === 'versions' && selectedConfig) {
      const loadVersions = async () => {
        try {
          setVersionsLoading(true);
          const data = await getConfigVersions(selectedConfig);
          setVersions(data);
          setError(null);
        } catch (err) {
          setError((err as Error).message);
        } finally {
          setVersionsLoading(false);
        }
      };

      loadVersions();
    }
  }, [currentTab, selectedConfig]);

  // Load audit log when tab changes
  useEffect(() => {
    if (currentTab === 'audit' && selectedConfig) {
      const loadAuditLog = async () => {
        try {
          setAuditLoading(true);
          const data = await getConfigAuditLog(selectedConfig);
          setAuditLog(data);
          setError(null);
        } catch (err) {
          setError((err as Error).message);
        } finally {
          setAuditLoading(false);
        }
      };

      loadAuditLog();
    }
  }, [currentTab, selectedConfig]);

  const handleSaveConfig = useCallback(async () => {
    if (!selectedConfig) return;

    try {
      setSaving(true);
      setError(null);

      await saveConfig(
        selectedConfig,
        editData,
        editDescription || undefined,
        editReason || undefined
      );

      setSuccessMessage('Configuration saved successfully');
      setTimeout(() => setSuccessMessage(null), 3000);

      // Reload configs
      const data = await getAllConfigs();
      setConfigs(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }, [selectedConfig, editData, editDescription, editReason]);

  const handleRollback = useCallback(async (version: number) => {
    if (!selectedConfig) return;

    try {
      setSaving(true);
      setError(null);

      await rollbackConfig(selectedConfig, version, `Rolled back via UI`);

      setSuccessMessage(`Configuration rolled back to version ${version}`);
      setTimeout(() => setSuccessMessage(null), 3000);

      // Reload configs and versions
      const data = await getAllConfigs();
      setConfigs(data);
      const versionData = await getConfigVersions(selectedConfig);
      setVersions(versionData);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }, [selectedConfig]);

  const handleReloadConfig = useCallback(async () => {
    if (!selectedConfig) return;

    try {
      setReloading(true);
      setError(null);

      await reloadConfig(selectedConfig);
      const [data, version, configData] = await Promise.all([
        getAllConfigs(),
        getConfigVersion(selectedConfig),
        getConfig(selectedConfig),
      ]);
      setConfigs(data);
      setEditData(configData);
      setSuccessMessage(`Configuration ${selectedConfig} reloaded (v${version})`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setReloading(false);
    }
  }, [selectedConfig]);

  if (loading) {
    return (
      <div className="config-manager">
        <div className="loading-spinner">Loading configurations...</div>
      </div>
    );
  }

  return (
    <div className="config-manager">
      <div className="config-manager-container">
        {/* Sidebar */}
        <div className="config-sidebar">
          <h3 className="sidebar-title">System Configurations</h3>
          <div className="config-list">
            {configs.map((config) => (
              <button
                key={config.config_key}
                className={`config-item ${selectedConfig === config.config_key ? 'active' : ''}`}
                onClick={() => setSelectedConfig(config.config_key)}
              >
                <span className="config-item-name">{config.config_key}</span>
                <span className="config-item-version">v{config.versions[0]?.version || 0}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="config-main">
          {selectedConfig && (
            <>
              {/* Tabs */}
              <div className="config-tabs">
                <button
                  className={`tab-button ${currentTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('overview')}
                >
                  Overview
                </button>
                <button
                  className={`tab-button ${currentTab === 'editor' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('editor')}
                >
                  Edit Configuration
                </button>
                <button
                  className={`tab-button ${currentTab === 'versions' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('versions')}
                >
                  Version History
                </button>
                <button
                  className={`tab-button ${currentTab === 'audit' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('audit')}
                >
                  Audit Log
                </button>
              </div>

              {/* Messages */}
              {error && <div className="config-error">{error}</div>}
              {successMessage && <div className="config-success">{successMessage}</div>}

              {/* Overview Tab */}
              {currentTab === 'overview' && (
                <div className="config-content">
                  <div className="config-header">
                    <h2>{selectedConfig}</h2>
                    <div className="config-header-actions">
                      <span className="config-type">JSON Configuration</span>
                      <button
                        className="save-button"
                        onClick={handleReloadConfig}
                        disabled={reloading || saving}
                      >
                        {reloading ? 'Reloading...' : 'Reload Config'}
                      </button>
                    </div>
                  </div>
                  <div className="config-stats">
                    <div className="stat">
                      <span className="stat-label">Current Version</span>
                      <span className="stat-value">
                        {configs.find((c) => c.config_key === selectedConfig)?.versions[0]?.version || 0}
                      </span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Last Updated</span>
                      <span className="stat-value">
                        {configs.find((c) => c.config_key === selectedConfig)?.versions[0]?.updated_at
                          ? new Date(
                              configs.find((c) => c.config_key === selectedConfig)?.versions[0]?.updated_at || ''
                            ).toLocaleString()
                          : 'Never'}
                      </span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Last Updated By</span>
                      <span className="stat-value">
                        {configs.find((c) => c.config_key === selectedConfig)?.versions[0]?.updated_by || 'Unknown'}
                      </span>
                    </div>
                  </div>
                  <div className="config-preview">
                    <h3>Current Configuration</h3>
                    <pre>{JSON.stringify(editData, null, 2)}</pre>
                  </div>
                </div>
              )}

              {/* Editor Tab */}
              {currentTab === 'editor' && (
                <div className="config-content">
                  <div className="editor-section">
                    <h2>Edit Configuration</h2>
                    <JsonEditor value={editData} onChange={setEditData} isSaving={saving} error={error ?? undefined} />

                    <div className="editor-metadata">
                      <div className="metadata-field">
                        <label htmlFor="edit-description">Change Description</label>
                        <input
                          id="edit-description"
                          type="text"
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                          placeholder="Describe what changed in this update"
                          className="metadata-input"
                        />
                      </div>

                      <div className="metadata-field">
                        <label htmlFor="edit-reason">Change Reason (Audit Trail)</label>
                        <textarea
                          id="edit-reason"
                          value={editReason}
                          onChange={(e) => setEditReason(e.target.value)}
                          placeholder="Reason for this change (compliance/traceability)"
                          className="metadata-textarea"
                        />
                      </div>

                      <button
                        className="save-button"
                        onClick={handleSaveConfig}
                        disabled={saving}
                      >
                        {saving ? 'Saving...' : 'Save Configuration'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Versions Tab */}
              {currentTab === 'versions' && (
                <div className="config-content">
                  <h2>Version History</h2>
                  {versionsLoading ? (
                    <div className="loading-spinner">Loading versions...</div>
                  ) : versions.length === 0 ? (
                    <p className="no-data">No versions available</p>
                  ) : (
                    <div className="versions-list">
                      {versions.map((version, index) => (
                        <div key={version.id} className="version-item">
                          <div className="version-header">
                            <span className="version-number">Version {version.version}</span>
                            <span className="version-date">{new Date(version.updated_at).toLocaleString()}</span>
                            {index === 0 && <span className="version-badge">CURRENT</span>}
                          </div>
                          <div className="version-info">
                            <p>
                              <strong>Updated By:</strong> {version.updated_by || 'Unknown'}
                            </p>
                            {version.description && (
                              <p>
                                <strong>Description:</strong> {version.description}
                              </p>
                            )}
                          </div>
                          {index > 0 && (
                            <button
                              className="rollback-button"
                              onClick={() => handleRollback(version.version)}
                              disabled={saving}
                            >
                              Rollback to v{version.version}
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Audit Log Tab */}
              {currentTab === 'audit' && (
                <div className="config-content">
                  <h2>Audit Log</h2>
                  {auditLoading ? (
                    <div className="loading-spinner">Loading audit log...</div>
                  ) : auditLog.length === 0 ? (
                    <p className="no-data">No audit entries</p>
                  ) : (
                    <div className="audit-list">
                      {auditLog.map((entry) => (
                        <div key={entry.id} className="audit-item">
                          <div className="audit-header">
                            <span className={`audit-action ${entry.action.toLowerCase()}`}>{entry.action}</span>
                            <span className="audit-date">{new Date(entry.changed_at).toLocaleString()}</span>
                          </div>
                          <div className="audit-details">
                            <p>
                              <strong>Changed By:</strong> {entry.changed_by}
                            </p>
                            {entry.reason && (
                              <p>
                                <strong>Reason:</strong> {entry.reason}
                              </p>
                            )}
                            {entry.ip_address && (
                              <p>
                                <strong>IP Address:</strong> {entry.ip_address}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
