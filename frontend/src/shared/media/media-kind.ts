import { YkIcons } from "@/shared/icons";
import { type LucideIcon } from "@/shared/icons/YkIcons";

export type MediaKind =
  | "image"
  | "audio"
  | "video"
  | "pdf"
  | "zip"
  | "document"
  | "youtube"
  | "text"
  | "file";

const backendLabelToKind: Record<string, MediaKind> = {
  Imagem: "image",
  Audio: "audio",
  Video: "video",
  Documento: "document",
  YouTube: "youtube",
  Arquivo: "file",
};

const knownKinds: ReadonlySet<string> = new Set<MediaKind>([
  "image",
  "audio",
  "video",
  "pdf",
  "zip",
  "document",
  "youtube",
  "text",
  "file",
]);

// Reconcilia o rotulo em portugues do backend ("Imagem") com o kind por extensao usado em Conversas ("image").
export function normalizeMediaKind(rawKind?: string | null): MediaKind {
  if (!rawKind) {
    return "file";
  }

  if (knownKinds.has(rawKind)) {
    return rawKind as MediaKind;
  }

  return backendLabelToKind[rawKind] ?? "file";
}

export function mediaKindFromExtension(extension?: string | null): MediaKind | undefined {
  const normalized = (extension ?? "").toLowerCase().replace(/^\./, "");
  if (!normalized) {
    return undefined;
  }
  if (["jpg", "jpeg", "png", "webp", "gif", "bmp"].includes(normalized)) {
    return "image";
  }
  if (["mp3", "wav", "ogg", "m4a", "aac", "flac"].includes(normalized)) {
    return "audio";
  }
  if (["mp4", "mov", "avi", "mkv", "webm"].includes(normalized)) {
    return "video";
  }
  if (normalized === "pdf") {
    return "pdf";
  }
  if (["zip", "rar", "7z"].includes(normalized)) {
    return "zip";
  }
  if (["txt", "md", "rtf"].includes(normalized)) {
    return "text";
  }
  return "document";
}

const kindLabels: Record<MediaKind, string> = {
  image: "Imagem",
  audio: "Audio",
  video: "Video",
  pdf: "PDF",
  zip: "Arquivo ZIP",
  document: "Documento",
  youtube: "YouTube",
  text: "Texto",
  file: "Arquivo",
};

export function mediaKindLabel(kind: MediaKind): string {
  return kindLabels[kind];
}

const kindIcons: Record<MediaKind, LucideIcon> = {
  image: YkIcons.Image,
  audio: YkIcons.Music,
  video: YkIcons.Video,
  pdf: YkIcons.FileText,
  zip: YkIcons.Archive,
  document: YkIcons.FileText,
  youtube: YkIcons.Play,
  text: YkIcons.FileText,
  file: YkIcons.File,
};

export function mediaKindIcon(kind: MediaKind): LucideIcon {
  return kindIcons[kind];
}

const kindTones: Record<MediaKind, "success" | "accent" | "warning" | "danger" | "neutral"> = {
  image: "success",
  audio: "accent",
  video: "warning",
  pdf: "danger",
  zip: "neutral",
  document: "neutral",
  youtube: "danger",
  text: "neutral",
  file: "neutral",
};

export function mediaKindTone(kind: MediaKind): "success" | "accent" | "warning" | "danger" | "neutral" {
  return kindTones[kind];
}
