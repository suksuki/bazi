import { useEffect, useState } from "react";

import type { RuntimeMediaManifest } from "../api";
import {
  generateMingliAgentReading,
  loadMingliReadingSummary,
  loadMingliStage,
} from "../mingliStageApi";
import {
  clearMingliLeafEntry,
  readMingliLeafEntry,
  readMingliStageRoute,
  type MingliReadingLayer,
  writeMingliStageRoute,
} from "../mingliStageNavigation";
import type {
  MingliReadingSummaryProjection,
  MingliStageProjection,
  MingliStageViewContext,
} from "../mingliStageTypes";
import { resolveHomeWorldLight } from "../homeWorldLight";
import { MingliBranchJourney } from "./MingliBranchJourney";

export function MingliBranchSceneHost({
  media,
  onContextChange,
  onExit,
  onOpenStage,
}: {
  media: RuntimeMediaManifest;
  onContextChange: (context: MingliStageViewContext) => void;
  onExit: () => void;
  onOpenStage: () => void;
}) {
  const [route, setRoute] = useState(readMingliStageRoute);
  const [entry] = useState(readMingliLeafEntry);
  const [stage, setStage] = useState<MingliStageProjection | null>(null);
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

  const selectLayer = (layer: MingliReadingLayer) => {
    const next = { ...route, layer };
    setRoute(next);
    writeMingliStageRoute(next, "replace", "mingli");
  };
  const openStage = (expandTime: boolean) => {
    const next = expandTime
      ? { ...route, mode: "NATAL_DAYUN_YEAR_6" as const, year: null }
      : route;
    writeMingliStageRoute(next, "replace", "lab");
    onOpenStage();
  };
  const generateAgentReading = () => {
    if (stage === null || agentGenerating) return;
    setAgentGenerating(true);
    setAgentError(null);
    void generateMingliAgentReading(stage)
      .then(() => loadMingliReadingSummary(stage))
      .then((nextSummary) => setSummary(nextSummary))
      .catch((cause) => {
        setAgentError(cause instanceof Error ? cause.message : String(cause));
      })
      .finally(() => setAgentGenerating(false));
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
      onLayerChange={selectLayer}
      onGenerateAgent={generateAgentReading}
      onOpenStage={openStage}
      stage={stage}
      summary={summary}
    />
  );
}
