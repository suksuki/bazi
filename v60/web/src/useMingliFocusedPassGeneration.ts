import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  generateMingliFocusedPass,
  loadMingliReadingSummary,
} from "./mingliStageApi";
import type { MingliReadingLayer } from "./mingliStageNavigation";
import {
  mingliLayerFocuses,
  type MingliLayerNarrationProjection,
} from "./mingliLayerNarrationProjection";
import type {
  MingliFocus,
  MingliFocusedPassRecord,
  MingliReadingSummaryProjection,
  MingliStageProjection,
} from "./mingliStageTypes";
import { summaryMatchesStage } from "./components/MingliReadingJourney";

export function useMingliFocusedPassGeneration({
  onSummary,
  stage,
}: {
  onSummary: (summary: MingliReadingSummaryProjection) => void;
  stage: MingliStageProjection | null;
}) {
  const requestRef = useRef(0);
  const controllerRef = useRef<AbortController | null>(null);
  const activeStageRef = useRef(stage);
  const [agentGenerating, setAgentGenerating] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);
  activeStageRef.current = stage;

  const resetAgentGeneration = useCallback(() => {
    requestRef.current += 1;
    controllerRef.current?.abort();
    controllerRef.current = null;
    setAgentGenerating(false);
    setAgentError(null);
  }, []);

  useEffect(() => () => {
    requestRef.current += 1;
    controllerRef.current?.abort();
  }, []);

  const generateAgentReading = useCallback((focus: MingliFocus) => {
    if (stage === null || controllerRef.current !== null) return;
    const requestedStage = stage;
    const requestId = requestRef.current + 1;
    const controller = new AbortController();
    requestRef.current = requestId;
    controllerRef.current = controller;
    setAgentGenerating(true);
    setAgentError(null);
    void generateMingliFocusedPass(requestedStage, focus, controller.signal)
      .then(() => loadMingliReadingSummary(requestedStage, controller.signal))
      .then((summary) => {
        const activeStage = activeStageRef.current;
        if (
          !controller.signal.aborted
          && requestRef.current === requestId
          && activeStage !== null
          && summaryMatchesStage(summary, activeStage)
        ) onSummary(summary);
      })
      .catch((caught) => {
        if (!controller.signal.aborted && requestRef.current === requestId) {
          setAgentError(caught instanceof Error ? caught.message : String(caught));
        }
      })
      .finally(() => {
        if (requestRef.current === requestId) {
          setAgentGenerating(false);
          controllerRef.current = null;
        }
      });
  }, [onSummary, stage]);

  return {
    agentError,
    agentGenerating,
    generateAgentReading,
    resetAgentGeneration,
  };
}

export function usePublicMingliAutoGeneration({
  agentGenerating,
  currentSummary,
  generateAgentReading,
  layer,
  publicMode,
  rehearsalOpen,
  stage,
}: {
  agentGenerating: boolean;
  currentSummary: MingliReadingSummaryProjection | null;
  generateAgentReading: (focus: MingliFocus) => void;
  layer: MingliReadingLayer;
  publicMode: boolean;
  rehearsalOpen: boolean;
  stage: MingliStageProjection | null;
}) {
  const attemptedRef = useRef(new Set<string>());
  const missingFocus = useMemo(() => {
    if (!publicMode || currentSummary === null) return null;
    const existing = new Set<MingliFocus>([
      ...(currentSummary.focused_reading?.passes.map((item) => item.focus) ?? []),
      ...currentSummary.focused_pass_records.map((record) => record.focus),
    ]);
    const required: MingliFocus[] = [
      ...(layer !== "principle" && !existing.has("STRUCTURE")
        ? ["STRUCTURE" as const]
        : []),
      ...mingliLayerFocuses(layer),
    ];
    return required.find((focus) => !existing.has(focus)) ?? null;
  }, [currentSummary, layer, publicMode]);

  useEffect(() => {
    if (
      !publicMode
      || !rehearsalOpen
      || missingFocus === null
      || stage === null
      || agentGenerating
    ) return;
    const key = `${stage.projection_hash}:${missingFocus}`;
    if (attemptedRef.current.has(key)) return;
    attemptedRef.current.add(key);
    generateAgentReading(missingFocus);
  }, [
    agentGenerating,
    generateAgentReading,
    missingFocus,
    publicMode,
    rehearsalOpen,
    stage,
  ]);
}

export function selectMingliRehearsalSpeechRecords(
  summary: MingliReadingSummaryProjection | null,
  narration: MingliLayerNarrationProjection | null,
): MingliFocusedPassRecord[] {
  if (summary === null || narration === null) return [];
  const passRefs = new Set(
    narration.chapters.map((chapter) => chapter.sourceItemRef),
  );
  return summary.focused_pass_records.filter((record) =>
    passRefs.has(record.pass_result.pass_ref),
  );
}
