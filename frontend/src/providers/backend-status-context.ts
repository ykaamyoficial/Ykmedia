import { createContext } from "react";

export type BackendConnectionState = "connecting" | "online" | "offline" | "error";

export type BackendStatusContextValue = {
  state: BackendConnectionState;
  isOnline: boolean;
  isChecking: boolean;
  error: Error | null;
  refresh: () => void;
};

export const BackendStatusContext = createContext<BackendStatusContextValue | null>(null);
