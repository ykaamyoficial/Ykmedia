import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { useDownloadJobs } from "@/features/downloads/hooks";
import { createAppQueryClient } from "@/shared/query";

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("useDownloadJobs", () => {
  it("loads download jobs through TanStack Query", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [],
            total: 0,
          }),
      }),
    );

    const { result } = renderHook(() => useDownloadJobs(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total).toBe(0);
  });
});
