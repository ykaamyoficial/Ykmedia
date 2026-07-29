import { useCallback, useState } from "react";

export function useToggle(initialValue = false) {
  const [enabled, setEnabled] = useState(initialValue);
  const toggle = useCallback(() => setEnabled((current) => !current), []);
  return { enabled, setEnabled, toggle };
}
