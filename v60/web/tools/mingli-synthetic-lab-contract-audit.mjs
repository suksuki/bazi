import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const read = (...parts) =>
  readFile(path.resolve(here, "../src", ...parts), "utf8");
const failures = [];
const expect = (condition, message) => {
  if (!condition) failures.push(message);
};

const [app, exposure, home, hotspots, labHost, overview, sceneHost] =
  await Promise.all([
    read("App.tsx"),
    read("productExposure.ts"),
    read("components", "HomeLifeTreeScene.tsx"),
    read("components", "HomeWorldHotspots.tsx"),
    read("components", "MingliLabWorkspaceHost.tsx"),
    read("components", "MingliResearchOverview.tsx"),
    read("components", "MingliSceneHost.tsx"),
  ]);

expect(
  exposure.includes('"v60.public-product-exposure.003"') &&
    exposure.includes('publicUnits: ["MINGLI_READING", "ABU_SAYS"]') &&
    exposure.includes('status: "INTERNAL_ONLY"') &&
    exposure.includes("publicEntryAllowed: false") &&
    exposure.includes("publicRouteAllowed: false"),
  "public-exposure:lab-must-remain-internal",
);

expect(
  app.includes('type PublicView = "HOME" | "BRANCH" | "STAGE"') &&
    !app.includes("MingliLabWorkspaceHost") &&
    !app.includes("onOpenLab"),
  "public-shell:only-home-branch-and-stage-may-be-reachable",
);

expect(
  !home.includes("onOpenLab") &&
    !hotspots.includes("onOpenLab") &&
    hotspots.includes("onOpenMingli") &&
    hotspots.includes("onOpenSettings"),
  "home:must-expose-only-chart-and-profile-actions",
);

expect(
  labHost.includes('mode is "overview" | "current" | "narration"') &&
    labHost.includes('mode: "NATAL_DAYUN_YEAR_6"') &&
    labHost.includes('autoOpenNarration={route.mode === "narration"}') &&
    labHost.includes("<MingliResearchOverview") &&
    labHost.includes("<MingliSceneHost"),
  "internal-lab:must-preserve-six-pillar-and-narration-demo",
);

expect(
  overview.includes("当前开放六柱与阿布说演示") &&
    overview.includes("六柱演示") &&
    overview.includes("阿布说"),
  "internal-lab:overview-must-name-the-two-preserved-demos",
);

expect(
  sceneHost.includes("autoOpenNarration") &&
    sceneHost.includes("MingliNarrationDirector") &&
    sceneHost.includes("MingliScenePlayer"),
  "shared-scene:must-keep-narration-and-particle-stage-on-one-host",
);

if (failures.length) {
  throw new Error(`mingli-synthetic-lab-contract-audit failed:\n${failures.join("\n")}`);
}

console.log("mingli-synthetic-lab-contract-audit passed");
