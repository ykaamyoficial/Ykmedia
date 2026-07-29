import { useInfiniteQuery } from "@tanstack/react-query";

import { fetchConversationMessages } from "@/features/conversations/api";
import { conversationPagination, conversationPolling } from "@/features/conversations/utils";
import { useOnlineStatus } from "@/shared/hooks";
import { queryKeys } from "@/shared/query";

export function useConversationMessages(conversationId?: string) {
  const isOnline = useOnlineStatus();
  const pageSize = conversationPagination.messagesPageSize;

  return useInfiniteQuery({
    queryKey: queryKeys.conversations.messages(conversationId ?? "", pageSize),
    queryFn: ({ pageParam }) =>
      fetchConversationMessages(conversationId ?? "", Number(pageParam), pageSize),
    initialPageParam: 1,
    enabled: Boolean(conversationId) && isOnline,
    refetchInterval: isOnline ? conversationPolling.messagesMs : false,
    getNextPageParam: (lastPage) => (lastPage.has_next ? lastPage.page + 1 : undefined),
  });
}
