import { useEffect } from "react";

export function useDebounce<TValue>(
  value: TValue,
  delayMs: number,
  onChange: (value: TValue) => void,
) {
  useEffect(() => {
    const timeout = window.setTimeout(() => onChange(value), delayMs);
    return () => window.clearTimeout(timeout);
  }, [delayMs, onChange, value]);
}
