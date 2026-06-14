import {
  CheckCircle2,
  XCircle
} from 'lucide-react';

import type {
  StartupDiagnostics
} from '../../types/systemHealth';

interface Props {
  diagnostics:
    StartupDiagnostics | null;
}

export function StartupTimeline({
  diagnostics
}: Props) {

  const items = [
    {
      label: 'Database',
      value: diagnostics?.database
    },
    {
      label: 'Camera',
      value: diagnostics?.camera
    },
    {
      label: 'PLC',
      value: diagnostics?.plc
    },
    {
      label: 'Storage',
      value: diagnostics?.storage
    },
    {
      label: 'Model',
      value: diagnostics?.model
    }
  ];

  return (
    <section className="sys-panel">

      <div className="sys-panel-header">
        <h3>Startup Diagnostics</h3>
      </div>

      <div className="sys-startup-timeline">

        {items.map((item) => {

          const success =
            String(item.value)
              .toUpperCase()
              .includes('ONLINE');

          return (
            <div
              key={item.label}
              className="sys-startup-step"
            >

              {success ? (
                <CheckCircle2
                  size={18}
                />
              ) : (
                <XCircle
                  size={18}
                />
              )}

              <div>

                <strong>
                  {item.label}
                </strong>

                <div>
                  {item.value ??
                    'UNKNOWN'}
                </div>

              </div>

            </div>
          );
        })}

      </div>

    </section>
  );
}