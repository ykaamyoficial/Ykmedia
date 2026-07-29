import { useLocation } from "react-router-dom";

import { YkAvatar } from "@/components/system/YkAvatar";
import { YkButton } from "@/components/system/YkButton";
import { YkSearch } from "@/components/system/YkSearch";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { useBackendStatus } from "@/providers/useBackendStatus";
import { findNavigationItem } from "@/routes/navigation";
import { YkIcons } from "@/shared/icons";

export function YkHeader() {
  const location = useLocation();
  const item = findNavigationItem(location.pathname);
  const backend = useBackendStatus();

  return (
    <header className="flex h-[68px] shrink-0 items-center justify-between gap-4 border-b border-border bg-background px-5">
      <div className="min-w-0">
        <h1 className="truncate text-xl font-semibold tracking-tight text-foreground">{item.label}</h1>
        <p className="truncate text-sm text-secondary">{item.description}</p>
      </div>

      <div className="flex min-w-0 flex-1 items-center justify-end gap-3">
        <YkSearch className="hidden w-full max-w-sm lg:block" placeholder="Pesquisar..." aria-label="Pesquisar" />
        <YkStatusBadge
          label={backend.isOnline ? "Backend online" : "Backend offline"}
          tone={backend.isOnline ? "success" : "danger"}
        />
        <YkButton type="button" variant="secondary" size="sm" onClick={backend.refresh}>
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Atualizar
        </YkButton>
        <YkButton type="button" variant="ghost" size="sm" aria-label="Notificacoes">
          <YkIcons.Bell className="h-4 w-4" aria-hidden="true" />
        </YkButton>
        <YkAvatar name="YkMedia" size="sm" />
      </div>
    </header>
  );
}
