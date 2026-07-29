export const conversationPolling = {
  listMs: 15000,
  detailsMs: 10000,
  messagesMs: 7000,
} as const;

export const conversationPagination = {
  conversationsPageSize: 30,
  messagesPageSize: 50,
} as const;
