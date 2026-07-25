import {
  ELEMENT_META,
  loadScene,
  scenePillars,
  stageFor,
} from "../../shared/s0-v12-shared/scene-runtime.js";

const workspace = document.querySelector("#workspace");
const onecanvasScene = document.querySelector("#onecanvasScene");
const labChart = document.querySelector("#labChart");
const roleSelect = document.querySelector("#roleSelect");
const labGate = document.querySelector("#labGate");
const labWorkspace = document.querySelector("#labWorkspace");
const xiangfaFrame = document.querySelector("#xiangfaFrame");
const abuSheet = document.querySelector("#abuSheet");
const abuToggle = document.querySelector("#abuToggle");
const abuClose = document.querySelector("#abuClose");
const abuPeek = document.querySelector("#abuPeek");
const abuMode = document.querySelector("#abuMode");
const abuSelection = document.querySelector("#abuSelection");
const abuMessage = document.querySelector("#abuMessage");
const overviewTimeTitle = document.querySelector("#overviewTimeTitle");
const overviewTimeCopy = document.querySelector("#overviewTimeCopy");
const theaterStageCopy = document.querySelector("#theaterStageCopy");

const MODES = ["overview", "onecanvas", "xiangfa", "theater", "lab"];
const STAGES = ["original", "luck", "year"];
const PROFESSIONAL_ROLES = new Set(["practitioner", "researcher", "admin"]);
const THEATER_TIME = {original: 10.6, luck: 24.2, year: 31.7};

const MODE_LABELS = {
  overview: "概览",
  onecanvas: "命局",
  xiangfa: "象法",
  theater: "时间",
  lab: "实验室",
};

const state = {
  mode: "overview",
  stage: "original",
  role: "admin",
  selectedRef: "path-observed-jia-ding-geng",
  abuOpen: false,
  sandboxVariant: "formal",
};

let source;
let pillars = [];
let selectionIndex = new Map();
let xiangfaReady = false;

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function elementName(element) {
  return {wood: "木", fire: "火", earth: "土", metal: "金", water: "水"}[element] || "";
}

function polarityName(polarity) {
  return polarity === "yang" ? "阳" : "阴";
}

function nodeRefFor(slot, position) {
  const exact = {
    "slot-natal-year:stem": "node-stem-year-geng",
    "slot-natal-year:branch": "node-branch-year-chen",
    "slot-natal-month:stem": "node-stem-month-ding",
    "slot-natal-day:stem": "node-stem-day-jia",
    "slot-natal-day:branch": "node-branch-day-xu",
    "slot-natal-hour:branch": "node-branch-hour-chen",
    "slot-luck-gengyin:stem": "node-luck-geng",
    "slot-luck-gengyin:branch": "node-luck-yin",
    "slot-year-bingwu:stem": "node-year-bing",
    "slot-year-bingwu:branch": "node-year-wu",
  };
  return exact[`${slot.slot_ref}:${position}`] || slot.slot_ref;
}

function buildSelectionIndex() {
  const index = new Map();
  index.set(source.observed_natal_path.path_ref, {
    label: source.observed_natal_path.public_label,
    summary: `${source.observed_natal_path.professional_expression}。${source.observed_natal_path.public_limit}`,
  });

  const pathNodeCopy = {
    "node-stem-day-jia": ["甲木 · 观察链起点", "在当前 Scene 中，甲木是这条结构观察链的来源端。"],
    "node-stem-month-ding": ["丁火 · 转化节点", "在当前 Scene 中，丁火承接甲木，并继续作用于庚金。"],
    "node-stem-year-geng": ["庚金 · 结构边界", "在当前 Scene 中，庚金是这条观察链所作用的结构边界。"],
  };
  Object.entries(pathNodeCopy).forEach(([ref, [label, summary]]) => index.set(ref, {label, summary}));
  index.set("relation-jia-generates-ding", {
    label: "甲木生丁火",
    summary: "这是当前观察链的第一段确定性五行关系：甲木生丁火。",
  });
  index.set("relation-ding-controls-geng", {
    label: "丁火作用于庚金",
    summary: "这是当前观察链的第二段确定性五行关系：丁火进一步作用于庚金。",
  });

  source.chart.semantic_slots.forEach((slot) => {
    index.set(slot.slot_ref, {
      label: `${slot.label} · ${slot.pillar}`,
      summary: `这是正式原局中的${slot.label}，当前页面只呈现 Scene Source 已提供的命盘事实。`,
    });
  });

  source.structural_tensions.forEach((relation) => {
    index.set(relation.relation_ref, {
      label: relation.public_label,
      summary: `这条${relation.public_label}来自正式原局关系，当前状态为 ${relation.epistemic_status}。`,
    });
    index.set(relation.from_ref, index.get(relation.from_ref) || {label: "辰 · 结构节点", summary: `该节点参与${relation.public_label}。`});
    index.set(relation.to_ref, index.get(relation.to_ref) || {label: "戌 · 结构节点", summary: `该节点参与${relation.public_label}。`});
  });

  source.temporal_stages.forEach((stage, stageIndex) => {
    const label = stageIndex === 0 ? "大运" : "流年";
    index.set(stage.temporal_ref, {label: `${label} · ${stage.pillar}`, summary: stage.explanation});
    index.set(stage.pillar_slot_ref, {label: `${label} · ${stage.pillar}`, summary: stage.explanation});
    stage.display_node_refs.forEach((ref, nodeIndex) => index.set(ref, {
      label: `${stage.pillar[nodeIndex]} · ${label}节点`,
      summary: stage.explanation,
    }));
    stage.relation_refs.forEach((ref) => index.set(ref, {
      label: stage.display_label,
      summary: stage.explanation,
    }));
  });
  selectionIndex = index;
  workspace.dataset.selectionCount = String(index.size);
  workspace.dataset.jiaSelectionKnown = String(index.has("node-stem-day-jia"));
}

