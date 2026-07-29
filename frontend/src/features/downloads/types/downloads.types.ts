import { z } from "zod";

export const downloadJobStatusSchema = z.enum(["PENDENTE", "PROCESSANDO", "CONCLUIDO", "ERRO"]);

export const downloadJobItemSchema = z.object({
  id: z.string(),
  short_id: z.string(),
  sender: z.string(),
  sender_raw: z.string(),
  origin: z.string(),
  file: z.string(),
  kind: z.string(),
  status: downloadJobStatusSchema,
  created_at: z.string(),
});

export const downloadJobsResponseSchema = z.object({
  items: z.array(downloadJobItemSchema),
  total: z.number(),
});

export const clearCompletedDownloadsResponseSchema = z.object({
  removed: z.number(),
});

export type DownloadJobStatus = z.infer<typeof downloadJobStatusSchema>;
export type DownloadJobItem = z.infer<typeof downloadJobItemSchema>;
export type DownloadJobsResponse = z.infer<typeof downloadJobsResponseSchema>;
export type ClearCompletedDownloadsResponse = z.infer<typeof clearCompletedDownloadsResponseSchema>;

export const downloadStatusFilterOptions = [
  "Todos",
  "PENDENTE",
  "PROCESSANDO",
  "CONCLUIDO",
  "ERRO",
] as const;

export type DownloadStatusFilter = (typeof downloadStatusFilterOptions)[number];
