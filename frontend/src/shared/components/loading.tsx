import { cn } from "@/components/ui/utils";
import { YkIcons } from "@/shared/icons";

export function YkSpinner({ label = "Carregando" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-secondary" aria-label={label}>
      <YkIcons.Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      {label}
    </span>
  );
}

export function YkSkeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-muted", className)} />;
}

export function YkProgress({ value }: { value: number }) {
  const normalizedValue = Math.max(0, Math.min(100, value));
  return (
    <div
      className="h-2 overflow-hidden rounded-full bg-muted"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={normalizedValue}
    >
      <div className="h-full bg-accent transition-[width]" style={{ width: `${normalizedValue}%` }} />
    </div>
  );
}

export function YkInlineLoading({ label = "Carregando" }: { label?: string }) {
  return <YkSpinner label={label} />;
}

export function YkFullscreenLoading() {
  return (
    <div className="grid min-h-screen place-items-center bg-background">
      <YkSpinner label="Preparando interface" />
    </div>
  );
}
