import { describe, expect, it } from "vitest";

import { queryKeys } from "@/shared/query";

describe("conversation query keys", () => {
  it("keeps official query key shapes", () => {
    expect(queryKeys.conversations.list({ page: 1, pageSize: 30, search: "" })).toEqual([
      "conversations",
      "list",
      { page: 1, pageSize: 30, search: "" },
    ]);
    expect(queryKeys.conversations.detail("abc")).toEqual(["conversations", "detail", "abc"]);
    expect(queryKeys.conversations.messages("abc", 50)).toEqual([
      "conversations",
      "messages",
      "abc",
      50,
    ]);
  });
});
