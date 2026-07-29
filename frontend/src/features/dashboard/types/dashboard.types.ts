import { z } from "zod";

const healthItemSchema = z.object({
  key: z.string(),
  label: z.string(),
  status: z.string(),
  description: z.string(),
});

const historyItemSchema = z.object({
  id: z.string(),
  date: z.string(),
  sender: z.string(),
  origin: z.string(),
  category: z.string().nullable(),
  final_name: z.string().nullable(),
  file_path: z.string().nullable(),
  status: z.string(),
});

const conversationMessageSchema = z.object({
  sender: z.string(),
  last_content: z.string().nullable(),
  last_activity: z.string().nullable(),
  status: z.string(),
  message_count: z.number(),
});

export const dashboardOverviewSchema = z.object({
  generated_at: z.string(),
  system: z.object({
    version: z.string(),
    uptime_seconds: z.number(),
    backend_online: z.boolean(),
    database_connected: z.boolean(),
  }),
  evolution: z.object({
    online: z.boolean(),
    instance: z.string(),
    last_sync: z.string().nullable(),
    error: z.string().nullable(),
  }),
  whatsapp: z.object({
    status: z.string(),
    connected: z.boolean(),
    qr_pending: z.boolean(),
  }),
  downloads: z.object({
    in_progress: z.number(),
    completed: z.number(),
    failures: z.number(),
    queue: z.number(),
  }),
  files: z.object({
    stored_count: z.number(),
    storage_used_bytes: z.number(),
    categories: z.array(z.string()),
  }),
  conversations: z.object({
    total: z.number(),
    active_contacts: z.number(),
    latest_messages: z.array(conversationMessageSchema),
  }),
  history: z.array(historyItemSchema),
  health: z.array(healthItemSchema),
  has_data: z.boolean(),
});

export type DashboardOverview = z.infer<typeof dashboardOverviewSchema>;
export type DashboardHistoryItem = z.infer<typeof historyItemSchema>;
