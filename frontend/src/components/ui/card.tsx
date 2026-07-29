import { type HTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <section
      className={cn("rounded-xl border border-border bg-panel shadow-panel", className)}
      {...props}
    />
  );
}
