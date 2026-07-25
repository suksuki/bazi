import type { DreamGameState } from "./dream_game_api";
import type { DreamVisitView } from "./dream_api";


export type DreamBusinessState =
  | "HOME_AWAKE"
  | "DREAM_AVAILABLE"
  | "DREAM_PORTAL_READY"
  | "ENTERING_DREAM"
  | "THREE_TREE_SELECTION"
  | "ENCOUNTER_COMMITTED"
  | "FIXED_TREE_EXPLORATION"
  | "FOUNDATION_COMPLETE"
  | "BLIND_ROUND_OPEN"
  | "JUDGMENT_SUBMITTED"
  | "DOUBLE_SEALED"
  | "REVEALABLE"
  | "REVEAL_COMPLETE"
  | "RETURNED_WITH_SEED";

export type DreamPresentationState =
  | "HOME_TREE_QUIET"
  | "HOME_TREE_CALLING"
  | "ABU_CURLING_TO_SLEEP"
  | "ABU_SLEEP_BREATH"
  | "FOG_GATE_OPENING"
  | "GHOST_ORBIT_SETTLING"
  | "GHOST_ORBIT_FOCUSED"
  | "TREE_COMMIT_DISSOLVE"
  | "ABU_TREE_LEAP"
  | "FIXED_TREE_IDLE"
  | "QUESTION_NODE_ACTIVE"
  | "FLOWER_OPENING"
  | "FRUIT_FORMING"
  | "REVEAL_ACT_ACTIVE"
  | "RETURN_MIST"
  | "SEED_LANDING"
  | "FAIL_CLOSED";

export type DreamStoryCommand =
  | "OpenDream"
  | "ResumeDream"
  | "FocusCandidate"
  | "CommitCandidate"
  | "OpenQuestionNode"
  | "SubmitFoundationAnswer"
  | "AcknowledgeLearning"
  | "OpenBlindRound"
  | "SubmitJudgment"
  | "RequestReveal"
  | "CompleteReveal"
  | "ReturnHome";

export type DreamAssetIntent =
  | "home_tree"
  | "abu_curl_to_sleep"
  | "abu_sleep_breath"
  | "fog_gate"
  | "ghost_orbit"
  | "abu_tree_leap"
  | "fixed_tree"
  | "question_leaf"
  | "question_branch"
  | "question_bud"
  | "fruit_form"
  | "knowledge_seed"
  | "return_mist";

export type DreamAudioCue =
  | "none"
  | "opening_theme"
  | "sleep_breath"
  | "leaf_whisper"
  | "root_light"
  | "mist_open"
  | "mist_close"
  | "branch_wake"
  | "flower_open"
  | "fruit_form"
  | "seed_land";

export interface DreamStorySnapshot {
  businessState: DreamBusinessState;
  presentationState: DreamPresentationState;
  focusedCandidateIndex: number;
  committedRoundId: string;
  foundationComplete: boolean;
  revealAct: "user" | "system" | "evidence" | "seed";
  revision: number;
  lastEvent: DreamStoryEvent["type"];
}

export type DreamStoryEvent =
  | { type: "SYNC_SERVER"; context: DreamStoryServerContext }
  | { type: "DREAM_BECAME_AVAILABLE" }
  | { type: "OPEN_DREAM_REQUESTED" }
  | { type: "PORTAL_READY" }
  | { type: "FOG_GATE_COMPLETED" }
  | { type: "FOCUS_CANDIDATE"; index: number; candidateCount: number }
  | { type: "COMMIT_CANDIDATE"; roundId: string }
  | { type: "TREE_ENTRY_COMPLETED" }
  | { type: "FOUNDATION_PROGRESS"; complete: boolean }
  | { type: "QUESTION_NODE_OPENED" }
  | { type: "FLOWER_OPENED" }
  | { type: "JUDGMENT_SEALED" }
  | { type: "DOUBLE_SEAL_CONFIRMED" }
  | { type: "REVEAL_STARTED" }
  | { type: "REVEAL_ACT_CHANGED"; act: DreamStorySnapshot["revealAct"] }
  | { type: "REVEAL_COMPLETED" }
  | { type: "RETURN_STARTED" }
  | { type: "RETURNED_WITH_SEED" }
  | { type: "FAIL_CLOSED" };

export interface DreamStoryServerContext {
  dreamAvailable: boolean;
  resumable: boolean;
  visit: DreamVisitView | null;
  gameState: DreamGameState | "";
  hasAttempt: boolean;
  hasResult: boolean;
  foundationComplete: boolean;
  returnedWithSeed: boolean;
}

export interface DreamSceneContract {
  sceneId: string;
  businessState: DreamBusinessState;
  presentationState: DreamPresentationState;
  entryIntent: string;
  idleIntent: string;
  exitIntent: string;
  allowedCommands: DreamStoryCommand[];
  audioCues: DreamAudioCue[];
  subtitleCues: string[];
  assetDependencies: DreamAssetIntent[];
  reducedMotionFallback: string;
  resumePolicy: string;
  errorPolicy: "FAIL_CLOSED" | "RETURN_TO_SAFE_SCENE";
  telemetry: string[];
}
