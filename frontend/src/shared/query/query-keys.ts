export const queryKeys = {
  backendHealth: ["backend-health"] as const,
  dashboard: {
    overview: ["dashboard", "overview"] as const,
  },
  downloads: {
    all: ["downloads"] as const,
    jobs: ["downloads", "jobs"] as const,
  },
  files: {
    all: ["files"] as const,
    list: ["files", "list"] as const,
  },
  history: {
    all: ["history"] as const,
    list: ["history", "list"] as const,
  },
  categories: {
    all: ["categories"] as const,
    list: ["categories", "list"] as const,
  },
  settings: {
    all: ["settings"] as const,
    detail: ["settings", "detail"] as const,
    evolution: ["settings", "evolution"] as const,
    diagnostics: ["settings", "diagnostics"] as const,
  },
  conversations: {
    all: ["conversations"] as const,
    list: (filters: { page: number; pageSize: number; search: string }) =>
      ["conversations", "list", filters] as const,
    detail: (conversationId: string) => ["conversations", "detail", conversationId] as const,
    messages: (conversationId: string, pageSize: number) =>
      ["conversations", "messages", conversationId, pageSize] as const,
  },
} as const;
