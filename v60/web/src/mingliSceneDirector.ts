import type {
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "./mingliStageTypes";

export type MingliSceneSurface = "READING" | "LAB";

export type MingliSceneFocus =
  | "ALL_PILLARS"
  | "RELATION_MEMBERS"
  | "EVIDENCE_BOUNDARY"
  | "TIME_LAYER"
  | "LAB_SELECTION";

export interface MingliSceneFrame {
  projectionRef: string;
  projectionHash: string;
  surface: MingliSceneSurface;
  focus: MingliSceneFocus;
  phase: MingliNarrationVisualClock["phase"] | "LAB_OBSERVE" | "IDLE";
  currentTimeMs: number;
  cueProgress: number;
  activeColumnRefs: string[];
  selectedRelationRef: string | null;
  semanticRunning: boolean;
  ambientRunning: boolean;
}

export const INITIAL_MINGLI_CLOCK: MingliNarrationVisualClock = {
  phase: null,
  currentTimeMs: 0,
  activeCueId: null,
  cueProgress: 0,
  semanticAction: null,
  activeColumnRefs: [],
};

export function directMingliScene({
  clock,
  narrationOpen,
  selectedRelationRef,
  stage,
  surface,
}: {
  clock: MingliNarrationVisualClock;
  narrationOpen: boolean;
  selectedRelationRef: string | null;
  stage: MingliStageProjection;
  surface: MingliSceneSurface;
}): MingliSceneFrame {
  if (!narrationOpen) {
    return {
      projectionRef: stage.projection_ref,
      projectionHash: stage.projection_hash,
      surface,
      focus: surface === "LAB" && selectedRelationRef ? "LAB_SELECTION" : "ALL_PILLARS",
      phase: surface === "LAB" ? "LAB_OBSERVE" : "IDLE",
      currentTimeMs: 0,
      cueProgress: surface === "LAB" && selectedRelationRef ? 1 : 0,
      activeColumnRefs: [],
      selectedRelationRef,
      semanticRunning: false,
      ambientRunning: true,
    };
  }

  const focus: MingliSceneFocus =
    clock.semanticAction === "RELATIONS_PRESENT"
      ? "RELATION_MEMBERS"
      : clock.semanticAction === "BOUNDARY_HOLD"
        ? "EVIDENCE_BOUNDARY"
        : clock.semanticAction === "TIME_COORDINATES_PRESENT"
          ? "TIME_LAYER"
          : "ALL_PILLARS";
  const frozen = clock.phase === "PAUSED" || clock.phase === "BUFFERING";
  return {
    projectionRef: stage.projection_ref,
    projectionHash: stage.projection_hash,
    surface,
    focus,
    phase: clock.phase ?? "IDLE",
    currentTimeMs: clock.currentTimeMs,
    cueProgress: clock.cueProgress,
    activeColumnRefs: clock.activeColumnRefs ?? [],
    selectedRelationRef:
      focus === "RELATION_MEMBERS" || focus === "EVIDENCE_BOUNDARY"
        ? selectedRelationRef
        : null,
    semanticRunning: clock.phase === "PLAYING",
    ambientRunning: !frozen && clock.phase !== "PREPARING" && clock.phase !== "FAILED",
  };
}

export function relationRefsForFrame(
  stage: MingliStageProjection,
  frame: MingliSceneFrame,
): Set<string> {
  if (frame.focus === "LAB_SELECTION" && frame.selectedRelationRef) {
    return new Set([frame.selectedRelationRef]);
  }
  if (
    frame.focus === "RELATION_MEMBERS" ||
    frame.focus === "EVIDENCE_BOUNDARY"
  ) {
    return new Set(stage.relations.map((relation) => relation.relation_ref));
  }
  return new Set();
}
