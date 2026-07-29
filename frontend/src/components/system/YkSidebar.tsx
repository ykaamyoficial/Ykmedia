import { YkButton } from "@/components/system/YkButton";
import { YkSeparator } from "@/components/system/YkSeparator";
import { YkSidebarItem } from "@/components/system/YkSidebarItem";
import { YkSidebarSection } from "@/components/system/YkSidebarSection";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { cn } from "@/components/ui/utils";
import { useApp } from "@/providers/useApp";
import { useBackendStatus } from "@/providers/useBackendStatus";
import { navigationItems } from "@/routes/navigation";
import { YkIcons } from "@/shared/icons";

function statusTone(isOnline: boolean) {
  return isOnline ? "success" : "danger";
}

export function YkSidebar() {
  const { sidebarCompact, toggleSidebar } = useApp();
  const backend = useBackendStatus();
  const serviceLabel = backend.isOnline ? "Online" : "Offline";

  return (
    <nav
      className={cn(
        "flex h-full shrink-0 flex-col border-r border-border bg-panel px-3 py-3 transition-[width]",
        sidebarCompact ? "w-[72px]" : "w-[252px]",
      )}
      aria-label="Navegacao principal"
    >
      <div className={cn("flex items-center gap-3", sidebarCompact && "justify-center")}>
        <img src="/ykmedia.png" alt="" className="h-9 w-9 rounded-xl" />
        {!sidebarCompact && (
          <div className="min-w-0">
            <p className="truncate text-base font-semibold text-foreground">YkMedia</p>
            <p className="truncate text-xs text-secondary">Gerenciador de midias</p>
          </div>
        )}
      </div>

      <YkSeparator />

      <div className="mt-3 flex-1 space-y-4">
        <YkSidebarSection title="Workspace" compact={sidebarCompact}>
          {navigationItems.map((item) => (
            <YkSidebarItem key={item.path} item={item} compact={sidebarCompact} />
          ))}
        </YkSidebarSection>
      </div>

      <div className="space-y-3">
        <YkSeparator />
        <div className="space-y-2 rounded-xl border border-border bg-surface p-2">
          <YkStatusBadge label={`Backend ${serviceLabel}`} tone={statusTone(backend.isOnline)} compact={sidebarCompact} />
          <YkStatusBadge label={`Evolution ${serviceLabel}`} tone={statusTone(backend.isOnline)} compact={sidebarCompact} />
          <YkStatusBadge label={`WhatsApp ${serviceLabel}`} tone={statusTone(backend.isOnline)} compact={sidebarCompact} />
        </div>
        <YkButton
          type="button"
          variant="ghost"
          size="sm"
          className="w-full"
          onClick={toggleSidebar}
          aria-label={sidebarCompact ? "Expandir sidebar" : "Compactar sidebar"}
        >
          {sidebarCompact ? <YkIcons.ChevronRight className="h-4 w-4" /> : <YkIcons.ChevronLeft className="h-4 w-4" />}
          {!sidebarCompact && "Compactar"}
        </YkButton>
      </div>
    </nav>
  );
}
