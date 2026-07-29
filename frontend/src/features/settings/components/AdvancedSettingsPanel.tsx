import { YkInput } from "@/shared/forms";
import { SettingsField } from "@/features/settings/components/SettingsField";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

type AdvancedSettingsPanelProps = {
  sqliteDatabase: string;
  whatsappInstance: string;
  ffmpegPath: string;
  disabled?: boolean;
  onSqliteChange: (value: string) => void;
  onWhatsappInstanceChange: (value: string) => void;
  onFfmpegChange: (value: string) => void;
};

export function AdvancedSettingsPanel({
  sqliteDatabase,
  whatsappInstance,
  ffmpegPath,
  disabled = false,
  onSqliteChange,
  onWhatsappInstanceChange,
  onFfmpegChange,
}: AdvancedSettingsPanelProps) {
  return (
    <SettingsSection title="Avancado" description="Area tecnica. Use apenas se souber exatamente o que esta fazendo.">
      <div className="grid gap-4 lg:grid-cols-2">
        <SettingsField label="API Key">
          <span className="text-sm text-secondary">Oculta por seguranca</span>
        </SettingsField>
        <SettingsField label="Webhook Secret">
          <span className="text-sm text-secondary">Oculto por seguranca</span>
        </SettingsField>
        <SettingsField label="Porta backend">
          <span className="text-sm text-secondary">8010</span>
        </SettingsField>
        <SettingsField label="Webhook">
          <span className="text-sm text-secondary">Configurado automaticamente</span>
        </SettingsField>
        <SettingsField label="Docker">
          <span className="text-sm text-secondary">Gerenciado automaticamente</span>
        </SettingsField>
        <SettingsField label="SQLite">
          <YkInput value={sqliteDatabase} disabled={disabled} onChange={(event) => onSqliteChange(event.target.value)} />
        </SettingsField>
        <SettingsField label="Instancia">
          <YkInput value={whatsappInstance} disabled={disabled} onChange={(event) => onWhatsappInstanceChange(event.target.value)} />
        </SettingsField>
        <SettingsField label="FFmpeg">
          <YkInput value={ffmpegPath} disabled={disabled} onChange={(event) => onFfmpegChange(event.target.value)} />
        </SettingsField>
      </div>
    </SettingsSection>
  );
}
