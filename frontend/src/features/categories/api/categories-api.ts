import { ValidationError } from "@/shared/errors";
import { httpClient } from "@/shared/services";
import {
  categoriesResponseSchema,
  saveCategoriesResponseSchema,
  type CategoriesResponse,
} from "@/features/categories/types";

export async function fetchCategories(): Promise<CategoriesResponse> {
  const payload = await httpClient.getJson<unknown>("/categories");
  const parsed = categoriesResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Categories payload is invalid.", parsed.error);
  }

  return parsed.data;
}

export async function saveCategories(categories: string[]): Promise<CategoriesResponse> {
  const payload = await httpClient.requestJson<unknown>("/categories", {
    method: "PUT",
    body: { categories },
  });
  const parsed = saveCategoriesResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Save categories payload is invalid.", parsed.error);
  }

  return parsed.data;
}
