import { YkAvatar } from "@/components/system/YkAvatar";
import { type ConversationDetails } from "@/features/conversations/types";
import { formatConversationTimestamp } from "@/features/conversations/utils";
import { YkIcons } from "@/shared/icons";
import { formatCount } from "@/shared/utils";

type ConversationHeaderProps = {
  details: ConversationDetails;
  isFetching: boolean;
  fileCount: number;
  lastSync?: string | null;
};

export function ConversationHeader({
  details,
  isFetching,
  fileCount,
  lastSync,
}: ConversationHeaderProps) {
  return (
    <header className="flex items-center justify-between gap-4 border-b border-border px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <YkAvatar
          name={details.profile.display_name}
          imageUrl={details.profile.profile_photo_url ?? undefined}
          size="lg"
          alt={`Foto de ${details.profile.display_name}`}
        />
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold text-foreground">{details.profile.display_name}</h2>
          <p className="mt-1 truncate text-xs text-secondary">
            {formatCount(fileCount)} arquivos
            {lastSync ? ` - Ultima sincronizacao ${formatConversationTimestamp(lastSync)}` : ""}
          </p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="hidden items-center gap-1.5 rounded-full border border-border bg-panel px-2 py-1 text-xs text-secondary lg:inline-flex">
          <YkIcons.RefreshCcw className={isFetching ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
          {isFetching ? "Atualizando" : "Dados recentes"}
        </span>
        {details.category ? <span className="rounded-full bg-muted px-2 py-1 text-xs text-secondary">{details.category}</span> : null}
      </div>
    </header>
  );
}
