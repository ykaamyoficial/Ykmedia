import { formatConversationTimestamp } from "@/features/conversations/utils";
import { YkIcons } from "@/shared/icons";
import { formatCount } from "@/shared/utils";

type ConversationWorkspaceInfoBarProps = {
  loadedMessages: number;
  totalMessages: number;
  lastSync?: string | null;
  pollingActive: boolean;
  isFetching: boolean;
};

export function ConversationWorkspaceInfoBar({
  loadedMessages,
  totalMessages,
  lastSync,
  pollingActive,
  isFetching,
}: ConversationWorkspaceInfoBarProps) {
  const syncLabel = lastSync ? formatConversationTimestamp(lastSync) : "Sem sincronizacao";
  const pollingLabel = pollingActive ? "Polling ativo" : "Polling pausado";

  return (
    <div className="flex items-center justify-between gap-3 border-b border-border bg-surface/60 px-4 py-2 text-xs text-secondary">
      <div className="flex items-center gap-3">
        <span>
          {formatCount(loadedMessages)} de {formatCount(totalMessages)} mensagens carregadas
        </span>
        <span>Ultima sincronizacao: {syncLabel}</span>
      </div>
      <span className="inline-flex items-center gap-1.5">
        <YkIcons.RefreshCcw className={isFetching ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
        {isFetching ? "Atualizando" : pollingLabel}
      </span>
    </div>
  );
}
