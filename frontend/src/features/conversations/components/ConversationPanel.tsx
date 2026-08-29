import { useMemo, useState } from "react";

import { YkPanel } from "@/components/system/YkPanel";
import { ConversationFileList } from "@/features/conversations/components/ConversationFileList";
import { ConversationHeader } from "@/features/conversations/components/ConversationHeader";
import { type ConversationDetails, type ConversationMessageItem } from "@/features/conversations/types";
import { buildConversationFiles, fileMatchesSearch } from "@/features/conversations/utils";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkErrorState, YkSearchBox, YkSkeleton } from "@/shared/components";
import { YkIcons } from "@/shared/icons";

type ConversationPanelProps = {
  selectedId?: string;
  details?: ConversationDetails;
  messages: ConversationMessageItem[];
  detailsLoading: boolean;
  detailsError: boolean;
  messagesLoading: boolean;
  messagesError: boolean;
  hasMoreMessages: boolean;
  isFetchingMoreMessages: boolean;
  isRefreshing: boolean;
  lastSync?: string | null;
  onLoadMoreMessages: () => void;
};

export function ConversationPanel({
  selectedId,
  details,
  messages,
  detailsLoading,
  detailsError,
  messagesLoading,
  messagesError,
  hasMoreMessages,
  isFetchingMoreMessages,
  isRefreshing,
  lastSync,
  onLoadMoreMessages,
}: ConversationPanelProps) {
  const [fileSearch, setFileSearch] = useState("");
  const files = useMemo(() => buildConversationFiles(messages, details), [details, messages]);
  const filteredFiles = useMemo(
    () => files.filter((file) => fileMatchesSearch(file, fileSearch)),
    [fileSearch, files],
  );

  if (!selectedId) {
    return (
      <YkPanel className="grid min-h-0 flex-1 place-items-center">
        <YkEmptyState
          icon={YkIcons.FolderOpen}
          title="Selecione um remetente"
          description="Escolha um contato para visualizar os arquivos recebidos."
        />
      </YkPanel>
    );
  }

  if (detailsError) {
    return (
      <YkPanel className="grid min-h-0 flex-1 place-items-center">
        <YkErrorState />
      </YkPanel>
    );
  }

  return (
    <YkPanel className="flex min-h-0 flex-1 overflow-hidden">
      <div className="flex min-w-0 flex-1 flex-col">
        {detailsLoading || !details ? (
          <div className="border-b border-border p-4">
            <YkSkeleton className="h-14" />
          </div>
        ) : (
          <ConversationHeader
            details={details}
            isFetching={isRefreshing}
            fileCount={details.message_count}
            lastSync={lastSync}
          />
        )}
        <div className="border-b border-border px-4 py-3">
          <YkSearchBox
            value={fileSearch}
            onChange={setFileSearch}
            placeholder="Buscar por arquivo, extensao, categoria ou remetente..."
          />
        </div>
        <ConversationFileList
          files={filteredFiles}
          isLoading={messagesLoading}
          isError={messagesError}
          hasMore={hasMoreMessages}
          isFetchingMore={isFetchingMoreMessages}
          onLoadMore={onLoadMoreMessages}
          searchTerm={fileSearch}
        />
      </div>
    </YkPanel>
  );
}
