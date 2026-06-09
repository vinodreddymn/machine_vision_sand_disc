import type { ModelRegistryEntry } from '../../services/adminService';

interface AdminModelsTabProps {
  models: ModelRegistryEntry[];
  modelVersion: string;
  modelPath: string;
  modelNotes: string;
  busy: boolean;
  onVersionChange: (val: string) => void;
  onPathChange: (val: string) => void;
  onNotesChange: (val: string) => void;
  onCreateModel: () => void;
  onModelAction: (action: 'activate' | 'deactivate' | 'rollback', version: string) => void;
}

export function AdminModelsTab({
  models,
  modelVersion,
  modelPath,
  modelNotes,
  busy,
  onVersionChange,
  onPathChange,
  onNotesChange,
  onCreateModel,
  onModelAction,
}: AdminModelsTabProps) {
  return (
    <>
      <div className="settings-group">
        <h3 style={{ margin: 0 }}>Create Model Version</h3>
        <div className="settings-grid">
          <div className="settings-field">
            <label>Version</label>
            <input value={modelVersion} onChange={(e) => onVersionChange(e.target.value)} placeholder="v1.0.0" />
          </div>
          <div className="settings-field">
            <label>Model Path</label>
            <input value={modelPath} onChange={(e) => onPathChange(e.target.value)} placeholder="models/v1/model.onnx" />
          </div>
          <div className="settings-field">
            <label>Notes</label>
            <input value={modelNotes} onChange={(e) => onNotesChange(e.target.value)} placeholder="Training notes or run id" />
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="button good" onClick={onCreateModel} disabled={busy || !modelVersion.trim() || !modelPath.trim()}>
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
                      <button className="button" onClick={() => onModelAction('activate', model.version)} disabled={busy || model.active}>Activate</button>
                      <button className="button" onClick={() => onModelAction('deactivate', model.version)} disabled={busy || !model.active}>Deactivate</button>
                      <button className="button" onClick={() => onModelAction('rollback', model.version)} disabled={busy}>Rollback</button>
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
  );
}
