import { Outlet } from "react-router-dom";

import { YkHeader } from "@/components/system/YkHeader";
import { YkSidebar } from "@/components/system/YkSidebar";
import { ErrorBoundary } from "@/shared/errors";

export function YkAppShell() {
  return (
    <div className="flex h-dvh min-h-0 min-w-0 flex-col overflow-hidden bg-background text-foreground">
      <YkHeader />
      <div className="flex min-h-0 flex-1">
        <YkSidebar />
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </div>
    </div>
  );
}
