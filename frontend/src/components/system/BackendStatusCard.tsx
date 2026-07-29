import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { YkIcons } from "@/shared/icons";

type BackendStatusCardProps = {
  isLoading: boolean;
  isOnline: boolean;
  isRefetching: boolean;
  onRetry: () => void;
};

export function BackendStatusCard({
  isLoading,
  isOnline,
  isRefetching,
  onRetry,
}: BackendStatusCardProps) {
  const statusLabel = isOnline ? "Backend conectado" : "Backend indisponivel";
  const description = isOnline ? "Sistema pronto para uso." : "Tentando estabelecer conexao...";

  return (
    <Card className="max-w-xl p-5">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
          <YkIcons.Server className="h-5 w-5 text-accent" aria-hidden="true" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-secondary">Status</p>
          <h2 className="mt-1 text-xl font-semibold text-foreground">
            {isOnline ? "Backend online" : "Backend offline"}
          </h2>

          <div className="mt-4 flex items-center gap-2 text-sm text-foreground">
            {isLoading || isRefetching ? (
              <YkIcons.Loader2 className="h-4 w-4 animate-spin text-accent" aria-hidden="true" />
            ) : isOnline ? (
              <YkIcons.CheckCircle2 className="h-4 w-4 text-success" aria-hidden="true" />
            ) : (
              <YkIcons.AlertCircle className="h-4 w-4 text-danger" aria-hidden="true" />
            )}
            <span>{statusLabel}</span>
          </div>

          <p className="mt-2 text-sm text-secondary">{description}</p>
        </div>
      </div>

      <div className="mt-5 flex justify-end">
        <Button onClick={onRetry} disabled={isRefetching}>
          {isRefetching ? "Verificando..." : "Tentar novamente"}
        </Button>
      </div>
    </Card>
  );
}
