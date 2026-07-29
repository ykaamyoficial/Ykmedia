import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchBackendHealth } from "@/services/health-service";

describe("fetchBackendHealth", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("validates an online backend response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: "ok" }),
      }),
    );

    await expect(fetchBackendHealth()).resolves.toEqual({ status: "ok" });
  });

  it("rejects an offline backend response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network")));

    await expect(fetchBackendHealth()).rejects.toThrow("Nao foi possivel conectar");
  });

  it("rejects an invalid health payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: "starting" }),
      }),
    );

    await expect(fetchBackendHealth()).rejects.toThrow("Resposta de saude invalida");
  });
});
