import { useContext } from "react";

import { BackendStatusContext } from "@/providers/backend-status-context";

export function useBackendStatus() {
  const value = useContext(BackendStatusContext);
  if (value === null) {
    throw new Error("useBackendStatus must be used inside BackendStatusProvider.");
  }
  return value;
}
