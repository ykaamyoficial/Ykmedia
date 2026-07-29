import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StartupPage } from "@/pages/StartupPage";
import { fetchBackendHealth } from "@/services/health-service";
import { createAppQueryClient } from "@/shared/query";

vi.mock("@/services/health-service", () => ({
  fetchBackendHealth: vi.fn(),
}));

const mockedFetchBackendHealth = vi.mocked(fetchBackendHealth);

function renderStartupPage() {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });

  return render(
    <QueryClientProvider client={queryClient}>
      <StartupPage />
    </QueryClientProvider>,
  );
}

describe("StartupPage", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows the backend online state", async () => {
    mockedFetchBackendHealth.mockResolvedValue({ status: "ok" });

    renderStartupPage();

    expect(await screen.findByText("Backend online")).toBeInTheDocument();
    expect(screen.getByText("Sistema pronto para uso.")).toBeInTheDocument();
  });

  it("shows the backend offline state", async () => {
    mockedFetchBackendHealth.mockRejectedValue(new Error("offline"));

    renderStartupPage();

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
    expect(screen.getByText("Tentando estabelecer conexao...")).toBeInTheDocument();
  });

  it("retries when the user clicks the retry button", async () => {
    mockedFetchBackendHealth
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ status: "ok" });

    renderStartupPage();
    await screen.findByText("Backend offline");

    await userEvent.click(screen.getByRole("button", { name: /tentar novamente/i }));

    await waitFor(() => {
      expect(mockedFetchBackendHealth).toHaveBeenCalledTimes(2);
    });
  });
});
