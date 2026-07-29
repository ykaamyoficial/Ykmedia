import { useCallback, useState } from "react";

export function useLocalStorage<TValue>(key: string, initialValue: TValue) {
  const [value, setValue] = useState<TValue>(() => {
    const rawValue = window.localStorage.getItem(key);
    if (rawValue === null) {
      return initialValue;
    }
    try {
      return JSON.parse(rawValue) as TValue;
    } catch {
      return initialValue;
    }
  });

  const updateValue = useCallback(
    (nextValue: TValue) => {
      setValue(nextValue);
      window.localStorage.setItem(key, JSON.stringify(nextValue));
    },
    [key],
  );

  return [value, updateValue] as const;
}
