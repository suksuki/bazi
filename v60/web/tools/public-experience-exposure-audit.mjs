import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, "..");
const repoRoot = path.resolve(webRoot, "..");
const readWeb = (...parts) => readFile(path.resolve(webRoot, ...parts), "utf8");
const readRepo = (...parts) => readFile(path.resolve(repoRoot, ...parts), "utf8");
const failures = [];
const expect = (condition, message) => {
  if (!condition) failures.push(message);
};

const [
  app,
  homeTree,
  hotspots,
  branch,
  branchHost,
  sceneHost,
  rehearsal,
  focusedSpeechDirector,
  focusedSpeechTimeline,
  speechApi,
  sceneDirector,
  sceneCanvas,
  presentation,
  layerProjection,
  styles,
  exposureSource,
  main,
  manifest,
  publicHome,
  focusedSpeechService,
] = await Promise.all([
  readWeb("src", "App.tsx"),
  readWeb("src", "components", "HomeLifeTreeScene.tsx"),
  readWeb("src", "components", "HomeWorldHotspots.tsx"),
  readWeb("src", "components", "MingliBranchJourney.tsx"),
  readWeb("src", "components", "MingliBranchSceneHost.tsx"),
  readWeb("src", "components", "MingliSceneHost.tsx"),
  readWeb("src", "components", "MingliLayerRehearsal.tsx"),
  readWeb("src", "useMingliFocusedSpeechDirector.ts"),
  readWeb("src", "mingliFocusedSpeechTimeline.ts"),
  readWeb("src", "publicSpeechApi.ts"),
  readWeb("src", "mingliSceneDirector.ts"),
  readWeb("src", "components", "MingliSceneCanvas.tsx"),
  readWeb("src", "publicReadingPresentation.ts"),
  readWeb("src", "mingliLayerNarrationProjection.ts"),
  readWeb("src", "styles.css"),
  readWeb("src", "productExposure.ts"),
  readRepo("backend", "src", "abu_v60", "main.py"),
  readRepo("backend", "src", "abu_v60", "system_manifest.py"),
  readRepo("backend", "src", "abu_v60", "api", "public_experience.py"),
  readRepo("backend", "src", "abu_v60", "media", "focused_speech.py"),
]);

const vite = await createServer({
  root: webRoot,
  server: { middlewareMode: true },
  appType: "custom",
  logLevel: "silent",
});

try {
  const exposure = await vite.ssrLoadModule("/src/productExposure.ts");
  const rejected = exposure.normalizePublicExperienceUrl(
    new URL(
      "https://v60.test/experience?scope=retired&view=lab&lab_mode=synthetic&mingli_stage=1&keep=ok",
    ),
  );
  expect(
    rejected.pathname === "/experience" &&
      rejected.searchParams.get("keep") === "ok" &&
      !rejected.searchParams.has("scope") &&
      !rejected.searchParams.has("view") &&
      !rejected.searchParams.has("lab_mode") &&
      !rejected.searchParams.has("mingli_stage"),
    "route:retired-and-lab-deep-links-must-be-removed",
  );
  const admitted = exposure.normalizePublicExperienceUrl(
    new URL(
      "https://v60.test/experience?view=mingli&mingli_subject=current&mingli_stage=1&keep=ok",
    ),
  );
  expect(
    admitted.searchParams.get("view") === "mingli" &&
      admitted.searchParams.get("mingli_subject") === "current" &&
      admitted.searchParams.get("mingli_stage") === "1",
    "route:public-mingli-branch-and-stage-state-must-survive-refresh",
  );
  expect(
    exposure.PUBLIC_PRODUCT_EXPOSURE.policyVersion ===
      "v60.public-product-exposure.003" &&
      exposure.PUBLIC_PRODUCT_EXPOSURE.publicUnits.join(",") ===
        "MINGLI_READING,ABU_SAYS" &&
      exposure.PUBLIC_PRODUCT_EXPOSURE.lab.publicRouteAllowed === false,
    "client:public-policy-must-expose-only-mingli-reading-and-abu-says",
  );
} finally {
  await vite.close();
}

