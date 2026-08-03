import { useEffect, useMemo, useState } from "react";
import {
  directMingliScene,
  INITIAL_MINGLI_CLOCK,
} from "../mingliSceneDirector";
import {
  loadSyntheticExperimentCatalog,
  loadSyntheticExperimentSnapshot,
} from "../mingliSyntheticLabApi";
import { loadSyntheticSuiteCatalog } from "../mingliSyntheticSuiteApi";
import type { MingliSyntheticLabRoute } from "../mingliSyntheticLabNavigation";
import type {
  MingliSyntheticExperimentCatalog,
  MingliSyntheticExperimentSnapshot,
} from "../mingliSyntheticLabTypes";
import type {
  MingliSyntheticSuiteCatalog,
  MingliSyntheticSuiteRunSelection,
} from "../mingliSyntheticSuiteTypes";
import {
  compareWithPreviousSyntheticSuiteRun,
  exactSyntheticSuiteItem,
  findSyntheticSuiteRun,
  firstSyntheticSuiteRoute,
  latestSyntheticSuiteRunSelection,
  resolveSyntheticSuiteRoute,
} from "../mingliSyntheticSuiteSelection";
import type { MingliStageViewContext } from "../mingliStageTypes";
import { MingliScenePlayer } from "./MingliScenePlayer";
import {
  MingliSyntheticEmptyState,
  MingliSyntheticSceneHeader,
  MingliSyntheticStageBoundary,
  MingliSyntheticSwitchingFeedback,
} from "./MingliSyntheticExperimentFeedback";
import { MingliSyntheticExperimentInspector } from "./MingliSyntheticExperimentInspector";
import { MingliSyntheticExperimentToolbar } from "./MingliSyntheticExperimentToolbar";
import { MingliSyntheticSuiteSummary } from "./MingliSyntheticSuiteSummary";

