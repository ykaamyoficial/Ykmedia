import { z } from "zod";

export const conversationListItemSchema = z.object({
  id: z.string(),
  contact_id: z.string(),
  display_name: z.string(),
  phone: z.string(),
  profile_photo_url: z.string().nullable(),
  last_message_preview: z.string().nullable(),
  last_message_at: z.string().nullable(),
  last_message_direction: z.string().nullable(),
  unread_count: z.number(),
  session_status: z.string().nullable(),
  category: z.string().nullable(),
  is_active: z.boolean(),
  message_count: z.number(),
});

export const conversationListResponseSchema = z.object({
  items: z.array(conversationListItemSchema),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
  has_next: z.boolean(),
});

export const conversationProfileSchema = z.object({
  display_name: z.string(),
  phone: z.string(),
  profile_photo_url: z.string().nullable(),
  profile_photo_path: z.string().nullable(),
});

export const conversationDetailsSchema = z.object({
  id: z.string(),
  contact_id: z.string(),
  profile: conversationProfileSchema,
  session_status: z.string().nullable(),
  category: z.string().nullable(),
  created_at: z.string().nullable(),
  updated_at: z.string().nullable(),
  additional_status: z.string().nullable(),
  message_count: z.number(),
  unread_count: z.number(),
  is_active: z.boolean(),
});

export const conversationMessageItemSchema = z.object({
  id: z.string(),
  conversation_id: z.string(),
  direction: z.string(),
  message_type: z.string(),
  content: z.string(),
  created_at: z.string(),
  status: z.string(),
  sender_name: z.string(),
  media_metadata: z.record(z.unknown()).nullable(),
});

export const conversationMessagesResponseSchema = z.object({
  items: z.array(conversationMessageItemSchema),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
  has_next: z.boolean(),
});

export type ConversationListItem = z.infer<typeof conversationListItemSchema>;
export type ConversationListResponse = z.infer<typeof conversationListResponseSchema>;
export type ConversationDetails = z.infer<typeof conversationDetailsSchema>;
export type ConversationMessageItem = z.infer<typeof conversationMessageItemSchema>;
export type ConversationMessagesResponse = z.infer<typeof conversationMessagesResponseSchema>;

export type ConversationListFilters = {
  page: number;
  pageSize: number;
  search: string;
};
