import { type ReactNode } from "react";

import { YkCard } from "@/components/system/YkCard";
import { YkSkeleton } from "@/shared/components";

type DashboardSectionProps = {
  title: string;
  description?: string;
  loading?: boolean;
  children: ReactNode;
};

export function DashboardSection({
  title,
  description,
  loading = false,
  children,
}: DashboardSectionProps) {
  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
        {description ? <p className="text-xs text-secondary">{description}</p> : null}
      </div>
      <YkCard className="min-h-32">
        {loading ? <YkSkeleton className="h-28 w-full" /> : children}
      </YkCard>
    </section>
  );
}
