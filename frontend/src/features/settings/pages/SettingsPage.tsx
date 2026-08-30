import { useEffect, useMemo, useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkPage } from "@/components/system/YkPage";
import { navigationItems } from "@/routes/navigation";
import { YkErrorState, YkOfflineState, YkSkeleton } from "@/shared/components";
import { isOfflineError } from "@/shared/errors";
import { YkIcons } from "@/shared/icons";
import { openExternalUrl } from "@/shared/services";
import { toast } from "@/shared/toast";
import {
  AdvancedSettingsPanel,
  FoldersSettingsPanel,
  EvolutionLicensePanel,
  SettingsNav,
  type SettingsNavItem,
  type SettingsSectionId,
  SimpleSettingsPanel,
  SystemSettingsPanel,
  WhatsAppSettingsPanel,
} from "@/features/settings/components";
import {
  useConnectEvolutionSession,
  useDisconnectEvolutionSession,
  useEvolutionLicense,
  useEvolutionSession,
  useStartEvolutionLicenseRegistration,
  useWhatsAppPairing,
  usePrepareSystem,
  useRunDiagnostics,
  useSaveSettings,
  useSettings,
} from "@/features/settings/hooks";
import { type AppSettings } from "@/features/settings/types";

const settingsItem = navigationItems.find((item) => item.path === "/configuracoes") ?? navigationItems[0];

const settingsNavItems: SettingsNavItem[] = [
  { id: "folders", label: "Pastas", icon: YkIcons.FolderOpen },
  { id: "whatsapp", label: "WhatsApp", icon: YkIcons.Smartphone },
  { id: "downloads", label: "Downloads", icon: YkIcons.Download },
  { id: "updates", label: "Atualizacoes", icon: YkIcons.RefreshCcw },
  { id: "theme", label: "Tema", icon: YkIcons.Moon },
  { id: "language", label: "Idioma", icon: YkIcons.Globe },
  { id: "backup", label: "Backup", icon: YkIcons.Archive },
  { id: "system", label: "Sistema", icon: YkIcons.Shield },
  { id: "advanced", label: "Avancado", icon: YkIcons.Lock },
];

const simplePanels: Record<SettingsSectionId, { title: string; description: string } | undefined> = {
  folders: undefined,
  whatsapp: undefined,
  downloads: {
    title: "Downloads",
    description: "Downloads automaticos de midias e links estao ativos. O YkMedia prepara os componentes necessarios pelo botao Sistema.",
  },
  updates: {
    title: "Atualizacoes",
    description: "Estrutura reservada para atualizacoes automaticas futuras.",
  },
  theme: {
    title: "Tema",
    description: "Tema escuro premium ativo. Outras opcoes serao adicionadas futuramente.",
  },
  language: {
    title: "Idioma",
    description: "Portugues do Brasil ativo. Estrutura preparada para idiomas futuros.",
  },
  backup: {
    title: "Backup",
    description: "Estrutura preparada para backup e restauracao das configuracoes.",
  },
  system: undefined,
  advanced: undefined,
};

function emptySettings(): AppSettings {
  return {
    downloads_root: "",
    ffmpeg_path: "",
    sqlite_database: "",
    whatsapp_instance: "ykmedia",
    evolution_state: "Desconhecida",
    evolution_message: "",
  };
}

