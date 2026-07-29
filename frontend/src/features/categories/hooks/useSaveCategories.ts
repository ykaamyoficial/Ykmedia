import { useMutation, useQueryClient } from "@tanstack/react-query";

import { saveCategories } from "@/features/categories/api";
import { queryKeys } from "@/shared/query";

export function useSaveCategories() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: saveCategories,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.categories.list });
    },
  });
}
