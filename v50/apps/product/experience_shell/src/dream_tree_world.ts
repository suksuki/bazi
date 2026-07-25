import type {
  DreamGameAttemptView,
  DreamGameLearningQuestionPublic,
  DreamGameLens,
  DreamGameRoundCard,
} from "./dream_game_api";
import { DREAM_RUNTIME_ASSETS } from "./dream_asset_registry";
import { abuMotionFor, renderAbuActor } from "./dream_abu_motion_director";
import type { DreamSceneContract } from "./dream_story_contracts";
import {
  SEMANTIC_TREE_SCENE_BUNDLE,
  semanticTreeOrganStyle,
} from "./semantic_tree_scene_bundle";


export type DreamTreeQuestionNodeId =
  | "leaf_structure"
  | "leaf_support"
  | "branch_path"
  | "problem_flower";

export type DreamTreeRevealAct =
  | "user"
  | "system"
  | "evidence"
  | "seed";

export type DreamTreeMediaCue =
  | "none"
  | "tree_enter"
  | "flower_open"
  | "fruit_forming";

export interface DreamTreeQuestionDefinition {
  nodeId: Exclude<DreamTreeQuestionNodeId, "problem_flower">;
  questionId: string;
  title: string;
  prompt: string;
  lens: DreamGameLens;
  available: boolean;
  options: Array<{ optionId: string; label: string }>;
}

export interface DreamTreeWorldPorchView {
  rounds: DreamGameRoundCard[];
  activeIndex: number;
  banner: string;
  entering: boolean;
  mediaCue: DreamTreeMediaCue;
  focusedWhisper: string;
  scene: DreamSceneContract;
}

export interface DreamTreeQuestionMapView {
  attempt: DreamGameAttemptView;
  residentDisplayLabel: string;
  banner: string;
  activeLens: DreamGameLens;
  lensOpen: boolean;
  canvasMarkup: string;
  questionBandMarkup: string;
  resultMarkup: string;
  activeNode: DreamTreeQuestionNodeId | "";
  passedNodes: DreamTreeQuestionNodeId[];
  flowerUnlocked: boolean;
  flowerOpened: boolean;
  fruitVisible: boolean;
  mediaCue: DreamTreeMediaCue;
  statusMessage: string;
  scene: DreamSceneContract;
}

export const DREAM_TREE_DIRECTOR_ROOT = "/assets/dream/encounter-01-v1/director-v2";

const LENS_META: Record<DreamGameLens, {
  label: string;
  objectLabel: string;
}> = {
  overview: { label: "总览", objectLabel: "树干年轮" },
  five_element: { label: "五行", objectLabel: "叶面五行" },
  roots_reveal: { label: "根透", objectLabel: "根脉承托" },
  combination_conflict: { label: "合冲", objectLabel: "枝路分合" },
  work_path: { label: "做功", objectLabel: "主枝路径" },
  timing: { label: "时运", objectLabel: "叶间露时" },
};


