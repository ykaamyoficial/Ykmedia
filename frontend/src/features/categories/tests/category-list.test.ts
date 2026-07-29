import { describe, expect, it } from "vitest";

import { moveCategory, removeCategoryAt, replaceCategoryAt } from "@/features/categories/utils";

describe("category list utilities", () => {
  it("replaces, removes and moves categories", () => {
    expect(replaceCategoryAt(["Louvores", "Mensagens"], 1, "Jovens")).toEqual(["Louvores", "Jovens"]);
    expect(removeCategoryAt(["Louvores", "Mensagens"], 0)).toEqual(["Mensagens"]);
    expect(moveCategory(["Louvores", "Mensagens"], 1, -1)).toEqual(["Mensagens", "Louvores"]);
    expect(moveCategory(["Louvores", "Mensagens"], 0, -1)).toEqual(["Louvores", "Mensagens"]);
  });
});
