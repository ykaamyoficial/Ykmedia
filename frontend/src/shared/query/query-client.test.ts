import { describe, expect, it } from "vitest";

import { appQueryDefaults, createAppQueryClient, queryKeys } from "@/shared/query";

describe("query infrastructure", () => {
  it("centralizes default query options", () => {
    const client = createAppQueryClient();
    const defaults = client.getDefaultOptions().queries;

    expect(defaults?.staleTime).toBe(appQueryDefaults.staleTime);
    expect(defaults?.gcTime).toBe(appQueryDefaults.gcTime);
    expect(defaults?.retry).toBe(appQueryDefaults.retry);
    expect(defaults?.refetchOnWindowFocus).toBe(false);
  });

  it("centralizes query keys", () => {
    expect(queryKeys.backendHealth).toEqual(["backend-health"]);
    expect(queryKeys.dashboard.overview).toEqual(["dashboard", "overview"]);
  });
});
