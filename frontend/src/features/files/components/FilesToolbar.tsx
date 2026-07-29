import { YkButton } from "@/components/system/YkButton";
import { YkSearchBox } from "@/shared/components/YkSearchBox";
import { YkSelect } from "@/shared/forms";
import { YkIcons } from "@/shared/icons";
import {
  type FileCategoryFilter,
  type FileOriginFilter,
} from "@/features/files/types";

type FilesToolbarProps = {
  search: string;
  category: FileCategoryFilter;
  origin: FileOriginFilter;
  categories: string[];
  origins: string[];
  refreshing: boolean;
  total: number;
  onSearchChange: (value: string) => void;
  onCategoryChange: (value: FileCategoryFilter) => void;
  onOriginChange: (value: FileOriginFilter) => void;
  onRefresh: () => void;
};

export function FilesToolbar({
  search,
  category,
  origin,
  categories,
  origins,
  refreshing,
  total,
  onSearchChange,
  onCategoryChange,
  onOriginChange,
  onRefresh,
}: FilesToolbarProps) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-panel-elevated p-3 xl:flex-row xl:items-center xl:justify-between">
      <div className="grid flex-1 gap-3 md:grid-cols-[minmax(260px,1fr)_180px_180px]">
        <YkSearchBox
          value={search}
          onChange={onSearchChange}
          placeholder="Buscar por nome, remetente ou categoria..."
        />
        <label className="flex items-center gap-2 text-xs font-medium text-secondary">
          Categoria
          <YkSelect
            aria-label="Filtrar por categoria"
            value={category}
            onChange={(event) => onCategoryChange(event.target.value)}
          >
            <option value="Todos">Todos</option>
            {categories.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </YkSelect>
        </label>
        <label className="flex items-center gap-2 text-xs font-medium text-secondary">
          Origem
          <YkSelect
            aria-label="Filtrar por origem"
            value={origin}
            onChange={(event) => onOriginChange(event.target.value)}
          >
            <option value="Todas">Todas</option>
            {origins.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </YkSelect>
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-xs text-secondary">{total} registros</span>
        <YkButton variant="secondary" size="sm" disabled={refreshing} onClick={onRefresh}>
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Atualizar
        </YkButton>
      </div>
    </div>
  );
}
