import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { mediaStatusLabel, mediaStatusTone } from "@/shared/media/media-status";

type MediaStatusBadgeProps = {
  status?: string | null;
  compact?: boolean;
};

// Badge unica de status, substitui as implementacoes duplicadas de Downloads/Arquivos/Historico.
export function MediaStatusBadge({ status, compact = false }: MediaStatusBadgeProps) {
  return <YkStatusBadge label={mediaStatusLabel(status)} tone={mediaStatusTone(status)} compact={compact} />;
}