function currentSelection() {
  return selectionIndex.get(state.selectedRef) || selectionIndex.get(source.observed_natal_path.path_ref);
}

window.getLifeScriptWorkspaceState = () => ({
  ...state,
  selection: currentSelection(),
  knownSelection: selectionIndex.has(state.selectedRef),
});

function currentStage() {
  return stageFor(source, state.stage);
}

function isPillarPresent(index) {
  if (index < 4) return true;
  if (index === 4) return state.stage !== "original";
  return state.stage === "year";
}

function pillarMarkup(slot, index) {
  const stem = slot.pillar[0];
  const branch = slot.pillar[1];
  const stemMeta = ELEMENT_META[stem];
  const branchMeta = ELEMENT_META[branch];
  const present = isPillarPresent(index);
  const status = index < 4 ? "正式原局" : present ? "时间进入" : "尚未进入";
  const stemRef = nodeRefFor(slot, "stem");
  const branchRef = nodeRefFor(slot, "branch");
  return `
    <article class="pillar" data-slot-ref="${escapeHtml(slot.slot_ref)}" data-temporal="${slot.temporal}" data-present="${present}" data-entering="${index >= 4 && present}">
      <div class="pillar-label"><span>${escapeHtml(slot.label)}</span><small>${status}</small></div>
      <button class="pillar-node" type="button" data-select-ref="${escapeHtml(stemRef)}" data-element="${stemMeta.element}" data-polarity="${stemMeta.polarity}" aria-pressed="${state.selectedRef === stemRef}">
        <span class="glyph">${stem}</span><small>${polarityName(stemMeta.polarity)}${elementName(stemMeta.element)}</small>
      </button>
      <span class="pillar-axis" aria-hidden="true"></span>
      <button class="pillar-node" type="button" data-select-ref="${escapeHtml(branchRef)}" data-element="${branchMeta.element}" data-polarity="${branchMeta.polarity}" aria-pressed="${state.selectedRef === branchRef}">
        <span class="glyph">${branch}</span><small>${polarityName(branchMeta.polarity)}${elementName(branchMeta.element)}</small>
      </button>
      <span class="pillar-foot">${slot.temporal ? "时间变量" : "原局语义槽"}</span>
    </article>`;
}

function relationBoardMarkup() {
  const stage = currentStage();
  const luck = source.temporal_stages[0];
  const annual = source.temporal_stages[1];
  const stageTitle = state.stage === "original" ? source.observed_natal_path.public_label : (state.stage === "luck" ? luck.display_label : annual.display_label);
  const explanation = state.stage === "original" ? source.observed_natal_path.public_limit : (state.stage === "luck" ? luck.explanation : annual.explanation);
  const edgeClass = state.stage === "luck" ? "is-soft" : state.stage === "year" ? "is-supported" : "";
  return `
    <div class="relation-board">
      <div class="observed-path-row" data-select-ref="${escapeHtml(source.observed_natal_path.path_ref)}" tabindex="0" role="button">
        <button type="button" class="path-glyph" data-select-ref="node-stem-day-jia" data-element="wood" data-polarity="yang">甲</button>
        <button type="button" class="relation-edge ${edgeClass}" data-select-ref="relation-jia-generates-ding"><span>生</span></button>
        <button type="button" class="path-glyph" data-select-ref="node-stem-month-ding" data-element="fire" data-polarity="yin">丁</button>
        <button type="button" class="relation-edge ${edgeClass}" data-select-ref="relation-ding-controls-geng"><span>作用</span></button>
        <button type="button" class="path-glyph" data-select-ref="node-stem-year-geng" data-element="metal" data-polarity="yang">庚</button>
      </div>
      <div class="stage-fact">
        <span>${escapeHtml(stage.label)} · Scene Source</span>
        <strong>${escapeHtml(stageTitle)}</strong>
        <p>${escapeHtml(explanation)}</p>
      </div>
    </div>`;
}

