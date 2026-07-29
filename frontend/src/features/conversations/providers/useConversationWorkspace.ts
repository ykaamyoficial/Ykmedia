import { useContext } from "react";

import { ConversationWorkspaceContext } from "./conversation-workspace-context";

export function useConversationWorkspace() {
  const context = useContext(ConversationWorkspaceContext);
  if (!context) {
    throw new Error("useConversationWorkspace must be used inside ConversationWorkspaceProvider.");
  }
  return context;
}
