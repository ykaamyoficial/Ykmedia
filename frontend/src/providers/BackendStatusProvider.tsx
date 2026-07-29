import { type ReactNode, useMemo } from "react";

import { useBackendHealth } from "@/hooks/use-backend-health";
import {
  BackendStatusContext,
  type BackendConnectionState,
  type BackendStatusContextValue,
} from "@/providers/backend-status-context";

export function BackendStatusProvider({ children }: { children: ReactNode }) {
  const health = useBackendHealth();
  const { data, error, isError, isLoading, isRefetching, refetch } = health;

  const value = useMemo<BackendStatusContextValue>(() => {
    const state: BackendConnectionState = isLoading
      ? "connecting"
      : isError
        ? "offline"
        : data?.status === "ok"
          ? "online"
          : "error";

    return {
      state,
      isOnline: state === "online",
      isChecking: isLoading || isRefetching,
      error: error instanceof Error ? error : null,
      refresh: () => {
        void refetch();
      },
    };
  }, [data?.status, error, isError, isLoading, isRefetching, refetch]);

  return <BackendStatusContext.Provider value={value}>{children}</BackendStatusContext.Provider>;
}
