import { YkButton } from "@/components/system/YkButton";
import { YkSearchBox } from "@/shared/components/YkSearchBox";
import { YkSelect } from "@/shared/forms";
import { YkIcons } from "@/shared/icons";
import {
  downloadStatusFilterOptions,
  type DownloadStatusFilter,
} from "@/features/downloads/types";

type DownloadsToolbarProps = {
  search: string;
  status: DownloadStatusFilter;
  refreshing: boolean;
  clearingCompleted: boolean;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: DownloadStatusFilter) => void;
  onRefresh: () => void;
  onClearCompleted: () => void;
};

export function DownloadsToolbar({
  search,
  status,
  refreshing,
  clearingCompleted,
  onSearchChange,
  onStatusChange,
  onRefresh,
  onClearCompleted,
}: DownloadsToolbarProps) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-panel-elevated p-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="grid flex-1 gap-3 md:grid-cols-[minmax(260px,1fr)_180px]">
        <YkSearchBox
          value={search}
          onChange={onSearchChange}
          placeholder="Buscar por remetente, arquivo ou tipo..."
        />
        <label className="flex items-center gap-2 text-xs font-medium text-secondary">
          Status
          <YkSelect
            aria-label="Filtrar por status"
            value={status}
            onChange={(event) => onStatusChange(event.target.value as DownloadStatusFilter)}
          >
            {downloadStatusFilterOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </YkSelect>
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        <YkButton variant="secondary" size="sm" disabled={refreshing} onClick={onRefresh}>
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Atualizar
        </YkButton>
        <YkButton
          variant="secondary"
          size="sm"
          className="border-danger/40 text-danger hover:bg-danger/10"
          disabled={clearingCompleted}
          onClick={onClearCompleted}
        >
          <YkIcons.Trash2 className="h-4 w-4" aria-hidden="true" />
          Limpar concluidos
        </YkButton>
      </div>
    </div>
  );
}
