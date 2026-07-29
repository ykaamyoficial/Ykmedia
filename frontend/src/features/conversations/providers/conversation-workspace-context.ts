import { createContext } from "react";

export type ConversationWorkspaceContextValue = {
  sidePanelOpen: boolean;
  setSidePanelOpen: (open: boolean) => void;
  searchOpen: boolean;
  setSearchOpen: (open: boolean) => void;
  messageSearch: string;
  setMessageSearch: (value: string) => void;
  activeSearchIndex: number;
  setActiveSearchIndex: (index: number) => void;
};

export const ConversationWorkspaceContext = createContext<ConversationWorkspaceContextValue | null>(null);
