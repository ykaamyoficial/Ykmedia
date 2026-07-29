import { useSyncExternalStore } from "react";

import { type WebSocketConnectionState } from "@/shared/websocket/connection-manager";

export function useStaticWebSocketState(state: WebSocketConnectionState = "idle") {
  return useSyncExternalStore(
    () => () => undefined,
    () => state,
    () => state,
  );
}
