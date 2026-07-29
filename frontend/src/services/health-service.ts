import { z } from "zod";

import { httpClient } from "@/shared/services/http-client";
import { backendHealthSchema, type BackendHealth } from "@/types/health";

export async function fetchBackendHealth(): Promise<BackendHealth> {
  const payload = await httpClient.getJson<unknown>("/health");

  try {
    return backendHealthSchema.parse(payload);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new Error("Resposta de saude invalida.");
    }
    throw error;
  }
}
