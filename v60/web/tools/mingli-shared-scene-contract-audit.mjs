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
  occurrences(storyCanvas, /<MingliSceneHost/g) === 1,
  "story-canvas:scene-host-must-mount-once",
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
for (const lineageCheck of [
  "stage.case_ref === home.case.case_ref",
  "stage.chart_version_ref === home.chart.chart_version_ref",
  "stage.life_case_revision_ref === home.life_case.life_case_revision_ref",
  "stage.reading_ref === reading.reading_ref",
]) {
  expect(
    readingJourney.includes(lineageCheck),
    `reading-journey:missing-home-stage-lineage-guard:${lineageCheck}`,
  );
}
expect(
  readingJourney.includes("这不是专业复核后的命理 Reading") &&
    readingJourney.includes("stage.columns"),
  "reading-journey:synthetic-subject-must-use-stage-only-boundary",
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
      scenePlayerMounts: 1,
      narratorOwnsCanvas: false,
      labOwnsCanvas: false,
      independentAbuDockUnit: false,
      canonicalDetailsReachable: true,
      audioReleaseOnUnmount: true,
      reducedMotionPoster: true,
      exactReadingLineageGuard: true,
      syntheticReadingIsolation: true,
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
