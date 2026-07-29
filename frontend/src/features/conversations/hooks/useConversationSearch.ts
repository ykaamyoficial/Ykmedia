import { useState } from "react";

import { useDebounce } from "@/shared/hooks";

export function useConversationSearch(initialValue = "") {
  const [search, setSearch] = useState(initialValue);
  const [debouncedSearch, setDebouncedSearch] = useState(initialValue);

  useDebounce(search, 300, setDebouncedSearch);

  return {
    search,
    setSearch,
    debouncedSearch,
  };
}
