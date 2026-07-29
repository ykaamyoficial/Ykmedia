import { type RouteObject } from "react-router-dom";

import { YkAppShell } from "@/components/system/YkAppShell";
import { CategoriesPage } from "@/features/categories";
import { ConversationsPage } from "@/features/conversations";
import { DashboardPage } from "@/features/dashboard";
import { DownloadsPage } from "@/features/downloads";
import { FilesPage } from "@/features/files";
import { HistoryPage } from "@/features/history";
import { SettingsPage } from "@/features/settings";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { navigationItems } from "@/routes/navigation";
import { internalRoutes, publicRoutes } from "@/routes/route-paths";

export const routes: RouteObject[] = [
  {
    path: publicRoutes.root,
    element: <YkAppShell />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: internalRoutes.dashboard.replace("/", ""),
        element: <DashboardPage />,
      },
      {
        path: internalRoutes.conversations.replace("/", ""),
        element: <ConversationsPage />,
      },
      {
        path: `${internalRoutes.conversations.replace("/", "")}/:conversationId`,
        element: <ConversationsPage />,
      },
      {
        path: internalRoutes.downloads.replace("/", ""),
        element: <DownloadsPage />,
      },
      {
        path: internalRoutes.files.replace("/", ""),
        element: <FilesPage />,
      },
      {
        path: internalRoutes.history.replace("/", ""),
        element: <HistoryPage />,
      },
      {
        path: internalRoutes.categories.replace("/", ""),
        element: <CategoriesPage />,
      },
      {
        path: internalRoutes.settings.replace("/", ""),
        element: <SettingsPage />,
      },
      ...navigationItems
        .filter(
          (item) =>
            item.path !== internalRoutes.dashboard &&
            item.path !== internalRoutes.conversations &&
            item.path !== internalRoutes.downloads &&
            item.path !== internalRoutes.files &&
            item.path !== internalRoutes.history &&
            item.path !== internalRoutes.categories &&
            item.path !== internalRoutes.settings,
        )
        .map((item) => ({
          path: item.path.replace("/", ""),
          element: <PlaceholderPage item={item} />,
        })),
    ],
  },
];
