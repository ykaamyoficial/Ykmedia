import { YkButton } from "@/components/system/YkButton";
import { YkSearch } from "@/components/system/YkSearch";
import { useConversationWorkspace } from "@/features/conversations/providers";
import { YkIcons } from "@/shared/icons";

type ConversationLocalSearchBarProps = {
  matchCount: number;
};

export function ConversationLocalSearchBar({ matchCount }: ConversationLocalSearchBarProps) {
  const {
    searchOpen,
    setSearchOpen,
    messageSearch,
    setMessageSearch,
    activeSearchIndex,
    setActiveSearchIndex,
  } = useConversationWorkspace();

  if (!searchOpen) {
    return null;
  }

  const currentMatch = matchCount === 0 ? 0 : activeSearchIndex + 1;

  return (
    <div className="flex items-center gap-2 border-b border-border bg-panel px-4 py-2">
      <div className="w-72">
        <YkSearch
          autoFocus
          value={messageSearch}
          onChange={(event) => {
            setMessageSearch(event.target.value);
            setActiveSearchIndex(0);
          }}
          placeholder="Buscar nesta conversa..."
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setSearchOpen(false);
              setMessageSearch("");
            }
          }}
        />
      </div>
      <span className="text-xs text-secondary">
        {currentMatch}/{matchCount}
      </span>
      <YkButton
        type="button"
        variant="secondary"
        size="sm"
        disabled={matchCount === 0}
        onClick={() => setActiveSearchIndex(Math.max(activeSearchIndex - 1, 0))}
      >
        Anterior
      </YkButton>
      <YkButton
        type="button"
        variant="secondary"
        size="sm"
        disabled={matchCount === 0}
        onClick={() => setActiveSearchIndex(Math.min(activeSearchIndex + 1, matchCount - 1))}
      >
        Proximo
      </YkButton>
      <YkButton
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => {
          setSearchOpen(false);
          setMessageSearch("");
        }}
        aria-label="Fechar busca"
      >
        <YkIcons.X className="h-4 w-4" />
      </YkButton>
    </div>
  );
}