export function SettingsPage() {
  const settingsQuery = useSettings();
  const evolutionQuery = useEvolutionSession();
  const licenseQuery = useEvolutionLicense();
  const startLicenseRegistration = useStartEvolutionLicenseRegistration();
  const saveMutation = useSaveSettings();
  const connectMutation = useConnectEvolutionSession();
  const disconnectMutation = useDisconnectEvolutionSession();
  const prepareMutation = usePrepareSystem();
  const diagnosticsMutation = useRunDiagnostics();
  const [selectedId, setSelectedId] = useState<SettingsSectionId>("system");
  const [draft, setDraft] = useState<AppSettings>(emptySettings);
  const pairing = useWhatsAppPairing();

  useEffect(() => {
    if (settingsQuery.data) {
      setDraft(settingsQuery.data);
    }
  }, [settingsQuery.data]);

  const loading = settingsQuery.isLoading;
  const saving = saveMutation.isPending;
  const actionLoading = connectMutation.isPending || disconnectMutation.isPending || prepareMutation.isPending || diagnosticsMutation.isPending;
  const evolutionSession = useMemo(
    () => evolutionQuery.data ?? {
      instance_name: draft.whatsapp_instance,
      state: draft.evolution_state,
      message: draft.evolution_message,
    },
    [draft.evolution_message, draft.evolution_state, draft.whatsapp_instance, evolutionQuery.data],
  );

  function updateDraft(field: keyof AppSettings, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  function save() {
    saveMutation.mutate(draft, {
      onSuccess: () => toast.success("Configuracoes salvas."),
      onError: () => toast.error("Nao foi possivel salvar as configuracoes."),
    });
  }

  function cancel() {
    setDraft(settingsQuery.data ?? emptySettings());
    toast.info("Alteracoes descartadas.");
  }

  function connectWhatsApp() {
    pairing.start();
  }

  function disconnectWhatsApp() {
    pairing.stop();
    disconnectMutation.mutate(undefined, {
      onSuccess: (session) => {
        void evolutionQuery.refetch();
        toast.info("WhatsApp", session.message);
      },
      onError: () => toast.error("Nao foi possivel desconectar a sessao."),
    });
  }

  function prepareSystemAction() {
    prepareMutation.mutate(undefined, {
      onSuccess: (report) => toast.info("Sistema", report.message),
      onError: () => toast.error("Nao foi possivel preparar o sistema."),
    });
  }

  function runDiagnosticsAction() {
    diagnosticsMutation.mutate(undefined, {
      onSuccess: (report) => toast.info("Diagnostico", report.message),
      onError: () => toast.error("Nao foi possivel executar o diagnostico."),
    });
  }

  function renderPanel() {
    const simplePanel = simplePanels[selectedId];
    if (simplePanel) {
      return <SimpleSettingsPanel title={simplePanel.title} description={simplePanel.description} />;
    }

    if (selectedId === "folders") {
      return (
        <FoldersSettingsPanel
          value={draft.downloads_root}
          disabled={saving}
          onChange={(value) => updateDraft("downloads_root", value)}
        />
      );
    }

    if (selectedId === "whatsapp") {
      return (
        <div className="space-y-4">
          <EvolutionLicensePanel
            license={licenseQuery.data}
            loading={licenseQuery.isFetching || startLicenseRegistration.isPending}
            registerUrl={startLicenseRegistration.data?.register_url}
            onRefresh={() => void licenseQuery.refetch()}
            onStartRegistration={() => startLicenseRegistration.mutate()}
            onOpenRegisterUrl={(url) => void openExternalUrl(url)}
          />
          <WhatsAppSettingsPanel
            session={evolutionSession}
            loading={actionLoading}
            pairingPhase={pairing.phase}
            qrcodeBase64={pairing.qrcodeBase64}
            secondsLeft={pairing.secondsLeft}
            pairingError={pairing.errorMessage}
            onRefresh={() => void evolutionQuery.refetch()}
            onConnect={connectWhatsApp}
            onCancelPairing={pairing.stop}
            onDisconnect={disconnectWhatsApp}
          />
        </div>
      );
    }

    if (selectedId === "advanced") {
      return (
        <AdvancedSettingsPanel
          sqliteDatabase={draft.sqlite_database}
          whatsappInstance={draft.whatsapp_instance}
          ffmpegPath={draft.ffmpeg_path}
          disabled={saving}
          onSqliteChange={(value) => updateDraft("sqlite_database", value)}
          onWhatsappInstanceChange={(value) => updateDraft("whatsapp_instance", value)}
          onFfmpegChange={(value) => updateDraft("ffmpeg_path", value)}
        />
      );
    }

    return (
      <SystemSettingsPanel
        diagnostic={diagnosticsMutation.data}
        setup={prepareMutation.data}
        loading={actionLoading}
        onPrepare={prepareSystemAction}
        onDiagnostics={runDiagnosticsAction}
      />
    );
  }

  if (settingsQuery.isError) {
    return (
      <YkPage item={settingsItem}>
        {isOfflineError(settingsQuery.error) ? <YkOfflineState /> : <YkErrorState />}
        <YkButton variant="secondary" className="w-fit" onClick={() => void settingsQuery.refetch()}>
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Tentar novamente
        </YkButton>
      </YkPage>
    );
  }

  return (
    <YkPage item={settingsItem}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-foreground">Configuracoes do sistema</h2>
          <p className="text-sm text-secondary">Preferencias e conexoes atuais do YkMedia.</p>
        </div>
        <div className="flex items-center gap-2">
          <YkButton type="button" variant="secondary" size="sm" disabled={loading || saving} onClick={cancel}>
            Cancelar
          </YkButton>
          <YkButton type="button" size="sm" disabled={loading || saving} onClick={save}>
            Salvar
          </YkButton>
        </div>
      </div>

      {loading ? (
        <YkSkeleton className="h-96 w-full" />
      ) : (
        <div className="flex gap-5">
          <SettingsNav items={settingsNavItems} selectedId={selectedId} onSelect={setSelectedId} />
          <div className="min-w-0 flex-1">{renderPanel()}</div>
        </div>
      )}
    </YkPage>
  );
}
