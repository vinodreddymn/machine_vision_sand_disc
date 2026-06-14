import {
  Camera,
  Database,
  Network,
  Workflow
} from 'lucide-react';

import type {
  DeviceStatus,
  SystemHealth
} from '../../types/systemHealth';

interface Props {
  health: SystemHealth | null;
  devices: DeviceStatus | null;
}

export function InfrastructurePanel({
  health,
  devices
}: Props) {
  return (
    <section className="sys-infrastructure">

      <div className="sys-resource-grid">

        <div className="sys-resource-card">
          <span>CPU Usage</span>
          <strong>
            {health?.cpu_usage ?? '--'}%
          </strong>
        </div>

        <div className="sys-resource-card">
          <span>Memory Usage</span>
          <strong>
            {health?.memory_usage ?? '--'}%
          </strong>
        </div>

        <div className="sys-resource-card">
          <span>Disk Usage</span>
          <strong>
            {health?.disk_usage ?? '--'}%
          </strong>
        </div>

        <div className="sys-resource-card">
          <span>Temperature</span>
          <strong>
            {health?.temperature ?? '--'}°C
          </strong>
        </div>

      </div>

      <div className="sys-device-grid">

        <div className="sys-device-card">
          <Camera size={18} />
          <strong>Camera</strong>
          <span>{devices?.camera}</span>
        </div>

        <div className="sys-device-card">
          <Workflow size={18} />
          <strong>PLC</strong>
          <span>{devices?.plc}</span>
        </div>

        <div className="sys-device-card">
          <Database size={18} />
          <strong>Database</strong>
          <span>{devices?.database}</span>
        </div>

        <div className="sys-device-card">
          <Network size={18} />
          <strong>Network</strong>
          <span>{devices?.network}</span>
        </div>

      </div>

    </section>
  );
}