import { describe, expect, it, vi } from "vitest";

import { fetchHistory } from "@/features/history/api";
import { ValidationError } from "@/shared/errors";

const historyPayload = {
  items: [
    {
      id: "hist-1",
      date: "2026-07-29T10:00:00+00:00",
      date_display: "29/07/2026 10:00",
      sender: "+55 62 99999-9999",
      sender_raw: "5562999999999@s.whatsapp.net",
      origin: "WhatsApp",
      category: "Louvores",
      final_name: "imagem.jpg",
      file_path: "Louvores/imagem.jpg",
      kind: "Imagem",
      status: "CONCLUIDO",
    },
  ],
  total: 1,
};

describe("history api", () => {
  it("loads and validates history", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(historyPayload),
      }),
    );

    await expect(fetchHistory()).resolves.toMatchObject({
      total: 1,
      items: [{ final_name: "imagem.jpg" }],
    });
  });

  it("rejects invalid payloads", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ invalid: true }),
      }),
    );

    await expect(fetchHistory()).rejects.toBeInstanceOf(ValidationError);
  });
});
