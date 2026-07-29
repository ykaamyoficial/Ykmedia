import { type ReactNode, useMemo } from "react";

import {
  defaultPreferences,
  UserPreferencesContext,
  type UserPreferences,
} from "@/shared/config/user-preferences-context";
import { useLocalStorage } from "@/shared/hooks/useLocalStorage";

export function UserPreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useLocalStorage<UserPreferences>(
    "ykmedia-preferences",
    defaultPreferences,
  );

  const value = useMemo(() => ({ preferences, setPreferences }), [preferences, setPreferences]);

  return <UserPreferencesContext.Provider value={value}>{children}</UserPreferencesContext.Provider>;
}
