import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { fetchBackendHealth } from "@/services/health-service";
import { renderShellRoute } from "@/test/render-shell";

vi.mock("@/services/health-service", () => ({
  fetchBackendHealth: vi.fn(),
}));

describe("YkSidebar", () => {
  it("renders primary navigation items", async () => {
    vi.mocked(fetchBackendHealth).mockResolvedValue({ status: "ok" });

    renderShellRoute("/dashboard");

    expect(screen.getByRole("navigation", { name: /navegacao principal/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /conversas/i })).toBeInTheDocument();
    expect(await screen.findByText("Backend Online")).toBeInTheDocument();
  });

  it("can switch to compact mode", async () => {
    vi.mocked(fetchBackendHealth).mockResolvedValue({ status: "ok" });

    renderShellRoute("/dashboard");

    await userEvent.click(screen.getByRole("button", { name: /compactar sidebar/i }));

    expect(screen.getByRole("button", { name: /expandir sidebar/i })).toBeInTheDocument();
  });
});
