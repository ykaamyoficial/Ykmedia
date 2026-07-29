import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkIcons } from "@/shared/icons";

const kindIcon = {
  Imagem: YkIcons.Image,
  Audio: YkIcons.Music,
  Video: YkIcons.Video,
  Documento: YkIcons.FileText,
  YouTube: YkIcons.Video,
  Arquivo: YkIcons.File,
} as const;

export function FileKindBadge({ kind }: { kind: string }) {
  const Icon = kindIcon[kind as keyof typeof kindIcon] ?? YkIcons.File;

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-panel px-2 py-1 text-xs font-medium text-foreground">
      <Icon className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
      {kind || "Arquivo"}
    </span>
  );
}

export function FileStatusBadge({ status }: { status: string }) {
  const tone = status === "CONCLUIDO" ? "success" : status === "ERRO" ? "danger" : "neutral";
  return <YkStatusBadge label={status || "-"} tone={tone} />;
}