function canvasMarkup() {
  return `<div class="pillar-grid">${pillars.map(pillarMarkup).join("")}</div>${relationBoardMarkup()}`;
}

function renderCanvases() {
  onecanvasScene.innerHTML = canvasMarkup();
  labChart.innerHTML = `<div class="pillar-grid">${pillars.map(pillarMarkup).join("")}</div>`;
  syncSelectedPresentation();
}

function syncSelectedPresentation() {
  const selection = currentSelection();
  document.querySelectorAll("[data-selected-label]").forEach((node) => { node.textContent = selection.label; });
  document.querySelectorAll("[data-selected-summary]").forEach((node) => { node.textContent = selection.summary; });
  document.querySelectorAll("[data-select-ref]").forEach((node) => {
    const selected = node.dataset.selectRef === state.selectedRef;
    node.classList.toggle("is-selected-semantic", selected);
    if (node.matches("button")) node.setAttribute("aria-pressed", String(selected));
  });
  abuSelection.textContent = selection.label;
  abuMessage.textContent = selection.summary;
  syncXiangfa();
}

function syncStagePresentation() {
  const stage = currentStage();
  workspace.dataset.stage = state.stage;
  document.querySelectorAll("[data-stage-target]").forEach((button) => {
    const active = button.dataset.stageTarget === state.stage;
    button.setAttribute("aria-pressed", String(active));
    button.classList.toggle("is-active", active);
  });
  overviewTimeTitle.textContent = stage.label;
  overviewTimeCopy.textContent = stage.shortLabel;
  theaterStageCopy.textContent = stage.shortLabel;
  abuMode.textContent = `${MODE_LABELS[state.mode]} · ${stage.label}`;
  renderCanvases();
  syncXiangfa();
}

function setStage(stage) {
  if (!STAGES.includes(stage) || state.stage === stage) return;
  state.stage = stage;
  syncStagePresentation();
}

function setMode(mode) {
  if (!MODES.includes(mode)) return;
  if (mode === "lab" && !PROFESSIONAL_ROLES.has(state.role)) mode = "overview";
  state.mode = mode;
  workspace.dataset.mode = mode;
  document.querySelectorAll("[data-mode-target]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.modeTarget === mode));
  });
  document.querySelectorAll("[data-mode-panel]").forEach((panel) => {
    const active = panel.dataset.modePanel === mode;
    panel.hidden = !active;
    panel.classList.toggle("is-active", active);
  });
  abuMode.textContent = `${MODE_LABELS[mode]} · ${currentStage().label}`;
  syncSelectedPresentation();
}

function setRole(role) {
  state.role = role;
  workspace.dataset.role = role;
  const professional = PROFESSIONAL_ROLES.has(role);
  document.querySelectorAll('[data-mode-target="lab"]').forEach((button) => { button.hidden = !professional; });
  labGate.hidden = professional;
  labWorkspace.hidden = !professional;
  if (!professional && state.mode === "lab") setMode("overview");
}

function setSelection(ref, {openAbu = false} = {}) {
  if (!selectionIndex.has(ref)) return;
  state.selectedRef = ref;
  syncSelectedPresentation();
  if (openAbu) setAbu(true);
}

function setAbu(open) {
  state.abuOpen = Boolean(open);
  workspace.dataset.abu = open ? "open" : "peek";
  abuSheet.hidden = !open;
  abuToggle.setAttribute("aria-expanded", String(open));
  if (open) abuClose.focus({preventScroll: true});
}

function setVariant(variant) {
  state.sandboxVariant = variant;
  workspace.dataset.variant = variant;
  document.querySelectorAll("[data-variant]").forEach((button) => button.classList.toggle("is-active", button.dataset.variant === variant));
  const copy = variant === "formal"
    ? "正式盘保持只读。这里的任何比较都不会写入 LifeCase。"
    : "实验 A 是本地展示状态；它不会成为正式命盘，也不会改变当前 Scene Source。";
  abuPeek.textContent = copy;
}

