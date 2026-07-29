import { type ReactNode } from "react";

import { type LucideIcon } from "@/shared/icons/YkIcons";

type YkEmptyStateProps = {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
};

export function YkEmptyState({ icon: Icon, title, description, action }: YkEmptyStateProps) {
  return (
    <div className="flex min-h-[260px] flex-col items-center justify-center rounded-xl border border-dashed border-border bg-panel/60 p-6 text-center">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-muted">
        <Icon className="h-5 w-5 text-secondary" aria-hidden="true" />
      </div>
      <h2 className="mt-4 text-base font-semibold text-foreground">{title}</h2>
      <p className="mt-1 max-w-md text-sm text-secondary">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
