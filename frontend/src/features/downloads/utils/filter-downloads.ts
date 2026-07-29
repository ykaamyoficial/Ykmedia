import {
  type DownloadJobItem,
  type DownloadStatusFilter,
} from "@/features/downloads/types";

export type DownloadFilters = {
  search: string;
  status: DownloadStatusFilter;
};

export function filterDownloadJobs(
  jobs: DownloadJobItem[],
  filters: DownloadFilters,
): DownloadJobItem[] {
  const normalizedSearch = filters.search.trim().toLowerCase();

  return jobs.filter((job) => {
    const matchesStatus = filters.status === "Todos" || job.status === filters.status;
    if (!matchesStatus) {
      return false;
    }

    if (!normalizedSearch) {
      return true;
    }

    return Object.values(job).some((value) =>
      String(value).toLowerCase().includes(normalizedSearch),
    );
  });
}
