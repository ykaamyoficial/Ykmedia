import { YkButton } from "@/components/system/YkButton";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkIcons } from "@/shared/icons";
import { type EvolutionSession } from "@/features/settings/types";
import { friendlyEvolutionState, statusTone } from "@/features/settings/utils";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

type WhatsAppSettingsPanelProps = {
  session?: EvolutionSession;
  loading?: boolean;
  qrcodeBase64?: string | null;
  onRefresh: () => void;
  onConnect: () => void;
  onDisconnect: () => void;
};

function qrcodeSource(value?: string | null): string | undefined {
  if (!value) {
    return undefined;
  }
  return value.startsWith("data:") ? value : `data:image/png;base64,${value}`;
}

export function WhatsAppSettingsPanel({
  session,
  loading = false,
  qrcodeBase64,
  onRefresh,
  onConnect,
  onDisconnect,
}: WhatsAppSettingsPanelProps) {
  const state = session?.state ?? "Desconhecida";
  const source = qrcodeSource(qrcodeBase64);

  return (
    <SettingsSection
      title="WhatsApp"
      description="Conexao da sessao utilizada pelo YkMedia."
      actions={
        <>
          <YkButton type="button" variant="secondary" size="sm" disabled={loading} onClick={onRefresh}>
            <YkIcons.Search className="h-4 w-4" aria-hidden="true" />
            Verificar
          </YkButton>
          <YkButton type="button" size="sm" disabled={loading} onClick={onConnect}>
            <YkIcons.QrCode className="h-4 w-4" aria-hidden="true" />
            Conectar WhatsApp
          </YkButton>
          <YkButton type="button" variant="secondary" size="sm" disabled={loading} onClick={onDisconnect}>
            <YkIcons.Power className="h-4 w-4" aria-hidden="true" />
            Desconectar
          </YkButton>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-[1fr_240px]">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground">Status</span>
            <YkStatusBadge label={friendlyEvolutionState(state)} tone={statusTone(state)} />
          </div>
          <p className="text-sm text-secondary">{session?.message ?? "Nao verificado"}</p>
        </div>
        <div className="flex h-60 w-60 items-center justify-center rounded-xl border border-border bg-background p-3 text-center text-sm text-secondary">
          {source ? (
            <img src={source} alt="QR Code do WhatsApp" className="h-full w-full object-contain" />
          ) : (
            "Clique em Gerar QR Code para conectar uma nova sessao."
          )}
        </div>
      </div>
    </SettingsSection>
  );
}
