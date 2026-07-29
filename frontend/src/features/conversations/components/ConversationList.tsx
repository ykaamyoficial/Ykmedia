import { YkButton } from "@/components/system/YkButton";
import { YkPanel } from "@/components/system/YkPanel";
import { ConversationListItem } from "@/features/conversations/components/ConversationListItem";
import { type ConversationListItem as ConversationListItemType } from "@/features/conversations/types";
import { conversationPagination } from "@/features/conversations/utils";
import { YkErrorState, YkNoDataState, YkNoResultsState, YkOfflineState, YkPagination, YkSearchBox, YkSkeleton } from "@/shared/components";
import { YkIcons } from "@/shared/icons";

type ConversationListProps = {
  conversations: ConversationListItemType[];
  total: number;
  page: number;
  search: string;
  selectedId?: string;
  isLoading: boolean;
  isError: boolean;
  isOffline: boolean;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onSelect: (id: string) => void;
  onRefresh: () => void;
};

export function ConversationList({
  conversations,
  total,
  page,
  search,
  selectedId,
  isLoading,
  isError,
  isOffline,
  onSearchChange,
  onPageChange,
  onSelect,
  onRefresh,
}: ConversationListProps) {
  const pageCount = Math.max(1, Math.ceil(total / conversationPagination.conversationsPageSize));

  return (
    <YkPanel className="flex min-h-0 w-[320px] shrink-0 flex-col overflow-hidden">
      <div className="border-b border-border p-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Remetentes</h2>
            <p className="text-xs text-secondary">{total} contatos</p>
          </div>
          <YkButton type="button" variant="secondary" size="sm" onClick={onRefresh} aria-label="Atualizar conversas">
            <YkIcons.RefreshCcw className="h-4 w-4" />
          </YkButton>
        </div>
        <div className="mt-3">
          <YkSearchBox
            value={search}
            onChange={onSearchChange}
            placeholder="Buscar remetente ou arquivo..."
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-2">
        {isOffline ? <YkOfflineState /> : null}
        {isError && !isOffline ? <YkErrorState /> : null}
        {isLoading ? (
          <div className="grid gap-2">
            <YkSkeleton className="h-16" />
            <YkSkeleton className="h-16" />
            <YkSkeleton className="h-16" />
          </div>
        ) : null}
        {!isLoading && !isError && !isOffline && conversations.length === 0 ? (
          search ? <YkNoResultsState /> : <YkNoDataState />
        ) : null}
        {!isLoading && !isError && !isOffline && conversations.length > 0 ? (
          <div className="grid gap-1">
            {conversations.map((item) => (
              <ConversationListItem
                key={item.id}
                item={item}
                selected={item.id === selectedId}
                onSelect={onSelect}
              />
            ))}
          </div>
        ) : null}
      </div>

      {total > conversationPagination.conversationsPageSize ? (
        <div className="border-t border-border p-3">
          <YkPagination page={page} pageCount={pageCount} onPageChange={onPageChange} />
        </div>
      ) : null}
    </YkPanel>
  );
}
