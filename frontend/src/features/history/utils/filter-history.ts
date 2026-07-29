import {
  type HistoryCategoryFilter,
  type HistoryItem,
  type HistoryOriginFilter,
} from "@/features/history/types";

export type HistoryFilters = {
  search: string;
  category: HistoryCategoryFilter;
  origin: HistoryOriginFilter;
};

export function filterHistory(items: HistoryItem[], filters: HistoryFilters): HistoryItem[] {
  const normalizedSearch = filters.search.trim().toLowerCase();

  return items.filter((item) => {
    if (filters.category !== "Todos" && item.category !== filters.category) {
      return false;
    }

    if (filters.origin !== "Todas" && item.origin !== filters.origin) {
      return false;
    }

    if (!normalizedSearch) {
      return true;
    }

    return Object.values(item).some((value) =>
      String(value).toLowerCase().includes(normalizedSearch),
    );
  });
}

export function uniqueHistoryCategories(items: HistoryItem[]): string[] {
  return Array.from(new Set(items.map((item) => item.category).filter(Boolean))).sort();
}

export function uniqueHistoryOrigins(items: HistoryItem[]): string[] {
  return Array.from(new Set(items.map((item) => item.origin).filter(Boolean))).sort();
}
