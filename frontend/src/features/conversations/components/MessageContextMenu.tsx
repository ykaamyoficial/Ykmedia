import { type ConversationMessageItem } from "@/features/conversations/types";
import { YkIcons } from "@/shared/icons";

type MessageContextMenuProps = {
  message: ConversationMessageItem;
  position: { x: number; y: number };
  onClose: () => void;
};

async function copyText(value: string) {
  await navigator.clipboard?.writeText(value);
}

export function MessageContextMenu({ message, position, onClose }: MessageContextMenuProps) {
  const items = [
    {
      label: "Copiar texto",
      value: message.content,
    },
    {
      label: "Copiar conteudo bruto",
      value: JSON.stringify(message, null, 2),
    },
  ];

  return (
    <div
      className="fixed z-50 min-w-48 rounded-xl border border-border bg-panel p-1 shadow-panel"
      style={{ left: position.x, top: position.y }}
      role="menu"
      onMouseLeave={onClose}
    >
      {items.map((item) => (
        <button
          key={item.label}
          type="button"
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs text-foreground hover:bg-muted"
          onClick={() => {
            void copyText(item.value);
            onClose();
          }}
          role="menuitem"
        >
          <YkIcons.Copy className="h-3.5 w-3.5 text-secondary" />
          {item.label}
        </button>
      ))}
    </div>
  );
}
