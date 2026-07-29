export type WebSocketConnectionState = "idle" | "connecting" | "connected" | "reconnecting" | "closed" | "error";

export type WebSocketMessageHandler = (message: MessageEvent) => void;

export class ConnectionManager {
  private socket: WebSocket | null = null;
  private handler: WebSocketMessageHandler | null = null;
  state: WebSocketConnectionState = "idle";

  connect(url: string) {
    this.state = "connecting";
    this.socket = new WebSocket(url);
    this.socket.onopen = () => {
      this.state = "connected";
    };
    this.socket.onmessage = (message) => this.handler?.(message);
    this.socket.onerror = () => {
      this.state = "error";
    };
    this.socket.onclose = () => {
      this.state = "closed";
    };
  }

  onMessage(handler: WebSocketMessageHandler) {
    this.handler = handler;
  }

  close() {
    this.socket?.close();
    this.socket = null;
    this.state = "closed";
  }
}
