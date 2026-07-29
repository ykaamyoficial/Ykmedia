import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { type DownloadJobStatus } from "@/features/downloads/types";

const statusTone: Record<DownloadJobStatus, "success" | "warning" | "danger" | "neutral"> = {
  PENDENTE: "neutral",
  PROCESSANDO: "warning",
  CONCLUIDO: "success",
  ERRO: "danger",
};

export function DownloadStatusBadge({ status }: { status: DownloadJobStatus }) {
  return <YkStatusBadge label={status} tone={statusTone[status]} />;
}
