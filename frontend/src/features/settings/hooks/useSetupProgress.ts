import { useQuery } from "@tanstack/react-query";

import { fetchSetupProgress } from "@/features/settings/api";
import { type SetupProgress } from "@/features/settings/types";

/** Com que frequencia perguntamos ao backend em que etapa ele esta. */
const POLL_MS = 1500;

/**
 * Acompanha o preparo enquanto ele corre.
 *
 * O POST /settings/prepare so responde no fim -- e o fim pode levar minutos,
 * porque a primeira execucao baixa mais de 1 GB. Ate aqui a tela ficava muda
 * esse tempo todo e o usuario nao sabia se estava trabalhando ou travado.
 */
export function useSetupProgress(preparing: boolean): SetupProgress | undefined {
  const query = useQuery({
    queryKey: ["settings", "prepare", "progress"],
    queryFn: fetchSetupProgress,
    // Sem preparo em curso, consultar seria trafego inutil a cada segundo.
    enabled: preparing,
    refetchInterval: preparing ? POLL_MS : false,
    // O backend fica ocupado durante o preparo: uma consulta perdida nao pode
    // derrubar a tela que mostra o andamento.
    retry: false,
    gcTime: 0,
  });

  return query.data;
}
