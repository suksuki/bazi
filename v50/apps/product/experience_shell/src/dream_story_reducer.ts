import type {
  DreamBusinessState,
  DreamPresentationState,
  DreamStoryEvent,
  DreamStoryServerContext,
  DreamStorySnapshot,
} from "./dream_story_contracts";


export function initialDreamStorySnapshot(): DreamStorySnapshot {
  return {
    businessState: "HOME_AWAKE",
    presentationState: "HOME_TREE_QUIET",
    focusedCandidateIndex: 0,
    committedRoundId: "",
    foundationComplete: false,
    revealAct: "user",
    revision: 0,
    lastEvent: "SYNC_SERVER",
  };
}


export function reduceDreamStory(
  current: DreamStorySnapshot,
  event: DreamStoryEvent,
): DreamStorySnapshot {
  const next = { ...current, revision: current.revision + 1, lastEvent: event.type };
  if (event.type === "SYNC_SERVER") return syncServer(next, event.context);
  if (event.type === "DREAM_BECAME_AVAILABLE") {
    return withState(next, "DREAM_AVAILABLE", "HOME_TREE_CALLING");
  }
  if (event.type === "OPEN_DREAM_REQUESTED") {
    return withState(next, "DREAM_PORTAL_READY", "ABU_CURLING_TO_SLEEP");
  }
  if (event.type === "PORTAL_READY") {
    return withState(next, "DREAM_PORTAL_READY", "ABU_SLEEP_BREATH");
  }
  if (event.type === "FOG_GATE_COMPLETED") {
    return withState(next, "THREE_TREE_SELECTION", "GHOST_ORBIT_SETTLING");
  }
  if (event.type === "FOCUS_CANDIDATE") {
    const count = Math.max(1, event.candidateCount);
    return {
      ...withState(next, "THREE_TREE_SELECTION", "GHOST_ORBIT_FOCUSED"),
      focusedCandidateIndex: ((event.index % count) + count) % count,
    };
  }
  if (event.type === "COMMIT_CANDIDATE") {
    return {
      ...withState(next, "ENCOUNTER_COMMITTED", "TREE_COMMIT_DISSOLVE"),
      committedRoundId: event.roundId,
    };
  }
  if (event.type === "TREE_ENTRY_COMPLETED") {
    return withState(next, "FIXED_TREE_EXPLORATION", "FIXED_TREE_IDLE");
  }
  if (event.type === "FOUNDATION_PROGRESS") {
    return {
      ...withState(
        next,
        event.complete ? "FOUNDATION_COMPLETE" : "FIXED_TREE_EXPLORATION",
        event.complete ? "FIXED_TREE_IDLE" : "QUESTION_NODE_ACTIVE",
      ),
      foundationComplete: event.complete,
    };
  }
  if (event.type === "QUESTION_NODE_OPENED") {
    return withState(next, next.businessState, "QUESTION_NODE_ACTIVE");
  }
  if (event.type === "FLOWER_OPENED") {
    return withState(next, "BLIND_ROUND_OPEN", "FLOWER_OPENING");
  }
  if (event.type === "JUDGMENT_SEALED") {
    return withState(next, "JUDGMENT_SUBMITTED", "FIXED_TREE_IDLE");
  }
  if (event.type === "DOUBLE_SEAL_CONFIRMED") {
    return withState(next, "DOUBLE_SEALED", "FRUIT_FORMING");
  }
  if (event.type === "REVEAL_STARTED") {
    return withState(next, "REVEALABLE", "REVEAL_ACT_ACTIVE");
  }
  if (event.type === "REVEAL_ACT_CHANGED") {
    return {
      ...withState(next, "REVEALABLE", "REVEAL_ACT_ACTIVE"),
      revealAct: event.act,
    };
  }
  if (event.type === "REVEAL_COMPLETED") {
    return withState(next, "REVEAL_COMPLETE", "REVEAL_ACT_ACTIVE");
  }
  if (event.type === "RETURN_STARTED") {
    return withState(next, next.businessState, "RETURN_MIST");
  }
  if (event.type === "RETURNED_WITH_SEED") {
    return withState(next, "RETURNED_WITH_SEED", "SEED_LANDING");
  }
  return withState(next, next.businessState, "FAIL_CLOSED");
}


function syncServer(
  current: DreamStorySnapshot,
  context: DreamStoryServerContext,
): DreamStorySnapshot {
  if (context.returnedWithSeed) {
    return withState(current, "RETURNED_WITH_SEED", "SEED_LANDING");
  }
  if (!context.visit) {
    return context.dreamAvailable
      ? withState(current, context.resumable ? "DREAM_PORTAL_READY" : "DREAM_AVAILABLE", "HOME_TREE_CALLING")
      : withState(current, "HOME_AWAKE", "HOME_TREE_QUIET");
  }
  if (context.visit.state === "COMPLETED") {
    return withState(current, "HOME_AWAKE", "HOME_TREE_QUIET");
  }
  if (["HOME_GROVE", "PATH_OFFERED"].includes(context.visit.state)) {
    return withState(current, "DREAM_PORTAL_READY", "ABU_SLEEP_BREATH");
  }
  if (context.visit.state === "DREAM_ENTERING") {
    return withState(current, "ENTERING_DREAM", "FOG_GATE_OPENING");
  }
  if (!context.hasAttempt) {
    return withState(current, "THREE_TREE_SELECTION", "GHOST_ORBIT_FOCUSED");
  }
  if (context.hasResult) {
    return {
      ...withState(current, "REVEAL_COMPLETE", "REVEAL_ACT_ACTIVE"),
      foundationComplete: true,
    };
  }
  if (context.gameState === "OUTCOME_REVEALABLE") {
    return {
      ...withState(current, "DOUBLE_SEALED", "FRUIT_FORMING"),
      foundationComplete: true,
    };
  }
  if (context.gameState === "JUDGMENT_DRAFTING") {
    return {
      ...withState(current, "BLIND_ROUND_OPEN", "QUESTION_NODE_ACTIVE"),
      foundationComplete: context.foundationComplete,
    };
  }
  if (["QUESTION_FLOWER_OPEN", "OPTIONAL_DIVINATION"].includes(context.gameState)) {
    return {
      ...withState(current, "BLIND_ROUND_OPEN", "FIXED_TREE_IDLE"),
      foundationComplete: true,
    };
  }
  return {
    ...withState(
      current,
      context.foundationComplete ? "FOUNDATION_COMPLETE" : "FIXED_TREE_EXPLORATION",
      "FIXED_TREE_IDLE",
    ),
    foundationComplete: context.foundationComplete,
  };
}


function withState(
  snapshot: DreamStorySnapshot,
  businessState: DreamBusinessState,
  presentationState: DreamPresentationState,
): DreamStorySnapshot {
  return { ...snapshot, businessState, presentationState };
}
