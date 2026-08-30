import { YkButton } from "@/components/system/YkButton";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkIcons } from "@/shared/icons";
import { type EvolutionLicense } from "@/features/settings/types";
import { SettingsSection } from "@/features/settings/components/SettingsSection";
import { type ActivationPhase } from "@/features/settings/hooks";

type EvolutionLicensePanelProps = {
  license?: EvolutionLicense;
  loading?: boolean;
  activationPhase: ActivationPhase;
  registerUrl?: string | null;
  activationError?: string | null;
  onRefresh: () => void;
  onStartActivation: () => void;
  onCancelActivation: () => void;
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

const STEPS = [
  "Clique em Abrir cadastro — o navegador vai abrir",
  "Entre com e-mail, Google ou GitHub (é gratuito)",
  "Volte para esta tela: a ativação é detectada sozinha",
];

export function EvolutionLicensePanel({
  license,
  loading = false,
  activationPhase,
  registerUrl,
  activationError,
  onRefresh,
  onStartActivation,
  onCancelActivation,
  onOpenRegisterUrl,
}: EvolutionLicensePanelProps) {
  const status = license?.status ?? "INDISPONIVEL";
  const activating = activationPhase === "loading" || activationPhase === "waiting";
  const active = activationPhase === "activated" || status === "ATIVA" || status === "NAO_EXIGIDA";

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
          {activating ? (
            <YkButton type="button" variant="secondary" size="sm" onClick={onCancelActivation}>
              Cancelar
            </YkButton>
          ) : active ? null : (
            <YkButton type="button" size="sm" disabled={loading} onClick={onStartActivation}>
              <YkIcons.Power className="h-4 w-4" aria-hidden="true" />
              Ativar licença
            </YkButton>
          )}
        </>
      }
    >
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">Status</span>
          <YkStatusBadge
            label={activationPhase === "activated" ? "Ativa" : (LABEL_BY_STATUS[status] ?? status)}
            tone={activationPhase === "activated" ? "success" : (TONE_BY_STATUS[status] ?? "neutral")}
          />
        </div>

        {activationPhase === "activated" ? (
          <p className="text-sm text-success">
            Licença ativada. Agora é só conectar o WhatsApp abaixo.
          </p>
        ) : null}

        {activationPhase === "error" ? (
          <p className="text-sm text-danger">{activationError ?? "Falha ao ativar a licença."}</p>
        ) : null}

        {!active && !activating && activationPhase !== "error" ? (
          <p className="text-sm text-secondary">
            A Evolution passou a exigir uma ativação gratuita. Sem ela, o envio e o recebimento de
            mensagens ficam bloqueados.
          </p>
        ) : null}

        {activationPhase === "loading" ? (
          <p className="text-sm text-secondary">Gerando o endereço de cadastro...</p>
        ) : null}

        {activationPhase === "waiting" && registerUrl ? (
          <div className="space-y-2 rounded-xl border border-border bg-background p-3">
            <ol className="space-y-1.5 text-sm text-secondary">
              {STEPS.map((step, index) => (
                <li key={step} className="flex gap-2">
                  <span className="font-medium text-foreground">{index + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
            <YkButton type="button" size="sm" onClick={() => onOpenRegisterUrl(registerUrl)}>
              <YkIcons.QrCode className="h-4 w-4" aria-hidden="true" />
              Abrir cadastro
            </YkButton>
            <p className="text-xs text-secondary">
              Aguardando a conclusão do cadastro... O navegador pode mostrar um texto técnico ao
              final — pode fechar e voltar para cá.
            </p>
          </div>
        ) : null}
      </div>
    </SettingsSection>
  );
}
