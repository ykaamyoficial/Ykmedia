import { z } from "zod";

export const fileLibraryItemSchema = z.object({
  id: z.string(),
  date: z.string(),
  date_display: z.string(),
  sender: z.string(),
  sender_raw: z.string(),
  origin: z.string(),
  category: z.string(),
  final_name: z.string(),
  file_path: z.string(),
  absolute_path: z.string(),
  kind: z.string(),
  status: z.string(),
  size: z.string(),
  exists: z.boolean(),
});

export const fileLibraryResponseSchema = z.object({
  items: z.array(fileLibraryItemSchema),
  total: z.number(),
});

export type FileLibraryItem = z.infer<typeof fileLibraryItemSchema>;
export type FileLibraryResponse = z.infer<typeof fileLibraryResponseSchema>;

export type FileOriginFilter = string;
export type FileCategoryFilter = string;
