import { createContext } from "react";

export type Permission = "dashboard:view" | "media:view" | "settings:view";

export type PermissionContextValue = {
  permissions: Permission[];
  hasPermission: (permission: Permission) => boolean;
};

export const PermissionContext = createContext<PermissionContextValue | null>(null);
