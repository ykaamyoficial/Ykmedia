import { ValidationError } from "@/shared/errors";
import { httpClient } from "@/shared/services";
import {
  clearCompletedDownloadsResponseSchema,
  downloadJobsResponseSchema,
  type ClearCompletedDownloadsResponse,
  type DownloadJobsResponse,
} from "@/features/downloads/types";

export async function fetchDownloadJobs(): Promise<DownloadJobsResponse> {
  const payload = await httpClient.getJson<unknown>("/downloads/jobs");
  const parsed = downloadJobsResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Downloads payload is invalid.", parsed.error);
  }

  return parsed.data;
}

export async function clearCompletedDownloadJobs(): Promise<ClearCompletedDownloadsResponse> {
  const payload = await httpClient.requestJson<unknown>("/downloads/jobs/completed", {
    method: "DELETE",
  });
  const parsed = clearCompletedDownloadsResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Clear completed downloads payload is invalid.", parsed.error);
  }

  return parsed.data;
}
