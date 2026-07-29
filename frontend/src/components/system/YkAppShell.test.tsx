import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { fetchBackendHealth } from "@/services/health-service";
import { renderShellRoute } from "@/test/render-shell";

vi.mock("@/services/health-service", () => ({
  fetchBackendHealth: vi.fn(),
}));

describe("YkAppShell", () => {
  it("keeps header, sidebar and page content visible", async () => {
    vi.mocked(fetchBackendHealth).mockResolvedValue({ status: "ok" });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ items: [], total: 0 }),
      }),
    );

    renderShellRoute("/historico");

    expect(screen.getByRole("navigation", { name: /navegacao principal/i })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "Historico" })).toHaveLength(2);
    expect(await screen.findByText("Nenhuma midia processada ainda.")).toBeInTheDocument();
    expect(await screen.findByText("Backend online")).toBeInTheDocument();
  });
});
