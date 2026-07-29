import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { useHistory } from "@/features/history/hooks";
import { createAppQueryClient } from "@/shared/query";

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("useHistory", () => {
  it("loads history through TanStack Query", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ items: [], total: 0 }),
      }),
    );

    const { result } = renderHook(() => useHistory(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total).toBe(0);
  });
});
