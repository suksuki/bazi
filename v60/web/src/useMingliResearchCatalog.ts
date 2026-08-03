import { useEffect, useState } from "react";
import { loadSyntheticExperimentCatalog } from "./mingliSyntheticLabApi";
import type { MingliSyntheticExperimentCatalog } from "./mingliSyntheticLabTypes";
import { loadSyntheticSuiteCatalog } from "./mingliSyntheticSuiteApi";
import type { MingliSyntheticSuiteCatalog } from "./mingliSyntheticSuiteTypes";

export function useMingliResearchCatalog() {
  const [experiments, setExperiments] =
    useState<MingliSyntheticExperimentCatalog | null>(null);
  const [suites, setSuites] = useState<MingliSyntheticSuiteCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void Promise.all([
      loadSyntheticExperimentCatalog(controller.signal),
      loadSyntheticSuiteCatalog(null, controller.signal),
    ])
      .then(([experimentCatalog, suiteCatalog]) => {
        if (controller.signal.aborted) return;
        setExperiments(experimentCatalog);
        setSuites(suiteCatalog);
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : String(caught));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [retryKey]);

  return {
    error,
    experiments,
    loading,
    retry: () => setRetryKey((value) => value + 1),
    suites,
  };
}
