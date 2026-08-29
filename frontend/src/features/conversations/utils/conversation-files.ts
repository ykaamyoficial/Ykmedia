import { mediaKindFromExtension, mediaKindLabel, normalizeMediaKind, type MediaKind } from "@/shared/media";
import { formatBytes } from "@/shared/utils";

import { type ConversationDetails, type ConversationMessageItem } from "@/features/conversations/types";

export type ConversationFileItem = {
  id: string;
  name: string;
  extension: string;
  kind: MediaKind;
  typeLabel: string;
  createdAt: string;
  status?: string;
  category?: string | null;
  sizeLabel?: string;
  path?: string;
  exists: boolean;
  senderName?: string;
};

const mediaTypeHints = ["image", "audio", "video", "document", "media", "file", "youtube"];

function metadataString(metadata: Record<string, unknown> | null, keys: string[]) {
  if (!metadata) {
    return undefined;
  }

  for (const key of keys) {
    const value = metadata[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return undefined;
}

function metadataNumber(metadata: Record<string, unknown> | null, keys: string[]) {
  if (!metadata) {
    return undefined;
  }

  for (const key of keys) {
    const value = metadata[key];
    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === "string") {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
  }

  return undefined;
}

function basename(value?: string) {
  if (!value) {
    return undefined;
  }

  return value.replace(/\\/g, "/").split("/").filter(Boolean).pop();
}

function extensionFromName(name: string) {
  const match = /\.([a-z0-9]{1,12})$/i.exec(name.trim());
  return match?.[1]?.toLowerCase() ?? "";
}

function kindFromMessage(message: ConversationMessageItem, extension: string): MediaKind {
  const byExtension = mediaKindFromExtension(extension);
  if (byExtension) {
    return byExtension;
  }

  const normalizedType = message.message_type.toLowerCase();
  return normalizeMediaKind(
    ["image", "audio", "video", "youtube", "document"].find((hint) => normalizedType.includes(hint)),
  );
}

function hasMedia(message: ConversationMessageItem) {
  if (metadataString(message.media_metadata, ["final_name", "file_name", "filename", "file_path", "absolute_path", "path"])) {
    return true;
  }

  const normalizedType = message.message_type.toLowerCase();
  return normalizedType !== "text" && mediaTypeHints.some((hint) => normalizedType.includes(hint));
}

function fileNameFromMessage(message: ConversationMessageItem) {
  const metadata = message.media_metadata;
  const path = metadataString(metadata, ["absolute_path", "file_path", "path", "relative_path", "url"]);
  const metadataName = metadataString(metadata, [
    "final_name",
    "file_name",
    "filename",
    "name",
    "original_name",
    "title",
  ]);
  const pathName = basename(path);
  const contentName = message.message_type.toLowerCase() !== "text" && message.content.trim()
    ? message.content.trim()
    : undefined;

  return metadataName ?? pathName ?? contentName ?? "Arquivo recebido";
}

export function buildConversationFiles(
  messages: ConversationMessageItem[],
  details?: ConversationDetails,
): ConversationFileItem[] {
  return messages
    .filter(hasMedia)
    .map((message) => {
      const metadata = message.media_metadata;
      const name = fileNameFromMessage(message);
      const extension = extensionFromName(name);
      const kind = kindFromMessage(message, extension);
      const size = metadataNumber(metadata, ["size", "file_size", "bytes", "fileSize"]);
      const path = metadataString(metadata, ["absolute_path", "file_path", "path", "stored_path"]);
      const existsValue = metadata?.exists;

      return {
        id: message.id,
        name,
        extension,
        kind,
        typeLabel: mediaKindLabel(kind),
        createdAt: message.created_at,
        status: message.status,
        category: metadataString(metadata, ["category"]) ?? details?.category ?? null,
        sizeLabel: size ? formatBytes(size) : undefined,
        path,
        exists: typeof existsValue === "boolean" ? existsValue : Boolean(path),
        senderName: message.sender_name || details?.profile.display_name,
      };
    })
    .sort((first, second) => {
      return new Date(second.createdAt).getTime() - new Date(first.createdAt).getTime();
    });
}

export function fileMatchesSearch(file: ConversationFileItem, searchTerm: string) {
  const normalized = searchTerm.trim().toLowerCase();
  if (!normalized) {
    return true;
  }

  return [
    file.name,
    file.extension,
    file.category,
    file.senderName,
    file.typeLabel,
  ].some((value) => value?.toLowerCase().includes(normalized));
}
