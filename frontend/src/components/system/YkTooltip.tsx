import { type ReactNode } from "react";

import { cn } from "@/components/ui/utils";

type YkTooltipProps = {
  label: string;
  children: ReactNode;
  disabled?: boolean;
  className?: string;
};

export function YkTooltip({ label, children, disabled = false, className }: YkTooltipProps) {
  return (
    <span className={cn("group relative inline-flex", className)}>
      {children}
      {!disabled && (
        <span
          role="tooltip"
          className="pointer-events-none absolute left-full top-1/2 z-50 ml-2 -translate-y-1/2 whitespace-nowrap rounded-md border border-border bg-panel-elevated px-2 py-1 text-xs text-foreground opacity-0 shadow-panel transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
        >
          {label}
        </span>
      )}
    </span>
  );
}
