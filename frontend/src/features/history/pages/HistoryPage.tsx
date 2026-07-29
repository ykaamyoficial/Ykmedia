import { useMemo, useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkPage } from "@/components/system/YkPage";
import { navigationItems } from "@/routes/navigation";
import { YkErrorState } from "@/shared/components";
import { friendlyErrorMessage } from "@/shared/errors";
import { YkIcons } from "@/shared/icons";
import { toast } from "@/shared/toast";
import { HistoryTable, HistoryToolbar } from "@/features/history/components";
import { useHistory } from "@/features/history/hooks";
import {
  type HistoryCategoryFilter,
  type HistoryOriginFilter,
} from "@/features/history/types";
import {
  filterHistory,
  uniqueHistoryCategories,
  uniqueHistoryOrigins,
} from "@/features/history/utils";

const historyItem = navigationItems.find((item) => item.path === "/historico") ?? navigationItems[0];

export function HistoryPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<HistoryCategoryFilter>("Todos");
  const [origin, setOrigin] = useState<HistoryOriginFilter>("Todas");
  const historyQuery = useHistory();

  const items = useMemo(() => historyQuery.data?.items ?? [], [historyQuery.data?.items]);
  const categories = useMemo(() => uniqueHistoryCategories(items), [items]);
  const origins = useMemo(() => uniqueHistoryOrigins(items), [items]);
  const filteredItems = useMemo(
    () => filterHistory(items, { search, category, origin }),
    [items, search, category, origin],
  );

  function refreshHistory() {
    void historyQuery.refetch();
  }

  if (historyQuery.isError) {
    return (
      <YkPage item={historyItem}>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Historico</h1>
          <p className="text-sm text-secondary">Midias processadas e arquivos organizados.</p>
        </div>
        <YkErrorState />
        <YkButton
          variant="secondary"
          className="w-fit"
          onClick={() => {
            toast.error("Nao foi possivel carregar o historico.", friendlyErrorMessage(historyQuery.error));
            refreshHistory();
          }}
        >
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Tentar novamente
        </YkButton>
      </YkPage>
    );
  }

  const showEmpty = !historyQuery.isLoading && filteredItems.length === 0;

  return (
    <YkPage item={historyItem}>
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Historico</h1>
        <p className="text-sm text-secondary">Midias processadas e arquivos organizados.</p>
      </div>

      <HistoryToolbar
        search={search}
        category={category}
        origin={origin}
        categories={categories}
        origins={origins}
        refreshing={historyQuery.isFetching}
        total={filteredItems.length}
        onSearchChange={setSearch}
        onCategoryChange={setCategory}
        onOriginChange={setOrigin}
        onRefresh={refreshHistory}
      />

      {showEmpty ? (
        <YkEmptyState
          icon={YkIcons.History}
          title="Nenhuma midia processada ainda."
          description="Os arquivos organizados aparecerao aqui apos o primeiro fluxo concluido."
        />
      ) : (
        <HistoryTable items={filteredItems} loading={historyQuery.isLoading} />
      )}
    </YkPage>
  );
}
