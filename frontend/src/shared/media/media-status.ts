export type MediaStatusTone = "success" | "warning" | "danger" | "neutral";

const statusLabels: Record<string, string> = {
  PENDENTE: "Aguardando",
  PROCESSANDO: "Processando",
  CONCLUIDO: "Salvo",
  ERRO: "Erro",
};

const statusTones: Record<string, MediaStatusTone> = {
  PENDENTE: "neutral",
  PROCESSANDO: "warning",
  CONCLUIDO: "success",
  ERRO: "danger",
};

// Traduz o status real do backend (PENDENTE/PROCESSANDO/CONCLUIDO/ERRO) para a linguagem visual padronizada.
export function mediaStatusLabel(rawStatus?: string | null): string {
  if (!rawStatus) {
    return "-";
  }
  return statusLabels[rawStatus] ?? rawStatus;
}

export function mediaStatusTone(rawStatus?: string | null): MediaStatusTone {
  if (!rawStatus) {
    return "neutral";
  }
  return statusTones[rawStatus] ?? "neutral";
}
