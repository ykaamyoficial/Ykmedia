import { YkButton } from "@/components/system/YkButton";

type CategoryDeleteDialogProps = {
  onCancel: () => void;
  onConfirm: () => void;
};

export function CategoryDeleteDialog({ onCancel, onConfirm }: CategoryDeleteDialogProps) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4" role="presentation">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="category-delete-title"
        className="w-full max-w-sm rounded-xl border border-border bg-panel p-4 shadow-panel"
      >
        <h2 id="category-delete-title" className="text-base font-semibold text-foreground">
          Excluir categoria
        </h2>
        <p className="mt-2 text-sm text-secondary">Deseja excluir esta categoria?</p>
        <div className="mt-4 flex justify-end gap-2">
          <YkButton type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </YkButton>
          <YkButton type="button" onClick={onConfirm}>
            OK
          </YkButton>
        </div>
      </section>
    </div>
  );
}
