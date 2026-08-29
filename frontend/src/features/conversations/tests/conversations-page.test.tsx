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

function mediaMessage(id: string, name: string, createdAt: string) {
  return {
    id,
    conversation_id: "abc",
    direction: "INBOUND",
    message_type: "image",
    content: name,
    created_at: createdAt,
    status: "RECEBIDA",
    sender_name: "Maria",
    media_metadata: {
      media_id: id,
      file_name: name,
      file_path: `C:\\YkMedia\\Louvores\\${name}`,
      size: 2048,
      exists: true,
    },
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

  it("keeps contacts and file timeline in independent scroll containers", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(conversationListPayload()) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(detailPayload()) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(messagesPayload()) }),
    );

    const { container } = wrapper(<ConversationsPage />, "/conversas/abc");

    await waitFor(() => expect(screen.getByText("foto-culto.jpg")).toBeInTheDocument());

    const scrollContainers = Array.from(container.querySelectorAll(".overflow-auto"));
    const contactsScroll = scrollContainers.find((element) => element.textContent?.includes("Maria"));
    const filesScroll = scrollContainers.find((element) => element.textContent?.includes("foto-culto.jpg"));

    expect(contactsScroll).toBeDefined();
    expect(filesScroll).toBeDefined();
    expect(contactsScroll).not.toBe(filesScroll);

    if (contactsScroll && filesScroll) {
      contactsScroll.scrollTop = 40;
      expect(filesScroll.scrollTop).toBe(0);
    }
  });

  it("filters the timeline by file search without reintroducing text messages", async () => {
    const twoFilesPayload = {
      items: [
        mediaMessage("msg-1", "foto-culto.jpg", "2026-07-29T10:02:00+00:00"),
        mediaMessage("msg-2", "roteiro.pdf", "2026-07-29T10:03:00+00:00"),
      ],
      total: 1,
      page: 1,
      page_size: 50,
      has_next: false,
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(conversationListPayload()) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(detailPayload()) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(twoFilesPayload) }),
    );
    const user = userEvent.setup();

    wrapper(<ConversationsPage />, "/conversas/abc");

    await waitFor(() => expect(screen.getByText("roteiro.pdf")).toBeInTheDocument());
    expect(screen.getByText("foto-culto.jpg")).toBeInTheDocument();

    await user.type(
      screen.getByPlaceholderText("Buscar por arquivo, extensao, categoria ou remetente..."),
      "roteiro",
    );

    expect(screen.getByText("roteiro.pdf")).toBeInTheDocument();
    expect(screen.queryByText("foto-culto.jpg")).not.toBeInTheDocument();
  });

  it("loads older files without duplicating already loaded items", async () => {
    const pageOne = {
      items: [mediaMessage("msg-1", "recente.jpg", "2026-07-29T10:05:00+00:00")],
      total: 2,
      page: 1,
      page_size: 50,
      has_next: true,
    };
    const pageTwo = {
      items: [mediaMessage("msg-2", "antigo.jpg", "2026-07-29T09:00:00+00:00")],
      total: 2,
      page: 2,
      page_size: 50,
      has_next: false,
    };

    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.includes("/conversations/abc/messages")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(url.includes("page=2") ? pageTwo : pageOne),
          });
        }
        if (url.includes("/conversations/abc")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(detailPayload()) });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve(conversationListPayload()) });
      }),
    );
    const user = userEvent.setup();

    wrapper(<ConversationsPage />, "/conversas/abc");

    await waitFor(() => expect(screen.getByText("recente.jpg")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /carregar anteriores/i }));

    await waitFor(() => expect(screen.getByText("antigo.jpg")).toBeInTheDocument());
    expect(screen.getAllByText("recente.jpg")).toHaveLength(1);
    expect(screen.getAllByText("antigo.jpg")).toHaveLength(1);
  });
});
