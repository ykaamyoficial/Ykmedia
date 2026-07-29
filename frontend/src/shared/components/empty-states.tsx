import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkIcons } from "@/shared/icons";

export function YkNoDataState() {
  return <YkEmptyState icon={YkIcons.Ban} title="Sem dados" description="Ainda nao ha informacoes para exibir." />;
}

export function YkNoConnectionState() {
  return <YkEmptyState icon={YkIcons.WifiOff} title="Sem conexao" description="Verifique o backend e tente novamente." />;
}

export function YkErrorState() {
  return <YkEmptyState icon={YkIcons.AlertCircle} title="Erro ao carregar" description="Nao foi possivel carregar esta area." />;
}

export function YkNoResultsState() {
  return <YkEmptyState icon={YkIcons.SearchX} title="Sem resultados" description="Ajuste a busca ou remova filtros." />;
}

export function YkNoPermissionState() {
  return <YkEmptyState icon={YkIcons.Lock} title="Sem permissao" description="Seu perfil nao permite acessar esta area." />;
}

export const YkForbiddenState = YkNoPermissionState;
export const YkOfflineState = YkNoConnectionState;

export function YkNoHistoryState() {
  return <YkEmptyState icon={YkIcons.History} title="Sem historico" description="Nenhuma atividade foi registrada ainda." />;
}
