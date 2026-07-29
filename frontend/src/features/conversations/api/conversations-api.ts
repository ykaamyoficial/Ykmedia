import { ValidationError } from "@/shared/errors";
import { httpClient } from "@/shared/services";
import {
  conversationDetailsSchema,
  conversationListResponseSchema,
  conversationMessagesResponseSchema,
  type ConversationDetails,
  type ConversationListFilters,
  type ConversationListResponse,
  type ConversationMessagesResponse,
} from "@/features/conversations/types";

function toQuery(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function fetchConversations(
  filters: ConversationListFilters,
): Promise<ConversationListResponse> {
  const payload = await httpClient.getJson<unknown>(
    `/conversations${toQuery({
      page: filters.page,
      page_size: filters.pageSize,
      search: filters.search,
    })}`,
  );
  const parsed = conversationListResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Conversation list payload is invalid.", parsed.error);
  }

  return parsed.data;
}

export async function fetchConversationDetails(conversationId: string): Promise<ConversationDetails> {
  const payload = await httpClient.getJson<unknown>(`/conversations/${conversationId}`);
  const parsed = conversationDetailsSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Conversation details payload is invalid.", parsed.error);
  }

  return parsed.data;
}

export async function fetchConversationMessages(
  conversationId: string,
  page: number,
  pageSize: number,
): Promise<ConversationMessagesResponse> {
  const payload = await httpClient.getJson<unknown>(
    `/conversations/${conversationId}/messages${toQuery({
      page,
      page_size: pageSize,
    })}`,
  );
  const parsed = conversationMessagesResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Conversation messages payload is invalid.", parsed.error);
  }

  return parsed.data;
}
