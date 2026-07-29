import { useQuery } from "@tanstack/react-query";

import { fetchDashboardOverview } from "@/features/dashboard/api";
import { queryKeys } from "@/shared/query";

export function useDashboardOverview() {
  return useQuery({
    queryKey: queryKeys.dashboard.overview,
    queryFn: fetchDashboardOverview,
    refetchInterval: 15000,
    staleTime: 10000,
  });
}
