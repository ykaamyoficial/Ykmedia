import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { fetchBackendHealth } from "@/services/health-service";
import { renderShellRoute } from "@/test/render-shell";

vi.mock("@/services/health-service", () => ({
  fetchBackendHealth: vi.fn(),
}));

describe("YkHeader", () => {
  it("shows the current route title and backend status", async () => {
    vi.mocked(fetchBackendHealth).mockResolvedValue({ status: "ok" });

    renderShellRoute("/categorias");

    expect(screen.getByRole("heading", { name: "Categorias" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Pesquisar...")).toBeInTheDocument();
    expect(await screen.findByText("Backend online")).toBeInTheDocument();
  });
});
