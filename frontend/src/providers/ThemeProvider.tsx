import { type ReactNode, useEffect, useMemo, useState } from "react";

import { ThemeContext, type ThemeMode } from "@/providers/theme-context";
const storageKey = "ykmedia-theme";

function readInitialMode(): ThemeMode {
  const storedMode = window.localStorage.getItem(storageKey);
  if (storedMode === "light" || storedMode === "dark" || storedMode === "system") {
    return storedMode;
  }
  return "system";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(readInitialMode);

  useEffect(() => {
    window.localStorage.setItem(storageKey, mode);
    const root = document.documentElement;
    if (mode === "system") {
      root.removeAttribute("data-theme");
      return;
    }
    root.dataset.theme = mode;
  }, [mode]);

  const value = useMemo(() => ({ mode, setMode }), [mode]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
