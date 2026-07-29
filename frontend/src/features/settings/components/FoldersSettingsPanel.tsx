import { YkButton } from "@/components/system/YkButton";
import { YkIcons } from "@/shared/icons";
import { YkInput } from "@/shared/forms";
import { SettingsField } from "@/features/settings/components/SettingsField";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

type FoldersSettingsPanelProps = {
  value: string;
  disabled?: boolean;
  onChange: (value: string) => void;
};

function openPath(path: string) {
  const normalized = path.replace(/\\/g, "/");
  window.open(`file:///${normalized}`, "_blank", "noopener,noreferrer");
}

export function FoldersSettingsPanel({ value, disabled = false, onChange }: FoldersSettingsPanelProps) {
  return (
    <SettingsSection
      title="Pastas"
      description="Pasta onde as midias organizadas sao armazenadas."
      actions={
        <>
          <YkButton type="button" variant="secondary" size="sm" disabled={disabled}>
            <YkIcons.FolderOpen className="h-4 w-4" aria-hidden="true" />
            Escolher pasta
          </YkButton>
          <YkButton type="button" variant="secondary" size="sm" onClick={() => openPath(value)}>
            <YkIcons.FolderOpen className="h-4 w-4" aria-hidden="true" />
            Abrir pasta
          </YkButton>
        </>
      }
    >
      <SettingsField label="Pasta das midias">
        <YkInput value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} />
      </SettingsField>
    </SettingsSection>
  );
}
