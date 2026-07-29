import { type ReactNode } from "react";

import { PermissionContext, type Permission } from "@/shared/rbac/permission-context";
import { usePermission } from "@/shared/rbac/usePermission";

export function PermissionProvider({
  permissions,
  children,
}: {
  permissions: Permission[];
  children: ReactNode;
}) {
  return (
    <PermissionContext.Provider
      value={{
        permissions,
        hasPermission: (permission) => permissions.includes(permission),
      }}
    >
      {children}
    </PermissionContext.Provider>
  );
}

export function PermissionGuard({
  permission,
  fallback = null,
  children,
}: {
  permission: Permission;
  fallback?: ReactNode;
  children: ReactNode;
}) {
  return usePermission(permission) ? children : fallback;
}
