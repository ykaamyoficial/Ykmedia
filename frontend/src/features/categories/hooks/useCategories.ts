import { useQuery } from "@tanstack/react-query";

import { fetchCategories } from "@/features/categories/api";
import { queryKeys } from "@/shared/query";

export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories.list,
    queryFn: fetchCategories,
    staleTime: 10000,
  });
}
