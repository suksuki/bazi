import { useEffect, useRef, useState } from "react";

import type { RuntimeMediaManifest } from "../publicRuntimeTypes";
import {
  generateMingliFocusedPass,
  loadMingliReadingSummary,
  loadMingliStage,
} from "../mingliStageApi";
import {
  clearMingliLeafEntry,
  readMingliLeafEntry,
  readMingliStageRoute,
  type MingliReadingLayer,
  type MingliStageEntryMode,
  writeMingliStageExperience,
  writeMingliStageRoute,
} from "../mingliStageNavigation";
import {
  hasMingliSummaryLayerNarration,
  mingliLayerFocuses,
} from "../mingliLayerNarrationProjection";
import type {
  MingliFocus,
  MingliReadingSummaryProjection,
  MingliStageProjection,
  MingliStageViewContext,
} from "../mingliStageTypes";
import { resolveHomeWorldLight } from "../homeWorldLight";
import { MingliBranchJourney } from "./MingliBranchJourney";
import { summaryMatchesStage } from "./MingliReadingJourney";

export function MingliBranchSceneHost({
  media,
  onContextChange,
  onExit,
  onOpenStage,
  publicMode = false,
}: {
  media: RuntimeMediaManifest;
  onContextChange: (context: MingliStageViewContext) => void;
  onExit: () => void;
  onOpenStage: (entryMode: MingliStageEntryMode) => void;
  publicMode?: boolean;
}) {
  const [route, setRoute] = useState(readMingliStageRoute);
  const [entry] = useState(readMingliLeafEntry);
  const [stage, setStage] = useState<MingliStageProjection | null>(null);
  const stageRef = useRef<MingliStageProjection | null>(null);
  const generationRequestRef = useRef(0);
  const generationControllerRef = useRef<AbortController | null>(null);
  const [summary, setSummary] = useState<MingliReadingSummaryProjection | null>(null);
  const [agentGenerating, setAgentGenerating] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const light = entry?.light ?? (
    new URL(window.location.href).searchParams.get("mingli_light") === "night"
      ? "night"
      : resolveHomeWorldLight()
  );

  useEffect(() => {
    const controller = new AbortController();
    generationRequestRef.current += 1;
    generationControllerRef.current?.abort();
    generationControllerRef.current = null;
    stageRef.current = null;
    const requestedYear = route.mode === "NATAL_DAYUN_YEAR_6" ? route.year : null;
    setStage(null);
    setSummary(null);
    setAgentGenerating(false);
    setAgentError(null);
    setError(null);
    onContextChange({ subjectId: route.subjectId, status: "LOADING", projection: null });
    void loadMingliStage(route.subjectId, route.mode, requestedYear, controller.signal)
      .then(async (projection) => ({
        projection,
        summary:
          projection.reading_ref === null
            ? null
            : await loadMingliReadingSummary(projection, controller.signal),
      }))
      .then(({ projection, summary: nextSummary }) => {
        if (controller.signal.aborted) return;
        stageRef.current = projection;
        setStage(projection);
        setSummary(nextSummary);
        onContextChange({
          subjectId: projection.subject_id,
          status: "READY",
          projection,
        });
      })
      .catch((cause) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof Error ? cause.message : String(cause));
        onContextChange({ subjectId: route.subjectId, status: "ERROR", projection: null });
      });
    return () => controller.abort();
  }, [onContextChange, retry, route.mode, route.subjectId, route.year]);

  useEffect(() => () => {
    generationRequestRef.current += 1;
    generationControllerRef.current?.abort();
  }, []);

  const selectLayer = (layer: MingliReadingLayer) => {
    const next = { ...route, layer };
    setRoute(next);
    writeMingliStageRoute(next, "replace", "mingli");
  };
  const openLayerRehearsal = (layer: MingliReadingLayer) => {
    const current = readMingliStageRoute();
    const next = {
      ...current,
      layer,
      mode: publicMode || layer === "timing"
        ? "NATAL_DAYUN_YEAR_6" as const
        : "NATAL_4" as const,
      year: null,
    };
    writeMingliStageRoute(next, "replace", "mingli");
    writeMingliStageExperience("stage", "rehearsal", "push");
    onOpenStage("rehearsal");
  };
  const activateLayer = (layer: MingliReadingLayer) => {
    selectLayer(layer);
    if (stage === null || agentGenerating || generationControllerRef.current) return;
    const currentSummary = summaryMatchesStage(summary, stage) ? summary : null;
    if (
      currentSummary !== null
      && hasMingliSummaryLayerNarration(currentSummary, layer)
    ) {
      setAgentError(null);
      openLayerRehearsal(layer);
      return;
    }
    if (
      currentSummary === null
      || !currentSummary.focused_generation_available
      || stage.reading_ref === null
    ) {
      setAgentError("这一层还没有形成可直接讲述的初断。");
      return;
    }
    const requestedStage = stage;
    const requestId = generationRequestRef.current + 1;
    generationRequestRef.current = requestId;
    const controller = new AbortController();
    generationControllerRef.current = controller;
    setAgentGenerating(true);
    setAgentError(null);
    const existingFocuses = new Set<MingliFocus>([
      ...(currentSummary.focused_reading?.passes.map((item) => item.focus) ?? []),
      ...currentSummary.focused_pass_records.map((record) => record.focus),
    ]);
    const requiredFocuses: MingliFocus[] = [
      ...(layer !== "principle" && !existingFocuses.has("STRUCTURE")
        ? ["STRUCTURE" as const]
        : []),
      ...mingliLayerFocuses(layer),
    ];
    const missingFocuses = requiredFocuses.filter(
      (focus, index) =>
        !existingFocuses.has(focus)
        && requiredFocuses.indexOf(focus) === index,
    );
    void missingFocuses
      .reduce<Promise<void>>(
        (pending, focus) => pending.then(async () => {
          await generateMingliFocusedPass(requestedStage, focus, controller.signal);
        }),
        Promise.resolve(),
      )
      .then(() => loadMingliReadingSummary(requestedStage, controller.signal))
      .then((nextSummary) => {
        const activeStage = stageRef.current;
        if (
          !controller.signal.aborted
          && generationRequestRef.current === requestId
          && activeStage !== null
          && summaryMatchesStage(nextSummary, activeStage)
        ) {
          setSummary(nextSummary);
          if (hasMingliSummaryLayerNarration(nextSummary, layer)) {
            openLayerRehearsal(layer);
          } else {
            setAgentError("这一层还没有形成可直接讲述的初断。");
          }
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted && generationRequestRef.current === requestId) {
          setAgentError(cause instanceof Error ? cause.message : String(cause));
        }
      })
      .finally(() => {
        if (generationRequestRef.current === requestId) {
          setAgentGenerating(false);
          generationControllerRef.current = null;
        }
      });
  };

  if (error) {
    return (
      <div className="mingli-growth-load-state is-error" role="alert">
        <strong>这片命理枝暂时没有长出来</strong>
        <p>档案与命盘没有完整对应，请重新读取；原有档案不会受到影响。</p>
        <button onClick={() => setRetry((value) => value + 1)} type="button">重新读取</button>
        <button onClick={onExit} type="button">回到生命树</button>
      </div>
    );
  }
  if (!stage) {
    return (
      <div className="mingli-growth-load-state" role="status">
        <i aria-hidden="true" />
        <strong>正在读这片档案叶</strong>
        <p>命盘确认后，属于这份档案的命理枝就会从这里长出来。</p>
      </div>
    );
  }
  return (
    <MingliBranchJourney
      agentError={agentError}
      agentGenerating={agentGenerating}
      entry={entry}
      layer={route.layer}
      light={light}
      media={media}
      onClose={onExit}
      onEntryConsumed={clearMingliLeafEntry}
      onActivateLayer={activateLayer}
      stage={stage}
    />
  );
}
