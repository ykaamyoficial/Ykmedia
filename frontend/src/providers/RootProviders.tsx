import { QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";

import { AppProvider } from "@/providers/AppProvider";
import { BackendStatusProvider } from "@/providers/BackendStatusProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { UserPreferencesProvider } from "@/shared/config/user-preferences";
import { DialogProvider } from "@/shared/dialogs";
import { createAppQueryClient } from "@/shared/query";
import { PermissionProvider } from "@/shared/rbac/permissions";
import { ToastProvider } from "@/shared/toast";

const queryClient = createAppQueryClient();

export function RootProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <UserPreferencesProvider>
        <ThemeProvider>
          <BackendStatusProvider>
            <PermissionProvider permissions={["dashboard:view", "media:view", "settings:view"]}>
              <AppProvider>
                <DialogProvider>
                  <ToastProvider>{children}</ToastProvider>
                </DialogProvider>
              </AppProvider>
            </PermissionProvider>
          </BackendStatusProvider>
        </ThemeProvider>
      </UserPreferencesProvider>
    </QueryClientProvider>
  );
}
