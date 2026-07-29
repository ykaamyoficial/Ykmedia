import { useQuery } from "@tanstack/react-query";

import { fetchFiles } from "@/features/files/api";
import { queryKeys } from "@/shared/query";

export function useFiles() {
  return useQuery({
    queryKey: queryKeys.files.list,
    queryFn: fetchFiles,
    refetchInterval: 15000,
    staleTime: 10000,
  });
}
