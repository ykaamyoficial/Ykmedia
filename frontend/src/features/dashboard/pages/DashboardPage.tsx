import { YkButton } from "@/components/system/YkButton";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkPage } from "@/components/system/YkPage";
import { navigationItems } from "@/routes/navigation";
import { YkNoConnectionState, YkNoDataState } from "@/shared/components";
import { YkIcons } from "@/shared/icons";
import { friendlyErrorMessage } from "@/shared/errors";
import { toast } from "@/shared/toast";
import {
  DashboardMetricCard,
  DashboardSection,
} from "@/features/dashboard/components";
import { useDashboardOverview } from "@/features/dashboard/hooks";

const dashboardItem = navigationItems.find((item) => item.path === "/dashboard") ?? navigationItems[0];

function whatsappStatusLabel(connected?: boolean, qrPending?: boolean) {
  if (connected) {
    return "Conectado";
  }
  if (qrPending) {
    return "QR pendente";
  }
  return "Desconectado";
}

export function DashboardPage() {
  const dashboard = useDashboardOverview();

  if (dashboard.isError) {
    return (
      <YkPage item={dashboardItem}>
        <YkNoConnectionState />
        <YkButton
          className="w-fit"
          variant="secondary"
          onClick={() => {
            toast.error(friendlyErrorMessage(dashboard.error));
            void dashboard.refetch();
          }}
        >
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Tentar novamente
        </YkButton>
      </YkPage>
    );
  }

  const data = dashboard.data;
  const loading = dashboard.isLoading;

  return (
    <YkPage item={dashboardItem}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
          <p className="text-sm text-secondary">Operacao do YkMedia em tempo real.</p>
        </div>
        <YkButton
          variant="secondary"
          size="sm"
          disabled={dashboard.isFetching}
          onClick={() => void dashboard.refetch()}
        >
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Atualizar
        </YkButton>
      </div>

      {!loading && data && !data.has_data ? <YkNoDataState /> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <DashboardMetricCard
          label="Sistema"
          value={data?.system.backend_online ? "Online" : "Offline"}
          description="API local do YkMedia."
          icon={YkIcons.Server}
          tone={data?.system.backend_online ? "success" : "danger"}
          loading={loading}
        />
        <DashboardMetricCard
          label="WhatsApp"
          value={whatsappStatusLabel(data?.whatsapp.connected, data?.whatsapp.qr_pending)}
          description="Conexao do WhatsApp."
          icon={YkIcons.Smartphone}
          tone={data?.whatsapp.connected ? "success" : data?.whatsapp.qr_pending ? "warning" : "danger"}
          loading={loading}
        />
        <DashboardMetricCard
          label="Worker"
          value="Ativo"
          description="Processamento local."
          icon={YkIcons.Activity}
          tone="primary"
          loading={loading}
        />
        <DashboardMetricCard
          label="Na fila"
          value={data?.downloads.queue}
          description="Aguardando processamento."
          icon={YkIcons.Inbox}
          tone="warning"
          loading={loading}
        />
        <DashboardMetricCard
          label="Concluidos"
          value={data?.downloads.completed}
          description="Total concluido."
          icon={YkIcons.CheckCircle2}
          tone="success"
          loading={loading}
        />
        <DashboardMetricCard
          label="Erros"
          value={data?.downloads.failures}
          description="Requer atencao."
          icon={YkIcons.AlertCircle}
          tone="danger"
          loading={loading}
        />
      </div>

      <div className="grid min-h-[360px] gap-4 xl:grid-cols-[2fr_1fr]">
        <DashboardSection
          title="Atividade nas ultimas 24 horas"
          loading={loading}
        >
          <YkEmptyState
            icon={YkIcons.Activity}
            title="Nenhuma atividade registrada ainda."
            description="Quando novas midias chegarem pelo WhatsApp, o resumo aparecera aqui."
          />
        </DashboardSection>

        <DashboardSection title="Resumo operacional" loading={loading}>
          <div className="grid gap-3 text-sm text-secondary">
            <div className="flex items-center justify-between gap-3">
              <span>Pendentes</span>
              <strong className="text-foreground">{data?.downloads.queue ?? "Sem dados"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Processando</span>
              <strong className="text-foreground">{data?.downloads.in_progress ?? "Sem dados"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Concluidos</span>
              <strong className="text-foreground">{data?.downloads.completed ?? "Sem dados"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Erros</span>
              <strong className="text-foreground">{data?.downloads.failures ?? "Sem dados"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Backend</span>
              <strong className="text-foreground">{data?.system.backend_online ? "Online" : "Offline"}</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Inicializacao</span>
              <strong className="text-foreground">Sem dados</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Pasta de midias</span>
              <strong className="max-w-52 truncate text-foreground">Sem dados</strong>
            </div>
          </div>
        </DashboardSection>
      </div>
    </YkPage>
  );
}
