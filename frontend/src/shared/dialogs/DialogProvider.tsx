import { useEffect, useState, type ReactNode } from "react";

import { YkButton } from "@/components/system/YkButton";
import { dialog } from "@/shared/dialogs/dialog-service";
import { type DialogRequest } from "@/shared/dialogs/dialog-types";

export function DialogProvider({ children }: { children: ReactNode }) {
  const [activeDialog, setActiveDialog] = useState<DialogRequest | null>(null);

  useEffect(() => {
    const unsubscribeOpen = dialog.subscribe("open", setActiveDialog);
    const unsubscribeClose = dialog.subscribe("close", (id) => {
      setActiveDialog((current) => (current?.id === id ? null : current));
    });
    return () => {
      unsubscribeOpen();
      unsubscribeClose();
    };
  }, []);

  return (
    <>
      {children}
      {activeDialog && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4" role="presentation">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="yk-dialog-title"
            className="w-full max-w-sm rounded-xl border border-border bg-panel p-4 shadow-panel"
          >
            <h2 id="yk-dialog-title" className="text-base font-semibold text-foreground">
              {activeDialog.title}
            </h2>
            {activeDialog.description && (
              <p className="mt-2 text-sm text-secondary">{activeDialog.description}</p>
            )}
            <div className="mt-4 flex justify-end gap-2">
              {activeDialog.type === "confirm" && (
                <YkButton type="button" variant="secondary" onClick={() => dialog.close(activeDialog.id)}>
                  {activeDialog.cancelLabel ?? "Cancelar"}
                </YkButton>
              )}
              <YkButton type="button" onClick={() => dialog.close(activeDialog.id)}>
                {activeDialog.confirmLabel ?? "OK"}
              </YkButton>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
