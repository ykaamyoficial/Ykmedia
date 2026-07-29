import { useContext } from "react";

import { UserPreferencesContext } from "@/shared/config/user-preferences-context";

export function useUserPreferences() {
  const context = useContext(UserPreferencesContext);
  if (context === null) {
    throw new Error("useUserPreferences must be used inside UserPreferencesProvider.");
  }
  return context;
}
