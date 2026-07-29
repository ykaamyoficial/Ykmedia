import { type ReactNode, useMemo, useState } from "react";

import { AppContext } from "@/providers/app-context";

export function AppProvider({ children }: { children: ReactNode }) {
  const [sidebarCompact, setSidebarCompact] = useState(false);

  const value = useMemo(
    () => ({
      sidebarCompact,
      toggleSidebar: () => setSidebarCompact((current) => !current),
    }),
    [sidebarCompact],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
