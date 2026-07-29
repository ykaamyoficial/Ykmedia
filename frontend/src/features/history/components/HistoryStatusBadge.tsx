import { YkStatusBadge } from "@/components/system/YkStatusBadge";

export function HistoryStatusBadge({ status }: { status: string }) {
  const tone = status === "CONCLUIDO" ? "success" : status === "ERRO" ? "danger" : "neutral";
  return <YkStatusBadge label={status || "-"} tone={tone} />;
}
