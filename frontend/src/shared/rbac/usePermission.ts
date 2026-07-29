import { useContext } from "react";

import { PermissionContext, type Permission } from "@/shared/rbac/permission-context";

export function usePermission(permission: Permission) {
  const context = useContext(PermissionContext);
  if (context === null) {
    return false;
  }
  return context.hasPermission(permission);
}
