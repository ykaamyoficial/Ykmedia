import { YkIcons } from "@/shared/icons";
import { cn } from "@/components/ui/utils";

type DashboardStatusCardProps = {
  label: string;
  status: string;
  description: string;
};

function statusClass(status: string) {
  if (status === "online") {
    return "bg-success text-success";
  }
  if (status === "warning") {
    return "bg-warning text-warning";
  }
  return "bg-danger text-danger";
}

export function DashboardStatusCard({ label, status, description }: DashboardStatusCardProps) {
  const Icon = status === "online" ? YkIcons.CheckCircle2 : YkIcons.AlertCircle;

  return (
    <div className="rounded-xl border border-border bg-panel p-3">
      <div className="flex items-center gap-2">
        <span className={cn("rounded-full bg-opacity-15 p-1.5", statusClass(status))}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-foreground">{label}</p>
          <p className="text-xs capitalize text-secondary">{status}</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-secondary">{description}</p>
    </div>
  );
}
