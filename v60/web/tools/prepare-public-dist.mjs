import { copyFile, mkdir, readdir, rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const assetsRoot = resolve(webRoot, "dist", "assets");
const releaseMedia = [
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
];

for (const entry of await readdir(assetsRoot, { withFileTypes: true })) {
  if (entry.isFile() && /\.(?:js|css|js\.map)$/.test(entry.name)) {
    continue;
  }
  await rm(resolve(assetsRoot, entry.name), { force: true, recursive: true });
}

for (const relativePath of releaseMedia) {
  const target = resolve(webRoot, "dist", relativePath);
  await mkdir(dirname(target), { recursive: true });
  await copyFile(resolve(webRoot, "public", relativePath), target);
}

const topLevel = await readdir(assetsRoot);
if (topLevel.some((name) => ["audio", "tree"].includes(name))) {
  throw new Error("v60_public_dist_contains_unreachable_assets");
}
