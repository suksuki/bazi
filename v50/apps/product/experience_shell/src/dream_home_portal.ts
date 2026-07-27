import type { DreamFeatureStatus } from "./dream_api";
import type { RealLifeTreeBootstrap } from "./relation_work_api";
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
  questionNodes: DreamHomeQuestionNode[];
  visualProfile: RealLifeTreeBootstrap["tree_visual_profile"] | null;
}

export interface DreamHomeQuestionNode {
  nodeId: string;
  questionId: string;
  category: string;
  label: string;
  status: "available" | "explored" | "locked" | "unavailable";
  answeredCount: number;
  questionCount: number;
}


export function renderDreamHomeLifeTree(view: DreamHomePortalView): string {
  const portalReady = Boolean(view.status?.enabled && view.status.available);
  const motion = abuMotionFor("home_sleeping_portal", prefersReducedMotion());
  const callState = view.returnedWithSeed
    ? "seed-return"
    : portalReady
      ? "portal-ready"
      : "quiet";
  const visual = view.visualProfile;
  const visualClass = visual
    ? ` is-${visual.form.replaceAll("_", "-")} is-${visual.material.replaceAll("_", "-")}`
    : "";
  const visualStyle = visual
    ? [
        `--tree-scale-x:${finiteNumber(visual.render_tokens.scale_x, 1)}`,
        `--tree-scale-y:${finiteNumber(visual.render_tokens.scale_y, 1)}`,
        `--tree-rotation:${finiteNumber(visual.render_tokens.rotation_deg, 0)}deg`,
        `--tree-hue:${finiteNumber(visual.render_tokens.hue_rotate_deg, 0)}deg`,
        `--tree-saturation:${finiteNumber(visual.render_tokens.saturation, 1)}`,
        `--tree-brightness:${finiteNumber(visual.render_tokens.brightness, 1)}`,
        `--tree-canopy-echo:${finiteNumber(visual.render_tokens.canopy_echo_opacity, 0)}`,
        `--tree-ground-sheen:${finiteNumber(visual.render_tokens.ground_sheen_opacity, 0)}`,
        `--tree-density:${finiteNumber(visual.metrics.density, 0.5)}`,
        `--tree-moisture:${finiteNumber(visual.metrics.moisture, 0.2)}`,
        `--tree-light:${finiteNumber(visual.metrics.light, 0.3)}`,
      ].join(";")
    : "";
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
  const questionNodes = view.questionNodes.length
    ? view.questionNodes.map(renderQuestionNode).join("")
    : `
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
    `;

  return `<div
    class="life-tree dream-home-life-tree${visualClass}"
    data-dream-home-state="${callState}"
    data-tree-visual-profile="${escapeAttr(visual?.profile_id || "pending")}"
    data-tree-visual-source="${escapeAttr(visual?.source || "pending")}"
    style="${escapeAttr(visualStyle)}"
    aria-label="你的生命树"
  >
    <img
      class="dream-home-tree-art"
      src="${escapeAttr(DREAM_RUNTIME_ASSETS.homeTree.source)}"
      alt=""
      draggable="false"
    >
    <img
      class="dream-home-tree-canopy-echo"
      src="${escapeAttr(DREAM_RUNTIME_ASSETS.homeTree.source)}"
      alt=""
      aria-hidden="true"
      draggable="false"
    >
    <span class="dream-home-tree-ground-sheen" aria-hidden="true"></span>
    <span class="dream-home-canopy-light" aria-hidden="true"></span>
    <div class="dream-home-question-organs" aria-label="当前命局生长出的命题">${questionNodes}</div>
    ${view.returnedWithSeed ? `<span class="dream-home-seed-landing" aria-label="一颗知识种子回到了你的生命树根"></span>` : ""}
    ${abu}
  </div>`;
}


function finiteNumber(value: number, fallback: number): number {
  return Number.isFinite(value) ? value : fallback;
}


function renderQuestionNode(node: DreamHomeQuestionNode): string {
  const asset = ({
    "leaf-observation": "leaf_basic_01.png",
    "leaf-timing": "leaf_basic_02.png",
    "trunk-framework": "trunk_backbone_01.png",
    "flower-question": node.status === "explored"
      ? "flower_open.png"
      : "flower_bud_closed.png",
  } as Record<string, string>)[node.nodeId] || "leaf_basic_01.png";
  const disabled = !node.questionId || node.status === "locked" || node.status === "unavailable";
  const organVisual = node.nodeId === "root-counterfactual"
    ? `<i class="dream-home-root-ripple" aria-hidden="true"></i>`
    : `<img src="/assets/dream/semantic-tree-visible-v1/assets/${asset}" alt="" aria-hidden="true">`;
  return `<button
    type="button"
    class="dream-home-question-organ is-${escapeAttr(node.nodeId)} is-${escapeAttr(node.status)}"
    data-life-tree-question="${escapeAttr(node.questionId)}"
    data-life-tree-category="${escapeAttr(node.category)}"
    aria-label="${escapeAttr(`${node.label}，已探索 ${node.answeredCount}/${node.questionCount}`)}"
    ${disabled ? "disabled" : ""}
  >
    ${organVisual}
    <span>${escapeHtml(node.label)}</span>
    <small>${node.answeredCount}/${node.questionCount}</small>
  </button>`;
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
