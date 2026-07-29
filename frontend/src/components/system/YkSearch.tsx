import { type InputHTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";
import { YkIcons } from "@/shared/icons";

export function YkSearch({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={cn("relative block", className)}>
      <YkIcons.Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
      <input
        className="h-9 w-full rounded-lg border border-border bg-panel pl-8 pr-3 text-sm text-foreground outline-none transition focus:border-accent"
        type="search"
        {...props}
      />
    </label>
  );
}
