import { useCallback, useEffect, useRef, useState } from "react";
import {
  createSyntheticTrainingRequest,
  loadSyntheticTrainingRequest,
  loadSyntheticTrainingStatus,
} from "./mingliSyntheticTrainingApi";
import type {
  MingliSyntheticTrainingRequest,
  MingliSyntheticTrainingStatus,
  MingliSyntheticTrainingSuiteStatus,
} from "./mingliSyntheticTrainingTypes";

const ACTIVE_STATUSES = new Set(["QUEUED", "RUNNING", "SEALING"]);

export function useMingliSyntheticTraining(onSettled: () => void) {
  const [status, setStatus] = useState<MingliSyntheticTrainingStatus | null>(null);
  const [runRequest, setRunRequest] = useState<MingliSyntheticTrainingRequest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const settledRef = useRef(onSettled);
  const notifiedRef = useRef<string | null>(null);
  settledRef.current = onSettled;

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const next = await loadSyntheticTrainingStatus(signal);
      if (signal?.aborted) return;
      setStatus(next);
      setRunRequest(next.latest_request);
    } catch (caught) {
      if (!signal?.aborted) {
        setError(caught instanceof Error ? caught.message : String(caught));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);

  const activeRequestRef = runRequest && ACTIVE_STATUSES.has(runRequest.status)
    ? runRequest.request_ref
    : null;

  useEffect(() => {
    if (!activeRequestRef) return undefined;
    const controller = new AbortController();
    let timer: number | null = null;
    const schedulePoll = () => {
      timer = window.setTimeout(() => {
        void loadSyntheticTrainingRequest(activeRequestRef, controller.signal)
          .then((next) => {
            if (controller.signal.aborted) return;
            setError(null);
            setRunRequest(next);
            if (ACTIVE_STATUSES.has(next.status)) {
              schedulePoll();
            } else if (notifiedRef.current !== next.request_ref) {
              notifiedRef.current = next.request_ref;
              settledRef.current();
              void refresh();
            }
          })
          .catch((caught) => {
            if (controller.signal.aborted) return;
            setError(caught instanceof Error ? caught.message : String(caught));
            schedulePoll();
          });
      }, 1200);
    };
    schedulePoll();
    return () => {
      controller.abort();
      if (timer !== null) window.clearTimeout(timer);
    };
  }, [activeRequestRef, refresh]);

  const start = useCallback(async (suite: MingliSyntheticTrainingSuiteStatus) => {
    setStarting(true);
    setError(null);
    try {
      const id = typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const next = await createSyntheticTrainingRequest(suite, `v60-lab:${id}`);
      setRunRequest(next);
      notifiedRef.current = null;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setStarting(false);
    }
  }, []);

  return {
    error,
    loading,
    refresh: () => void refresh(),
    runRequest,
    start,
    starting,
    status,
  };
}
