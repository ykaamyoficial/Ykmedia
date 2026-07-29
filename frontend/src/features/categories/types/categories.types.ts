import { z } from "zod";

export const categoryItemSchema = z.object({
  position: z.number(),
  name: z.string(),
  folder: z.string(),
});

export const categoriesResponseSchema = z.object({
  items: z.array(categoryItemSchema),
  total: z.number(),
});

export const saveCategoriesResponseSchema = categoriesResponseSchema;

export type CategoryItem = z.infer<typeof categoryItemSchema>;
export type CategoriesResponse = z.infer<typeof categoriesResponseSchema>;
