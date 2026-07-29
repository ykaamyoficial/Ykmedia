import { type ReactNode } from "react";

type SettingsFieldProps = {
  label: string;
  children: ReactNode;
};

export function SettingsField({ label, children }: SettingsFieldProps) {
  return (
    <label className="grid gap-1.5 text-sm font-medium text-foreground">
      {label}
      {children}
    </label>
  );
}
