import { useCallback, useRef } from "react";

/** Mantiene una referencia estable al handler más reciente (evita loops en deps de useEffect). */
export function useStableHandler<T extends (...args: never[]) => void>(handler: T | undefined): T | undefined {
  const ref = useRef(handler);
  ref.current = handler;
  return useCallback(((...args: Parameters<T>) => {
    ref.current?.(...args);
  }) as T, []);
}
