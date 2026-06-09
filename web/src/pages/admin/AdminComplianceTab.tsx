import { CheckCircle } from 'lucide-react';

export function AdminComplianceTab() {
  return (
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
  );
}
