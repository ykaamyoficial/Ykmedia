import { YkAvatar } from "@/components/system/YkAvatar";
import { YkButton } from "@/components/system/YkButton";
import { type ConversationDetails } from "@/features/conversations/types";
import { formatConversationTimestamp } from "@/features/conversations/utils";
import { YkIcons } from "@/shared/icons";
import { formatCount } from "@/shared/utils";

type ConversationContextPanelProps = {
  details: ConversationDetails;
  onClose: () => void;
};

function InfoRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="grid gap-0.5">
      <span className="text-[11px] font-medium uppercase tracking-wide text-secondary">{label}</span>
      <span className="break-words text-sm text-foreground">{value || "-"}</span>
    </div>
  );
}

export function ConversationContextPanel({ details, onClose }: ConversationContextPanelProps) {
  return (
    <aside className="hidden w-[280px] shrink-0 border-l border-border bg-surface/40 xl:flex xl:flex-col">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h3 className="text-sm font-semibold text-foreground">Contexto</h3>
        <YkButton type="button" variant="ghost" size="sm" onClick={onClose} aria-label="Recolher painel">
          <YkIcons.PanelRightClose className="h-4 w-4" />
        </YkButton>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-3">
        <section className="rounded-xl border border-border bg-panel p-3 text-center">
          <div className="flex justify-center">
            <YkAvatar
              name={details.profile.display_name}
              imageUrl={details.profile.profile_photo_url ?? undefined}
              size="lg"
              alt={`Foto de ${details.profile.display_name}`}
            />
          </div>
          <h4 className="mt-3 truncate text-sm font-semibold text-foreground">{details.profile.display_name}</h4>
          <p className="truncate text-xs text-secondary">{details.profile.phone}</p>
        </section>

        <section className="mt-3 grid gap-3 rounded-xl border border-border bg-panel p-3">
          <InfoRow label="Origem" value="WhatsApp" />
          <InfoRow label="Primeira interacao" value={formatConversationTimestamp(details.created_at)} />
          <InfoRow label="Ultima atividade" value={formatConversationTimestamp(details.updated_at)} />
          <InfoRow label="Mensagens" value={formatCount(details.message_count)} />
        </section>

        <section className="mt-3 grid gap-3 rounded-xl border border-border bg-panel p-3">
          <InfoRow label="Sessao" value={details.session_status} />
          <InfoRow label="Categoria" value={details.category} />
          <InfoRow label="Status adicional" value={details.additional_status} />
        </section>
      </div>
    </aside>
  );
}
