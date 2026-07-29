import { describe, expect, it, vi } from "vitest";

import { fetchCategories, saveCategories } from "@/features/categories/api";
import { ValidationError } from "@/shared/errors";

const categoriesPayload = {
  items: [
    {
      position: 1,
      name: "Louvores",
      folder: "C:\\media\\Louvores",
    },
  ],
  total: 1,
};

describe("categories api", () => {
  it("loads and validates categories", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(categoriesPayload),
      }),
    );

    await expect(fetchCategories()).resolves.toMatchObject({
      total: 1,
      items: [{ name: "Louvores" }],
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

    await expect(fetchCategories()).rejects.toBeInstanceOf(ValidationError);
  });

  it("saves the ordered category list", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(categoriesPayload),
    });
    vi.stubGlobal("fetch", fetcher);

    await expect(saveCategories(["Louvores"])).resolves.toMatchObject({ total: 1 });
    expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/categories",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ categories: ["Louvores"] }),
      }),
    );
  });
});
