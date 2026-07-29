import { YkStatusBadge } from "@/components/system/YkStatusBadge";
import { SettingsSection } from "@/features/settings/components/SettingsSection";

type SimpleSettingsPanelProps = {
  title: string;
  description: string;
};

export function SimpleSettingsPanel({ title, description }: SimpleSettingsPanelProps) {
  return (
    <SettingsSection title={title} description={description}>
      <YkStatusBadge label="Configuracao automatica" tone="success" />
    </SettingsSection>
  );
}
