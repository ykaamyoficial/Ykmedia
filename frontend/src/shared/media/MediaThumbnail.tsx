import { useState } from "react";

import { cn } from "@/components/ui/utils";
import { MediaTypeIcon } from "@/shared/media/MediaTypeIcon";

type MediaThumbnailProps = {
  kind: string;
  thumbnailUrl?: string | null;
  alt: string;
  size?: "sm" | "md";
  className?: string;
};

const sizeClass: Record<"sm" | "md", string> = {
  sm: "h-8 w-8",
  md: "h-11 w-11",
};

// Hoje nenhum DTO expoe thumbnailUrl, entao sempre recai no icone por tipo; fica pronto para quando existir.
export function MediaThumbnail({ kind, thumbnailUrl, alt, size = "md", className }: MediaThumbnailProps) {
  const [failed, setFailed] = useState(false);

  if (!thumbnailUrl || failed) {
    return <MediaTypeIcon kind={kind} size={size} className={className} />;
  }

  return (
    <img
      src={thumbnailUrl}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
      className={cn(
        "shrink-0 rounded-xl border border-border object-cover",
        sizeClass[size],
        className,
      )}
    />
  );
}