function syncXiangfa() {
  if (!xiangfaReady || !xiangfaFrame.contentWindow) return;
  xiangfaFrame.contentWindow.postMessage({
    type: "deepbazi:xiangfa-state",
    stage: state.stage,
    mode: "xiangfa",
    selectedRef: state.selectedRef,
  }, location.origin);
}

function openTheater() {
  const url = new URL("../../internal-tools/abu-says-mingli-s0-v12/index.html", location.href);
  url.hash = `t=${THEATER_TIME[state.stage]}`;
  window.open(url.href, "_blank", "noopener");
}

function createIcons() {
  if (window.lucide?.createIcons) window.lucide.createIcons();
}

document.addEventListener("click", (event) => {
  const modeButton = event.target.closest("[data-mode-target]");
  if (modeButton) {
    setMode(modeButton.dataset.modeTarget);
    return;
  }
  const stageButton = event.target.closest("[data-stage-target]");
  if (stageButton) {
    setStage(stageButton.dataset.stageTarget);
    return;
  }
  const openAbu = event.target.closest("[data-open-abu]");
  if (openAbu) setAbu(true);
  const variant = event.target.closest("[data-variant]");
  if (variant) setVariant(variant.dataset.variant);
});

document.addEventListener("click", (event) => {
  const selectButton = event.target.closest?.("[data-select-ref]");
  if (selectButton) setSelection(selectButton.dataset.selectRef);
}, {capture: true});

document.addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && event.target.matches('[role="button"][data-select-ref]')) {
    event.preventDefault();
    setSelection(event.target.dataset.selectRef);
  }
  if (event.key === "Escape" && state.abuOpen) setAbu(false);
});

roleSelect.addEventListener("change", () => setRole(roleSelect.value));
abuToggle.addEventListener("click", () => setAbu(!state.abuOpen));
abuClose.addEventListener("click", () => setAbu(false));
document.querySelector("#overviewAskAbu").addEventListener("click", () => setAbu(true));
document.querySelector("#openTheater").addEventListener("click", openTheater);
document.querySelector("#addVariant").addEventListener("click", () => setVariant("experiment"));

document.querySelectorAll("[data-abu-action]").forEach((button) => button.addEventListener("click", () => {
  if (button.dataset.abuAction === "locate") setMode("onecanvas");
  if (button.dataset.abuAction === "time") setMode("theater");
  setAbu(false);
}));

xiangfaFrame.addEventListener("load", () => {
  xiangfaReady = true;
  syncXiangfa();
});

window.addEventListener("message", (event) => {
  if (event.data?.type?.startsWith?.("deepbazi:xiangfa")) {
    workspace.dataset.lastXiangfaMessage = `${event.data.type}:${event.data.interaction || ""}:${event.data.value || ""}`;
    workspace.dataset.lastXiangfaSourceMatch = String(event.source === xiangfaFrame.contentWindow);
  }
  if (event.origin !== location.origin || event.source !== xiangfaFrame.contentWindow) return;
  if (event.data?.type === "deepbazi:xiangfa-ready") {
    xiangfaReady = true;
    syncXiangfa();
  }
  if (event.data?.type === "deepbazi:xiangfa-engaged") {
    if (event.data.interaction === "stage" && STAGES.includes(event.data.value)) setStage(event.data.value);
    if (event.data.interaction === "hotspot" && selectionIndex.has(event.data.value)) setSelection(event.data.value);
  }
});

async function init() {
  try {
    const payload = await loadScene();
    source = payload.source;
    pillars = scenePillars(source);
    buildSelectionIndex();
    document.querySelector("#caseMeta").textContent = `${source.chart.chart_type} · ${source.chart.semantic_slots.map((slot) => slot.pillar).join(" ")}`;
    document.querySelector("#overviewPathText").textContent = `${source.observed_natal_path.professional_expression}。`;
    setRole(state.role);
    syncStagePresentation();
    setMode(state.mode);
    createIcons();
  } catch (error) {
    onecanvasScene.innerHTML = '<div class="lab-gate"><h2>Scene Source 暂时不可用</h2><p>请通过 DeepBazi 本地 HTTP 服务打开本页。</p></div>';
    document.querySelector("#caseMeta").textContent = "场景载入失败";
    console.error(error);
  }
}

init();