export function MingliSyntheticExperimentScene({
  onBackToCurrent,
  onContextChange,
  onExit,
  onOpenReading,
  onRouteChange,
  route,
}: {
  onBackToCurrent: () => void;
  onContextChange: (context: MingliStageViewContext) => void;
  onExit: () => void;
  onOpenReading: () => void;
  onRouteChange: (
    route: MingliSyntheticLabRoute,
    mode?: "push" | "replace",
  ) => void;
  route: MingliSyntheticLabRoute;
}) {
  const [catalog, setCatalog] = useState<MingliSyntheticExperimentCatalog | null>(null);
  const [suiteCatalog, setSuiteCatalog] =
    useState<MingliSyntheticSuiteCatalog | null>(null);
  const [suiteHistoryCatalog, setSuiteHistoryCatalog] =
    useState<MingliSyntheticSuiteCatalog | null>(null);
  const [snapshot, setSnapshot] =
    useState<MingliSyntheticExperimentSnapshot | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [snapshotError, setSnapshotError] = useState<{
    experimentRef: string;
    message: string;
    runRef: string;
    variant: "A" | "B";
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const suiteSelection = useMemo(
    () => route.suiteRunRef && suiteCatalog
      ? findSyntheticSuiteRun(suiteCatalog, route.suiteRunRef)
      : null,
    [route.suiteRunRef, suiteCatalog],
  );
  const suiteComparison = useMemo(
    () => suiteSelection && suiteHistoryCatalog
      ? compareWithPreviousSyntheticSuiteRun(
          suiteHistoryCatalog,
          suiteSelection,
        )
      : null,
    [suiteHistoryCatalog, suiteSelection],
  );
  const boundSuiteItem = useMemo(
    () => exactSyntheticSuiteItem(suiteSelection, route),
    [route, suiteSelection],
  );
  const committedSnapshot = snapshot
    && snapshot.experiment_ref === route.experimentRef
    && snapshot.run_ref === route.runRef
    ? snapshot
    : null;
  const activeSnapshotError = snapshotError
    && snapshotError.experimentRef === route.experimentRef
    && snapshotError.runRef === route.runRef
    && snapshotError.variant === route.variant
    ? snapshotError.message
    : null;

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setCatalogError(null);
    setSuiteCatalog(null);
    onContextChange({ subjectId: "current", status: "LOADING", projection: null });
    const historyRequest = loadSyntheticSuiteCatalog(null, controller.signal);
    const selectedRequest = route.suiteRunRef
      ? loadSyntheticSuiteCatalog(route.suiteRunRef, controller.signal)
      : historyRequest;
    void Promise.all([
      loadSyntheticExperimentCatalog(controller.signal),
      selectedRequest,
      historyRequest,
    ])
      .then(([experimentValue, suiteValue, historyValue]) => {
        if (controller.signal.aborted) return;
        setCatalog(experimentValue);
        setSuiteCatalog(suiteValue);
        setSuiteHistoryCatalog(historyValue);
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setCatalogError(caught instanceof Error ? caught.message : String(caught));
          setLoading(false);
          onContextChange({ subjectId: "current", status: "ERROR", projection: null });
        }
      });
    return () => controller.abort();
  }, [onContextChange, retry, route.suiteRunRef]);

  useEffect(() => {
    if (!catalog || !suiteCatalog) return;
    if (route.suiteRunRef) {
      if (!suiteSelection) {
        setSnapshot(null);
        setCatalogError("mingli_synthetic_suite_run_not_found");
        setLoading(false);
        onContextChange({ subjectId: "current", status: "ERROR", projection: null });
        return;
      }
      const resolution = resolveSyntheticSuiteRoute(suiteSelection, route);
      if (resolution.status === "PATCH") {
        onRouteChange({
          ...route,
          experimentRef: resolution.experimentRef,
          runRef: resolution.runRef,
        }, "replace");
        return;
      }
      if (resolution.status === "ERROR") {
        setSnapshot(null);
        setCatalogError(resolution.error);
        setLoading(false);
        onContextChange({ subjectId: "current", status: "ERROR", projection: null });
        return;
      }
    } else if (!route.experimentRef && !route.runRef) {
      const latest = latestSyntheticSuiteRunSelection(suiteCatalog);
      const first = latest?.review.items.find(
        (item) => item.execution_status === "SEALED" && item.experiment_run_ref,
      );
      if (latest && first?.experiment_run_ref) {
        onRouteChange({
          mode: "synthetic",
          suiteRunRef: latest.run.suite_run_ref,
          experimentRef: first.experiment_ref,
          runRef: first.experiment_run_ref,
          variant: "A",
        }, "replace");
        return;
      }
    }
    const selected = route.experimentRef
      ? catalog.experiments.find(
          (item) => item.experiment_ref === route.experimentRef,
        )
      : catalog.experiments[0];
    if (!selected) {
      setSnapshot(null);
      setSnapshotError(null);
      setCatalogError("mingli_synthetic_experiment_not_found");
      setLoading(false);
      onContextChange({ subjectId: "current", status: "ERROR", projection: null });
      return;
    }
    if (selected.run_status !== "SEALED" || !selected.latest_run_ref) {
      setSnapshot(null);
      setSnapshotError(null);
      setCatalogError(null);
      setLoading(false);
      onContextChange({ subjectId: "current", status: "LOADING", projection: null });
      if (
        route.experimentRef !== selected.experiment_ref
        || route.runRef !== null
      ) {
        onRouteChange({
          mode: "synthetic",
          suiteRunRef: null,
          experimentRef: selected.experiment_ref,
          runRef: null,
          variant: route.variant,
        }, "replace");
      }
      return;
    }
    setCatalogError(null);
    const next = {
      mode: "synthetic" as const,
      suiteRunRef: route.suiteRunRef,
      experimentRef: selected.experiment_ref,
      runRef:
        route.experimentRef === selected.experiment_ref && route.runRef
          ? route.runRef
          : selected.latest_run_ref,
      variant: route.variant,
    };
    if (next.experimentRef !== route.experimentRef || next.runRef !== route.runRef) {
      onRouteChange(next, "replace");
    }
  }, [
    boundSuiteItem,
    catalog,
    onContextChange,
    onRouteChange,
    route,
    suiteCatalog,
    suiteSelection,
  ]);

  useEffect(() => {
    if (
      !catalog
      || !route.experimentRef
      || !route.runRef
      || (route.suiteRunRef && !boundSuiteItem)
    ) return;
    const experimentRef = route.experimentRef;
    const runRef = route.runRef;
    const variant = route.variant;
    const selected = catalog.experiments.find(
      (item) => item.experiment_ref === experimentRef,
    );
    if (!selected || selected.run_status !== "SEALED") return;
    const controller = new AbortController();
    setSnapshot((current) => current
      && current.experiment_ref === experimentRef
      && current.run_ref === runRef
      ? current
      : null);
    setLoading(true);
    setSnapshotError(null);
    onContextChange({
      subjectId: "current",
      status: "LOADING",
      projection: null,
    });
    void loadSyntheticExperimentSnapshot(
      experimentRef,
      runRef,
      variant,
      controller.signal,
    )
      .then((value) => {
        if (controller.signal.aborted) return;
        if (
          boundSuiteItem?.experiment_run_hash
          && value.run_hash !== boundSuiteItem.experiment_run_hash
        ) throw new Error("mingli_synthetic_suite_run_hash_mismatch");
        setSnapshot(value);
        setLoading(false);
        onContextChange({
          subjectId: value.stage.subject_id,
          status: "READY",
          projection: value.stage,
        });
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setSnapshotError({
            experimentRef,
            message: caught instanceof Error ? caught.message : String(caught),
            runRef,
            variant,
          });
          setLoading(false);
          onContextChange({
            subjectId: "current",
            status: "ERROR",
            projection: null,
          });
        }
      });
    return () => controller.abort();
  }, [
    boundSuiteItem,
    catalog,
    onContextChange,
    retry,
    route.experimentRef,
    route.runRef,
    route.suiteRunRef,
    route.variant,
  ]);

  const frame = useMemo(
    () => committedSnapshot
      ? directMingliScene({
          clock: INITIAL_MINGLI_CLOCK,
          narrationOpen: false,
          selectedRelationRef: null,
          stage: committedSnapshot.stage,
          surface: "LAB",
        })
      : null,
    [committedSnapshot],
  );
  const experiment = route.experimentRef
    ? catalog?.experiments.find(
        (item) => item.experiment_ref === route.experimentRef,
      ) ?? null
    : catalog?.experiments[0] ?? null;
  const displayedVariant = committedSnapshot?.selected_variant ?? route.variant;
  const latestRunRef = experiment?.latest_run_ref ?? null;
  const hasSealedRun = experiment?.run_status === "SEALED"
    && Boolean(route.experimentRef && route.runRef)
    && (!route.suiteRunRef || Boolean(boundSuiteItem));

  const retryCurrent = () => {
    setLoading(true);
    setCatalogError(null);
    setSnapshotError(null);
    setRetry((value) => value + 1);
  };

  const restoreLatest = () => {
    if (!experiment || !latestRunRef) return;
    if (
      route.experimentRef === experiment.experiment_ref
      && route.runRef === latestRunRef
    ) {
      retryCurrent();
      return;
    }
    onRouteChange({
      mode: "synthetic",
      suiteRunRef: null,
      experimentRef: experiment.experiment_ref,
      runRef: latestRunRef,
      variant: committedSnapshot?.selected_variant ?? route.variant,
    }, "replace");
  };

  const selectExperiment = (experimentRef: string) => {
    const selected = catalog?.experiments.find(
      (item) => item.experiment_ref === experimentRef,
    );
    if (!selected) return;
    setSnapshot(null);
    setCatalogError(null);
    setSnapshotError(null);
    const suiteItem = suiteSelection?.review.items.find(
      (item) => item.experiment_ref === selected.experiment_ref
        && item.execution_status === "SEALED"
        && item.experiment_run_ref,
    );
    onRouteChange({
      mode: "synthetic",
      suiteRunRef: suiteItem ? suiteSelection?.run.suite_run_ref ?? null : null,
      experimentRef: selected.experiment_ref,
      runRef: suiteItem?.experiment_run_ref ?? selected.latest_run_ref,
      variant: "A",
    });
  };

  const selectRun = (runRef: string) => {
    if (!experiment) return;
    setSnapshot(null);
    setSnapshotError(null);
    onRouteChange({
      ...route,
      suiteRunRef: null,
      experimentRef: experiment.experiment_ref,
      runRef,
    });
  };

  const selectVariant = (variant: "A" | "B") => {
    if (route.variant === variant) {
      if (activeSnapshotError) retryCurrent();
      return;
    }
    onRouteChange({ ...route, variant });
  };

  const selectSuiteItem = (experimentRef: string, runRef: string) => {
    if (!suiteSelection) return;
    setSnapshot(null);
    setSnapshotError(null);
    onRouteChange({
      mode: "synthetic",
      suiteRunRef: suiteSelection.run.suite_run_ref,
      experimentRef,
      runRef,
      variant: "A",
    });
  };

  const selectSuiteRun = (selection: MingliSyntheticSuiteRunSelection) => {
    const nextRoute = firstSyntheticSuiteRoute(selection);
    if (!nextRoute) return;
    setSnapshot(null);
    setCatalogError(null);
    setSnapshotError(null);
    onRouteChange(nextRoute);
  };

  const suiteSummary = suiteSelection && catalog ? (
    <MingliSyntheticSuiteSummary
      comparison={suiteComparison}
      currentExperimentRef={route.experimentRef}
      experiments={catalog}
      onSelect={selectSuiteItem}
      onSelectRun={selectSuiteRun}
      selection={suiteSelection}
    />
  ) : undefined;

  return (
    <div
      className="mingli-scene-host mingli-synthetic-host"
      data-lab-mode="synthetic"
      data-stage-loading={loading}
    >
      <MingliSyntheticSceneHeader
        hasSnapshot={Boolean(committedSnapshot)}
        onBackToCurrent={onBackToCurrent}
        onExit={onExit}
        onOpenReading={onOpenReading}
        title={experiment?.title ?? "正在读取封存实验"}
        variant={committedSnapshot?.selected_variant ?? route.variant}
      />

      <MingliSyntheticExperimentToolbar
        boundSuiteItem={boundSuiteItem}
        catalog={catalog}
        displayedVariant={displayedVariant}
        experiment={experiment}
        hasSealedRun={hasSealedRun}
        onSelectExperiment={selectExperiment}
        onSelectRun={selectRun}
        onSelectVariant={selectVariant}
        selectedRunRef={route.runRef}
        suiteSelection={suiteSelection}
      />

      {committedSnapshot && frame ? (
        <div className="mingli-scene-composition mingli-synthetic-composition" data-overlay="LAB">
          <MingliScenePlayer
            fallbackClock={INITIAL_MINGLI_CLOCK}
            frame={frame}
            stage={committedSnapshot.stage}
          />
          <MingliSyntheticExperimentInspector
            snapshot={committedSnapshot}
            suiteSummary={suiteSummary}
          />
          <MingliSyntheticSwitchingFeedback
            activeError={activeSnapshotError}
            displayedVariant={displayedVariant}
            loading={loading}
            onRestoreLatest={restoreLatest}
            onRetry={retryCurrent}
            requestedVariant={route.variant}
          />
        </div>
      ) : (
        <MingliSyntheticEmptyState
          activeError={activeSnapshotError}
          canRestoreLatest={Boolean(experiment && latestRunRef)}
          catalogError={catalogError}
          loading={loading}
          onRestoreLatest={restoreLatest}
          onRetry={retryCurrent}
          suiteSummary={suiteSummary}
        />
      )}

      <MingliSyntheticStageBoundary
        inferenceLimit={experiment?.inference_limit ?? "只展示离线封存的开发证据。"}
      />
    </div>
  );
}
