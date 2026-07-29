import { useQuery } from "@tanstack/react-query";

import { fetchConversationDetails } from "@/features/conversations/api";
import { conversationPolling } from "@/features/conversations/utils";
import { useOnlineStatus } from "@/shared/hooks";
import { queryKeys } from "@/shared/query";

export function useConversationDetails(conversationId?: string) {
  const isOnline = useOnlineStatus();

  return useQuery({
    queryKey: queryKeys.conversations.detail(conversationId ?? ""),
    queryFn: () => fetchConversationDetails(conversationId ?? ""),
    enabled: Boolean(conversationId) && isOnline,
    refetchInterval: isOnline ? conversationPolling.detailsMs : false,
    placeholderData: (previous) => previous,
  });
}
