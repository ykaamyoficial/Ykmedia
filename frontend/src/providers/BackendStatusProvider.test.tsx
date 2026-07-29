import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useBackendStatus } from "@/providers/useBackendStatus";
import { fetchBackendHealth } from "@/services/health-service";
import { renderWithShellProviders } from "@/test/render-shell";

vi.mock("@/services/health-service", () => ({
  fetchBackendHealth: vi.fn(),
}));

function StatusProbe() {
  const backend = useBackendStatus();
  return <span>{backend.state}</span>;
}

describe("BackendStatusProvider", () => {
  it("centralizes the online backend state", async () => {
    vi.mocked(fetchBackendHealth).mockResolvedValue({ status: "ok" });

    renderWithShellProviders(<StatusProbe />);

    expect(await screen.findByText("online")).toBeInTheDocument();
  });

  it("centralizes the offline backend state", async () => {
    vi.mocked(fetchBackendHealth).mockRejectedValue(new Error("offline"));

    renderWithShellProviders(<StatusProbe />);

    expect(await screen.findByText("offline")).toBeInTheDocument();
  });
});
