import { describe, expect, it, vi } from "vitest";

import { NetworkError, ServerError, UnknownError } from "@/shared/errors/app-error";
import { HttpClient, setApiAuthToken } from "@/shared/services/http-client";

function response(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

describe("HttpClient", () => {
  it("returns valid JSON responses", async () => {
    const fetcher = vi.fn().mockResolvedValue(response({ status: "ok" }));
    const client = new HttpClient({ baseUrl: "http://api.test", fetcher });

    await expect(client.getJson("/health")).resolves.toEqual({ status: "ok" });
    expect(fetcher).toHaveBeenCalledWith("http://api.test/health", expect.any(Object));
  });

  it("maps network failures", async () => {
    const client = new HttpClient({
      baseUrl: "http://api.test",
      fetcher: vi.fn().mockRejectedValue(new Error("network")),
    });

    await expect(client.getJson("/health")).rejects.toBeInstanceOf(NetworkError);
  });

  it("maps server failures", async () => {
    const client = new HttpClient({
      baseUrl: "http://api.test",
      fetcher: vi.fn().mockResolvedValue(response({}, false, 500)),
    });

    await expect(client.getJson("/health")).rejects.toBeInstanceOf(ServerError);
  });

  it("maps invalid JSON failures", async () => {
    const invalidJsonResponse = response({});
    vi.spyOn(invalidJsonResponse, "json").mockRejectedValue(new Error("invalid"));
    const client = new HttpClient({
      baseUrl: "http://api.test",
      fetcher: vi.fn().mockResolvedValue(invalidJsonResponse),
    });

    await expect(client.getJson("/health")).rejects.toBeInstanceOf(UnknownError);
  });

  it("sends the configured API auth token", async () => {
    const fetcher = vi.fn().mockResolvedValue(response({ status: "ok" }));
    const client = new HttpClient({ baseUrl: "http://api.test", fetcher });

    setApiAuthToken("segredo-local");
    try {
      await client.getJson("/health");
    } finally {
      setApiAuthToken(null);
    }

    const [, request] = fetcher.mock.calls[0] as [string, RequestInit];
    const headers = request.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer segredo-local");
  });

  it("omits the Authorization header when no token is set", async () => {
    const fetcher = vi.fn().mockResolvedValue(response({ status: "ok" }));
    const client = new HttpClient({ baseUrl: "http://api.test", fetcher });

    await client.getJson("/health");

    const [, request] = fetcher.mock.calls[0] as [string, RequestInit];
    const headers = request.headers as Headers;
    expect(headers.has("Authorization")).toBe(false);
  });

  it("retries retryable failures", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new Error("network"))
      .mockResolvedValueOnce(response({ status: "ok" }));
    const client = new HttpClient({ baseUrl: "http://api.test", fetcher, retries: 1 });

    await expect(client.getJson("/health")).resolves.toEqual({ status: "ok" });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});
