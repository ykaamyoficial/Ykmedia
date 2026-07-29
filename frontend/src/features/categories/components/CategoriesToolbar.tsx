import { YkButton } from "@/components/system/YkButton";
import { YkIcons } from "@/shared/icons";

type CategoriesToolbarProps = {
  selectedIndex: number;
  total: number;
  saving: boolean;
  onAdd: () => void;
  onEdit: () => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
};

export function CategoriesToolbar({
  selectedIndex,
  total,
  saving,
  onAdd,
  onEdit,
  onRemove,
  onMoveUp,
  onMoveDown,
}: CategoriesToolbarProps) {
  const hasSelection = selectedIndex >= 0;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-panel-elevated p-3">
      <YkButton size="sm" disabled={saving} onClick={onAdd}>
        <YkIcons.Plus className="h-4 w-4" aria-hidden="true" />
        Nova categoria
      </YkButton>
      <YkButton variant="secondary" size="sm" disabled={!hasSelection || saving} onClick={onEdit}>
        <YkIcons.Pencil className="h-4 w-4" aria-hidden="true" />
        Editar
      </YkButton>
      <YkButton
        variant="secondary"
        size="sm"
        className="border-danger/40 text-danger hover:bg-danger/10"
        disabled={!hasSelection || saving}
        onClick={onRemove}
      >
        <YkIcons.Trash2 className="h-4 w-4" aria-hidden="true" />
        Excluir
      </YkButton>
      <YkButton
        variant="secondary"
        size="sm"
        disabled={!hasSelection || selectedIndex === 0 || saving}
        onClick={onMoveUp}
      >
        <YkIcons.ArrowUp className="h-4 w-4" aria-hidden="true" />
        Mover acima
      </YkButton>
      <YkButton
        variant="secondary"
        size="sm"
        disabled={!hasSelection || selectedIndex >= total - 1 || saving}
        onClick={onMoveDown}
      >
        <YkIcons.ArrowDown className="h-4 w-4" aria-hidden="true" />
        Mover abaixo
      </YkButton>
    </div>
  );
}