export function renderDreamTreePorch(view: DreamTreeWorldPorchView): string {
  const rounds = view.rounds.slice(0, 3);
  const count = Math.max(1, rounds.length);
  const activeIndex = ((view.activeIndex % count) + count) % count;
  const active = rounds[activeIndex];
  const abu = abuMotionFor("ghost_orbit_observer", prefersReducedMotion());
  const sceneAssets = [
    DREAM_RUNTIME_ASSETS.porchBlue,
    DREAM_RUNTIME_ASSETS.porchJade,
    DREAM_RUNTIME_ASSETS.porchAmber,
  ];
  const treeTargets = rounds.map((round, index) => {
    const activeTree = index === activeIndex;
    const forward = (index - activeIndex + count) % count;
    const orbitSlot = forward === 0 ? 0 : forward === 1 ? 1 : -1;
    const sceneAsset = sceneAssets[index] || sceneAssets[0];
    return `<button
      class="dream-tree-porch-tree is-porch-actor${activeTree ? " is-active is-dream-heart" : " is-ghost"}"
      type="button"
      data-dream-game-command="porch-select"
      data-porch-index="${index}"
      data-orbit-slot="${orbitSlot}"
      aria-current="${activeTree ? "true" : "false"}"
      aria-label="${escapeAttr(activeTree ? `${round.anonymous_label}位于梦心，轻触进入` : `让${round.anonymous_label}来到梦心`)}"
    ><img src="${sceneAsset.source}" alt="" draggable="false" aria-hidden="true" decoding="async" fetchpriority="${activeTree ? "high" : "auto"}"><span aria-hidden="true"></span></button>`;
  }).join("");
  const whisper = view.focusedWhisper
    ? `<p class="dream-ghost-orbit-whisper" aria-live="polite">${escapeHtml(view.focusedWhisper)}</p>`
    : `<p class="dream-ghost-orbit-whisper" aria-hidden="true"></p>`;
  const treeEnter = view.mediaCue === "tree_enter"
    ? `<div class="dream-director-transition is-tree-enter" data-dream-director-transition="tree-enter">
        <video
          data-dream-director-video="tree-enter"
          src="${DREAM_RUNTIME_ASSETS.treeEnter.source}"
          autoplay muted playsinline preload="auto"
        ></video>
      </div>`
    : "";

  return `<div
      class="dream-tree-world-shell is-porch is-layered-porch-v5${view.entering ? " is-entering" : ""}"
      data-tree-world-mode="porch"
      data-dream-scene-id="${escapeAttr(view.scene.sceneId)}"
      data-dream-business-state="${escapeAttr(view.scene.businessState)}"
      data-dream-presentation-state="${escapeAttr(view.scene.presentationState)}"
      style="--porch-active-index:${activeIndex}"
  >
    <section
      class="dream-tree-porch-camera"
      data-dream-tree-porch
      aria-label="三棵冻结案例的梦树门廊"
      aria-roledescription="可左右转向的连续林境"
      tabindex="0"
    >
      <div class="dream-tree-porch-panorama" aria-hidden="true">
        <img
          class="dream-tree-porch-backdrop"
          src="${DREAM_RUNTIME_ASSETS.porchCleanBackdrop.source}"
          alt=""
          draggable="false"
          decoding="async"
          fetchpriority="high"
        >
        <span class="dream-tree-porch-mist"></span>
        <span class="dream-ghost-orbit-veil is-left"></span>
        <span class="dream-ghost-orbit-veil is-right"></span>
      </div>
      <button
        class="dream-tree-porch-abu"
        type="button"
        data-dream-game-command="porch-shift"
        data-direction="1"
        aria-label="请阿布带下一棵梦树来到眼前"
      >
        ${renderAbuActor(abu, "", "dream-tree-porch-abu-actor")}
      </button>
      <div class="dream-tree-porch-targets">${treeTargets}</div>
      ${whisper}
      <div class="dream-ghost-orbit-a11y sr-only">
        <button type="button" data-dream-game-command="porch-shift" data-direction="-1">上一棵梦树</button>
        <button type="button" data-dream-game-command="porch-shift" data-direction="1">下一棵梦树</button>
        ${active ? `<span data-porch-current-label>当前梦心位：${escapeHtml(active.anonymous_label)}</span>` : ""}
      </div>
      <button
        class="dream-tree-porch-departure"
        type="button"
        data-dream-game-command="depart"
        aria-label="沿雾径离开梦境"
      ><span aria-hidden="true"></span><b>沿雾径离开</b></button>
    </section>
    ${treeEnter}
  </div>`;
}


