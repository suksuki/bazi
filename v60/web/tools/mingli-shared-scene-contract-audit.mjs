import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = (...parts) => path.resolve(here, "../src", ...parts);
const read = (...parts) => readFile(source(...parts), "utf8");
const failures = [];

const [
  storyCanvas,
  sceneHost,
  scenePlayer,
  narrationDirector,
  labInspector,
  sceneDirector,
  sceneCanvas,
  stageTypes,
  experienceUnits,
  app,
  audioPlayer,
  characterMedia,
  canonicalDrawer,
  homeSceneCompanion,
  readingJourney,
  stageNavigation,
  profileManager,
  branchSceneHost,
  labWorkspaceHost,
  syntheticScene,
  syntheticInspector,
] = await Promise.all([
  read("components", "ExperienceStoryCanvas.tsx"),
  read("components", "MingliSceneHost.tsx"),
  read("components", "MingliScenePlayer.tsx"),
  read("components", "MingliNarrationDirector.tsx"),
  read("components", "MingliLabSceneInspector.tsx"),
  read("mingliSceneDirector.ts"),
  read("components", "MingliSceneCanvas.tsx"),
  read("mingliStageTypes.ts"),
  read("experienceUnits.ts"),
  read("App.tsx"),
  read("components", "MingliAudioPlayer.tsx"),
  read("components", "TransparentCharacterMedia.tsx"),
  read("components", "MingliCanonicalDrawer.tsx"),
  read("components", "HomeSceneCompanion.tsx"),
  read("components", "MingliReadingJourney.tsx"),
  read("mingliStageNavigation.ts"),
  read("components", "HomeProfileManager.tsx"),
  read("components", "MingliBranchSceneHost.tsx"),
  read("components", "MingliLabWorkspaceHost.tsx"),
  read("components", "MingliSyntheticExperimentScene.tsx"),
  read("components", "MingliSyntheticExperimentInspector.tsx"),
]);

const expect = (condition, message) => {
  if (!condition) failures.push(message);
};
const occurrences = (value, pattern) => value.match(pattern)?.length ?? 0;

