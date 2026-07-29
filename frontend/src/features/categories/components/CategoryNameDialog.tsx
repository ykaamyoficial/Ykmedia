import { useEffect, useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkInput } from "@/shared/forms";

type CategoryNameDialogProps = {
  title: string;
  initialValue?: string;
  onCancel: () => void;
  onConfirm: (value: string) => void;
};

export function CategoryNameDialog({
  title,
  initialValue = "",
  onCancel,
  onConfirm,
}: CategoryNameDialogProps) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4" role="presentation">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="category-name-title"
        className="w-full max-w-sm rounded-xl border border-border bg-panel p-4 shadow-panel"
      >
        <h2 id="category-name-title" className="text-base font-semibold text-foreground">
          {title}
        </h2>
        <label className="mt-4 block text-sm text-secondary">
          Nome da categoria:
          <YkInput
            autoFocus
            className="mt-2 w-full"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && value.trim()) {
                onConfirm(value);
              }
              if (event.key === "Escape") {
                onCancel();
              }
            }}
          />
        </label>
        <div className="mt-4 flex justify-end gap-2">
          <YkButton type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </YkButton>
          <YkButton type="button" disabled={!value.trim()} onClick={() => onConfirm(value)}>
            OK
          </YkButton>
        </div>
      </section>
    </div>
  );
}
