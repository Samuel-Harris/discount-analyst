import { useCallback, useEffect, useRef, useState } from "react";

import { subscribeQueryInvalidation } from "./invalidation";

type FetchMode = "initial" | "silent";

export interface UsePollingQueryOptions<T> {
  queryKey: string;
  enabled: boolean;
  pollMs: number;
  fetcher: (signal: AbortSignal) => Promise<T>;
  /** User-visible error when the thrown value is not an `Error`. */
  defaultErrorMessage: string;
  /**
   * When true and the query is enabled, `loading` starts true before the first
   * fetch settles (list UX). When false, `loading` flips true only once the
   * fetch begins (detail UX).
   */
  loadingStartsTrueWhenEnabled: boolean;
  /**
   * Whether to drop cached `data` when a fetch fails. List queries keep prior
   * rows on error; detail clears only on the first load attempt.
   */
  discardDataOnError: (mode: FetchMode) => boolean;
  /**
   * When `enabled` becomes false, apply this snapshot synchronously.
   * Read via ref inside effects so callers may pass stable inline factories.
   */
  resetWhenDisabled?: () => {
    data: T | null;
    error: string | null;
    loading: boolean;
  };
}

export interface PollingQueryResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Shared polling + invalidation primitive for dashboard GET endpoints.
 * One interval per mounted hook; invalidation triggers the same silent refetch path.
 */
export function usePollingQuery<T>(
  options: UsePollingQueryOptions<T>,
): PollingQueryResult<T> {
  const {
    queryKey,
    enabled,
    pollMs,
    fetcher,
    defaultErrorMessage,
    loadingStartsTrueWhenEnabled,
    discardDataOnError,
    resetWhenDisabled,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(() =>
    Boolean(enabled && loadingStartsTrueWhenEnabled),
  );
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);
  const abortRef = useRef<AbortController | null>(null);
  const resetWhenDisabledRef = useRef(resetWhenDisabled);
  resetWhenDisabledRef.current = resetWhenDisabled;

  const formatMessage = useCallback(
    (e: unknown) => (e instanceof Error ? e.message : defaultErrorMessage),
    [defaultErrorMessage],
  );

  const executeFetch = useCallback(
    async (mode: FetchMode) => {
      if (!enabled) return;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      const { signal } = controller;

      if (mode === "initial") setLoading(true);
      try {
        const result = await fetcher(signal);
        if (!mounted.current || signal.aborted) return;
        setData(result);
        setError(null);
      } catch (e) {
        if (e instanceof Error && e.name === "AbortError") return;
        if (!mounted.current || signal.aborted) return;
        const message = formatMessage(e);
        if (discardDataOnError(mode)) setData(null);
        setError(message);
      } finally {
        if (!mounted.current || signal.aborted) return;
        if (mode === "initial") setLoading(false);
      }
    },
    [enabled, fetcher, formatMessage, discardDataOnError],
  );

  useEffect(() => {
    mounted.current = true;
    if (!enabled) {
      abortRef.current?.abort();
      abortRef.current = null;
      const snap = resetWhenDisabledRef.current?.();
      if (snap) {
        setData(snap.data);
        setError(snap.error);
        setLoading(snap.loading);
      } else {
        setData(null);
        setError(null);
        setLoading(false);
      }
      return () => {
        mounted.current = false;
      };
    }

    void executeFetch("initial");
    const interval = window.setInterval(
      () => void executeFetch("silent"),
      pollMs,
    );
    const unsub = subscribeQueryInvalidation(queryKey, () =>
      executeFetch("silent"),
    );

    return () => {
      mounted.current = false;
      window.clearInterval(interval);
      unsub();
      abortRef.current?.abort();
    };
  }, [enabled, pollMs, queryKey, executeFetch]);

  const refresh = useCallback(async () => {
    await executeFetch("silent");
  }, [executeFetch]);

  return { data, loading, error, refresh };
}
