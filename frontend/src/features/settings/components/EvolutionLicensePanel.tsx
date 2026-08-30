import { YkButton } from "@/components/system/YkButton";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkIcons } from "@/shared/icons";
import { type EvolutionLicense } from "@/features/settings/types";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

type EvolutionLicensePanelProps = {
  license?: EvolutionLicense;
  loading?: boolean;
  registerUrl?: string | null;
  onRefresh: () => void;
  onStartRegistration: () => void;
  onOpenRegisterUrl: (url: string) => void;
};

const TONE_BY_STATUS: Record<string, "success" | "warning" | "danger" | "neutral"> = {
  ATIVA: "success",
  NAO_EXIGIDA: "success",
  PENDENTE: "danger",
  INDISPONIVEL: "warning",
};

const LABEL_BY_STATUS: Record<string, string> = {
  ATIVA: "Ativa",
  NAO_EXIGIDA: "Não exigida",
  PENDENTE: "Pendente",
  INDISPONIVEL: "Indisponível",
};

export function EvolutionLicensePanel({
  license,
  loading = false,
  registerUrl,
  onRefresh,
  onStartRegistration,
  onOpenRegisterUrl,
}: EvolutionLicensePanelProps) {
  const status = license?.status ?? "INDISPONIVEL";
  const needsActivation = status === "PENDENTE";

  return (
    <SettingsSection
      title="Licença da Evolution"
      description="Ativação gratuita exigida para o WhatsApp funcionar."
      actions={
        <>
          <YkButton type="button" variant="secondary" size="sm" disabled={loading} onClick={onRefresh}>
            <YkIcons.Search className="h-4 w-4" aria-hidden="true" />
            Verificar
          </YkButton>
          {needsActivation ? (
            <YkButton type="button" size="sm" disabled={loading} onClick={onStartRegistration}>
              <YkIcons.Power className="h-4 w-4" aria-hidden="true" />
              Ativar licença
            </YkButton>
          ) : null}
        </>
      }
    >
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">Status</span>
          <YkStatusBadge
            label={LABEL_BY_STATUS[status] ?? status}
            tone={TONE_BY_STATUS[status] ?? "neutral"}
          />
        </div>
        <p className="text-sm text-secondary">{license?.message ?? "Não verificado"}</p>

        {needsActivation && !registerUrl ? (
          <p className="text-sm text-secondary">
            A Evolution passou a exigir uma ativação gratuita. Sem ela, o envio e o recebimento de
            mensagens ficam bloqueados. Clique em <strong>Ativar licença</strong> para gerar o
            endereço de cadastro.
          </p>
        ) : null}

        {registerUrl ? (
          <div className="space-y-2 rounded-xl border border-border bg-background p-3">
            <p className="text-sm text-foreground">
              Conclua o cadastro gratuito no endereço abaixo. Ao terminar, a ativação é aplicada
              automaticamente.
            </p>
            <p className="break-all text-xs text-secondary">{registerUrl}</p>
            <YkButton type="button" size="sm" onClick={() => onOpenRegisterUrl(registerUrl)}>
              <YkIcons.QrCode className="h-4 w-4" aria-hidden="true" />
              Abrir cadastro
            </YkButton>
          </div>
        ) : null}
      </div>
    </SettingsSection>
  );
}
