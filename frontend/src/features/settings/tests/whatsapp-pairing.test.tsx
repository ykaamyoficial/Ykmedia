import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useWhatsAppPairing } from "@/features/settings/hooks";

const connectEvolutionSession = vi.fn();
const fetchEvolutionSession = vi.fn();

vi.mock("@/features/settings/api", () => ({
  connectEvolutionSession: () => connectEvolutionSession() as Promise<unknown>,
  fetchEvolutionSession: () => fetchEvolutionSession() as Promise<unknown>,
}));

function qrSession(state = "close") {
  return { instance_name: "ykmedia", state, message: "QR Code solicitado.", qrcode_base64: "AAA" };
}

describe("useWhatsAppPairing", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    connectEvolutionSession.mockReset().mockResolvedValue(qrSession());
    fetchEvolutionSession.mockReset().mockResolvedValue({ instance_name: "ykmedia", state: "close" });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows the qrcode and starts the countdown", async () => {
    const { result } = renderHook(() => useWhatsAppPairing());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.phase).toBe("waiting");
    expect(result.current.qrcodeBase64).toBe("AAA");
    expect(result.current.secondsLeft).toBeGreaterThan(0);
  });

  it("renews the qrcode before it expires", async () => {
    const { result } = renderHook(() => useWhatsAppPairing());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });
    expect(connectEvolutionSession).toHaveBeenCalledTimes(1);

    // O QR do WhatsApp morre em ~40s: sem renovacao o usuario escaneia um
    // codigo invalido sem receber aviso nenhum.
    await act(async () => {
      vi.advanceTimersByTime(40_000);
      await Promise.resolve();
    });

    expect(connectEvolutionSession.mock.calls.length).toBeGreaterThan(1);
  });

  it("detects the connection without the user pressing anything", async () => {
    const { result } = renderHook(() => useWhatsAppPairing());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    fetchEvolutionSession.mockResolvedValue({ instance_name: "ykmedia", state: "open" });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(result.current.phase).toBe("connected");
    expect(result.current.qrcodeBase64).toBeNull();
  });

  it("reports an error when the backend fails", async () => {
    connectEvolutionSession.mockRejectedValue(new Error("offline"));
    const { result } = renderHook(() => useWhatsAppPairing());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.phase).toBe("error");
    expect(result.current.errorMessage).toContain("backend");
  });

  it("stops cleanly", async () => {
    const { result } = renderHook(() => useWhatsAppPairing());

    act(() => result.current.start());
    await act(async () => {
      await Promise.resolve();
    });
    act(() => result.current.stop());

    expect(result.current.phase).toBe("idle");
    expect(result.current.qrcodeBase64).toBeNull();

    const callsAfterStop = connectEvolutionSession.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(60_000);
      await Promise.resolve();
    });
    expect(connectEvolutionSession.mock.calls.length).toBe(callsAfterStop);
  });
});
