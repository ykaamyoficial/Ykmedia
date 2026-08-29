import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { YkPage } from "@/components/system/YkPage";
import { ConversationList, ConversationPanel } from "@/features/conversations/components";
import {
  useConversationDetails,
  useConversationMessages,
  useConversationSearch,
  useConversations,
} from "@/features/conversations/hooks";
import { ConversationWorkspaceProvider } from "@/features/conversations/providers";
import { navigationItems } from "@/routes/navigation";
import { internalRoutes } from "@/routes/route-paths";
import { useOnlineStatus } from "@/shared/hooks";

export function ConversationsPage() {
  const navigate = useNavigate();
  const { conversationId } = useParams<{ conversationId: string }>();
  const isOnline = useOnlineStatus();
  const [page, setPage] = useState(1);
  const { search, setSearch, debouncedSearch } = useConversationSearch();
  const conversationsQuery = useConversations({ page, search: debouncedSearch });
  const detailsQuery = useConversationDetails(conversationId);
  const messagesQuery = useConversationMessages(conversationId);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const messages = useMemo(
    () => messagesQuery.data?.pages.slice().reverse().flatMap((response) => response.items) ?? [],
    [messagesQuery.data],
  );
  const lastSync = messagesQuery.dataUpdatedAt > 0 ? new Date(messagesQuery.dataUpdatedAt).toISOString() : null;

  const item = navigationItems.find((navItem) => navItem.path === internalRoutes.conversations) ?? navigationItems[0];

  return (
    <YkPage item={item}>
      <ConversationWorkspaceProvider>
        <section className="flex h-full min-h-[520px] flex-1 gap-4 overflow-hidden">
          <ConversationList
            conversations={conversationsQuery.data?.items ?? []}
            total={conversationsQuery.data?.total ?? 0}
            page={conversationsQuery.data?.page ?? page}
            search={search}
            selectedId={conversationId}
            isLoading={conversationsQuery.isLoading}
            isError={conversationsQuery.isError}
            isOffline={!isOnline}
            onSearchChange={setSearch}
            onPageChange={setPage}
            onRefresh={() => void conversationsQuery.refetch()}
            onSelect={(id) => navigate(`${internalRoutes.conversations}/${id}`)}
          />
          <ConversationPanel
            selectedId={conversationId}
            details={detailsQuery.data}
            messages={messages}
            detailsLoading={detailsQuery.isLoading}
            detailsError={detailsQuery.isError}
            messagesLoading={messagesQuery.isLoading}
            messagesError={messagesQuery.isError}
            hasMoreMessages={messagesQuery.hasNextPage}
            isFetchingMoreMessages={messagesQuery.isFetchingNextPage}
            isRefreshing={detailsQuery.isFetching || messagesQuery.isFetching}
            lastSync={lastSync}
            onLoadMoreMessages={() => void messagesQuery.fetchNextPage()}
          />
        </section>
      </ConversationWorkspaceProvider>
    </YkPage>
  );
}
