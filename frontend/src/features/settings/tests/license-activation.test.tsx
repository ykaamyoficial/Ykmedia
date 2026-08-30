import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useEvolutionLicenseActivation } from "@/features/settings/hooks";

const startEvolutionLicenseRegistration = vi.fn();
const fetchEvolutionLicense = vi.fn();

vi.mock("@/features/settings/api", () => ({
  startEvolutionLicenseRegistration: () => startEvolutionLicenseRegistration() as Promise<unknown>,
  fetchEvolutionLicense: () => fetchEvolutionLicense() as Promise<unknown>,
}));

const PENDING = {
  status: "PENDENTE",
  register_url: "https://license.test/register?token=abc",
  message: "",
};

describe("useEvolutionLicenseActivation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    startEvolutionLicenseRegistration.mockReset().mockResolvedValue(PENDING);
    fetchEvolutionLicense.mockReset().mockResolvedValue({ status: "PENDENTE", message: "" });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns the registration url to open in the browser", async () => {
    const { result } = renderHook(() => useEvolutionLicenseActivation());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.phase).toBe("waiting");
    expect(result.current.registerUrl).toBe("https://license.test/register?token=abc");
  });

  it("detects the activation without a manual refresh", async () => {
    const onActivated = vi.fn();
    const { result } = renderHook(() => useEvolutionLicenseActivation(onActivated));

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    // O cadastro termina no navegador; quem instala numa igreja nao tem por que
    // saber que precisa voltar e clicar em "Verificar".
    fetchEvolutionLicense.mockResolvedValue({ status: "ATIVA", message: "Licenca ativa." });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(result.current.phase).toBe("activated");
    expect(result.current.registerUrl).toBeNull();
    expect(onActivated).toHaveBeenCalled();
  });

  it("skips the browser when the license is already active", async () => {
    startEvolutionLicenseRegistration.mockResolvedValue({
      status: "ATIVA",
      register_url: null,
      message: "Licenca ja estava ativa.",
    });
    const { result } = renderHook(() => useEvolutionLicenseActivation());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.phase).toBe("activated");
  });

  it("gives up after the registration token expires", async () => {
    const { result } = renderHook(() => useEvolutionLicenseActivation());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(26 * 60 * 1000);
    });

    expect(result.current.phase).toBe("error");
    expect(result.current.errorMessage).toContain("expirou");
  });

  it("reports a backend failure", async () => {
    startEvolutionLicenseRegistration.mockRejectedValue(new Error("offline"));
    const { result } = renderHook(() => useEvolutionLicenseActivation());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.phase).toBe("error");
    expect(result.current.errorMessage).toContain("backend");
  });

  it("stops polling when cancelled", async () => {
    const { result } = renderHook(() => useEvolutionLicenseActivation());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });
    act(() => result.current.stop());

    const callsAfterStop = fetchEvolutionLicense.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    expect(fetchEvolutionLicense.mock.calls.length).toBe(callsAfterStop);
    expect(result.current.phase).toBe("idle");
  });
});
