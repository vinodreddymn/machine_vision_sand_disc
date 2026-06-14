import React from 'react';
import {
  Cpu,
  Database,
  Server,
  Settings2,
  MoveRight,
  Zap,
  ShieldCheck
} from 'lucide-react';

const APP_VERSION = '2.0.1';

const systemData = {
  plcStatus: 'RUN',
  conveyorMode: 'AUTO',
  conveyorStatus: 'RUNNING',
  rejectActuator: 'IDLE',
  apiStatus: true,
  dbStatus: true
};

export const Footer = React.memo(function Footer() {
  const currentYear = new Date().getFullYear();

  const getStatusType = (value: string) => {
    switch (value) {
      case 'RUN':
      case 'RUNNING':
      case 'AUTO':
      case 'ONLINE':
        return 'success';

      case 'ACTIVE':
      case 'MANUAL':
        return 'warning';

      case 'FAULTY':
      case 'STOP':
      case 'STOPPED':
        return 'danger';

      default:
        return 'neutral';
    }
  };

  return (
    <footer className="footer">

      <div className="footer-left">

        <div className="footer-brand">
          <div className="footer-brand-name">
            DiskVision Inspector
          </div>

          <div className="footer-brand-copy">
            © {currentYear} AI Industrial Solutions
          </div>
        </div>

      </div>

      <div className="footer-center">

        <StatusItem
          icon={<Cpu size={14} />}
          label="PLC"
          value={systemData.plcStatus}
          type={getStatusType(systemData.plcStatus)}
        />

        <StatusItem
          icon={<MoveRight size={14} />}
          label="Conveyor"
          value={systemData.conveyorStatus}
          type={getStatusType(systemData.conveyorStatus)}
        />

        <StatusItem
          icon={<Settings2 size={14} />}
          label="Mode"
          value={systemData.conveyorMode}
          type={getStatusType(systemData.conveyorMode)}
        />

        <StatusItem
          icon={<Zap size={14} />}
          label="Reject"
          value={systemData.rejectActuator}
          type={getStatusType(systemData.rejectActuator)}
        />

        <StatusItem
          icon={<Server size={14} />}
          label="API"
          value={systemData.apiStatus ? 'ONLINE' : 'OFFLINE'}
          type="success"
        />

        <StatusItem
          icon={<Database size={14} />}
          label="DB"
          value={systemData.dbStatus ? 'CONNECTED' : 'DISCONNECTED'}
          type="success"
        />

      </div>

      <div className="footer-right">

        <div className="footer-env">
          PRODUCTION
        </div>

        <div className="footer-version">
          <ShieldCheck size={12} />
          v{APP_VERSION}
        </div>

      </div>

    </footer>
  );
});

interface StatusItemProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  type: string;
}

function StatusItem({
  icon,
  label,
  value,
  type
}: StatusItemProps) {
  return (
    <div className={`status-item ${type}`}>
      {icon}

      <span className="status-label">
        {label}
      </span>

      <span className="status-value">
        {value}
      </span>
    </div>
  );
}

Footer.displayName = 'Footer';