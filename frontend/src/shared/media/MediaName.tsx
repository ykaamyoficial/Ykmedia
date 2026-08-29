import { YkTooltip } from "@/components/system/YkTooltip";
import { cn } from "@/components/ui/utils";

type MediaNameProps = {
  name: string;
  originalName?: string | null;
  className?: string;
};

function splitExtension(name: string): { base: string; extension: string } {
  const match = /^(.+)(\.[a-z0-9]{1,6})$/i.exec(name);
  if (!match) {
    return { base: name, extension: "" };
  }
  return { base: match[1], extension: match[2] };
}

// Trunca apenas a base do nome para manter a extensao sempre visivel.
export function MediaName({ name, originalName, className }: MediaNameProps) {
  const { base, extension } = splitExtension(name);
  const showsRename = Boolean(originalName && originalName !== name);
  const tooltipLabel = showsRename ? `${name} (original: ${originalName})` : name;

  return (
    <YkTooltip label={tooltipLabel} className={cn("flex min-w-0 items-baseline", className)}>
      <span className="truncate">{base}</span>
      {extension ? <span className="shrink-0">{extension}</span> : null}
    </YkTooltip>
  );
}
