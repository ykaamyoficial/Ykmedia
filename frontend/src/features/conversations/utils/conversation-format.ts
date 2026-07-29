import { formatConversationDate, formatTime } from "@/shared/utils";
import { type ConversationMessageItem } from "@/features/conversations/types";

export function formatConversationTimestamp(value?: string | null) {
  if (!value) {
    return "";
  }

  const day = formatConversationDate(value);
  const time = formatTime(value);
  return day === "Hoje" ? time : day;
}

export function formatMessageDate(value?: string | null) {
  return formatConversationDate(value);
}

export function formatMessageTime(value?: string | null) {
  return formatTime(value);
}

export function labelForMessageType(type: string) {
  const normalized = type.toLowerCase();
  if (normalized.includes("image")) {
    return "Imagem";
  }
  if (normalized.includes("audio")) {
    return "Audio";
  }
  if (normalized.includes("video")) {
    return "Video";
  }
  if (normalized.includes("document")) {
    return "Documento";
  }
  if (normalized.includes("youtube") || normalized.includes("link")) {
    return "Link";
  }
  return "Texto";
}

export function groupMessagesByDate(messages: ConversationMessageItem[]) {
  const groups = new Map<string, ConversationMessageItem[]>();
  messages.forEach((message) => {
    const label = formatMessageDate(message.created_at) || "Sem data";
    const current = groups.get(label) ?? [];
    current.push(message);
    groups.set(label, current);
  });
  return Array.from(groups.entries()).map(([label, groupedMessages]) => ({
    label,
    messages: groupedMessages,
  }));
}

export function countMessageMatches(messages: ConversationMessageItem[], searchTerm: string) {
  const normalizedSearch = searchTerm.trim().toLowerCase();
  if (!normalizedSearch) {
    return 0;
  }

  return messages.reduce((total, message) => {
    return message.content.toLowerCase().includes(normalizedSearch) ? total + 1 : total;
  }, 0);
}

export function messageMatchesSearch(message: ConversationMessageItem, searchTerm: string) {
  const normalizedSearch = searchTerm.trim().toLowerCase();
  return Boolean(normalizedSearch && message.content.toLowerCase().includes(normalizedSearch));
}

export function highlightText(text: string, searchTerm: string) {
  const normalizedSearch = searchTerm.trim();
  if (!normalizedSearch) {
    return [{ text, highlighted: false }];
  }

  const lowerText = text.toLowerCase();
  const lowerSearch = normalizedSearch.toLowerCase();
  const parts: Array<{ text: string; highlighted: boolean }> = [];
  let cursor = 0;
  let index = lowerText.indexOf(lowerSearch);

  while (index >= 0) {
    if (index > cursor) {
      parts.push({ text: text.slice(cursor, index), highlighted: false });
    }
    parts.push({ text: text.slice(index, index + normalizedSearch.length), highlighted: true });
    cursor = index + normalizedSearch.length;
    index = lowerText.indexOf(lowerSearch, cursor);
  }

  if (cursor < text.length) {
    parts.push({ text: text.slice(cursor), highlighted: false });
  }

  return parts.length > 0 ? parts : [{ text, highlighted: false }];
}
