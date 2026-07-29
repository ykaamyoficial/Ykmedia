import { useMemo, useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkPage } from "@/components/system/YkPage";
import { navigationItems } from "@/routes/navigation";
import { YkErrorState } from "@/shared/components";
import { friendlyErrorMessage } from "@/shared/errors";
import { YkIcons } from "@/shared/icons";
import { toast } from "@/shared/toast";
import { FilesTable, FilesToolbar } from "@/features/files/components";
import { useFiles } from "@/features/files/hooks";
import {
  type FileCategoryFilter,
  type FileOriginFilter,
} from "@/features/files/types";
import {
  filterFiles,
  uniqueFileCategories,
  uniqueFileOrigins,
} from "@/features/files/utils";

const filesItem = navigationItems.find((item) => item.path === "/arquivos") ?? navigationItems[0];

export function FilesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<FileCategoryFilter>("Todos");
  const [origin, setOrigin] = useState<FileOriginFilter>("Todas");
  const filesQuery = useFiles();

  const files = useMemo(() => filesQuery.data?.items ?? [], [filesQuery.data?.items]);
  const categories = useMemo(() => uniqueFileCategories(files), [files]);
  const origins = useMemo(() => uniqueFileOrigins(files), [files]);
  const filteredFiles = useMemo(
    () => filterFiles(files, { search, category, origin }),
    [files, search, category, origin],
  );

  function refreshFiles() {
    void filesQuery.refetch();
  }

  if (filesQuery.isError) {
    return (
      <YkPage item={filesItem}>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Arquivos</h1>
          <p className="text-sm text-secondary">Biblioteca de midias organizadas.</p>
        </div>
        <YkErrorState />
        <YkButton
          variant="secondary"
          className="w-fit"
          onClick={() => {
            toast.error("Nao foi possivel carregar os arquivos.", friendlyErrorMessage(filesQuery.error));
            refreshFiles();
          }}
        >
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Tentar novamente
        </YkButton>
      </YkPage>
    );
  }

  const showEmpty = !filesQuery.isLoading && filteredFiles.length === 0;

  return (
    <YkPage item={filesItem}>
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Arquivos</h1>
        <p className="text-sm text-secondary">Biblioteca de midias organizadas.</p>
      </div>

      <FilesToolbar
        search={search}
        category={category}
        origin={origin}
        categories={categories}
        origins={origins}
        refreshing={filesQuery.isFetching}
        total={filteredFiles.length}
        onSearchChange={setSearch}
        onCategoryChange={setCategory}
        onOriginChange={setOrigin}
        onRefresh={refreshFiles}
      />

      {showEmpty ? (
        <YkEmptyState
          icon={YkIcons.Archive}
          title="Nenhuma midia processada ainda."
          description="Os arquivos organizados aparecerao aqui apos o primeiro fluxo concluido."
        />
      ) : (
        <FilesTable files={filteredFiles} loading={filesQuery.isLoading} />
      )}
    </YkPage>
  );
}
