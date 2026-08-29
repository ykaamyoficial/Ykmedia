import { type ReactNode } from "react";

type YkSidebarSectionProps = {
  title: string;
  compact: boolean;
  children: ReactNode;
};

export function YkSidebarSection({ title, compact, children }: YkSidebarSectionProps) {
  return (
    <section className="flex flex-col gap-1">
      {!compact && (
        <h2 className="px-2 text-[11px] font-semibold uppercase tracking-wide text-secondary">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}
