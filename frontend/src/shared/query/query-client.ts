import { QueryClient } from "@tanstack/react-query";

export const appQueryDefaults = {
  staleTime: 10_000,
  gcTime: 5 * 60_000,
  retry: 1,
  refetchOnWindowFocus: false,
} as const;

export function createAppQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: appQueryDefaults,
    },
  });
}
