import { cn } from "@/components/ui/utils";
import { type ConversationMessageItem } from "@/features/conversations/types";
import { formatMessageTime, highlightText, labelForMessageType } from "@/features/conversations/utils";
import { YkIcons } from "@/shared/icons";

type ConversationMessageBubbleProps = {
  message: ConversationMessageItem;
  searchTerm?: string;
  activeMatch?: boolean;
  onContextMenu: (message: ConversationMessageItem, position: { x: number; y: number }) => void;
};

function MessageTypeIcon({ type }: { type: string }) {
  const normalized = type.toLowerCase();
  if (normalized.includes("image")) {
    return <YkIcons.Image className="h-4 w-4" aria-hidden="true" />;
  }
  if (normalized.includes("audio")) {
    return <YkIcons.Music className="h-4 w-4" aria-hidden="true" />;
  }
  if (normalized.includes("video")) {
    return <YkIcons.Video className="h-4 w-4" aria-hidden="true" />;
  }
  if (normalized.includes("document")) {
    return <YkIcons.FileText className="h-4 w-4" aria-hidden="true" />;
  }
  return <YkIcons.MessageSquare className="h-4 w-4" aria-hidden="true" />;
}

export function ConversationMessageBubble({
  message,
  searchTerm = "",
  activeMatch = false,
  onContextMenu,
}: ConversationMessageBubbleProps) {
  const outgoing = message.direction === "OUTBOUND";
  const parts = highlightText(message.content, searchTerm);
  const authorLabel = outgoing ? "Sistema" : message.sender_name;

  return (
    <article
      className={cn("flex", outgoing ? "justify-end" : "justify-start")}
      onContextMenu={(event) => {
        event.preventDefault();
        onContextMenu(message, { x: event.clientX, y: event.clientY });
      }}
    >
      <div
        className={cn(
          "max-w-[72%] rounded-2xl border px-3 py-2 shadow-panel",
          activeMatch && "ring-2 ring-accent",
          outgoing
            ? "border-accent/30 bg-accent/15"
            : "border-border bg-panel",
        )}
      >
        <div className="mb-1 flex items-center gap-1.5 text-[11px] text-secondary">
          <MessageTypeIcon type={message.message_type} />
          <span>{authorLabel}</span>
          <span>-</span>
          <span>{labelForMessageType(message.message_type)}</span>
          <span>-</span>
          <span>{formatMessageTime(message.created_at)}</span>
        </div>
        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground">
          {parts.map((part, index) =>
            part.highlighted ? (
              <mark key={`${part.text}-${index}`} className="rounded bg-warning/30 px-0.5 text-foreground">
                {part.text}
              </mark>
            ) : (
              <span key={`${part.text}-${index}`}>{part.text}</span>
            ),
          )}
        </p>
        <p className="mt-1 text-right text-[10px] text-secondary">{message.status}</p>
      </div>
    </article>
  );
}
