import { z } from "zod";

export const backendHealthSchema = z.object({
  status: z.literal("ok"),
});

export type BackendHealth = z.infer<typeof backendHealthSchema>;
