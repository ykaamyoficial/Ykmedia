import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { type ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationsPage } from "@/features/conversations";
import { createAppQueryClient } from "@/shared/query";

function conversationListPayload() {
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
        unread_count: 2,
        session_status: "WAITING_CATEGORY",
        category: "Louvores",
        is_active: true,
        message_count: 4,
      },
    ],
    total: 1,
    page: 1,
    page_size: 30,
    has_next: false,
  };
}

function detailPayload() {
  return {
    id: "abc",
    contact_id: "5562999999999@s.whatsapp.net",
    profile: {
      display_name: "Maria",
      phone: "(62) 99999-9999",
      profile_photo_url: null,
      profile_photo_path: null,
    },
    session_status: "WAITING_CATEGORY",
    category: "Louvores",
    created_at: "2026-07-29T09:00:00+00:00",
    updated_at: "2026-07-29T10:00:00+00:00",
    additional_status: null,
    message_count: 4,
    unread_count: 0,
    is_active: true,
  };
}

function messagesPayload() {
  return {
    items: [
      {
        id: "msg-1",
        conversation_id: "abc",
        direction: "INBOUND",
        message_type: "image",
        content: "foto-culto.jpg",
        created_at: "2026-07-29T10:02:00+00:00",
        status: "RECEBIDA",
        sender_name: "Maria",
        media_metadata: {
          media_id: "media-1",
          file_name: "foto-culto.jpg",
          file_path: "C:\\YkMedia\\Louvores\\foto-culto.jpg",
          size: 2048,
          exists: true,
        },
      },
      {
        id: "msg-2",
        conversation_id: "abc",
        direction: "INBOUND",
        message_type: "text",
        content: "mensagem de texto que nao deve aparecer",
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
  };
}

function wrapper(children: ReactNode, initialPath = "/conversas") {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/conversas" element={children} />
          <Route path="/conversas/:conversationId" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ConversationsPage", () => {
  afterEach(() => {
    Object.defineProperty(window.navigator, "onLine", {
      configurable: true,
      value: true,
    });
  });

  it("renders empty state when there is no selected conversation", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ...conversationListPayload(), items: [], total: 0 }),
      }),
    );

    wrapper(<ConversationsPage />);

    expect(screen.getByText("Selecione um remetente")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Sem dados")).toBeInTheDocument());
  });

  it("loads list, details and messages from route selection", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(conversationListPayload()) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(detailPayload()) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(messagesPayload()) }),
    );

    wrapper(<ConversationsPage />, "/conversas/abc");

    await waitFor(() => expect(screen.getAllByText("Maria").length).toBeGreaterThan(0));
    expect(screen.getByText("foto-culto.jpg")).toBeInTheDocument();
    expect(screen.queryByText("mensagem de texto que nao deve aparecer")).not.toBeInTheDocument();
    expect(screen.getAllByText("Louvores").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Abrir arquivo foto-culto.jpg")).toBeInTheDocument();
  });

  it("updates the URL selection when a conversation is selected", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue({ ok: true, json: () => Promise.resolve(conversationListPayload()) });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    wrapper(<ConversationsPage />);

    await user.click(await screen.findByText("Maria"));
    await waitFor(() =>
      expect(fetcher).toHaveBeenCalledWith(
        "http://127.0.0.1:8010/conversations/abc",
        expect.any(Object),
      ),
    );
  });

  it("renders offline state without requesting conversations", () => {
    Object.defineProperty(window.navigator, "onLine", {
      configurable: true,
      value: false,
    });
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);

    wrapper(<ConversationsPage />);

    expect(screen.getByText("Sem conexao")).toBeInTheDocument();
    expect(fetcher).not.toHaveBeenCalled();
  });
});
