import { z } from "zod";

export const appSettingsSchema = z.object({
  downloads_root: z.string(),
  ffmpeg_path: z.string(),
  sqlite_database: z.string(),
  whatsapp_instance: z.string(),
  evolution_state: z.string(),
  evolution_message: z.string(),
});

export const saveAppSettingsSchema = appSettingsSchema;

export const evolutionSessionSchema = z.object({
  instance_name: z.string(),
  state: z.string(),
  message: z.string(),
  qrcode_base64: z.string().nullable().optional(),
});

export const diagnosticItemSchema = z.object({
  key: z.string(),
  name: z.string(),
  status: z.string(),
  message: z.string(),
});

export const diagnosticReportSchema = z.object({
  status: z.string(),
  message: z.string(),
  items: z.array(diagnosticItemSchema),
});

export const setupStepSchema = z.object({
  key: z.string(),
  label: z.string(),
  status: z.string(),
  message: z.string(),
});

export const setupReportSchema = z.object({
  status: z.string(),
  message: z.string(),
  steps: z.array(setupStepSchema),
});

export type AppSettings = z.infer<typeof appSettingsSchema>;
export type EvolutionSession = z.infer<typeof evolutionSessionSchema>;
export type DiagnosticReport = z.infer<typeof diagnosticReportSchema>;
export type SetupReport = z.infer<typeof setupReportSchema>;
