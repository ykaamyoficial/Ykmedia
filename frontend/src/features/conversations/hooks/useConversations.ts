import { useQuery } from "@tanstack/react-query";

import { fetchConversations } from "@/features/conversations/api";
import { conversationPagination, conversationPolling } from "@/features/conversations/utils";
import { useOnlineStatus } from "@/shared/hooks";
import { queryKeys } from "@/shared/query";

type UseConversationsParams = {
  page: number;
  search: string;
};

export function useConversations({ page, search }: UseConversationsParams) {
  const isOnline = useOnlineStatus();
  const filters = {
    page,
    pageSize: conversationPagination.conversationsPageSize,
    search,
  };

  return useQuery({
    queryKey: queryKeys.conversations.list(filters),
    queryFn: () => fetchConversations(filters),
    enabled: isOnline,
    refetchInterval: isOnline ? conversationPolling.listMs : false,
    placeholderData: (previous) => previous,
  });
}
