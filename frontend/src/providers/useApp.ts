import { useContext } from "react";

import { AppContext } from "@/providers/app-context";

export function useApp() {
  const value = useContext(AppContext);
  if (value === null) {
    throw new Error("useApp must be used inside AppProvider.");
  }
  return value;
}
