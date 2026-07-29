import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  ConversationContextPanel,
  ConversationLocalSearchBar,
  ConversationMessageBubble,
  ConversationWorkspaceInfoBar,
  MessageContextMenu,
} from "@/features/conversations/components";
import { ConversationWorkspaceProvider, useConversationWorkspace } from "@/features/conversations/providers";
import { groupMessagesByDate } from "@/features/conversations/utils";

const details = {
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
  additional_status: "RECEBIDA",
  message_count: 4,
  unread_count: 0,
  is_active: true,
};

const message = {
  id: "msg-1",
  conversation_id: "abc",
  direction: "INBOUND",
  message_type: "text",
  content: "Arquivo recebido pela sonoplastia",
  created_at: "2026-07-29T10:00:00+00:00",
  status: "RECEBIDA",
  sender_name: "Maria",
  media_metadata: null,
};

function WorkspaceSearchFixture() {
  const { setSearchOpen } = useConversationWorkspace();
  return (
    <>
      <button type="button" onClick={() => setSearchOpen(true)}>
        Abrir busca
      </button>
      <ConversationLocalSearchBar matchCount={1} />
    </>
  );
}

describe("conversation workspace", () => {
  it("renders context panel with real conversation metadata", () => {
    render(<ConversationContextPanel details={details} onClose={vi.fn()} />);

    expect(screen.getByText("Contexto")).toBeInTheDocument();
    expect(screen.getByText("WhatsApp")).toBeInTheDocument();
    expect(screen.getByText("WAITING_CATEGORY")).toBeInTheDocument();
    expect(screen.getByText("Louvores")).toBeInTheDocument();
  });

  it("renders workspace info bar", () => {
    render(
      <ConversationWorkspaceInfoBar
        loadedMessages={2}
        totalMessages={4}
        lastSync="2026-07-29T10:00:00+00:00"
        pollingActive
        isFetching={false}
      />,
    );

    expect(screen.getByText("2 de 4 mensagens carregadas")).toBeInTheDocument();
    expect(screen.getByText("Polling ativo")).toBeInTheDocument();
  });

  it("uses workspace provider for local search", async () => {
    const user = userEvent.setup();
    render(
      <ConversationWorkspaceProvider>
        <WorkspaceSearchFixture />
      </ConversationWorkspaceProvider>,
    );

    expect(screen.queryByPlaceholderText("Buscar nesta conversa...")).not.toBeInTheDocument();
    await user.click(screen.getByText("Abrir busca"));
    expect(screen.getByPlaceholderText("Buscar nesta conversa...")).toBeInTheDocument();
  });

  it("highlights message search terms", () => {
    render(
      <ConversationMessageBubble
        message={message}
        searchTerm="sonoplastia"
        activeMatch
        onContextMenu={vi.fn()}
      />,
    );

    expect(screen.getByText("sonoplastia")).toBeInTheDocument();
  });

  it("copies text from message context menu", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    render(<MessageContextMenu message={message} position={{ x: 0, y: 0 }} onClose={vi.fn()} />);

    fireEvent.click(screen.getByText("Copiar texto"));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("Arquivo recebido pela sonoplastia"));
  });

  it("groups messages by date", () => {
    const groups = groupMessagesByDate([
      message,
      { ...message, id: "msg-2", created_at: "2026-07-29T11:00:00+00:00" },
    ]);

    expect(groups).toHaveLength(1);
    expect(groups[0].messages).toHaveLength(2);
  });
});
