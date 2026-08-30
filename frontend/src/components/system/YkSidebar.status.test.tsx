import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { type ReactNode } from "react";

import { useServiceStatus } from "@/hooks/use-service-status";
import { createAppQueryClient } from "@/shared/query";

const fetchEvolutionSession = vi.fn();
let backendOnline = true;

vi.mock("@/features/settings/api", () => ({
  fetchEvolutionSession: () => fetchEvolutionSession() as Promise<unknown>,
}));

vi.mock("@/providers/useBackendStatus", () => ({
  useBackendStatus: () => ({ isOnline: backendOnline }),
}));

function wrapper({ children }: { children: ReactNode }) {
  const client = createAppQueryClient();
  client.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useServiceStatus", () => {
  it("does not claim Evolution is online just because the backend is", async () => {
    // Era o bug: os tres indicadores vinham de backend.isOnline, entao a barra
    // dizia "Evolution Online" enquanto a tela mostrava falha de conexao.
    backendOnline = true;
    fetchEvolutionSession.mockReset().mockResolvedValue({
      instance_name: "ykmedia",
      state: "Erro",
      message: "Nao foi possivel falar com a Evolution.",
    });

    const { result } = renderHook(() => useServiceStatus(), { wrapper });

    await waitFor(() => expect(result.current.evolution).toBe("offline"));
    expect(result.current.backend).toBe("online");
    expect(result.current.whatsapp).toBe("unknown");
  });

  it("reports everything online when the session is open", async () => {
    backendOnline = true;
    fetchEvolutionSession.mockReset().mockResolvedValue({
      instance_name: "ykmedia",
      state: "open",
      message: "",
    });

    const { result } = renderHook(() => useServiceStatus(), { wrapper });

    await waitFor(() => expect(result.current.whatsapp).toBe("online"));
    expect(result.current.evolution).toBe("online");
  });

  it("separates Evolution up from WhatsApp disconnected", async () => {
    backendOnline = true;
    fetchEvolutionSession.mockReset().mockResolvedValue({
      instance_name: "ykmedia",
      state: "close",
      message: "",
    });

    const { result } = renderHook(() => useServiceStatus(), { wrapper });

    await waitFor(() => expect(result.current.whatsapp).toBe("offline"));
    expect(result.current.evolution).toBe("online");
  });

  it("admits it knows nothing while the backend is down", () => {
    backendOnline = false;
    fetchEvolutionSession.mockReset();

    const { result } = renderHook(() => useServiceStatus(), { wrapper });

    expect(result.current.backend).toBe("offline");
    expect(result.current.evolution).toBe("unknown");
    expect(fetchEvolutionSession).not.toHaveBeenCalled();
  });
});
