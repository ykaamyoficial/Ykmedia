import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useSetupProgress } from "@/features/settings/hooks/useSetupProgress";
import { HttpClient } from "@/shared/services";

function makeWrapper() {
  // O client precisa sobreviver aos re-renders: criado dentro do wrapper, cada
  // render comecava com um cache vazio e a consulta nunca se estabilizava.
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useSetupProgress", () => {
  it("does not ask the backend while nothing is being prepared", () => {
    // Consultar sem preparo em curso seria trafego inutil a cada segundo.
    const request = vi.spyOn(HttpClient.prototype, "getJson");

    renderHook(() => useSetupProgress(false), { wrapper: makeWrapper() });

    expect(request).not.toHaveBeenCalled();
  });

  it("reports the step in flight while preparing", async () => {
    vi.spyOn(HttpClient.prototype, "getJson").mockResolvedValue({
      running: true,
      status: "RUNNING",
      message: "Preparando o sistema...",
      steps: [
        { key: "config", label: "Configuracao", status: "OK", message: "pronto" },
        { key: "environment", label: "Ambiente", status: "RUNNING", message: "Em andamento..." },
      ],
    });

    const { result } = renderHook(() => useSetupProgress(true), { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(result.current?.steps).toHaveLength(2);
    });
    expect(result.current?.steps[1].status).toBe("RUNNING");
  });

  it("survives a failed poll without breaking the screen", async () => {
    // O backend fica ocupado durante o preparo: uma consulta pode falhar, e
    // isso nao pode derrubar a tela que mostra o andamento.
    vi.spyOn(HttpClient.prototype, "getJson").mockRejectedValue(new Error("timeout"));

    const { result } = renderHook(() => useSetupProgress(true), { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(result.current).toBeUndefined();
    });
  });
});
