import { type HTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

export function YkCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-lg border border-border bg-panel-elevated p-4", className)}
      {...props}
    />
  );
}
