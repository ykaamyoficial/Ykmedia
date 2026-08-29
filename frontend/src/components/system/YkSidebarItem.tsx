import { NavLink } from "react-router-dom";

import { cn } from "@/components/ui/utils";
import { YkTooltip } from "@/components/system/YkTooltip";
import { type NavigationItem } from "@/routes/navigation";

type YkSidebarItemProps = {
  item: NavigationItem;
  compact: boolean;
};

export function YkSidebarItem({ item, compact }: YkSidebarItemProps) {
  const Icon = item.icon;

  return (
    <YkTooltip label={item.label} disabled={!compact}>
      <NavLink
        to={item.path}
        className={({ isActive }) =>
          cn(
            "flex h-9 w-full items-center gap-2 rounded-lg px-2 text-sm font-medium transition",
            "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
            compact && "justify-center px-0",
            isActive
              ? "bg-accent text-white shadow-sm"
              : "text-secondary hover:bg-muted hover:text-foreground",
          )
        }
      >
        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
        {!compact && <span className="truncate">{item.label}</span>}
      </NavLink>
    </YkTooltip>
  );
}
