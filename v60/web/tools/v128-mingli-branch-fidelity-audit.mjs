import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(here, "../..");
const read = (...parts) => readFile(path.resolve(projectRoot, ...parts), "utf8");
const readBytes = (...parts) => readFile(path.resolve(projectRoot, ...parts));
const failures = [];

const [journey, host, styles, manifest, registry] = await Promise.all([
  read("web", "src", "components", "MingliBranchJourney.tsx"),
  read("web", "src", "components", "MingliBranchSceneHost.tsx"),
  read("web", "src", "styles", "mingli-growth.css"),
  read("media", "manifests", "V128_MINGLI_BRANCH_GROWTH_BASELINE_V1.v1.json").then(
    JSON.parse,
  ),
  read("assets", "registry.json").then(JSON.parse),
]);

const expect = (condition, message) => {
  if (!condition) failures.push(message);
};
const growingNodeNavRule =
  styles.match(
    /\.mingli-growth-world\[data-growth-state="growing"\] \.mingli-growth-nodes\s*\{([^}]*)\}/,
  )?.[1] ?? "";

expect(
  journey.includes("const LAYER_REVEAL_AT = [0.45, 3.32, 4.58, 5.32] as const"),
  "branch:must-use-frozen-v128-layer-reveal-timeline",
);
expect(
  journey.includes("onTimeUpdate={updateGrowthTimeline}") &&
    journey.includes("setRevealedCount(LAYERS.length)"),
  "branch:timeline-must-reveal-progressively-and-complete-safely",
);
expect(
  journey.includes("videoRef.current?.pause()") &&
    journey.includes('setGrowthState("growing")') &&
    journey.includes("setRevealedCount(0)") &&
    journey.includes("setReplayNonce((current) => current + 1)") &&
    !journey.includes("if (!video) return"),
  "branch:replay-must-work-after-refresh-static-poster-recovery",
);
expect(
  journey.includes("window.clearTimeout(entryTimerRef.current)") &&
    (journey.match(/entryTimerRef\.current = null/g)?.length ?? 0) >= 2,
  "branch:closing-during-entry-must-cancel-the-entry-timer-race",
);
expect(
  journey.includes('revealed ? "is-revealed" : ""') &&
    journey.includes("disabled={!ready || !revealed || agentGenerating}"),
  "branch:unrevealed-organs-must-remain-hidden-and-inert",
);
expect(
  styles.includes(".mingli-growth-node.is-revealed {") &&
    styles.includes("transition: opacity 440ms var(--mingli-ease-out);") &&
    styles.includes('.mingli-growth-node:not(.is-revealed)') &&
    !growingNodeNavRule.includes("opacity: 0"),
  "branch:growth-state-must-not-hide-the-whole-four-layer-sequence",
);
for (const desktopHotspot of [
  ".mingli-growth-node.is-principle { top: 67.1%; left: 41.25%; width: 5.2%; }",
  ".mingli-growth-node.is-image { top: 48.35%; left: 63.35%; width: 9.6%; }",
  "top: 44.8%;\n  left: 76.4%;\n  width: 6.2%;",
  "top: 58.9%;\n  left: 79.2%;\n  width: 5.4%;",
]) {
  expect(styles.includes(desktopHotspot), `branch:desktop-hotspot-drift:${desktopHotspot}`);
}

expect(
  host.includes("loadMingliStage") &&
    host.includes("loadMingliReadingSummary") &&
    ![journey, host].some((source) =>
      ["reading-bundles", "getMingliReadingBundle", "fixtureKey", "localStorage"].some(
        (forbidden) => source.includes(forbidden),
      ),
    ),
  "branch:prototype-mock-or-local-state-crossed-the-v60-domain-boundary",
);

expect(
  manifest.frozen_design_commit === "9a073a46438c29d1aa048241611249a761b08648",
  "manifest:wrong-v128-frozen-commit",
);
expect(
  manifest.boundaries.runtime_data_authority === "V60_CANONICAL" &&
    manifest.boundaries.imports_mock_data === false &&
    manifest.boundaries.product_scope === "MINGLI_ONLY",
  "manifest:v128-experience-import-crossed-product-boundary",
);

const assets = Object.fromEntries(registry.assets.map((asset) => [asset.asset_ref, asset]));
const expectedAssets = {
  "experience.v128.mingli-branch.day-video.v1":
    "0862c45a4b8409dafef897c36961bd1cb07c641b371ab3fcc4a4736b5bb9a160",
  "experience.v128.mingli-branch.day-start.v1":
    "8c87f3793bb132be0a342e5a3aff27509cb2a5c5c6ba0d67e721e3d85fc76312",
  "experience.v128.mingli-branch.day-poster.v1":
    "e7e6a0c120b1ba0ecbdaa76a7bc52493005e5c9da7f9390d2fee8462a2f7c7b4",
};
for (const [ref, expectedHash] of Object.entries(expectedAssets)) {
  expect(assets[ref]?.sha256 === expectedHash, `registry:missing-or-mismatched:${ref}`);
  if (assets[ref]?.runtime_path) {
    const bytes = await readBytes(assets[ref].runtime_path);
    const actualHash = createHash("sha256").update(bytes).digest("hex");
    expect(actualHash === expectedHash, `delivery:byte-hash-mismatch:${ref}`);
  }
}

if (failures.length) throw new Error(failures.join("\n"));
console.log(
  JSON.stringify(
    {
      baseline: "V128",
      frozenCommit: manifest.frozen_design_commit,
      dayGrowthAsset: "mingli-branch-growth-day-v7",
      sequentialRevealSeconds: manifest.experience_contract.layer_reveal_seconds,
      domainAuthority: manifest.boundaries.runtime_data_authority,
      productScope: manifest.boundaries.product_scope,
      importedMockState: false,
      byteVerifiedAssetCount: Object.keys(expectedAssets).length,
      failures,
    },
    null,
    2,
  ),
);