export function renderDreamTreeQuestionMap(view: DreamTreeQuestionMapView): string {
  const passed = new Set(view.passedNodes);
  const bundle = SEMANTIC_TREE_SCENE_BUNDLE;
  const abu = abuMotionFor("fixed_tree_companion", prefersReducedMotion());
  const transition = renderTreeMediaTransition(view.mediaCue);
  const nodeMarkup = [
    renderTreeNode({
      id: "leaf_structure",
      label: "读取树冠中的显现叶",
      active: view.activeNode === "leaf_structure",
      passed: passed.has("leaf_structure"),
      locked: false,
      asset: bundle.assets.leafBasic01,
      layout: "leafBasic01",
      disabled: Boolean(view.resultMarkup),
    }),
    renderTreeNode({
      id: "leaf_support",
      label: "读取树冠中的承载叶",
      active: view.activeNode === "leaf_support",
      passed: passed.has("leaf_support"),
      locked: false,
      asset: bundle.assets.leafBasic02,
      layout: "leafBasic02",
      disabled: Boolean(view.resultMarkup),
    }),
    renderTreeNode({
      id: "branch_path",
      label: "读取特殊枝干",
      active: view.activeNode === "branch_path",
      passed: passed.has("branch_path"),
      locked: !passed.has("leaf_structure") || !passed.has("leaf_support"),
      asset: bundle.assets.trunkBackbone01,
      layout: "trunkBackbone01",
      disabled: Boolean(view.resultMarkup),
    }),
    renderFlowerOrFruit(view),
  ].join("");

  return `<div
    class="dream-tree-world-shell is-question-map"
    data-tree-world-mode="question-map"
    data-dream-scene-id="${escapeAttr(view.scene.sceneId)}"
    data-dream-business-state="${escapeAttr(view.scene.businessState)}"
    data-dream-presentation-state="${escapeAttr(view.scene.presentationState)}"
    data-active-node="${view.activeNode || "none"}"
    data-semantic-tree-bundle="${bundle.bundleId}"
    data-semantic-tree-bundle-sha256="${bundle.ownerAcceptedOuterSha256}"
    data-semantic-tree-cue="${view.mediaCue}"
    data-flower-state="${view.fruitVisible ? "fruit" : view.flowerUnlocked ? "open" : "bud"}"
    data-fruit-visible="${view.fruitVisible ? "true" : "false"}"
  >
    <header class="dream-tree-world-header">
      <button type="button" data-dream-game-command="return-porch" aria-label="返回梦树门廊">‹</button>
      <div><small>阿布问果 · 三树局</small><strong>${escapeHtml(view.residentDisplayLabel)}</strong></div>
      <span aria-hidden="true">结构盲局</span>
    </header>
    <p class="dream-tree-world-banner" role="status">${escapeHtml(view.banner)}</p>
    <section class="dream-question-tree-stage${!view.activeNode && passed.size === 0 ? " is-first-growth" : ""}" aria-label="${escapeAttr(`${view.residentDisplayLabel}的生命树`)}">
      <picture class="semantic-tree-base-layer"><img
        class="dream-question-tree-master"
        src="${bundle.assets.treeBase.source}"
        data-asset-sha256="${bundle.assets.treeBase.sha256}"
        alt=""
        draggable="false"
      ></picture>
      <img
        class="semantic-tree-energy-flow${view.flowerUnlocked ? " is-active" : ""}${view.mediaCue === "flower_open" ? " is-awakening" : ""}"
        src="${bundle.assets.energyFlow.source}"
        data-asset-sha256="${bundle.assets.energyFlow.sha256}"
        alt=""
        draggable="false"
        aria-hidden="true"
      >
      <div class="dream-question-tree-nodes">${nodeMarkup}</div>
      <img
        class="semantic-tree-foreground-occlusion"
        src="${bundle.assets.foregroundOcclusion.source}"
        data-asset-sha256="${bundle.assets.foregroundOcclusion.sha256}"
        style="${semanticTreeOrganStyle("foregroundOcclusion")}"
        alt=""
        draggable="false"
        aria-hidden="true"
      >
      <div class="dream-question-tree-abu" aria-hidden="true">${renderAbuActor(abu, "", "dream-question-tree-abu-actor")}</div>
      ${view.resultMarkup}
      ${view.questionBandMarkup && !view.resultMarkup
        ? `<aside class="dream-question-band" aria-live="polite">${view.questionBandMarkup}</aside>`
        : ""}
    </section>
    ${view.lensOpen ? `<section class="dream-tree-lens-overlay" aria-label="${escapeAttr(LENS_META[view.activeLens].label)}命盘镜">
      <div class="dream-tree-lens-forest-edge" aria-hidden="true"></div>
      <header>
        <div><small>${escapeHtml(LENS_META[view.activeLens].objectLabel)}</small><strong>${escapeHtml(LENS_META[view.activeLens].label)}</strong></div>
        <button type="button" data-dream-game-command="close-lens" aria-label="回到生命树">回到树中</button>
      </header>
      <div class="dream-tree-lens-canvas">${view.canvasMarkup}</div>
    </section>` : ""}
    ${view.statusMessage ? `<p class="dream-game-status" role="status">${escapeHtml(view.statusMessage)}</p>` : ""}
    ${transition}
  </div>`;
}


export function buildDreamTreeQuestions(
  attempt: DreamGameAttemptView,
): DreamTreeQuestionDefinition[] {
  return attempt.question_set.questions.map((question) => ({
    nodeId: questionNodeId(question),
    questionId: question.question_id,
    title: question.title,
    prompt: question.prompt,
    lens: question.target_lens,
    available: question.available,
    options: question.options.map((option) => ({
      optionId: option.option_id,
      label: option.label,
    })),
  }));
}


export function treeQuestionForNode(
  attempt: DreamGameAttemptView,
  nodeId: DreamTreeQuestionNodeId,
): DreamTreeQuestionDefinition | undefined {
  return buildDreamTreeQuestions(attempt).find((item) => item.nodeId === nodeId);
}


function questionNodeId(
  question: DreamGameLearningQuestionPublic,
): Exclude<DreamTreeQuestionNodeId, "problem_flower"> {
  if (question.kind === "LEAF_BASIC_01") return "leaf_structure";
  if (question.kind === "LEAF_BASIC_02") return "leaf_support";
  return "branch_path";
}


