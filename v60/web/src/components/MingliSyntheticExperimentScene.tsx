import { useEffect, useMemo, useState } from "react";
import {
  directMingliScene,
  INITIAL_MINGLI_CLOCK,
} from "../mingliSceneDirector";
import {
  loadSyntheticExperimentCatalog,
  loadSyntheticExperimentSnapshot,
} from "../mingliSyntheticLabApi";
import type { MingliSyntheticLabRoute } from "../mingliSyntheticLabNavigation";
import type {
  MingliSyntheticExperimentCatalog,
  MingliSyntheticExperimentSnapshot,
} from "../mingliSyntheticLabTypes";
import type { MingliStageViewContext } from "../mingliStageTypes";
import { MingliScenePlayer } from "./MingliScenePlayer";
import { MingliSyntheticExperimentInspector } from "./MingliSyntheticExperimentInspector";

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
    onContextChange({ subjectId: "current", status: "LOADING", projection: null });
    void loadSyntheticExperimentCatalog(controller.signal)
      .then((value) => {
        if (controller.signal.aborted) return;
        setCatalog(value);
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setCatalogError(caught instanceof Error ? caught.message : String(caught));
          setLoading(false);
          onContextChange({ subjectId: "current", status: "ERROR", projection: null });
        }
      });
    return () => controller.abort();
  }, [onContextChange, retry]);

  useEffect(() => {
    if (!catalog) return;
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
  }, [catalog, onContextChange, onRouteChange, route]);

  useEffect(() => {
    if (!catalog || !route.experimentRef || !route.runRef) return;
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
  }, [catalog, onContextChange, retry, route.experimentRef, route.runRef, route.variant]);

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
    && Boolean(route.experimentRef && route.runRef);

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
      experimentRef: experiment.experiment_ref,
      runRef: latestRunRef,
      variant: committedSnapshot?.selected_variant ?? route.variant,
    }, "replace");
  };

  return (
    <div
      className="mingli-scene-host mingli-synthetic-host"
      data-lab-mode="synthetic"
      data-stage-loading={loading}
    >
      <header className="mingli-scene-host-header">
        <button className="mingli-scene-exit" onClick={onExit} type="button">
          <span aria-hidden="true">←</span>
          回到生命树
        </button>
        <div className="mingli-scene-title">
          <p>阿布 Lab · 合成验证</p>
          <h1>{experiment?.title ?? "正在读取封存实验"}</h1>
          <span>{committedSnapshot ? `${committedSnapshot.selected_variant} 组 · 研究合成命盘` : "离线运行 · 浏览器只读"}</span>
        </div>
        <div className="mingli-scene-surfaces" role="group" aria-label="命理阅读与 Lab">
          <button aria-pressed="false" onClick={onOpenReading} type="button">命理阅读</button>
          <button aria-pressed="false" onClick={onBackToCurrent} type="button">当前命盘</button>
          <button aria-pressed="true" type="button">合成验证</button>
        </div>
      </header>

      <div className="mingli-scene-toolbar" aria-label="选择合成命盘实验成员">
        <label className="mingli-synthetic-selector">
          <small>研究课题</small>
          <select
            aria-label="选择合成实验"
            disabled={!catalog}
            onChange={(event) => {
              const selected = catalog?.experiments.find(
                (item) => item.experiment_ref === event.target.value,
              );
              if (!selected) return;
              setSnapshot(null);
              setCatalogError(null);
              setSnapshotError(null);
              onRouteChange({
                mode: "synthetic",
                experimentRef: selected.experiment_ref,
                runRef: selected.latest_run_ref,
                variant: "A",
              });
            }}
            value={experiment?.experiment_ref ?? ""}
          >
            {!experiment && <option value="">未识别的研究课题</option>}
            {catalog?.experiments.map((item, index) => (
              <option key={item.experiment_ref} value={item.experiment_ref}>
                {index + 1} · {item.title}
              </option>
            ))}
          </select>
        </label>
        <label className="mingli-synthetic-selector mingli-synthetic-run-selector">
          <small>封存复盘</small>
          <select
            aria-label="选择封存运行"
            disabled={!experiment || experiment.runs.length === 0}
            onChange={(event) => {
              if (!experiment) return;
              setSnapshot(null);
              setSnapshotError(null);
              onRouteChange({
                ...route,
                experimentRef: experiment.experiment_ref,
                runRef: event.target.value,
              });
            }}
            value={route.runRef ?? ""}
          >
            {experiment?.runs.length ? experiment.runs.map((run) => (
              <option key={run.run_ref} value={run.run_ref}>
                {formatRunLabel(
                  run.created_at,
                  run.model_independence,
                  run.review_contract_status,
                )}
              </option>
            )) : <option value="">尚未生成</option>}
          </select>
        </label>
        <div className="mingli-stage-mode" role="group" aria-label="选择 A 或 B 命盘">
          {(["A", "B"] as const).map((variant) => (
            <button
              aria-pressed={displayedVariant === variant}
              disabled={!hasSealedRun}
              key={variant}
              onClick={() => {
                if (route.variant === variant) {
                  if (activeSnapshotError) retryCurrent();
                  return;
                }
                onRouteChange({ ...route, variant });
              }}
              type="button"
            >
              {variant} · {experiment?.changed_input[variant] ?? "--:--"}
            </button>
          ))}
        </div>
        <span className="mingli-synthetic-read-only">只读结果 · 页面不会调用模型</span>
      </div>

      {committedSnapshot && frame ? (
        <div className="mingli-scene-composition mingli-synthetic-composition" data-overlay="LAB">
          <MingliScenePlayer
            fallbackClock={INITIAL_MINGLI_CLOCK}
            frame={frame}
            stage={committedSnapshot.stage}
          />
          <MingliSyntheticExperimentInspector snapshot={committedSnapshot} />
          {loading && (
            <div className="mingli-synthetic-switching" role="status">
              正在读取 {route.variant} 组；当前仍显示 {displayedVariant} 组
            </div>
          )}
          {activeSnapshotError && (
            <div className="mingli-synthetic-load-error" role="alert">
              <strong>{route.variant} 组读取失败，当前仍显示 {displayedVariant} 组。</strong>
              <span>没有补跑模型，也没有把旧舞台冒充成新变体。</span>
              <div>
                <button onClick={retryCurrent} type="button">重试 {route.variant} 组</button>
                <button onClick={restoreLatest} type="button">改读最新封存结果</button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="mingli-synthetic-empty" role="status">
          {loading ? (
            <p>正在读取离线封存的 A／B 实验……</p>
          ) : catalogError || activeSnapshotError ? (
            <>
              <p>
                {activeSnapshotError
                  ? "当前链接的封存结果不可用；不会拿别的命盘顶替。"
                  : "封存实验暂时无法读取；不会在浏览器补跑模型。"}
              </p>
              <div>
                <button onClick={retryCurrent} type="button">重新读取</button>
                {activeSnapshotError && experiment && latestRunRef && (
                  <button onClick={restoreLatest} type="button">
                    改读最新封存结果
                  </button>
                )}
              </div>
            </>
          ) : (
            <p>尚无封存实验结果，请通过离线 Lab runner 生成。</p>
          )}
        </div>
      )}

      <footer className="mingli-stage-boundary">
        <span>Owner 命盘只做回归；合成命盘负责控制变量、发现漂移和推动方法升级。</span>
        <small>{experiment?.inference_limit ?? "只展示离线封存的开发证据。"}</small>
      </footer>
    </div>
  );
}

function formatRunLabel(
  createdAt: string,
  model: "PASS" | "FAIL" | "NOT_EVALUABLE",
  contract: "CURRENT" | "SUPERSEDED",
): string {
  const date = createdAt.replace("T", " ").slice(0, 16);
  const status = model === "PASS"
    ? "模型独立"
    : model === "FAIL"
      ? "仍需校正"
      : "实验不可评价";
  return `${date} · ${status} · ${contract === "CURRENT" ? "当前口径" : "旧口径"}`;
}
