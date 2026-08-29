import { type ReactNode } from "react";

import { YkEmptyState } from "@/components/system/YkEmptyState";
import { type NavigationItem } from "@/routes/navigation";

type YkPageProps = {
  item: NavigationItem;
  children?: ReactNode;
};

export function YkPage({ item, children }: YkPageProps) {
  const Icon = item.icon;

  return (
    <main className="min-h-0 flex-1 overflow-hidden bg-background p-5">
      <div className="yk-scroll mx-auto flex h-full min-h-0 w-full max-w-[1600px] flex-col gap-4 overflow-y-auto">
        {children ?? (
          <YkEmptyState
            icon={Icon}
            title={`${item.label} em preparacao`}
            description="A estrutura visual desta pagina esta pronta para receber o modulo em uma proxima etapa."
          />
        )}
      </div>
    </main>
  );
}
