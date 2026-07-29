import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { fetchBackendHealth } from "@/services/health-service";
import { renderShellRoute } from "@/test/render-shell";

vi.mock("@/services/health-service", () => ({
  fetchBackendHealth: vi.fn(),
}));

describe("routes", () => {
  it("redirects the root route to dashboard", async () => {
    vi.mocked(fetchBackendHealth).mockResolvedValue({ status: "ok" });

    renderShellRoute("/");

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });

  it("renders the downloads page", async () => {
    vi.mocked(fetchBackendHealth).mockResolvedValue({ status: "ok" });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ items: [], total: 0 }),
      }),
    );

    renderShellRoute("/downloads");

    expect(await screen.findByText("Fila vazia.")).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "Downloads" })).toHaveLength(2);
  });
});
