// ─── WebSocket Service ────────────────────────────────────────────────────────
// Returns a cleanup function that closes the socket.

const RECONNECT_DELAY_MS = 3000;
const LOG_WS_PATH = '/ws/logs';

export type WsLogMessage = { message: string };

export function createWebSocketConnection(
  onMessage: (message: string) => void,
  onStatusChange?: (connected: boolean) => void,
): () => void {
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let destroyed = false;

  function connect() {
    if (destroyed) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    socket = new WebSocket(`${protocol}://${window.location.host}${LOG_WS_PATH}`);

    socket.onopen = () => {
      onStatusChange?.(true);
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as WsLogMessage;
        onMessage(payload.message);
      } catch {
        // Malformed message — ignore
      }
    };

    socket.onclose = () => {
      onStatusChange?.(false);
      if (!destroyed) {
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      }
    };

    socket.onerror = () => {
      socket?.close();
    };
  }

  connect();

  // Return cleanup function
  return () => {
    destroyed = true;
    if (reconnectTimer !== null) clearTimeout(reconnectTimer);
    socket?.close();
  };
}