function renderTreeNode(input: {
  id: DreamTreeQuestionNodeId;
  label: string;
  active: boolean;
  passed: boolean;
  locked: boolean;
  asset: {
    source: string;
    sha256: string;
    hitMask?: string;
  };
  layout: "leafBasic01" | "leafBasic02" | "trunkBackbone01";
  disabled: boolean;
}): string {
  return `<button
    class="dream-question-tree-node semantic-tree-organ is-${input.id.replaceAll("_", "-")}${input.active ? " is-active" : ""}${input.passed ? " is-passed" : ""}${input.locked ? " is-locked" : ""}"
    type="button"
    data-dream-game-command="tree-node"
    data-tree-node="${input.id}"
    data-semantic-organ="${semanticOrganId(input.id)}"
    data-semantic-hit-mask="${escapeAttr(input.asset.hitMask || "")}"
    data-asset-sha256="${input.asset.sha256}"
    style="${semanticTreeOrganStyle(input.layout)}"
    aria-pressed="${input.active}"
    aria-disabled="${input.locked}"
    aria-label="${escapeAttr(input.label)}"
    ${input.disabled ? "disabled" : ""}
  ><img
    class="semantic-tree-organ-visual"
    src="${input.asset.source}"
    alt=""
    draggable="false"
    aria-hidden="true"
  >${input.asset.hitMask ? `<img
    class="semantic-tree-organ-hit-mask"
    src="${input.asset.hitMask}"
    alt=""
    draggable="false"
    aria-hidden="true"
  >` : ""}<span class="sr-only">${escapeHtml(input.label)}</span></button>`;
}


function renderFlowerOrFruit(view: DreamTreeQuestionMapView): string {
  const bundle = SEMANTIC_TREE_SCENE_BUNDLE;
  if (view.fruitVisible) {
    const fruit = bundle.assets.fruitWhite;
    return `<div
      class="dream-question-tree-node semantic-tree-organ is-problem-flower is-fruit-white"
      data-tree-node="problem_flower"
      data-semantic-organ="FRUIT_RESULT"
      data-semantic-anchor="FLOWER_BLINDROUND_01"
      data-semantic-hit-mask="${escapeAttr(fruit.hitMask || "")}"
      data-asset-sha256="${fruit.sha256}"
      style="${semanticTreeOrganStyle("fruitWhite")}"
      aria-label="双重封存后生成的雾白果实"
    ><img class="semantic-tree-organ-visual" src="${fruit.source}" alt="" draggable="false" aria-hidden="true"></div>`;
  }
  const flower = view.flowerUnlocked
    ? bundle.assets.flowerOpen
    : bundle.assets.flowerBudClosed;
  const layout = view.flowerUnlocked ? "flowerOpen" : "flowerBudClosed";
  const label = view.flowerUnlocked ? "查看已经解锁的问题花" : "尚未开放的问题花";
  return `<button
    class="dream-question-tree-node semantic-tree-organ is-problem-flower${view.activeNode === "problem_flower" ? " is-active" : ""}${view.flowerOpened ? " is-passed" : ""}${view.flowerUnlocked ? " is-open" : " is-locked"}"
    type="button"
    data-dream-game-command="tree-node"
    data-tree-node="problem_flower"
    data-semantic-organ="FLOWER_BLINDROUND_01"
    data-semantic-anchor="FLOWER_BLINDROUND_01"
    data-semantic-hit-mask="${escapeAttr(flower.hitMask || "")}"
    data-asset-sha256="${flower.sha256}"
    style="${semanticTreeOrganStyle(layout)}"
    aria-pressed="${view.activeNode === "problem_flower"}"
    aria-disabled="${!view.flowerUnlocked}"
    ${view.resultMarkup ? "disabled" : ""}
    aria-label="${escapeAttr(label)}"
  ><img class="semantic-tree-organ-visual" src="${flower.source}" alt="" draggable="false" aria-hidden="true">${flower.hitMask ? `<img
    class="semantic-tree-organ-hit-mask"
    src="${flower.hitMask}"
    alt=""
    draggable="false"
    aria-hidden="true"
  >` : ""}<span class="sr-only">${escapeHtml(label)}</span></button>`;
}


function semanticOrganId(nodeId: DreamTreeQuestionNodeId): string {
  if (nodeId === "leaf_structure") return "LEAF_BASIC_01";
  if (nodeId === "leaf_support") return "LEAF_BASIC_02";
  if (nodeId === "branch_path") return "TRUNK_BACKBONE_01";
  return "FLOWER_BLINDROUND_01";
}


function renderTreeMediaTransition(cue: DreamTreeMediaCue): string {
  return cue === "none" || cue === "tree_enter"
    ? ""
    : `<span class="semantic-tree-state-cue is-${cue.replaceAll("_", "-")}" data-dream-director-transition="${cue.replaceAll("_", "-")}" aria-hidden="true"></span>`;
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


function prefersReducedMotion(): boolean {
  return typeof window !== "undefined"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
