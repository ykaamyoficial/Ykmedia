import { cn } from "@/components/ui/utils";
import { mediaKindIcon, mediaKindTone, normalizeMediaKind } from "@/shared/media/media-kind";

const toneClass: Record<string, string> = {
  success: "bg-success/10 text-success",
  accent: "bg-accent/10 text-accent",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
  neutral: "bg-muted text-secondary",
};

type MediaTypeIconProps = {
  kind: string;
  size?: "sm" | "md";
  className?: string;
};

const sizeClass: Record<"sm" | "md", string> = {
  sm: "h-8 w-8",
  md: "h-11 w-11",
};

const iconSizeClass: Record<"sm" | "md", string> = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
};

export function MediaTypeIcon({ kind, size = "md", className }: MediaTypeIconProps) {
  const normalized = normalizeMediaKind(kind);
  const Icon = mediaKindIcon(normalized);
  const tone = mediaKindTone(normalized);

  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center rounded-xl border border-border",
        sizeClass[size],
        toneClass[tone],
        className,
      )}
      aria-hidden="true"
    >
      <Icon className={iconSizeClass[size]} />
    </div>
  );
}
