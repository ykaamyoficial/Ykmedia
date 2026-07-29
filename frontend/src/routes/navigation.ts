import { YkIcons } from "@/shared/icons";
import { type LucideIcon } from "@/shared/icons/YkIcons";
import { internalRoutes } from "@/routes/route-paths";

export type NavigationItem = {
  path: string;
  label: string;
  description: string;
  icon: LucideIcon;
};

export const navigationItems: NavigationItem[] = [
  {
    path: internalRoutes.dashboard,
    label: "Dashboard",
    description: "Visao geral do sistema",
    icon: YkIcons.Gauge,
  },
  {
    path: internalRoutes.conversations,
    label: "Conversas",
    description: "Remetentes e midias recebidas",
    icon: YkIcons.MessageCircle,
  },
  {
    path: internalRoutes.downloads,
    label: "Downloads",
    description: "Acompanhamento de downloads",
    icon: YkIcons.Download,
  },
  {
    path: internalRoutes.files,
    label: "Arquivos",
    description: "Biblioteca de midias organizadas",
    icon: YkIcons.Archive,
  },
  {
    path: internalRoutes.categories,
    label: "Categorias",
    description: "Estrutura de organizacao",
    icon: YkIcons.FolderTree,
  },
  {
    path: internalRoutes.history,
    label: "Historico",
    description: "Registros de processamento",
    icon: YkIcons.History,
  },
  {
    path: internalRoutes.settings,
    label: "Configuracoes",
    description: "Preferencias e conexoes",
    icon: YkIcons.Settings,
  },
];

export function findNavigationItem(pathname: string) {
  return navigationItems.find((item) => pathname.startsWith(item.path)) ?? navigationItems[0];
}
