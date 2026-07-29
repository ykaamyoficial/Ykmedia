import { useMutation, useQueryClient } from "@tanstack/react-query";

import { clearCompletedDownloadJobs } from "@/features/downloads/api";
import { queryKeys } from "@/shared/query";

export function useClearCompletedDownloads() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearCompletedDownloadJobs,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.downloads.jobs });
    },
  });
}
