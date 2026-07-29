import { describe, expect, it, vi } from "vitest";

import {
  fetchConversationDetails,
  fetchConversationMessages,
  fetchConversations,
} from "@/features/conversations/api";
import { ValidationError } from "@/shared/errors";

function listPayload() {
  return {
    items: [
      {
        id: "abc",
        contact_id: "5562999999999@s.whatsapp.net",
        display_name: "Maria",
        phone: "(62) 99999-9999",
        profile_photo_url: null,
        last_message_preview: "Arquivo recebido",
        last_message_at: "2026-07-29T10:00:00+00:00",
        last_message_direction: "INBOUND",
        unread_count: 0,
        session_status: null,
        category: null,
        is_active: false,
        message_count: 1,
      },
    ],
    total: 1,
    page: 1,
    page_size: 30,
    has_next: false,
  };
}

describe("conversations api", () => {
  it("loads and validates conversation list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(listPayload()),
      }),
    );

    await expect(fetchConversations({ page: 1, pageSize: 30, search: "maria" })).resolves.toMatchObject({
      total: 1,
    });
  });

  it("rejects invalid list payloads", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ invalid: true }),
      }),
    );

    await expect(fetchConversations({ page: 1, pageSize: 30, search: "" })).rejects.toBeInstanceOf(ValidationError);
  });

  it("loads details and messages", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            id: "abc",
            contact_id: "5562999999999@s.whatsapp.net",
            profile: {
              display_name: "Maria",
              phone: "(62) 99999-9999",
              profile_photo_url: null,
              profile_photo_path: null,
            },
            session_status: null,
            category: null,
            created_at: null,
            updated_at: null,
            additional_status: null,
            message_count: 1,
            unread_count: 0,
            is_active: false,
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [
              {
                id: "msg-1",
                conversation_id: "abc",
                direction: "INBOUND",
                message_type: "text",
                content: "Ola",
                created_at: "2026-07-29T10:00:00+00:00",
                status: "RECEBIDA",
                sender_name: "Maria",
                media_metadata: null,
              },
            ],
            total: 1,
            page: 1,
            page_size: 50,
            has_next: false,
          }),
      });
    vi.stubGlobal("fetch", fetcher);

    await expect(fetchConversationDetails("abc")).resolves.toMatchObject({
      profile: { display_name: "Maria" },
    });
    await expect(fetchConversationMessages("abc", 1, 50)).resolves.toMatchObject({
      items: [{ content: "Ola" }],
    });
  });
});