expect(
  storyCanvas.includes('activeUnit === "mingli" || activeUnit === "lab"'),
  "story-canvas:reading-and-lab-do-not-share-host-condition",
);
expect(
  occurrences(storyCanvas, /<MingliLabWorkspaceHost/g) === 1 &&
    occurrences(labWorkspaceHost, /<MingliSceneHost/g) === 1,
  "story-canvas:lab-workspace-must-own-current-scene-host",
);
expect(
  occurrences(sceneHost, /<MingliScenePlayer/g) === 1,
  "scene-host:scene-player-must-mount-once",
);
expect(
  !/MingliScenePlayer|Canvas/.test(narrationDirector),
  "narration-director:must-not-own-scene-player-or-canvas",
);
expect(
  !/MingliScenePlayer|Canvas/.test(labInspector),
  "lab-inspector:must-not-own-scene-player-or-canvas",
);
expect(
  occurrences(syntheticScene, /<MingliScenePlayer/g) === 1 &&
    !/key=\{.*projection/.test(syntheticScene) &&
    !/MingliScenePlayer|Canvas/.test(syntheticInspector),
  "synthetic-lab:must-reuse-one-keyless-player-and-inspector-must-not-own-canvas",
);
expect(
  labWorkspaceHost.includes('route.mode === "synthetic"') &&
    labWorkspaceHost.indexOf("<MingliSyntheticExperimentScene") <
      labWorkspaceHost.indexOf("<MingliSceneHost"),
  "lab-workspace:current-and-synthetic-scenes-must-be-mutually-exclusive",
);
expect(
  scenePlayer.includes('lazy(() => import("./MingliSceneCanvas"))'),
  "scene-player:three-renderer-must-remain-lazy",
);
expect(
  scenePlayer.includes("data-scene-instance-id"),
  "scene-player:missing-persistent-instance-evidence",
);
expect(
  sceneCanvas.includes("const semanticAmount = frame.cueProgress"),
  "scene-canvas:paused-and-buffering-must-retain-frozen-semantic-progress",
);
expect(
  !sceneCanvas.includes("frame.semanticRunning ? frame.cueProgress : 0"),
  "scene-canvas:frozen-semantic-progress-must-not-reset-to-zero",
);
expect(
  !experienceUnits.match(/key:\s*"abu"/),
  "experience-units:abu-says-must-not-be-an-independent-dock-unit",
);
expect(
  app.includes("<HomeSceneCompanion") &&
    homeSceneCompanion.includes("<MingliCanonicalDrawer") &&
    canonicalDrawer.includes('className="mingli-canonical-drawer"') &&
    canonicalDrawer.includes("<HomeCompanionRail"),
  "app:canonical-reading-and-lab-capabilities-must-remain-reachable",
);
expect(
  audioPlayer.includes('audio.removeAttribute("src")') &&
    audioPlayer.includes("audio.load()"),
  "audio-player:must-release-media-on-unmount",
);
expect(
  characterMedia.includes("useReducedMotion") &&
    characterMedia.includes('mode === "poster"'),
  "character-media:reduced-motion-must-use-poster",
);
expect(
  readingJourney.includes("summaryMatchesStage") &&
    readingJourney.includes("summary?.claim_graph") &&
    !readingJourney.includes("reading.output"),
  "reading-journey:must-consume-validated-shared-claim-graph",
);
expect(
  readingJourney.includes("dayMasterAdmitted") &&
    readingJourney.includes('"日主状态待校准"') &&
    readingJourney.includes("natalAdmitted ? natal.statement") &&
    readingJourney.includes('context="原局基线"'),
  "reading-journey:withheld-day-master-or-natal-must-not-leak",
);
expect(
  labInspector.includes("claimGraph: MingliReadingClaimGraph | null") &&
    labInspector.includes("data-claim-graph-ref={claimGraph.graph_ref}") &&
    sceneHost.includes("claimGraph={currentClaimGraph}") &&
    sceneHost.includes("summaryMatchesStage(readingSummary, stage)") &&
    !sceneHost.includes("claimGraph={readingSummary?.claim_graph ?? null}"),
  "lab-inspector:must-consume-the-same-summary-claim-graph",
);
expect(
  sceneHost.includes("generationRequestRef.current === requestId") &&
    sceneHost.includes("summaryMatchesStage(summary, activeStage)") &&
    branchSceneHost.includes("generationRequestRef.current === requestId") &&
    branchSceneHost.includes("summaryMatchesStage(nextSummary, activeStage)"),
  "agent-generation:stale-case-response-must-not-commit",
);
expect(
  !readingJourney.includes("讲这一层"),
  "reading-journey:must-not-claim-layer-bound-narration-before-contract-exists",
);
expect(
  stageNavigation.includes('url.searchParams.set("mingli_layer"') &&
    stageNavigation.includes('url.searchParams.get("mingli_layer")'),
  "stage-navigation:reading-layer-must-be-refresh-recoverable",
);
expect(
  profileManager.includes("<dialog") && profileManager.includes("showModal()"),
  "profile-manager:must-remain-a-focus-isolating-modal",
);
expect(
  profileManager.includes("pendingCaseRef") &&
    profileManager.includes("if (working) return") &&
    profileManager.includes("setPendingCaseRef(created.case_ref)"),
  "profile-manager:committed-case-must-survive-stale-home-refresh",
);

for (const action of [
  "PILLARS_PRESENT",
  "RELATIONS_PRESENT",
  "BOUNDARY_HOLD",
  "TIME_COORDINATES_PRESENT",
]) {
  expect(
    stageTypes.includes(action) &&
      (action === "PILLARS_PRESENT" || sceneDirector.includes(action)),
    `scene-director:missing-safe-action:${action}`,
  );
}
for (const forbidden of [
  "EFFECT_PRESENT",
  "USABLE_SOURCE_PRESENT",
  "WANGSHUAI_PRESENT",
  "WORK_CONFIRMED",
]) {
  expect(!sceneDirector.includes(forbidden), `scene-director:forbidden-action:${forbidden}`);
}

if (failures.length) throw new Error(failures.join("\n"));
console.log(
  JSON.stringify(
    {
      sharedHost: "PASS",
      currentScenePlayerMounts: 1,
      syntheticScenePlayerMounts: 1,
      narratorOwnsCanvas: false,
      labOwnsCanvas: false,
      independentAbuDockUnit: false,
      canonicalDetailsReachable: true,
      audioReleaseOnUnmount: true,
      reducedMotionPoster: true,
      exactReadingLineageGuard: true,
      staleAgentGenerationCommitBlocked: true,
      sharedClaimGraphConsumers: ["MingliReadingJourney", "MingliLabSceneInspector"],
      readingLayerRecovery: true,
      profileFocusIsolation: true,
      profileMutationRecovery: true,
      semanticBoundary: "COORDINATES_AND_MEMBERSHIP_ONLY",
      failures,
    },
    null,
    2,
  ),
);
