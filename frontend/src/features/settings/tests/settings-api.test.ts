import { describe, expect, it, vi } from "vitest";

import {
  connectEvolutionSession,
  fetchSettings,
  runDiagnostics,
  saveSettings,
} from "@/features/settings/api";

const settingsPayload = {
  downloads_root: "C:/YkMedia/Midias",
  ffmpeg_path: "C:/ffmpeg/bin/ffmpeg.exe",
  sqlite_database: "data/ykmedia.sqlite3",
  whatsapp_instance: "ykmedia",
  evolution_state: "open",
  evolution_message: "Estado atualizado.",
};

describe("settings api", () => {
  it("fetches and validates settings", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(settingsPayload) }));

    await expect(fetchSettings()).resolves.toEqual(settingsPayload);
  });

  it("saves only the existing PySide6 settings fields", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(settingsPayload) });
    vi.stubGlobal("fetch", fetcher);

    await saveSettings(settingsPayload);

    expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/settings",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({
          downloads_root: settingsPayload.downloads_root,
          ffmpeg_path: settingsPayload.ffmpeg_path,
          sqlite_database: settingsPayload.sqlite_database,
          whatsapp_instance: settingsPayload.whatsapp_instance,
        }),
      }),
    );
  });

  it("calls existing settings command endpoints", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ instance_name: "ykmedia", state: "connecting", message: "QR Code solicitado.", qrcode_base64: "base64" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: "OK", message: "Pronto.", items: [] }),
      });
    vi.stubGlobal("fetch", fetcher);

    await expect(connectEvolutionSession()).resolves.toMatchObject({ qrcode_base64: "base64" });
    await expect(runDiagnostics()).resolves.toMatchObject({ status: "OK" });
  });
});
