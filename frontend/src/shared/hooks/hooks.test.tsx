import { renderHook, act } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useLocalStorage } from "@/shared/hooks/useLocalStorage";
import { usePrevious } from "@/shared/hooks/usePrevious";
import { useToggle } from "@/shared/hooks/useToggle";

describe("shared hooks", () => {
  it("toggles boolean state", () => {
    const { result } = renderHook(() => useToggle(false));

    act(() => result.current.toggle());

    expect(result.current.enabled).toBe(true);
  });

  it("stores values in local storage", () => {
    const { result } = renderHook(() => useLocalStorage("test-key", "a"));

    act(() => result.current[1]("b"));

    expect(result.current[0]).toBe("b");
    expect(window.localStorage.getItem("test-key")).toBe('"b"');
  });

  it("returns the previous value", () => {
    const { result, rerender } = renderHook(({ value }) => usePrevious(value), {
      initialProps: { value: "first" },
    });

    rerender({ value: "second" });

    expect(result.current).toBe("first");
  });

  it("copies text to clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(window.navigator, { clipboard: { writeText } });
    const { useClipboard } = await import("@/shared/hooks/useClipboard");
    const { result } = renderHook(() => useClipboard());

    await act(async () => result.current.copy("texto"));

    expect(writeText).toHaveBeenCalledWith("texto");
    expect(result.current.copied).toBe(true);
  });
});
