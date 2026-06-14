import {
  Play,
  Square,
  RotateCw,
  Server
} from 'lucide-react';

import type {
  ServiceStatus
} from '../../types/systemHealth';

interface Props {
  services: Record<string, ServiceStatus>;
}

export function ServiceControlCenter({
  services
}: Props) {

  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>Service Control Center</h3>
      </div>

      <div className="sys-service-grid">

        {Object.entries(services).map(
          ([name, service]) => {

            const online =
              String(service.status)
                .toUpperCase() ===
              'ONLINE';

            return (
              <div
                key={name}
                className="sys-service-card"
              >

                <div className="sys-service-header">

                  <Server size={18} />

                  <div>

                    <div className="sys-service-name">
                      {name}
                    </div>

                    <div
                      className={
                        online
                          ? 'service-online'
                          : 'service-offline'
                      }
                    >
                      {service.status}
                    </div>

                  </div>

                </div>

                <div className="sys-service-info">

                  <div>
                    Version:
                    {' '}
                    {service.version ??
                      '--'}
                  </div>

                  <div>
                    Updated:
                    {' '}
                    {service.timestamp
                      ? new Date(
                          service.timestamp
                        ).toLocaleString()
                      : '--'}
                  </div>

                </div>

                <div className="sys-service-actions">

                  <button
                    className="button"
                    disabled
                  >
                    <Play size={14} />
                    Start
                  </button>

                  <button
                    className="button"
                    disabled
                  >
                    <Square size={14} />
                    Stop
                  </button>

                  <button
                    className="button"
                    disabled
                  >
                    <RotateCw size={14} />
                    Restart
                  </button>

                </div>

              </div>
            );
          }
        )}

      </div>

    </section>
  );
}