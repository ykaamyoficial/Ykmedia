import { YkButton } from "@/components/system/YkButton";
import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { YkIcons } from "@/shared/icons";
import { type EvolutionSession } from "@/features/settings/types";
import { friendlyEvolutionState, statusTone } from "@/features/settings/utils";
import { SettingsSection } from "@/features/settings/components/SettingsSection";
import { type PairingPhase } from "@/features/settings/hooks";

type WhatsAppSettingsPanelProps = {
  session?: EvolutionSession;
  loading?: boolean;
  pairingPhase: PairingPhase;
  qrcodeBase64?: string | null;
  secondsLeft?: number;
  pairingError?: string | null;
  onRefresh: () => void;
  onConnect: () => void;
  onCancelPairing: () => void;
  onDisconnect: () => void;
};

function qrcodeSource(value?: string | null): string | undefined {
  if (!value) {
    return undefined;
  }
  return value.startsWith("data:") ? value : `data:image/png;base64,${value}`;
}

const STEPS = [
  "Abra o WhatsApp no celular que vai receber os arquivos",
  "Toque em ⋮ (ou Ajustes) › Aparelhos conectados",
  "Toque em Conectar um aparelho",
  "Aponte a câmera para o código ao lado",
];

export function WhatsAppSettingsPanel({
  session,
  loading = false,
  pairingPhase,
  qrcodeBase64,
  secondsLeft = 0,
  pairingError,
  onRefresh,
  onConnect,
  onCancelPairing,
  onDisconnect,
}: WhatsAppSettingsPanelProps) {
  const state = session?.state ?? "Desconhecida";
  const source = qrcodeSource(qrcodeBase64);
  const pairing = pairingPhase === "loading" || pairingPhase === "waiting";
  const connected = pairingPhase === "connected" || state.toLowerCase() === "open";

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
          {pairing ? (
            <YkButton type="button" variant="secondary" size="sm" onClick={onCancelPairing}>
              Cancelar
            </YkButton>
          ) : (
            <YkButton type="button" size="sm" disabled={loading} onClick={onConnect}>
              <YkIcons.QrCode className="h-4 w-4" aria-hidden="true" />
              {connected ? "Reconectar" : "Conectar WhatsApp"}
            </YkButton>
          )}
          <YkButton type="button" variant="secondary" size="sm" disabled={loading} onClick={onDisconnect}>
            <YkIcons.Power className="h-4 w-4" aria-hidden="true" />
            Desconectar
          </YkButton>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-[1fr_260px]">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground">Status</span>
            <YkStatusBadge label={friendlyEvolutionState(state)} tone={statusTone(state)} />
          </div>

          {pairingPhase === "connected" ? (
            <p className="text-sm text-success">
              WhatsApp conectado. O YkMedia já pode receber arquivos.
            </p>
          ) : null}

          {pairingPhase === "error" ? (
            <p className="text-sm text-danger">{pairingError ?? "Falha ao gerar o QR Code."}</p>
          ) : null}

          {pairing ? (
            <ol className="space-y-1.5 text-sm text-secondary">
              {STEPS.map((step, index) => (
                <li key={step} className="flex gap-2">
                  <span className="font-medium text-foreground">{index + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-secondary">{session?.message ?? "Nao verificado"}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex h-60 w-full items-center justify-center rounded-xl border border-border bg-background p-3 text-center text-sm text-secondary">
            {source ? (
              <img src={source} alt="QR Code do WhatsApp" className="h-full w-full object-contain" />
            ) : pairingPhase === "loading" ? (
              "Gerando o QR Code..."
            ) : pairingPhase === "connected" ? (
              "Conectado ✅"
            ) : (
              "Clique em Conectar WhatsApp para gerar o código."
            )}
          </div>

          {pairingPhase === "waiting" ? (
            <p className="text-center text-xs text-secondary">
              O código se renova sozinho em <strong>{secondsLeft}s</strong> — pode escanear com calma.
            </p>
          ) : null}
        </div>
      </div>
    </SettingsSection>
  );
}