expect(
  app.includes("HomeLifeTreeScene") &&
    app.includes("MingliBranchSceneHost") &&
    app.includes("MingliSceneHost") &&
    !app.includes("PublicReadingWorkspace") &&
    !app.includes("MingliLabWorkspaceHost"),
  "app:public-entry-must-retain-the-original-life-tree-and-mingli-stage-ui",
);
expect(
  styles.includes('@import "./styles/v108-home-shell.css";') &&
    styles.includes('@import "./styles/mingli-growth.css";') &&
    styles.includes('@import "./styles/mingli-layer-rehearsal.css";') &&
    !styles.includes("v60-public.css"),
  "css:entry-must-use-the-established-v108-v131-visual-language",
);
expect(
  homeTree.includes("HomeWorldHotspots") &&
    homeTree.includes("MingliLeafRoute") &&
    !hotspots.includes("进入命理 Lab"),
  "home:life-tree-must-open-mingli-while-lab-remains-hidden",
);
expect(
  branch.includes("点枝、叶、花、果，直接听阿布说") &&
    branch.includes("onActivateLayer(item.id)") &&
    branchHost.includes('publicMode || layer === "timing"') &&
    sceneHost.includes('mode: "NATAL_DAYUN_YEAR_6"'),
  "branch:organs-must-open-the-reading-in-one action",
);
expect(
  rehearsal.includes("useMingliFocusedSpeechDirector") &&
    rehearsal.includes("MingliCharacterPerformance") &&
    focusedSpeechDirector.includes("loadFocusedPassSpeech") &&
    focusedSpeechDirector.includes("断语不用等") &&
    focusedSpeechDirector.includes("audio.currentTime") &&
    focusedSpeechDirector.includes("window.requestAnimationFrame(sample)") &&
    focusedSpeechDirector.includes("focusedSubtitle") &&
    focusedSpeechTimeline.includes("focusedColumnRefs") &&
    rehearsal.includes('className="mingli-rehearsal-subtitle"') &&
    rehearsal.includes("data-active-subtitle-index") &&
    speechApi.includes("stage_mode: stage.stage_mode") &&
    speechApi.includes("selected_year: stage.selected_year") &&
    speechApi.includes("X-Abu-Focused-Speech-Timeline") &&
    sceneDirector.includes("activeColumnRefs: clock.activeColumnRefs ?? []") &&
    sceneCanvas.includes("narratedColumnRefs.size > 0") &&
    focusedSpeechService.includes("audio_segment.frame_count") &&
    focusedSpeechService.includes("timeline_header_value"),
  "abu-says:old-stage-must-synchronize-the-character-and-particles-to-persisted-speech",
);
expect(
  presentation.includes("PUBLIC_SAFE_NORMALIZATION_CODES") &&
    presentation.includes("isPublicPassSafe") &&
    layerProjection.includes("!isPublicPassSafe(item)"),
  "presentation:unsafe-model-passes-must-fall-back-before-the-old-stage-renders",
);
expect(
  exposureSource.includes('"v60.public-product-exposure.003"') &&
    exposureSource.includes('publicUnits: ["MINGLI_READING", "ABU_SAYS"]'),
  "client:exposure-source-must-pin-policy-003",
);
expect(
  main.includes("if settings.internal_surfaces_enabled:") &&
    main.includes("mingli_synthetic_lab_router") &&
    manifest.includes('ENTRY_EXPERIENCE: Final = "MINGLI_HOME"') &&
    manifest.includes('"public_units": ["MINGLI_READING", "ABU_SAYS"]') &&
    manifest.includes('"status": "INTERNAL_ONLY"'),
  "server:only-the-lab-internal-surface-may-be-enabled",
);
expect(
  publicHome.includes('"scope": "MINGLI_HOME"') &&
    publicHome.includes('snapshot["tree"]') &&
    !publicHome.includes('snapshot["lab"]') &&
    !publicHome.includes('snapshot["units"]') &&
    !publicHome.includes('snapshot["lineage"]'),
  "api:public-home-may-project-tree-visuals-but-not-lab-or-internal-lineage",
);

