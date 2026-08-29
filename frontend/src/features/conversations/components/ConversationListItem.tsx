import { YkAvatar } from "@/components/system/YkAvatar";
import { cn } from "@/components/ui/utils";
import { type ConversationListItem as ConversationListItemType } from "@/features/conversations/types";
import { formatConversationTimestamp } from "@/features/conversations/utils";
import { formatCount } from "@/shared/utils";

type ConversationListItemProps = {
  item: ConversationListItemType;
  selected: boolean;
  onSelect: (id: string) => void;
};

function lastFilePreview(value?: string | null) {
  const text = value?.trim();
  if (!text) {
    return "Nenhum arquivo";
  }

  const normalized = text.toLowerCase();
  const automaticMessage = [
    "escolha a categoria",
    "nome do arquivo",
    "arquivo recebido pela sonoplastia",
    "responda",
    "!ajuda",
    "!cancelar",
    "!status",
    "!reiniciar",
    "!versao",
  ].some((prefix) => normalized.startsWith(prefix));

  return automaticMessage ? "Aguardando arquivo salvo" : text;
}

export function ConversationListItem({ item, selected, onSelect }: ConversationListItemProps) {
  const lastFileLabel = lastFilePreview(item.last_message_preview);

  return (
    <button
      type="button"
      className={cn(
        "grid w-full grid-cols-[auto_minmax(0,1fr)_auto] gap-3 rounded-xl border p-2.5 text-left transition",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        selected
          ? "border-accent bg-accent/15"
          : "border-transparent bg-transparent hover:border-border hover:bg-panel",
      )}
      onClick={() => onSelect(item.id)}
      aria-current={selected ? "page" : undefined}
    >
      <YkAvatar
        name={item.display_name || item.phone}
        imageUrl={item.profile_photo_url ?? undefined}
        size="md"
        alt={`Foto de ${item.display_name}`}
      />
      <span className="min-w-0">
        <span className="flex items-center gap-2">
          <span className="truncate text-sm font-semibold text-foreground">{item.display_name}</span>
        </span>
        {item.display_name !== item.phone ? (
          <span className="block truncate text-[11px] text-secondary">{item.phone}</span>
        ) : null}
        <span className="mt-0.5 block truncate text-xs text-secondary">
          {lastFileLabel}
        </span>
        <span className="mt-1 block text-[11px] text-secondary">
          {formatCount(item.message_count)} arquivos
        </span>
      </span>
      <span className="flex flex-col items-end gap-1">
        <span className="text-[11px] text-secondary">{formatConversationTimestamp(item.last_message_at)}</span>
        {item.unread_count > 0 && (
          <span className="rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-semibold text-white">
            {item.unread_count}
          </span>
        )}
      </span>
    </button>
  );
}
