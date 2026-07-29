import { describe, expect, it, vi } from "vitest";

import {
  clearCompletedDownloadJobs,
  fetchDownloadJobs,
} from "@/features/downloads/api";
import { ValidationError } from "@/shared/errors";

describe("downloads api", () => {
  it("loads and validates download jobs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [
              {
                id: "job-123456",
                short_id: "job-1234",
                sender: "+55 62 99999-9999",
                sender_raw: "5562999999999@s.whatsapp.net",
                origin: "WhatsApp",
                file: "foto.jpg",
                kind: "Imagem",
                status: "PENDENTE",
                created_at: "29/07/2026 10:00",
              },
            ],
            total: 1,
          }),
      }),
    );

    await expect(fetchDownloadJobs()).resolves.toMatchObject({
      total: 1,
      items: [{ file: "foto.jpg" }],
    });
  });

  it("rejects invalid download jobs payloads", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ invalid: true }),
      }),
    );

    await expect(fetchDownloadJobs()).rejects.toBeInstanceOf(ValidationError);
  });

  it("clears completed jobs through the backend endpoint", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ removed: 2 }),
    });
    vi.stubGlobal("fetch", fetcher);

    await expect(clearCompletedDownloadJobs()).resolves.toEqual({ removed: 2 });
    expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/downloads/jobs/completed",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
