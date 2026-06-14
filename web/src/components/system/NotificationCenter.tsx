import { postJson } from '../../services/apiService';

interface Props {
  channels:
    Array<{ type: string }>;
}

export function NotificationCenter({
  channels
}: Props) {

  return (
    <section className="sys-panel">

      <div className="sys-panel-header">

        <h3>
          Notification Center
        </h3>

        <button
          className="button"
          onClick={() =>
            postJson(
              '/api/admin/notification-test'
            )
          }
        >
          Send Test
        </button>

      </div>

      <div className="sys-notification-grid">

        {channels.length === 0 && (
          <div className="sys-empty-state">
            No channels configured
          </div>
        )}

        {channels.map((channel) => (
          <div
            key={channel.type}
            className="sys-notification-card"
          >

            <strong>
              {channel.type}
            </strong>

            <span>
              ACTIVE
            </span>

          </div>
        ))}

      </div>

    </section>
  );
}