import { useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkDataTable } from "@/shared/tables";
import { YkIcons } from "@/shared/icons";
import {
  type DiagnosticReport,
  type SetupReport,
} from "@/features/settings/types";
import { statusLabel, statusTone } from "@/features/settings/utils";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

function TechnicalDetail({ detail }: { detail: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="pt-1">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="text-xs font-medium text-secondary underline underline-offset-2 hover:text-foreground"
      >
        {open ? "Ocultar detalhes técnicos" : "Ver detalhes técnicos"}
      </button>
      {open ? (
        // Rolagem propria: o log do Docker e largo e esticava a pagina inteira.
        <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-surface p-2 text-xs text-secondary">
          {detail}
        </pre>
      ) : null}
    </div>
  );
}

type SystemSettingsPanelProps = {
  diagnostic?: DiagnosticReport;
  setup?: SetupReport;
  loading?: boolean;
  preparing?: boolean;
  onPrepare: () => void;
  onDiagnostics: () => void;
};

export function SystemSettingsPanel({
  diagnostic,
  setup,
  loading = false,
  preparing = false,
  onPrepare,
  onDiagnostics,
}: SystemSettingsPanelProps) {
  const [copied, setCopied] = useState(false);
  const rows = diagnostic?.items ?? [];
  const steps = setup?.steps ?? [];
  const hasProblem = steps.some(
    (step) => step.status === "ERROR" || step.status === "WARNING",
  );
  // A primeira etapa que falhou e a causa; as seguintes costumam ser efeito.
  const blockingStep = steps.find((step) => step.status === "ERROR");

  // Fotografar a tela corta a mensagem longa. Copiar o relatorio inteiro e a
  // forma mais rapida de o usuario nos mostrar o que realmente aconteceu.
  const copyDetails = async () => {
    const report = steps
      .map((step) => {
        const lines = [`[${step.status}] ${step.label}: ${step.message}`];
        if (step.action) lines.push(`  Acao: ${step.action}`);
        if (step.detail) lines.push(`  Detalhe: ${step.detail}`);
        return lines.join("\n");
      })
      .join("\n");
    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const summary =
    diagnostic?.message ??
    setup?.message ??
    "Clique em Preparar Sistema Automaticamente para verificar e corrigir tudo.";

  return (
    <SettingsSection
      title="Sistema"
      description="Tudo que o usuario precisa saber: funcionando ou corrigir."
      actions={
        <>
          <YkButton
            type="button"
            size="sm"
            disabled={loading}
            onClick={onPrepare}
          >
            <YkIcons.Wand2 className="h-4 w-4" aria-hidden="true" />
            {preparing ? "Preparando..." : "Preparar Sistema Automaticamente"}
          </YkButton>
          <YkButton
            type="button"
            variant="secondary"
            size="sm"
            disabled={loading}
            onClick={onDiagnostics}
          >
            <YkIcons.Search className="h-4 w-4" aria-hidden="true" />
            Executar Diagnostico
          </YkButton>
        </>
      }
    >
      <div className="space-y-4">
        {preparing ? (
          <div className="space-y-1 rounded-xl border border-border bg-background p-3">
            <p className="text-sm font-medium text-foreground">
              Preparando o sistema...
            </p>
            <p className="text-sm text-secondary">
              Na primeira vez isso baixa mais de 1&nbsp;GB de componentes e pode
              levar vários minutos. Pode deixar a janela aberta — se a internet
              cair, clique de novo que o download continua de onde parou.
            </p>
          </div>
        ) : (
          <p className="text-sm text-secondary">{summary}</p>
        )}

        {/* O item que bloqueia vem primeiro e com destaque. Antes as etapas
            tinham todas o mesmo peso e o usuario precisava descobrir sozinho
            qual delas exigia acao. */}
        {blockingStep && !preparing ? (
          <div
            data-testid="blocking-step"
            className="space-y-2 rounded-xl border border-danger/40 bg-danger/5 p-4"
          >
            <div className="flex items-center gap-2">
              <YkStatusBadge
                label={statusLabel(blockingStep.status)}
                tone={statusTone(blockingStep.status)}
              />
              <p className="text-sm font-semibold text-foreground">
                {blockingStep.label}
              </p>
            </div>
            <p className="break-words text-sm text-foreground">
              {blockingStep.message}
            </p>
            {blockingStep.action ? (
              <p className="text-sm text-secondary">{blockingStep.action}</p>
            ) : null}
            {blockingStep.detail ? (
              <TechnicalDetail detail={blockingStep.detail} />
            ) : null}
          </div>
        ) : null}

        {steps.length > 0 && !preparing ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-foreground">Etapas</p>
              {hasProblem ? (
                <YkButton
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    void copyDetails();
                  }}
                >
                  <YkIcons.Copy className="h-4 w-4" aria-hidden="true" />
                  {copied ? "Copiado!" : "Copiar detalhes"}
                </YkButton>
              ) : null}
            </div>
            <ul className="space-y-2">
              {/* O item em destaque ja aparece acima por inteiro: repeti-lo
                  aqui so faria o usuario ler a mesma coisa duas vezes. */}
              {steps
                .filter((step) => step.key !== blockingStep?.key)
                .map((step) => (
                  <li
                    key={step.key}
                    className="flex flex-col gap-1 rounded-xl border border-border bg-background p-3 sm:flex-row sm:items-start sm:gap-3"
                  >
                    <div className="shrink-0">
                      <YkStatusBadge
                        label={statusLabel(step.status)}
                        tone={statusTone(step.status)}
                      />
                    </div>
                    <div className="min-w-0 space-y-1">
                      <p className="text-sm font-medium text-foreground">
                        {step.label}
                      </p>
                      <p className="break-words text-sm text-secondary">
                        {step.message}
                      </p>

                      {step.action ? (
                        <p className="text-sm font-medium text-foreground">
                          {step.action}
                        </p>
                      ) : null}

                      {/* O log cru so aparece a pedido: com ele sempre visivel, a
                        frase util ficava perdida no meio do bloco tecnico. */}
                      {step.detail ? (
                        <TechnicalDetail detail={step.detail} />
                      ) : null}
                    </div>
                  </li>
                ))}
            </ul>
          </div>
        ) : null}

        {rows.length > 0 ? (
          <YkDataTable
            data={rows}
            columns={[
              { accessorKey: "name", header: "Item" },
              {
                accessorKey: "status",
                header: "Status",
                cell: ({ row }) => (
                  <YkStatusBadge
                    label={row.original.status}
                    tone={statusTone(row.original.status)}
                  />
                ),
              },
              { accessorKey: "message", header: "Mensagem" },
            ]}
          />
        ) : null}
      </div>
    </SettingsSection>
  );
}
