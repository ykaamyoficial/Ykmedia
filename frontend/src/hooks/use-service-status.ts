import { useQuery } from "@tanstack/react-query";

import { fetchEvolutionSession } from "@/features/settings/api";
import { useBackendStatus } from "@/providers/useBackendStatus";
import { queryKeys } from "@/shared/query";

export type ServiceState = "online" | "offline" | "warning" | "unknown";

export type ServiceStatus = {
  backend: ServiceState;
  evolution: ServiceState;
  whatsapp: ServiceState;
};

const REFRESH_MS = 15000;

/**
 * Estado real de cada servico da barra lateral.
 *
 * Antes os tres indicadores vinham do mesmo `backend.isOnline`: a barra dizia
 * "Evolution Online" e "WhatsApp Online" enquanto a tela de configuracoes
 * mostrava "Could not connect to Evolution API". Ver a barra mentir torna
 * qualquer diagnostico mais dificil, ainda mais numa instalacao remota.
 */
export function useServiceStatus(): ServiceStatus {
  const backend = useBackendStatus();

  const evolutionQuery = useQuery({
    queryKey: queryKeys.settings.evolution,
    queryFn: fetchEvolutionSession,
    refetchInterval: backend.isOnline ? REFRESH_MS : false,
    enabled: backend.isOnline,
    staleTime: 10000,
    retry: false,
  });

  if (!backend.isOnline) {
    // Sem backend nao ha como saber nada sobre os outros servicos.
    return { backend: "offline", evolution: "unknown", whatsapp: "unknown" };
  }

  if (evolutionQuery.isError) {
    return { backend: "online", evolution: "offline", whatsapp: "unknown" };
  }

  if (!evolutionQuery.data) {
    return { backend: "online", evolution: "unknown", whatsapp: "unknown" };
  }

  const state = (evolutionQuery.data.state ?? "").toLowerCase();

  // "Erro" vem do backend quando ele nao conseguiu falar com a Evolution.
  if (state === "erro" || state === "error" || state === "desconhecida") {
    return { backend: "online", evolution: "offline", whatsapp: "unknown" };
  }

  if (state === "open") {
    return { backend: "online", evolution: "online", whatsapp: "online" };
  }

  if (state === "connecting") {
    return { backend: "online", evolution: "online", whatsapp: "warning" };
  }

  // A Evolution respondeu, mas a sessao do WhatsApp nao esta aberta.
  return { backend: "online", evolution: "online", whatsapp: "offline" };
}
