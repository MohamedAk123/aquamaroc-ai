"use client";
import { useEffect, useState } from "react";

export function useRemote<T>(
  key: string,
  load: (signal: AbortSignal) => Promise<T>,
  enabled = true,
) {
  const [result, setResult] = useState<{
    key: string;
    data?: T;
    error?: Error;
  }>({ key: "" });
  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    load(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setResult({ key, data });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setResult({
            key,
            error:
              error instanceof Error
                ? error
                : new Error("Connexion indisponible"),
          });
      });
    return () => controller.abort();
  }, [key, load, enabled]);
  return result.key === key
    ? { ...result, loading: false }
    : { data: undefined, error: undefined, loading: enabled };
}
