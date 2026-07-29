import { describe, expect, it, vi } from "vitest";

import { fetchFiles } from "@/features/files/api";
import { ValidationError } from "@/shared/errors";

const filesPayload = {
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
      absolute_path: "C:\\media\\Louvores\\imagem.jpg",
      kind: "Imagem",
      status: "CONCLUIDO",
      size: "5 B",
      exists: true,
    },
  ],
  total: 1,
};

describe("files api", () => {
  it("loads and validates files", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(filesPayload),
      }),
    );

    await expect(fetchFiles()).resolves.toMatchObject({
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

    await expect(fetchFiles()).rejects.toBeInstanceOf(ValidationError);
  });
});
