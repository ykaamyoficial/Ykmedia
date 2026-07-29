import { YkButton } from "@/components/system/YkButton";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkTooltip } from "@/components/system/YkTooltip";
import { cn } from "@/components/ui/utils";
import {
  iconForConversationFile,
  openConversationFile,
  openConversationFileFolder,
  type ConversationFileItem,
} from "@/features/conversations/utils/conversation-files";
import { formatMessageDate, formatMessageTime } from "@/features/conversations/utils";
import { YkIcons } from "@/shared/icons";

type ConversationFileCardProps = {
  file: ConversationFileItem;
};

function statusTone(status?: string) {
  const normalized = status?.toLowerCase() ?? "";
  if (["erro", "error", "failed", "falha"].some((value) => normalized.includes(value))) {
    return "danger";
  }
  if (["pendente", "pending", "aguardando", "processando"].some((value) => normalized.includes(value))) {
    return "warning";
  }
  if (["concluido", "concluído", "success", "recebida", "received"].some((value) => normalized.includes(value))) {
    return "success";
  }
  return "neutral";
}

export function ConversationFileCard({ file }: ConversationFileCardProps) {
  const Icon = iconForConversationFile(file.kind);
  const date = formatMessageDate(file.createdAt);
  const time = formatMessageTime(file.createdAt);
  const canOpen = Boolean(file.path && file.exists);

  return (
    <article className="group rounded-xl border border-border bg-panel/80 p-3 transition hover:border-accent/45 hover:bg-panel-elevated">
      <div className="flex min-w-0 items-center gap-3">
        <div
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-border",
            file.kind === "image" && "bg-success/10 text-success",
            file.kind === "audio" && "bg-accent/10 text-accent",
            file.kind === "video" && "bg-warning/10 text-warning",
            file.kind === "pdf" && "bg-danger/10 text-danger",
            file.kind === "youtube" && "bg-danger/10 text-danger",
            !["image", "audio", "video", "pdf", "youtube"].includes(file.kind) && "bg-muted text-secondary",
          )}
          aria-hidden="true"
        >
          <Icon className="h-5 w-5" />
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-foreground">{file.name}</h3>
          <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-secondary">
            <span>{file.typeLabel}</span>
            {file.sizeLabel ? <span>{file.sizeLabel}</span> : null}
            {date ? <span>{date}</span> : null}
            {time ? <span>{time}</span> : null}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {file.category ? (
              <span className="rounded-full border border-border bg-muted px-2 py-0.5 text-[10px] font-medium text-secondary">
                {file.category}
              </span>
            ) : null}
            {!file.exists ? (
              <span className="rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-[10px] font-medium text-warning">
                Arquivo nao encontrado
              </span>
            ) : null}
            {file.status ? <YkStatusBadge compact tone={statusTone(file.status)} label={file.status} /> : null}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          <YkTooltip label={canOpen ? "Abrir arquivo" : "Arquivo indisponivel"}>
            <YkButton
              type="button"
              variant="secondary"
              size="sm"
              className="h-8 w-8 px-0"
              disabled={!canOpen}
              onClick={() => void openConversationFile(file.path)}
              aria-label={`Abrir arquivo ${file.name}`}
            >
              <YkIcons.Eye className="h-4 w-4" />
            </YkButton>
          </YkTooltip>
          <YkTooltip label={file.path ? "Abrir pasta" : "Pasta indisponivel"}>
            <YkButton
              type="button"
              variant="secondary"
              size="sm"
              className="h-8 w-8 px-0"
              disabled={!file.path}
              onClick={() => void openConversationFileFolder(file.path)}
              aria-label={`Abrir pasta de ${file.name}`}
            >
              <YkIcons.FolderOpen className="h-4 w-4" />
            </YkButton>
          </YkTooltip>
        </div>
      </div>
    </article>
  );
}