async function filesBelow(directory, prefix = "") {
  const rows = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const relative = path.posix.join(prefix, entry.name);
    if (entry.isDirectory()) {
      rows.push(...await filesBelow(path.resolve(directory, entry.name), relative));
    } else {
      rows.push(relative);
    }
  }
  return rows;
}

const expectedMedia = new Set([
  "assets/brand/abuknows-v60-logo-transparent-v1.png",
  "assets/abu/v60/abu-v60-seated-idle-loop-v1/actor.webm",
  "assets/abu/v60/abu-v60-seated-idle-loop-v1/actor.webp",
  "assets/abu/v60/abu-v60-seated-idle-loop-v1/poster.png",
  "assets/dodo/idle-transparent-v1.webm",
  "assets/dodo/idle-transparent-v1.webp",
  "assets/dodo/idle-poster-transparent-v1.png",
  "assets/brand/v60-life-tree-login-background-v1.png",
  "assets/v108/abuknows-logo-day-transparent-v2.png",
  "assets/v108/abuknows-logo-night-white-transparent-v1.png",
  "assets/v108/home-day-threshold-v1.webp",
  "assets/v108/home-night-threshold-v1.webp",
  "assets/v108/life-leaf-v1.webp",
  "assets/v108/mingli-branch/mingli-branch-growth-night-v3-poster.webp",
  "assets/v108/mingli-branch/mingli-branch-growth-night-v3-start.webp",
  "assets/v108/mingli-branch/mingli-branch-growth-night-v3.mp4",
  "assets/v128/mingli-branch/mingli-branch-growth-day-v7-poster.webp",
  "assets/v128/mingli-branch/mingli-branch-growth-day-v7-start.webp",
  "assets/v128/mingli-branch/mingli-branch-growth-day-v7.mp4",
  "assets/v131/lab/mingli-research-watercourt-day-v1.webp",
  "assets/v131/lab/mingli-research-watercourt-night-v1.webp",
]);
const distFiles = await filesBelow(path.resolve(webRoot, "dist"));
const unexpectedDistFiles = distFiles.filter(
  (item) =>
    item !== "index.html" &&
    !expectedMedia.has(item) &&
    !/^assets\/[A-Za-z0-9_-]+\.(?:js|css|js\.map)$/.test(item),
);
expect(
  [...expectedMedia].every((item) => distFiles.includes(item)) &&
    unexpectedDistFiles.length === 0 &&
    !distFiles.some((item) => /assets\/(?:audio|tree)\//.test(item)),
  `dist:must-contain-only-reachable-life-tree-media:${unexpectedDistFiles.join(",")}`,
);

if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify({
  publicExposureContract: "PASS",
  policyVersion: "v60.public-product-exposure.003",
  visualShell: "ORIGINAL_LIFE_TREE_AND_MINGLI_BRANCH",
  publicFlow: ["AUTH", "LIFE_TREE", "MINGLI_BRANCH", "ABU_SAYS"],
  publicUnits: ["MINGLI_READING", "ABU_SAYS"],
  labRoutes: "NOT_REGISTERED",
  abuSays: "REUSES_PERSISTED_FOCUSED_PASS",
  abuSaysStage: "SIX_PILLAR_DAYLIGHT_AWARE",
  abuSaysClock: "HTML_AUDIO_CURRENT_TIME",
  abuSaysSubtitles: "FRAME_EXACT_SENTENCE_CUES",
  distFileCount: distFiles.length,
  failures,
}, null, 2));
