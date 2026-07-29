import { useQuery } from "@tanstack/react-query";

import { fetchDownloadJobs } from "@/features/downloads/api";
import { queryKeys } from "@/shared/query";

export function useDownloadJobs() {
  return useQuery({
    queryKey: queryKeys.downloads.jobs,
    queryFn: fetchDownloadJobs,
    refetchInterval: 10000,
    staleTime: 5000,
  });
}
