import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { useDashboardOverview } from "@/features/dashboard/hooks";
import { createAppQueryClient } from "@/shared/query";

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("useDashboardOverview", () => {
  it("loads dashboard overview through TanStack Query", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            generated_at: "2026-07-29T10:00:00+00:00",
            system: {
              version: "0.1.0",
              uptime_seconds: 10,
              backend_online: true,
              database_connected: true,
            },
            evolution: {
              online: true,
              instance: "ykmedia",
              last_sync: "2026-07-29T10:00:00+00:00",
              error: null,
            },
            whatsapp: {
              status: "connected",
              connected: true,
              qr_pending: false,
            },
            downloads: {
              in_progress: 0,
              completed: 1,
              failures: 0,
              queue: 0,
            },
            files: {
              stored_count: 1,
              storage_used_bytes: 5,
              categories: ["Louvores"],
            },
            conversations: {
              total: 0,
              active_contacts: 0,
              latest_messages: [],
            },
            history: [],
            health: [],
            has_data: true,
          }),
      }),
    );

    const { result } = renderHook(() => useDashboardOverview(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.files.stored_count).toBe(1);
  });
});
