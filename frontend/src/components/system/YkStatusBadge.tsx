import { cn } from "@/components/ui/utils";
import { YkIcons } from "@/shared/icons";

type StatusTone = "success" | "warning" | "danger" | "neutral";

type YkStatusBadgeProps = {
  label: string;
  tone?: StatusTone;
  compact?: boolean;
};

const toneClass: Record<StatusTone, string> = {
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  neutral: "text-secondary",
};

export function YkStatusBadge({ label, tone = "neutral", compact = false }: YkStatusBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-panel px-2 py-1 text-xs font-medium text-foreground">
      <YkIcons.Circle className={cn("h-2 w-2 fill-current", toneClass[tone])} aria-hidden="true" />
      {!compact && label}
      <span className="sr-only">{compact ? label : ""}</span>
    </span>
  );
}
