import { type ReactNode } from "react";

import { YkPanel } from "@/components/system/YkPanel";

type SettingsSectionProps = {
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function SettingsSection({ title, description, actions, children }: SettingsSectionProps) {
  return (
    <YkPanel className="overflow-hidden">
      <div className="flex items-start justify-between gap-4 border-b border-border p-4">
        <div>
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
          <p className="mt-1 text-sm text-secondary">{description}</p>
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </div>
      <div className="p-4">{children}</div>
    </YkPanel>
  );
}
