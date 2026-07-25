import { DREAM_RUNTIME_ASSETS } from "./dream_asset_registry";


export type AbuDreamRole =
  | "home_sleeping_portal"
  | "ghost_orbit_observer"
  | "tree_commit_guide"
  | "fixed_tree_companion";

export interface AbuMotionContract {
  role: AbuDreamRole;
  assetId: string;
  source: string;
  poster: string;
  playback: "loop" | "once" | "poster";
  interruptible: boolean;
  semanticOwner: "ABU_MOTION_DIRECTOR";
  changesBusinessState: false;
  fallbackReason: string;
}


export function abuMotionFor(role: AbuDreamRole, reducedMotion = false): AbuMotionContract {
  if (role === "home_sleeping_portal") {
    const asset = DREAM_RUNTIME_ASSETS.abuSleep;
    return contract(
      role,
      asset.assetId,
      reducedMotion ? asset.poster || asset.source : asset.source,
      asset.poster || asset.source,
      reducedMotion ? "poster" : "loop",
      "ABU_03/04 canonical character-lock assets are not yet available; v6 is a registered non-semantic visual fallback.",
    );
  }
  if (role === "tree_commit_guide") {
    const asset = DREAM_RUNTIME_ASSETS.abuWalk;
    return contract(
      role,
      asset.assetId,
      reducedMotion ? asset.poster || asset.source : asset.source,
      asset.poster || asset.source,
      reducedMotion ? "poster" : "loop",
      "ABU_05 leap is missing; the approved calm walk is used only inside the masked transition.",
    );
  }
  const asset = DREAM_RUNTIME_ASSETS.abuSeated;
  return contract(
    role,
    asset.assetId,
    reducedMotion ? asset.poster || asset.source : asset.source,
    asset.poster || asset.source,
    reducedMotion ? "poster" : "loop",
    "",
  );
}


function contract(
  role: AbuDreamRole,
  assetId: string,
  source: string,
  poster: string,
  playback: AbuMotionContract["playback"],
  fallbackReason: string,
): AbuMotionContract {
  return {
    role,
    assetId,
    source,
    poster,
    playback,
    interruptible: true,
    semanticOwner: "ABU_MOTION_DIRECTOR",
    changesBusinessState: false,
    fallbackReason,
  };
}


export function renderAbuActor(
  motion: AbuMotionContract,
  alt: string,
  className: string,
): string {
  if (motion.playback === "poster" || !motion.source.endsWith(".webm")) {
    return `<img class="${escapeAttr(className)}" src="${escapeAttr(motion.source)}" alt="${escapeAttr(alt)}" draggable="false" data-abu-asset-id="${escapeAttr(motion.assetId)}">`;
  }
  return `<video class="${escapeAttr(className)}" src="${escapeAttr(motion.source)}" poster="${escapeAttr(motion.poster)}" ${motion.playback === "loop" ? "loop " : ""}autoplay muted playsinline preload="metadata" aria-label="${escapeAttr(alt)}" data-abu-asset-id="${escapeAttr(motion.assetId)}"></video>`;
}


function escapeAttr(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
