import { YkButton } from "@/components/system/YkButton";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { ConversationFileCard } from "@/features/conversations/components/ConversationFileCard";
import { type ConversationFileItem } from "@/features/conversations/utils/conversation-files";
import { YkErrorState, YkSkeleton } from "@/shared/components";
import { YkIcons } from "@/shared/icons";

type ConversationFileListProps = {
  files: ConversationFileItem[];
  isLoading: boolean;
  isError: boolean;
  hasMore: boolean;
  isFetchingMore: boolean;
  onLoadMore: () => void;
  searchTerm: string;
};

export function ConversationFileList({
  files,
  isLoading,
  isError,
  hasMore,
  isFetchingMore,
  onLoadMore,
  searchTerm,
}: ConversationFileListProps) {
  if (isError) {
    return (
      <div className="grid min-h-0 flex-1 place-items-center overflow-auto p-4">
        <YkErrorState />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-0 flex-1 overflow-auto p-4">
        <div className="grid gap-2">
          <YkSkeleton className="h-[74px]" />
          <YkSkeleton className="h-[74px]" />
          <YkSkeleton className="h-[74px]" />
          <YkSkeleton className="h-[74px]" />
        </div>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="grid min-h-0 flex-1 place-items-center overflow-auto p-4">
        <YkEmptyState
          icon={searchTerm ? YkIcons.SearchX : YkIcons.FolderOpen}
          title={searchTerm ? "Nenhum arquivo encontrado" : "Nenhum arquivo recebido"}
          description={
            searchTerm
              ? "A busca considera nome, extensao, categoria e remetente."
              : "Quando este remetente enviar midias, os arquivos aparecerão aqui."
          }
        />
      </div>
    );
  }

  return (
    <div className="min-h-0 flex-1 overflow-auto p-4">
      <div className="grid gap-2">
        {files.map((file) => (
          <ConversationFileCard key={file.id} file={file} />
        ))}
      </div>
      {hasMore ? (
        <div className="mt-3 flex justify-center">
          <YkButton type="button" variant="secondary" size="sm" onClick={onLoadMore} disabled={isFetchingMore}>
            <YkIcons.RefreshCcw className={isFetchingMore ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
            {isFetchingMore ? "Carregando" : "Carregar anteriores"}
          </YkButton>
        </div>
      ) : null}
    </div>
  );
}
