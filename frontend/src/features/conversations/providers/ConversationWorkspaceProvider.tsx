import { type ReactNode, useMemo, useState } from "react";

import { ConversationWorkspaceContext } from "./conversation-workspace-context";

export function ConversationWorkspaceProvider({ children }: { children: ReactNode }) {
  const [sidePanelOpen, setSidePanelOpen] = useState(true);
  const [searchOpen, setSearchOpen] = useState(false);
  const [messageSearch, setMessageSearch] = useState("");
  const [activeSearchIndex, setActiveSearchIndex] = useState(0);

  const value = useMemo(
    () => ({
      sidePanelOpen,
      setSidePanelOpen,
      searchOpen,
      setSearchOpen,
      messageSearch,
      setMessageSearch,
      activeSearchIndex,
      setActiveSearchIndex,
    }),
    [activeSearchIndex, messageSearch, searchOpen, sidePanelOpen],
  );

  return (
    <ConversationWorkspaceContext.Provider value={value}>
      {children}
    </ConversationWorkspaceContext.Provider>
  );
}
