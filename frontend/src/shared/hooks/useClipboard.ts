import { useState } from "react";

export function useClipboard() {
  const [copied, setCopied] = useState(false);

  async function copy(text: string) {
    await window.navigator.clipboard.writeText(text);
    setCopied(true);
  }

  return { copied, copy };
}
