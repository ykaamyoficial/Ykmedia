import { useQuery } from "@tanstack/react-query";

import { fetchHistory } from "@/features/history/api";
import { queryKeys } from "@/shared/query";

export function useHistory() {
  return useQuery({
    queryKey: queryKeys.history.list,
    queryFn: fetchHistory,
    refetchInterval: 15000,
    staleTime: 10000,
  });
}
