import { BackendStatusCard } from "@/components/system/BackendStatusCard";
import { useBackendHealth } from "@/hooks/use-backend-health";
import { YkIcons } from "@/shared/icons";

export function StartupPage() {
  const health = useBackendHealth();
  const isOnline = health.data?.status === "ok";

  return (
    <main className="min-h-screen bg-background px-6 py-6 text-foreground">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src="/ykmedia.png" alt="" className="h-10 w-10 rounded-xl" />
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">YkMedia</h1>
              <p className="mt-1 text-sm text-secondary">
                Sistema de gerenciamento de midias para sonoplastia
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-border bg-panel px-3 py-2 text-xs text-secondary sm:flex">
            <YkIcons.RefreshCcw className="h-3.5 w-3.5" aria-hidden="true" />
            Monitorando /health
          </div>
        </header>

        <BackendStatusCard
          isLoading={health.isLoading}
          isOnline={isOnline}
          isRefetching={health.isRefetching}
          onRetry={() => {
            void health.refetch();
          }}
        />
      </div>
    </main>
  );
}
