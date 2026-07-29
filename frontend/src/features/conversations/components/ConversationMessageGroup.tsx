import { ConversationDateDivider } from "@/features/conversations/components/ConversationDateDivider";
import { ConversationMessageBubble } from "@/features/conversations/components/ConversationMessageBubble";
import { type ConversationMessageItem } from "@/features/conversations/types";

type ConversationMessageGroupProps = {
  label: string;
  messages: ConversationMessageItem[];
  searchTerm: string;
  activeMatchId?: string;
  onContextMenu: (message: ConversationMessageItem, position: { x: number; y: number }) => void;
};

export function ConversationMessageGroup({
  label,
  messages,
  searchTerm,
  activeMatchId,
  onContextMenu,
}: ConversationMessageGroupProps) {
  return (
    <div>
      <ConversationDateDivider label={label} />
      <div className="grid gap-2">
        {messages.map((message) => (
          <ConversationMessageBubble
            key={message.id}
            message={message}
            searchTerm={searchTerm}
            activeMatch={message.id === activeMatchId}
            onContextMenu={onContextMenu}
          />
        ))}
      </div>
    </div>
  );
}
