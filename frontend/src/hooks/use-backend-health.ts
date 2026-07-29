import { useQuery } from "@tanstack/react-query";

import { fetchBackendHealth } from "@/services/health-service";
import { queryKeys } from "@/shared/query";

export function useBackendHealth() {
  return useQuery({
    queryKey: queryKeys.backendHealth,
    queryFn: fetchBackendHealth,
    refetchInterval: (query) => {
      if (query.state.status === "success") {
        return 30000;
      }
      return 5000;
    },
  });
}
