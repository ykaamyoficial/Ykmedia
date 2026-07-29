import { cn } from "@/components/ui/utils";
import { type LucideIcon } from "@/shared/icons/YkIcons";

export type SettingsSectionId =
  | "folders"
  | "whatsapp"
  | "downloads"
  | "updates"
  | "theme"
  | "language"
  | "backup"
  | "system"
  | "advanced";

export type SettingsNavItem = {
  id: SettingsSectionId;
  label: string;
  icon: LucideIcon;
};

type SettingsNavProps = {
  items: SettingsNavItem[];
  selectedId: SettingsSectionId;
  onSelect: (id: SettingsSectionId) => void;
};

export function SettingsNav({ items, selectedId, onSelect }: SettingsNavProps) {
  return (
    <nav className="w-56 shrink-0 rounded-xl border border-border bg-panel p-2" aria-label="Configuracoes">
      {items.map((item) => {
        const Icon = item.icon;
        const selected = item.id === selectedId;
        return (
          <button
            key={item.id}
            type="button"
            className={cn(
              "flex h-9 w-full items-center gap-2 rounded-lg px-3 text-left text-sm font-medium transition",
              selected ? "bg-accent text-white" : "text-foreground hover:bg-muted",
            )}
            onClick={() => onSelect(item.id)}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {item.label}
          </button>
        );
      })}
    </nav>
  );
}
