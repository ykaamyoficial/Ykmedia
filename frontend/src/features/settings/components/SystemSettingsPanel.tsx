import { useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkDataTable } from "@/shared/tables";
import { YkIcons } from "@/shared/icons";
import { type DiagnosticReport, type SetupReport } from "@/features/settings/types";
import { statusTone } from "@/features/settings/utils";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

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
  const hasProblem = steps.some((step) => step.status === "ERROR" || step.status === "WARNING");

  // Fotografar a tela corta a mensagem longa. Copiar o relatorio inteiro e a
  // forma mais rapida de o usuario nos mostrar o que realmente aconteceu.
  const copyDetails = async () => {
    const report = steps.map((step) => `[${step.status}] ${step.label}: ${step.message}`).join("\n");
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
          <YkButton type="button" size="sm" disabled={loading} onClick={onPrepare}>
            <YkIcons.Wand2 className="h-4 w-4" aria-hidden="true" />
            {preparing ? "Preparando..." : "Preparar Sistema Automaticamente"}
          </YkButton>
          <YkButton type="button" variant="secondary" size="sm" disabled={loading} onClick={onDiagnostics}>
            <YkIcons.Search className="h-4 w-4" aria-hidden="true" />
            Executar Diagnostico
          </YkButton>
        </>
      }
    >
      <div className="space-y-4">
        {preparing ? (
          <div className="space-y-1 rounded-xl border border-border bg-background p-3">
            <p className="text-sm font-medium text-foreground">Preparando o sistema...</p>
            <p className="text-sm text-secondary">
              Na primeira vez isso baixa mais de 1&nbsp;GB de componentes e pode levar vários
              minutos. Pode deixar a janela aberta — se a internet cair, clique de novo que o
              download continua de onde parou.
            </p>
          </div>
        ) : (
          <p className="text-sm text-secondary">{summary}</p>
        )}

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
              {steps.map((step) => (
                <li
                  key={step.key}
                  className="flex flex-col gap-1 rounded-xl border border-border bg-background p-3 sm:flex-row sm:items-start sm:gap-3"
                >
                  <div className="shrink-0">
                    <YkStatusBadge label={step.status} tone={statusTone(step.status)} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">{step.label}</p>
                    <p className="whitespace-pre-wrap break-words text-sm text-secondary">
                      {step.message}
                    </p>
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
                  <YkStatusBadge label={row.original.status} tone={statusTone(row.original.status)} />
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
