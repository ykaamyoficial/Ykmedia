import { z } from "zod";

export const historyItemSchema = z.object({
  id: z.string(),
  date: z.string(),
  date_display: z.string(),
  sender: z.string(),
  sender_raw: z.string(),
  origin: z.string(),
  category: z.string(),
  final_name: z.string(),
  file_path: z.string(),
  kind: z.string(),
  status: z.string(),
});

export const historyResponseSchema = z.object({
  items: z.array(historyItemSchema),
  total: z.number(),
});

export type HistoryItem = z.infer<typeof historyItemSchema>;
export type HistoryResponse = z.infer<typeof historyResponseSchema>;
export type HistoryCategoryFilter = string;
export type HistoryOriginFilter = string;
