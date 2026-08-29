import {
  type FileCategoryFilter,
  type FileLibraryItem,
  type FileOriginFilter,
} from "@/features/files/types";

export type FileFilters = {
  search: string;
  category: FileCategoryFilter;
  origin: FileOriginFilter;
};

export function filterFiles(files: FileLibraryItem[], filters: FileFilters): FileLibraryItem[] {
  const normalizedSearch = filters.search.trim().toLowerCase();

  return files.filter((file) => {
    if (filters.category !== "Todos" && file.category !== filters.category) {
      return false;
    }

    if (filters.origin !== "Todas" && file.origin !== filters.origin) {
      return false;
    }

    if (!normalizedSearch) {
      return true;
    }

    return Object.values(file).some((value) =>
      String(value).toLowerCase().includes(normalizedSearch),
    );
  });
}

export function uniqueFileCategories(files: FileLibraryItem[]): string[] {
  return Array.from(new Set(files.map((file) => file.category).filter(Boolean))).sort();
}

export function uniqueFileOrigins(files: FileLibraryItem[]): string[] {
  return Array.from(new Set(files.map((file) => file.origin).filter(Boolean))).sort();
}

export function fileDisplayName(file: FileLibraryItem): string {
  return file.final_name || file.file_path || "Arquivo";
}
