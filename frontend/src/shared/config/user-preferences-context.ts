import { createContext } from "react";

export type UserPreferences = {
  theme: "light" | "dark" | "system";
  language: "pt-BR";
  density: "compact" | "comfortable";
};

export const defaultPreferences: UserPreferences = {
  theme: "system",
  language: "pt-BR",
  density: "compact",
};

export type UserPreferencesContextValue = {
  preferences: UserPreferences;
  setPreferences: (preferences: UserPreferences) => void;
};

export const UserPreferencesContext = createContext<UserPreferencesContextValue | null>(null);
