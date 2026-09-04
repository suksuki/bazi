import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = (...parts) => path.resolve(here, "../src", ...parts);
const read = (...parts) => readFile(source(...parts), "utf8");
const failures = [];
const expect = (condition, message) => {
  if (!condition) failures.push(message);
};
const occurrences = (value, pattern) => value.match(pattern)?.length ?? 0;

const [
  app,
  sceneHost,
  scenePlayer,
  sceneCanvas,
  sceneDirector,
  stageTypes,
  branchJourney,
  branchHost,
  labHost,
  narrationDirector,
  labInspector,
  syntheticScene,
  syntheticInspector,
  layerProjection,
  layerRehearsal,
  focusedSpeechDirector,
  focusedSpeechTimeline,
  speechApi,
  focusedPassGeneration,
  stageNavigation,
  characterMedia,
  profileManager,
] = await Promise.all([
  read("App.tsx"),
  read("components", "MingliSceneHost.tsx"),
  read("components", "MingliScenePlayer.tsx"),
  read("components", "MingliSceneCanvas.tsx"),
  read("mingliSceneDirector.ts"),
  read("mingliStageTypes.ts"),
  read("components", "MingliBranchJourney.tsx"),
  read("components", "MingliBranchSceneHost.tsx"),
  read("components", "MingliLabWorkspaceHost.tsx"),
  read("components", "MingliNarrationDirector.tsx"),
  read("components", "MingliLabSceneInspector.tsx"),
  read("components", "MingliSyntheticExperimentScene.tsx"),
  read("components", "MingliSyntheticExperimentInspector.tsx"),
  read("mingliLayerNarrationProjection.ts"),
  read("components", "MingliLayerRehearsal.tsx"),
  read("useMingliFocusedSpeechDirector.ts"),
  read("mingliFocusedSpeechTimeline.ts"),
  read("publicSpeechApi.ts"),
  read("useMingliFocusedPassGeneration.ts"),
  read("mingliStageNavigation.ts"),
  read("components", "TransparentCharacterMedia.tsx"),
  read("components", "HomeProfileManager.tsx"),
]);

expect(
  app.includes("<HomeLifeTreeScene") &&
    app.includes("<MingliBranchSceneHost") &&
    app.includes("<MingliSceneHost") &&
    !app.includes("MingliLabWorkspaceHost") &&
    !app.includes("AbuSaysUnit"),
  "public-shell:must-use-one-home-branch-stage-path",
);

expect(
  occurrences(sceneHost, /<MingliScenePlayer/g) === 1 &&
    scenePlayer.includes('lazy(() => import("./MingliSceneCanvas"))') &&
    scenePlayer.includes("data-scene-instance-id"),
  "shared-stage:must-mount-one-lazy-persistent-player",
);

expect(
  !/MingliScenePlayer|Canvas/.test(narrationDirector) &&
    !/MingliScenePlayer|Canvas/.test(labInspector) &&
    !/MingliScenePlayer|Canvas/.test(syntheticInspector),
  "secondary-panels:must-not-own-a-renderer",
);

expect(
  occurrences(syntheticScene, /<MingliScenePlayer/g) === 1 &&
    !/key=\{.*projection/.test(syntheticScene) &&
    occurrences(labHost, /<MingliSceneHost/g) === 1 &&
    !labHost.includes("<MingliSyntheticExperimentScene"),
  "internal-lab:must-keep-bounded-shared-player-topology",
);

expect(
  branchJourney.includes("onActivateLayer(item.id)") &&
    !branchJourney.includes("onOpenLab") &&
    branchHost.includes("openLayerRehearsal(layer)") &&
    branchHost.includes("missingFocuses") &&
    branchHost.includes('layer === "timing"') &&
    branchHost.includes('writeMingliStageExperience("stage", "rehearsal", "push")'),
  "branch:each-organ-must-open-the-existing-reading-stage-directly",
);

expect(
  sceneHost.includes("useMingliFocusedPassGeneration") &&
    focusedPassGeneration.includes("requestRef.current === requestId") &&
    focusedPassGeneration.includes("summaryMatchesStage(summary, activeStage)") &&
    sceneHost.includes("summaryMatchesStage(readingSummary, stage)"),
  "focused-generation:stale-case-results-must-not-commit",
);

expect(
  layerProjection.includes('sourceKind: "CLAIM_GRAPH"') &&
    layerProjection.includes('sourceKind: "FOCUSED_PASSES"') &&
    layerProjection.includes('item.status !== "WITHHELD"') &&
    layerRehearsal.includes("data-source-item-ref={chapter.sourceItemRef}") &&
    layerRehearsal.includes("data-source-ref={projection.sourceRef}"),
  "rehearsal:must-render-only-lineage-bound-reading material",
);

expect(
  layerRehearsal.includes("useMingliFocusedSpeechDirector") &&
    layerRehearsal.includes('performanceMode="AUDIO"') &&
    layerRehearsal.includes('className="mingli-rehearsal-subtitle"') &&
    !layerRehearsal.includes("上一段") &&
    !layerRehearsal.includes("下一段"),
  "abu-says:must-use-one continuous subtitle presentation",
);

expect(
  focusedSpeechDirector.includes("audio.currentTime") &&
    focusedSpeechDirector.includes("window.requestAnimationFrame(sample)") &&
    focusedSpeechDirector.includes('setSpeechState("BUFFERING")') &&
    focusedSpeechDirector.includes("focusedSubtitle") &&
    focusedSpeechDirector.includes("subtitle.activeColumnRefs") &&
    focusedSpeechTimeline.includes("focusedCueAtTime") &&
    focusedSpeechTimeline.includes("focusedColumnRefs") &&
    speechApi.includes("X-Abu-Focused-Speech-Timeline"),
  "abu-says:audio-subtitle-and-pillar-focus-must-share-one-clock",
);

expect(
  sceneDirector.includes("activeColumnRefs: clock.activeColumnRefs ?? []") &&
    sceneCanvas.includes("const semanticAmount = frame.cueProgress") &&
    sceneCanvas.includes("narratedColumnRefs.size > 0") &&
    !sceneCanvas.includes("frame.semanticRunning ? frame.cueProgress : 0"),
  "particles:paused-cue-progress-and-explicit-column-focus-must-be-stable",
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
  expect(
    !sceneDirector.includes(forbidden),
    `scene-director:forbidden-action:${forbidden}`,
  );
}

expect(
  stageNavigation.includes('url.searchParams.set("mingli_layer"') &&
    stageNavigation.includes('url.searchParams.set("mingli_stage", "1")') &&
    stageNavigation.includes('params.get("mingli_rehearsal") === "1"'),
  "navigation:stage-layer-and-rehearsal-must-survive-refresh",
);

expect(
  characterMedia.includes("useReducedMotion") &&
    characterMedia.includes('mode === "poster"') &&
    profileManager.includes("<dialog") &&
    profileManager.includes("showModal()"),
  "accessibility:must-keep-poster-fallback-and-modal-focus-isolation",
);

if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify({
  sharedHost: "PASS",
  currentScenePlayerMounts: 1,
  publicPath: ["HOME", "MINGLI_BRANCH", "READING_STAGE", "ABU_SAYS"],
  focusedSpeechClockSource: "HTML_AUDIO_CURRENT_TIME",
  focusedSpeechSubtitleSync: "FRAME_EXACT_SENTENCE_CUES",
  focusedSpeechPillarFocus: "EXPLICIT_COORDINATE_TERMS_ONLY",
  semanticBoundary: "COORDINATES_AND_MEMBERSHIP_ONLY",
  failures,
}, null, 2));
