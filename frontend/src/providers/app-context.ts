import { createContext } from "react";

export type AppContextValue = {
  sidebarCompact: boolean;
  toggleSidebar: () => void;
};

export const AppContext = createContext<AppContextValue | null>(null);
