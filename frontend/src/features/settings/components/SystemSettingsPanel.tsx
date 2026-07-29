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
  onPrepare: () => void;
  onDiagnostics: () => void;
};

export function SystemSettingsPanel({
  diagnostic,
  setup,
  loading = false,
  onPrepare,
  onDiagnostics,
}: SystemSettingsPanelProps) {
  const rows = diagnostic?.items ?? [];
  const summary = diagnostic?.message ?? setup?.message ?? "Clique em Preparar Sistema Automaticamente para verificar e corrigir tudo.";

  return (
    <SettingsSection
      title="Sistema"
      description="Tudo que o usuario precisa saber: funcionando ou corrigir."
      actions={
        <>
          <YkButton type="button" size="sm" disabled={loading} onClick={onPrepare}>
            <YkIcons.Wand2 className="h-4 w-4" aria-hidden="true" />
            Preparar Sistema Automaticamente
          </YkButton>
          <YkButton type="button" variant="secondary" size="sm" disabled={loading}>
            <YkIcons.CornerDownRight className="h-4 w-4" aria-hidden="true" />
            Abrir assistente
          </YkButton>
          <YkButton type="button" variant="secondary" size="sm" disabled={loading} onClick={onDiagnostics}>
            <YkIcons.Search className="h-4 w-4" aria-hidden="true" />
            Executar Diagnostico
          </YkButton>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-sm text-secondary">{summary}</p>
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
