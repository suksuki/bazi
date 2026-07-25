import type { DreamFeatureStatus } from "./dream_api";
import { DREAM_RUNTIME_ASSETS } from "./dream_asset_registry";
import {
  abuMotionFor,
  renderAbuActor,
} from "./dream_abu_motion_director";


export interface DreamHomePortalView {
  status: DreamFeatureStatus | null;
  returnedWithSeed: boolean;
  pillars: string;
  pathSummary: string;
  condition: string;
}


export function renderDreamHomeLifeTree(view: DreamHomePortalView): string {
  const portalReady = Boolean(view.status?.enabled && view.status.available);
  const motion = abuMotionFor("home_sleeping_portal", prefersReducedMotion());
  const callState = view.returnedWithSeed
    ? "seed-return"
    : portalReady
      ? "portal-ready"
      : "quiet";
  const portalLabel = view.status?.resumable
    ? "轻触熟睡的阿布，继续上次的梦"
    : "轻触熟睡的阿布，随他进入梦境";
  const abu = portalReady
    ? `<button
        class="dream-home-abu-portal"
        type="button"
        data-command="enter-dream"
        aria-label="${escapeAttr(portalLabel)}"
      >
        ${renderAbuActor(motion, "阿布在生命树根旁安静睡着", "dream-home-sleeping-abu")}
        <span class="dream-home-root-call" aria-hidden="true"></span>
      </button>`
    : `<div class="dream-home-abu-resting" aria-hidden="true">
        <img src="${escapeAttr(DREAM_RUNTIME_ASSETS.abuSeated.poster || DREAM_RUNTIME_ASSETS.abuSeated.source)}" alt="" draggable="false">
      </div>`;

  return `<div
    class="life-tree dream-home-life-tree"
    data-dream-home-state="${callState}"
    aria-label="你的生命树"
  >
    <img
      class="dream-home-tree-art"
      src="${escapeAttr(DREAM_RUNTIME_ASSETS.homeTree.source)}"
      alt=""
      draggable="false"
    >
    <span class="dream-home-canopy-light" aria-hidden="true"></span>
    <button
      type="button"
      class="dream-home-tree-mark is-chart"
      data-product-area="workbench"
      aria-label="打开命盘基线"
    ><small>命</small><strong>${escapeHtml(view.pillars || "四柱待确认")}</strong></button>
    <button
      type="button"
      class="dream-home-tree-mark is-path"
      data-select-anchor="baseline-work-path"
      data-message="${escapeAttr(view.pathSummary)}"
      aria-label="查看当前认知"
    ><small>事</small><strong>${escapeHtml(firstSentence(view.pathSummary))}</strong></button>
    <button
      type="button"
      class="dream-home-tree-mark is-person"
      data-command="toggle-abu"
      aria-label="查看当前行动条件"
    ><small>人</small><strong>${escapeHtml(firstSentence(view.condition))}</strong></button>
    ${view.returnedWithSeed ? `<span class="dream-home-seed-landing" aria-label="一颗知识种子回到了你的生命树根"></span>` : ""}
    ${abu}
  </div>`;
}


function prefersReducedMotion(): boolean {
  return typeof window !== "undefined"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}


function firstSentence(value: string): string {
  return value.split(/[。！？!?]/)[0]?.trim() || value.trim();
}


function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function escapeAttr(value: string): string {
  return escapeHtml(value);
}
