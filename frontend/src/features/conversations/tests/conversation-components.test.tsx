import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  ConversationFileCard,
  ConversationHeader,
  ConversationListItem,
  ConversationMessageBubble,
} from "@/features/conversations/components";

const conversation = {
  id: "abc",
  contact_id: "5562999999999@s.whatsapp.net",
  display_name: "Maria",
  phone: "(62) 99999-9999",
  profile_photo_url: null,
  last_message_preview: "Arquivo recebido",
  last_message_at: "2026-07-29T10:00:00+00:00",
  last_message_direction: "INBOUND",
  unread_count: 3,
  session_status: "WAITING_CATEGORY",
  category: "Louvores",
  is_active: true,
  message_count: 12,
};

describe("conversation components", () => {
  it("renders list item with fallback avatar and unread badge", () => {
    render(<ConversationListItem item={conversation} selected={false} onSelect={vi.fn()} />);

    expect(screen.getByText("Maria")).toBeInTheDocument();
    expect(screen.getByText("Arquivo recebido")).toBeInTheDocument();
    expect(screen.getByText("12 arquivos")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders list item with profile image", () => {
    render(
      <ConversationListItem
        item={{ ...conversation, profile_photo_url: "https://example.com/avatar.jpg" }}
        selected={false}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.getByAltText("Foto de Maria")).toHaveAttribute("src", "https://example.com/avatar.jpg");
  });

  it("renders conversation header", () => {
    render(
      <ConversationHeader
        details={{
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
          created_at: null,
          updated_at: "2026-07-29T10:00:00+00:00",
          additional_status: null,
          message_count: 12,
          unread_count: 0,
          is_active: true,
        }}
        isFetching={false}
        fileCount={2}
        lastSync="2026-07-29T10:02:00+00:00"
      />,
    );

    expect(screen.getByText("Louvores")).toBeInTheDocument();
    expect(screen.getByText(/2 arquivos/)).toBeInTheDocument();
  });

  it("renders file card with icon-only actions and tooltips", () => {
    render(
      <ConversationFileCard
        file={{
          id: "file-1",
          name: "louvor.mp3",
          extension: "mp3",
          kind: "audio",
          typeLabel: "Audio",
          createdAt: "2026-07-29T10:00:00+00:00",
          status: "RECEBIDA",
          category: "Louvores",
          sizeLabel: "3,2 MB",
          path: "C:\\YkMedia\\Louvores\\louvor.mp3",
          exists: true,
          senderName: "Maria",
        }}
      />,
    );

    expect(screen.getByText("louvor.mp3")).toBeInTheDocument();
    expect(screen.getByLabelText("Abrir arquivo louvor.mp3")).toBeInTheDocument();
    expect(screen.getByLabelText("Abrir pasta de louvor.mp3")).toBeInTheDocument();
    expect(screen.getByText("Abrir arquivo")).toBeInTheDocument();
    expect(screen.getByText("Abrir pasta")).toBeInTheDocument();
  });

  it("renders message bubble without raw html execution", () => {
    render(
      <ConversationMessageBubble
        message={{
          id: "msg-1",
          conversation_id: "abc",
          direction: "INBOUND",
          message_type: "text",
          content: "<strong>ola</strong>",
          created_at: "2026-07-29T10:00:00+00:00",
          status: "RECEBIDA",
          sender_name: "Maria",
          media_metadata: null,
        }}
        onContextMenu={vi.fn()}
      />,
    );

    expect(screen.getByText("<strong>ola</strong>")).toBeInTheDocument();
  });
});
