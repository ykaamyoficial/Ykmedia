import { describe, expect, it, vi } from "vitest";

import { ValidationError } from "@/shared/errors/app-error";
import { fetchDashboardOverview } from "@/features/dashboard/api";

function dashboardPayload() {
  return {
    generated_at: "2026-07-29T10:00:00+00:00",
    system: {
      version: "0.1.0",
      uptime_seconds: 10,
      backend_online: true,
      database_connected: true,
    },
    evolution: {
      online: true,
      instance: "ykmedia",
      last_sync: "2026-07-29T10:00:00+00:00",
      error: null,
    },
    whatsapp: {
      status: "connected",
      connected: true,
      qr_pending: false,
    },
    downloads: {
      in_progress: 0,
      completed: 1,
      failures: 0,
      queue: 0,
    },
    files: {
      stored_count: 1,
      storage_used_bytes: 5,
      categories: ["Louvores"],
    },
    conversations: {
      total: 1,
      active_contacts: 0,
      latest_messages: [],
    },
    history: [],
    health: [],
    has_data: true,
  };
}

describe("fetchDashboardOverview", () => {
  it("loads and validates dashboard overview", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(dashboardPayload()),
      }),
    );

    await expect(fetchDashboardOverview()).resolves.toMatchObject({
      files: { stored_count: 1 },
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

    await expect(fetchDashboardOverview()).rejects.toBeInstanceOf(ValidationError);
  });
});
