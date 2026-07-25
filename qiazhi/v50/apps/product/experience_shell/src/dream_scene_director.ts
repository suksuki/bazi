import type {
  DreamBusinessState,
  DreamSceneContract,
  DreamStorySnapshot,
} from "./dream_story_contracts";


const STORY_SCENES: Record<DreamBusinessState, DreamSceneContract> = {
  HOME_AWAKE: scene("home-awake", "HOME_AWAKE", "HOME_TREE_QUIET", [], ["home_tree"]),
  DREAM_AVAILABLE: scene(
    "home-tree-call",
    "DREAM_AVAILABLE",
    "HOME_TREE_CALLING",
    ["OpenDream"],
    ["home_tree", "abu_sleep_breath"],
    ["opening_theme", "leaf_whisper"],
  ),
  DREAM_PORTAL_READY: scene(
    "home-sleeping-portal",
    "DREAM_PORTAL_READY",
    "ABU_SLEEP_BREATH",
    ["OpenDream", "ResumeDream"],
    ["home_tree", "abu_curl_to_sleep", "abu_sleep_breath"],
    ["sleep_breath", "root_light"],
  ),
  ENTERING_DREAM: scene(
    "fog-gate",
    "ENTERING_DREAM",
    "FOG_GATE_OPENING",
    [],
    ["fog_gate"],
    ["opening_theme", "mist_open"],
  ),
  THREE_TREE_SELECTION: scene(
    "ghost-orbit-three-tree-selection",
    "THREE_TREE_SELECTION",
    "GHOST_ORBIT_FOCUSED",
    ["FocusCandidate", "CommitCandidate", "ReturnHome"],
    ["ghost_orbit"],
    ["leaf_whisper"],
  ),
  ENCOUNTER_COMMITTED: scene(
    "tree-commit-dissolve",
    "ENCOUNTER_COMMITTED",
    "TREE_COMMIT_DISSOLVE",
    [],
    ["ghost_orbit", "abu_tree_leap"],
    ["root_light", "mist_close"],
  ),
  FIXED_TREE_EXPLORATION: scene(
    "fixed-tree-exploration",
    "FIXED_TREE_EXPLORATION",
    "FIXED_TREE_IDLE",
    ["OpenQuestionNode", "SubmitFoundationAnswer", "ReturnHome"],
    ["fixed_tree", "question_leaf", "question_branch", "question_bud"],
    ["leaf_whisper", "branch_wake"],
  ),
  FOUNDATION_COMPLETE: scene(
    "fixed-tree-foundation-complete",
    "FOUNDATION_COMPLETE",
    "FIXED_TREE_IDLE",
    ["OpenQuestionNode", "OpenBlindRound", "ReturnHome"],
    ["fixed_tree", "question_bud"],
    ["flower_open"],
  ),
  BLIND_ROUND_OPEN: scene(
    "problem-flower",
    "BLIND_ROUND_OPEN",
    "QUESTION_NODE_ACTIVE",
    ["SubmitJudgment", "ReturnHome"],
    ["question_bud"],
    ["flower_open"],
  ),
  JUDGMENT_SUBMITTED: scene(
    "judgment-sealed",
    "JUDGMENT_SUBMITTED",
    "FIXED_TREE_IDLE",
    ["RequestReveal", "ReturnHome"],
    ["fixed_tree"],
  ),
  DOUBLE_SEALED: scene(
    "fog-white-fruit",
    "DOUBLE_SEALED",
    "FRUIT_FORMING",
    ["RequestReveal", "ReturnHome"],
    ["fruit_form"],
    ["fruit_form"],
  ),
  REVEALABLE: scene(
    "three-act-reveal",
    "REVEALABLE",
    "REVEAL_ACT_ACTIVE",
    ["CompleteReveal", "ReturnHome"],
    ["fruit_form"],
  ),
  REVEAL_COMPLETE: scene(
    "knowledge-seed",
    "REVEAL_COMPLETE",
    "REVEAL_ACT_ACTIVE",
    ["ReturnHome"],
    ["knowledge_seed"],
    ["seed_land"],
  ),
  RETURNED_WITH_SEED: scene(
    "home-seed-landing",
    "RETURNED_WITH_SEED",
    "SEED_LANDING",
    ["OpenDream"],
    ["home_tree", "knowledge_seed"],
    ["seed_land"],
  ),
};


export function sceneForStory(snapshot: DreamStorySnapshot): DreamSceneContract {
  const base = STORY_SCENES[snapshot.businessState];
  return {
    ...base,
    presentationState: snapshot.presentationState,
  };
}


function scene(
  sceneId: string,
  businessState: DreamBusinessState,
  presentationState: DreamSceneContract["presentationState"],
  allowedCommands: DreamSceneContract["allowedCommands"],
  assetDependencies: DreamSceneContract["assetDependencies"],
  audioCues: DreamSceneContract["audioCues"] = ["none"],
): DreamSceneContract {
  return {
    sceneId,
    businessState,
    presentationState,
    entryIntent: `${sceneId}:enter`,
    idleIntent: `${sceneId}:idle`,
    exitIntent: `${sceneId}:exit`,
    allowedCommands,
    audioCues,
    subtitleCues: [],
    assetDependencies,
    reducedMotionFallback: `${sceneId}:static-crossfade`,
    resumePolicy: `${sceneId}:restore-from-server-and-local-presentation-checkpoint`,
    errorPolicy: "FAIL_CLOSED",
    telemetry: [
      "scene_entered",
      "scene_command_attempted",
      "scene_command_committed",
      "scene_fail_closed",
    ],
  };
}
