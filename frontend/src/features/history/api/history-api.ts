import { ValidationError } from "@/shared/errors";
import { httpClient } from "@/shared/services";
import {
  historyResponseSchema,
  type HistoryResponse,
} from "@/features/history/types";

export async function fetchHistory(): Promise<HistoryResponse> {
  const payload = await httpClient.getJson<unknown>("/history");
  const parsed = historyResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("History payload is invalid.", parsed.error);
  }

  return parsed.data;
}
