import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { formatMessageDate, formatMessageTime } from "@/features/conversations/utils";
import { type ConversationFileItem } from "@/features/conversations/utils/conversation-files";
import { MediaActions, MediaName, MediaTypeIcon } from "@/shared/media";

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
  const date = formatMessageDate(file.createdAt);
  const time = formatMessageTime(file.createdAt);
  const canOpen = Boolean(file.path && file.exists);

  return (
    <article className="group rounded-xl border border-border bg-panel/80 p-3 transition hover:border-accent/45 hover:bg-panel-elevated">
      <div className="flex min-w-0 items-center gap-3">
        <MediaTypeIcon kind={file.kind} />

        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-foreground">
            <MediaName name={file.name} />
          </h3>
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

        <MediaActions path={file.path} canOpen={canOpen} fileName={file.name} />
      </div>
    </article>
  );
}
