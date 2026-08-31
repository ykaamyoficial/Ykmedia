import { YkButton } from "@/components/system/YkButton";
import { YkIcons } from "@/shared/icons";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

type FirstRunGuideProps = {
  environmentReady: boolean;
  licenseActive: boolean;
  whatsappConnected: boolean;
  onPrepare: () => void;
  preparing?: boolean;
};

type Stage = {
  key: string;
  title: string;
  description: string;
  done: boolean;
};

/**
 * O caminho obrigatorio de uma maquina nova.
 *
 * Preparar, ativar a licenca e conectar o WhatsApp precisam acontecer nessa
 * ordem, mas a tela de Configuracoes mostrava tudo ao mesmo tempo e o usuario
 * tinha de adivinhar por onde comecar -- e descobrir a ordem errando.
 */
export function FirstRunGuide({
  environmentReady,
  licenseActive,
  whatsappConnected,
  onPrepare,
  preparing = false,
}: FirstRunGuideProps) {
  const stages: Stage[] = [
    {
      key: "environment",
      title: "Preparar o sistema",
      description:
        "Baixa e liga os componentes internos. Na primeira vez passa de 1 GB e leva alguns minutos.",
      done: environmentReady,
    },
    {
      key: "license",
      title: "Ativar a licenca",
      description: "A Evolution exige uma ativacao gratuita, feita uma vez por computador.",
      done: licenseActive,
    },
    {
      key: "whatsapp",
      title: "Conectar o WhatsApp",
      description: "Leia o QR Code com o celular que vai atender a equipe.",
      done: whatsappConnected,
    },
  ];

  const current = stages.find((stage) => !stage.done);
  // Cumprido o seu papel, o guia sai da frente em vez de virar ruido fixo.
  if (!current) {
    return null;
  }

  return (
    <SettingsSection
      title="Primeiros passos"
      description="Tres etapas, nesta ordem. Depois disso o programa esta pronto para uso."
    >
      <ol className="space-y-2">
        {stages.map((stage, index) => {
          const isCurrent = stage.key === current.key;
          return (
            <li
              key={stage.key}
              data-testid={isCurrent ? "current-stage" : `stage-${stage.key}`}
              className={
                isCurrent
                  ? "rounded-xl border border-accent/50 bg-accent/5 p-4"
                  : "rounded-xl border border-border bg-background p-3 opacity-70"
              }
            >
              <div className="flex items-start gap-3">
                <span
                  className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border text-xs font-semibold tabular-nums"
                  aria-hidden="true"
                >
                  {stage.done ? (
                    <YkIcons.CheckCircle2 className="h-4 w-4 text-success" />
                  ) : (
                    index + 1
                  )}
                </span>
                <div className="min-w-0 space-y-1">
                  <p className="text-sm font-semibold text-foreground">{stage.title}</p>
                  <p className="text-sm text-secondary">{stage.description}</p>
                  {stage.done ? (
                    <p className="text-xs font-medium text-success">Concluído</p>
                  ) : null}
                  {isCurrent && stage.key === "environment" ? (
                    <YkButton type="button" size="sm" disabled={preparing} onClick={onPrepare}>
                      <YkIcons.Wand2 className="h-4 w-4" aria-hidden="true" />
                      {preparing ? "Preparando..." : "Preparar agora"}
                    </YkButton>
                  ) : null}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </SettingsSection>
  );
}
