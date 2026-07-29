import { useLayoutEffect, useMemo, useRef, useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { ConversationMessageGroup } from "@/features/conversations/components/ConversationMessageGroup";
import { MessageContextMenu } from "@/features/conversations/components/MessageContextMenu";
import { useConversationWorkspace } from "@/features/conversations/providers";
import { type ConversationMessageItem } from "@/features/conversations/types";
import { groupMessagesByDate, messageMatchesSearch } from "@/features/conversations/utils";
import { YkErrorState, YkNoHistoryState, YkSkeleton } from "@/shared/components";
import { YkIcons } from "@/shared/icons";

type ConversationMessageListProps = {
  conversationId?: string;
  messages: ConversationMessageItem[];
  isLoading: boolean;
  isError: boolean;
  hasMore: boolean;
  isFetchingMore: boolean;
  onLoadMore: () => void;
};

export function ConversationMessageList({
  conversationId,
  messages,
  isLoading,
  isError,
  hasMore,
  isFetchingMore,
  onLoadMore,
}: ConversationMessageListProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const previousConversationId = useRef<string | undefined>(undefined);
  const previousMessageCount = useRef(0);
  const previousScrollHeight = useRef<number | null>(null);
  const [hasNewMessages, setHasNewMessages] = useState(false);
  const [showJumpToBottom, setShowJumpToBottom] = useState(false);
  const [contextMenu, setContextMenu] = useState<{
    message: ConversationMessageItem;
    position: { x: number; y: number };
  } | null>(null);
  const { messageSearch, activeSearchIndex } = useConversationWorkspace();
  const groups = useMemo(() => groupMessagesByDate(messages), [messages]);
  const searchMatches = useMemo(
    () => messages.filter((message) => messageMatchesSearch(message, messageSearch)),
    [messageSearch, messages],
  );
  const activeMatchId = searchMatches[activeSearchIndex]?.id;

  useLayoutEffect(() => {
    const node = scrollRef.current;
    if (!node) {
      return;
    }

    const changedConversation = previousConversationId.current !== conversationId;
    const nearBottom = node.scrollHeight - node.scrollTop - node.clientHeight < 96;
    const receivedNewMessages = messages.length > previousMessageCount.current;

    if (previousScrollHeight.current !== null && receivedNewMessages) {
      const delta = node.scrollHeight - previousScrollHeight.current;
      node.scrollTop += delta;
      previousScrollHeight.current = null;
    } else if (changedConversation || nearBottom) {
      node.scrollTop = node.scrollHeight;
      setHasNewMessages(false);
      setShowJumpToBottom(false);
    } else if (receivedNewMessages) {
      setHasNewMessages(true);
      setShowJumpToBottom(true);
    }

    previousConversationId.current = conversationId;
    previousMessageCount.current = messages.length;
  }, [conversationId, isFetchingMore, messages.length]);

  if (isError) {
    return <YkErrorState />;
  }

  return (
    <div className="relative min-h-0 flex-1">
      <div
        ref={scrollRef}
        className="h-full overflow-auto px-4 py-3"
        onScroll={(event) => {
          const node = event.currentTarget;
          const nearBottom = node.scrollHeight - node.scrollTop - node.clientHeight < 96;
          setShowJumpToBottom(!nearBottom);
          if (nearBottom) {
            setHasNewMessages(false);
          }
        }}
      >
        {isLoading ? (
          <div className="grid gap-3">
            <YkSkeleton className="h-16" />
            <YkSkeleton className="h-20" />
            <YkSkeleton className="h-14" />
          </div>
        ) : null}

        {!isLoading && messages.length === 0 ? <YkNoHistoryState /> : null}

        {!isLoading && messages.length > 0 ? (
          <div className="mx-auto grid max-w-5xl gap-2">
            {hasMore ? (
              <div className="flex justify-center">
                <YkButton
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    previousScrollHeight.current = scrollRef.current?.scrollHeight ?? null;
                    onLoadMore();
                  }}
                  disabled={isFetchingMore}
                >
                  {isFetchingMore ? "Carregando..." : "Carregar anteriores"}
                </YkButton>
              </div>
            ) : null}
            {groups.map((group) => (
              <ConversationMessageGroup
                key={group.label}
                label={group.label}
                messages={group.messages}
                searchTerm={messageSearch}
                activeMatchId={activeMatchId}
                onContextMenu={(message, position) => setContextMenu({ message, position })}
              />
            ))}
          </div>
        ) : null}
      </div>

      {showJumpToBottom ? (
        <button
          type="button"
          className="absolute bottom-4 right-4 inline-flex items-center gap-1.5 rounded-full border border-border bg-panel px-3 py-1 text-xs font-semibold text-foreground shadow-panel"
          onClick={() => {
            const node = scrollRef.current;
            if (node) {
              node.scrollTop = node.scrollHeight;
            }
            setShowJumpToBottom(false);
            setHasNewMessages(false);
          }}
        >
          <YkIcons.CornerDownRight className="h-3.5 w-3.5" />
          Ir para o final
        </button>
      ) : null}

      {hasNewMessages ? (
        <button
          type="button"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-white shadow-panel"
          onClick={() => {
            const node = scrollRef.current;
            if (node) {
              node.scrollTop = node.scrollHeight;
            }
            setHasNewMessages(false);
          }}
        >
          Novas mensagens
        </button>
      ) : null}
      {contextMenu ? (
        <MessageContextMenu
          message={contextMenu.message}
          position={contextMenu.position}
          onClose={() => setContextMenu(null)}
        />
      ) : null}
    </div>
  );
}
