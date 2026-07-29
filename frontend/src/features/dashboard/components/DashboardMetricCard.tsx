import { type LucideIcon } from "@/shared/icons/YkIcons";
import { YkSkeleton } from "@/shared/components";
import { cn } from "@/components/ui/utils";

type DashboardMetricCardProps = {
  label: string;
  value?: number | string;
  description: string;
  icon: LucideIcon;
  tone?: "primary" | "success" | "warning" | "danger" | "neutral";
  loading?: boolean;
};

const toneClasses = {
  primary: "bg-accent/15 text-accent",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
  danger: "bg-danger/15 text-danger",
  neutral: "bg-muted text-secondary",
};

export function DashboardMetricCard({
  label,
  value,
  description,
  icon: Icon,
  tone = "neutral",
  loading = false,
}: DashboardMetricCardProps) {
  if (loading) {
    return <YkSkeleton className="h-28 rounded-xl" />;
  }

  return (
    <div className="rounded-xl border border-border bg-panel-elevated p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-secondary">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-normal text-foreground">{value ?? "Sem dados"}</p>
        </div>
        <span className={cn("rounded-lg p-2", toneClasses[tone])}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
      <p className="mt-3 text-xs text-secondary">{description}</p>
    </div>
  );
}
