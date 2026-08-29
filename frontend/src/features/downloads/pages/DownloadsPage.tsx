import { useMemo, useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkPage } from "@/components/system/YkPage";
import { navigationItems } from "@/routes/navigation";
import { YkErrorState, YkOfflineState } from "@/shared/components";
import { friendlyErrorMessage, isOfflineError } from "@/shared/errors";
import { YkIcons } from "@/shared/icons";
import { toast } from "@/shared/toast";
import {
  DownloadsTable,
  DownloadsToolbar,
} from "@/features/downloads/components";
import {
  useClearCompletedDownloads,
  useDownloadJobs,
} from "@/features/downloads/hooks";
import {
  type DownloadStatusFilter,
} from "@/features/downloads/types";
import { filterDownloadJobs } from "@/features/downloads/utils";

const downloadsItem =
  navigationItems.find((item) => item.path === "/downloads") ?? navigationItems[0];

export function DownloadsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<DownloadStatusFilter>("Todos");
  const jobsQuery = useDownloadJobs();
  const clearCompleted = useClearCompletedDownloads();

  const filteredJobs = useMemo(
    () =>
      filterDownloadJobs(jobsQuery.data?.items ?? [], {
        search,
        status,
      }),
    [jobsQuery.data?.items, search, status],
  );

  function refreshDownloads() {
    void jobsQuery.refetch();
  }

  function clearCompletedJobs() {
    clearCompleted.mutate(undefined, {
      onSuccess: (result) => {
        toast.success("Fila atualizada.", `${result.removed} job(s) concluido(s) removido(s).`);
      },
      onError: (error) => {
        toast.error("Nao foi possivel limpar a fila.", friendlyErrorMessage(error));
      },
    });
  }

  if (jobsQuery.isError) {
    return (
      <YkPage item={downloadsItem}>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Downloads</h1>
          <p className="text-sm text-secondary">Acompanhamento de downloads.</p>
        </div>
        {isOfflineError(jobsQuery.error) ? <YkOfflineState /> : <YkErrorState />}
        <YkButton variant="secondary" className="w-fit" onClick={refreshDownloads}>
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Tentar novamente
        </YkButton>
      </YkPage>
    );
  }

  const showEmpty = !jobsQuery.isLoading && filteredJobs.length === 0;

  return (
    <YkPage item={downloadsItem}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Downloads</h1>
          <p className="text-sm text-secondary">Acompanhamento de downloads.</p>
        </div>
      </div>

      <DownloadsToolbar
        search={search}
        status={status}
        refreshing={jobsQuery.isFetching}
        clearingCompleted={clearCompleted.isPending}
        onSearchChange={setSearch}
        onStatusChange={setStatus}
        onRefresh={refreshDownloads}
        onClearCompleted={clearCompletedJobs}
      />

      {showEmpty ? (
        <YkEmptyState
          icon={YkIcons.Inbox}
          title="Fila vazia."
          description="Quando uma midia ou link entrar para processamento, o job aparecera aqui."
        />
      ) : (
        <DownloadsTable jobs={filteredJobs} loading={jobsQuery.isLoading} />
      )}
    </YkPage>
  );
}
