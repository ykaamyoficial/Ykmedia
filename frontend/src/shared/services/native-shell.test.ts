import { afterEach, describe, expect, it, vi } from "vitest";

import { openExternalUrl } from "@/shared/services/native-shell";

const invoke = vi.fn();

vi.mock("@tauri-apps/api/core", () => ({
  invoke: (...args: unknown[]) => invoke(...args) as unknown,
}));

afterEach(() => {
  invoke.mockReset();
  delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
});

describe("openExternalUrl", () => {
  it("uses the command made for web addresses", async () => {
    // `open_media_file` chama o Explorer, que descarta a query string: a URL de
    // cadastro (?redirect_uri=...) abria a pasta Documentos em vez do
    // navegador.
    (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__ = {};
    const url = "http://localhost:8090/license/register?redirect_uri=http%3A%2F%2Flocalhost";

    await openExternalUrl(url);

    expect(invoke).toHaveBeenCalledWith("open_external_url", { url });
    expect(invoke).not.toHaveBeenCalledWith("open_media_file", expect.anything());
  });

  it("ignores an empty address instead of opening a random folder", async () => {
    (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__ = {};

    await openExternalUrl("");

    expect(invoke).not.toHaveBeenCalled();
  });
});
