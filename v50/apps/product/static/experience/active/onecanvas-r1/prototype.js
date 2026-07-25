import {
  GENDER_LABELS,
  RELATION_LABELS,
  SLOT_LABELS,
  SLOT_ORDER,
  TEN_GOD_LABELS,
  cloneSnapshot,
  compileOneCanvasCues,
  createOneCanvasModel,
  recomputeViewModel,
} from "./onecanvas-runtime.js";
import {
  renderBranchNode,
  renderAnnualYearSelect,
  renderLuckObservation,
  renderOneCanvasStage,
  renderPillarSlot,
  renderStemNode,
  renderTargetResolution,
  renderTemporalNode,
  renderUndoRedoControl,
} from "./onecanvas-components.js";

const root = document.querySelector("#oneCanvasRoot");
if (!root) throw new Error("onecanvas_root_missing");

let model = null;
let playTimer = null;
let toastTimer = null;
let structuralRequestSerial = 0;
let pillarEditSessionSerial = 0;
let pillarEditExitTimer = null;

const state = {
  snapshot: null,
  selectedKey: "",
  lens: null,
  preview: null,
  history: [],
  future: [],
  drawMode: false,
  saved: { a: null, b: null },
  compareActive: false,
  compareRatio: 0,
  expressionRatio: 0,
  playCueIndex: -1,
  playing: false,
  temporalStage: 2,
  playSource: "system",
  pillarEdit: null,
  pendingAnnualYear: null,
  targetResolution: null,
  compiling: false,
  toast: "",
};

boot();

async function boot() {
  try {
    const response = await fetch("./fixture.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`fixture_http_${response.status}`);
    const fixture = await response.json();
    model = createOneCanvasModel(fixture);
    if (fixture.selection_catalogs) model.setSelectionCatalog(fixture.selection_catalogs);
    try {
      const catalogResponse = await fetch("/api/v50/experience/onecanvas/selection-catalog", {
        cache: "no-store",
        credentials: "same-origin",
      });
      if (!catalogResponse.ok) throw new Error(`selection_catalog_http_${catalogResponse.status}`);
      const catalogPayload = await catalogResponse.json();
      model.setSelectionCatalog(catalogPayload.catalog);
    } catch (error) {
      if (!fixture.selection_catalogs) throw error;
    }
    state.snapshot = formalSnapshot();
    render();
    bindEvents();
    await openReviewTargetIfRequested();
  } catch (error) {
    root.innerHTML = `<div class="fatal-state"><strong>六柱合同未能载入</strong><p>${escapeHtml(String(error))}</p></div>`;
  }
}

function bindEvents() {
  root.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target.closest("[data-action]") : null;
    if (!target) return;
    handleAction(target.dataset.action || "", target);
  });
  root.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (target.dataset.action === "compare-ratio") {
      state.compareRatio = Number(target.value);
      render();
      return;
    }
    if (target.dataset.action === "expression-ratio") {
      state.expressionRatio = Number(target.value);
      updateExpressionPresentation();
      return;
    }
  });
  root.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLSelectElement)) return;
    if (target.dataset.action === "birth-year-anchor") {
      const year = Number(target.value);
      if (Number.isInteger(year)) selectBirthYearAnchor(year);
      return;
    }
    if (target.dataset.action === "annual-year-select") {
      const year = Number(target.value);
      if (Number.isInteger(year)) selectAnnualYear(year);
    }
  });
  root.addEventListener("pointermove", (event) => {
    if (!state.pillarEdit || event.pointerType === "touch") return;
    const pillar = event.target instanceof Element
      ? event.target.closest(".pillar-column")
      : null;
    if (pillar?.dataset.slot === state.pillarEdit.slot) return cancelPillarEditExit();
    schedulePillarEditExit(event.clientX, event.clientY);
  });
  root.addEventListener("pointerleave", (event) => {
    if (state.pillarEdit && event.pointerType !== "touch") {
      schedulePillarEditExit(event.clientX, event.clientY);
    }
  });
  root.addEventListener("pointerdown", (event) => {
    if (!state.pillarEdit || !(event.target instanceof Element)) return;
    const activePillar = root.querySelector(`.pillar-column[data-slot="${state.pillarEdit.slot}"]`);
    if (activePillar && !activePillar.contains(event.target)) {
      schedulePillarEditExit(event.clientX, event.clientY);
    }
  });
  root.addEventListener("focusin", (event) => {
    if (!state.pillarEdit) return;
    const focusedPillar = event.target instanceof Element
      ? event.target.closest(".pillar-column")
      : null;
    if (focusedPillar?.dataset.slot === state.pillarEdit.slot) return cancelPillarEditExit();
    schedulePillarEditExit(Number.NaN, Number.NaN);
  });
  root.addEventListener("keydown", (event) => {
    if (state.pillarEdit && event.key === "Escape") {
      event.preventDefault();
      endPillarEditSession();
      return;
    }
    if (state.drawMode && (event.key === "Enter" || event.key === "Escape")) {
      event.preventDefault();
      finishDraftPath();
      return;
    }
  });
}

function handleAction(action, target) {
  if (action === "gender-select") return selectGender(target.dataset.gender || "unknown");
  if (action === "open-luck") return openLuckLens();
  if (action === "formal") return loadFormal();
  if (action === "undo") return undo();
  if (action === "redo") return redo();
  if (action === "reset") return resetExperiment();
  if (action === "close-lens") return closeLensAndRender();
  if (action === "select-node") return selectNode(target.dataset.nodeKey || "");
  if (action === "step-independent-pillar") return stepIndependentPillar(target.dataset.nodeKey || "", Number(target.dataset.direction));
  if (action === "step-dependent-pillar") return stepDependentPillar(target.dataset.nodeKey || "", Number(target.dataset.direction));
  if (action === "step-luck") return stepLuck(Number(target.dataset.direction));
  if (action === "draw-path") return toggleDrawMode();
  if (action === "finish-path") return finishDraftPath();
  if (action === "clear-draft") return clearDraft();
  if (action === "save-a") return saveSnapshot("a");
  if (action === "save-b") return saveSnapshot("b");
  if (action === "compare") return toggleCompare();
  if (action === "play") return playPath();
  if (action === "pause-play") return pausePlayback(true);
  if (action === "play-source-system") return setPlaySource("system");
  if (action === "play-source-draft") return setPlaySource("draft");
  if (action === "luck-observe") return observeLuck(Number(target.dataset.index));
  if (action === "select-target-variant") return selectTargetVariant(target.dataset.variantRef || "");
  if (action === "release-target-constraint") return releaseTargetConstraint(target.dataset.constraintPath || "");
  if (action === "cancel-target-resolution") return cancelTargetResolution();
}

function formalSnapshot() {
  return {
    mode: "formal",
    axis: "day",
    index: model ? model.fixture.baseline_candidate_index.day : 0,
    yearIndex: model ? model.officialYearIndex : 0,
    analysisYear: model ? model.fixture.formal.analysis_year : null,
    luckIndex: null,
    gender: model ? model.fixture.structural_context?.gender || "unknown" : "unknown",
    birthYearHint: model && Number.isInteger(model.fixture.structural_context?.birth_year_hint)
      ? model.fixture.structural_context.birth_year_hint
      : null,
    targetDraftId: "",
    constraintResolution: null,
    variant: null,
    draftNodes: [],
  };
}

function experimentSnapshot() {
  const base = formalSnapshot();
  base.mode = "experiment";
  return base;
}

function createExperiment() {
  structuralRequestSerial += 1;
  state.compiling = false;
  state.pendingAnnualYear = null;
  stopPlayback();
  if (state.snapshot.mode === "formal") {
    state.snapshot = experimentSnapshot();
    state.history = [];
    state.future = [];
  }
  state.compareActive = false;
  state.selectedKey = "";
  state.drawMode = false;
  state.lens = null;
  state.preview = null;
  state.pillarEdit = null;
  state.targetResolution = null;
  notify(state.snapshot.gender === "unknown"
    ? "实验副本已建立；请先确认乾造或坤造"
    : "实验副本已建立；正式命盘保持不变");
  render();
}

async function selectGender(gender) {
  if (!Object.hasOwn(GENDER_LABELS, gender) || gender === "unknown" || state.compiling) return;
  const nextSnapshot = state.snapshot.mode === "formal"
    ? experimentSnapshot()
    : cloneSnapshot(state.snapshot);
  if (nextSnapshot.gender === gender && nextSnapshot.variant?.timing_recalculation?.luck_sequence?.length) {
    return notify(`${GENDER_LABELS[gender]}已经确认`);
  }
  const selectedPillars = model.variantFor(nextSnapshot).pillars;
  const requestSerial = ++structuralRequestSerial;
  state.pendingAnnualYear = null;
  state.compiling = true;
  notify(`正在按${GENDER_LABELS[gender]}重新推算大运`);
  render();
  try {
    const payload = await requestTargetCompile(selectedPillars, nextSnapshot, { gender });
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    mutate(() => {
      nextSnapshot.gender = gender;
      nextSnapshot.variant = payload.variant;
      nextSnapshot.targetDraftId = payload.resolution.target_draft_id;
      nextSnapshot.constraintResolution = payload.resolution;
      nextSnapshot.birthYearHint = payload.resolution.cycle_year_anchor;
      nextSnapshot.luckIndex = null;
      nextSnapshot.draftNodes = [];
      state.snapshot = nextSnapshot;
      state.drawMode = false;
      state.pillarEdit = null;
      closeLens();
    }, `${GENDER_LABELS[gender]}已确认；大运顺逆与序列已重新推算`);
  } catch (error) {
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    notify(`命造重算失败：${String(error).replace(/^Error:\s*/, "")}`);
    render();
  }
}

async function selectBirthYearAnchor(year) {
  if (!Number.isInteger(year) || state.compiling) return;
  const workingSnapshot = state.snapshot.mode === "formal"
    ? experimentSnapshot()
    : cloneSnapshot(state.snapshot);
  const variant = model.variantFor(workingSnapshot);
  const yearPillar = variant.pillars[0];
  const allowedYears = model.cycleYearChoicesForPillar(
    yearPillar,
    model.fixture.formal.analysis_year,
  );
  if (!allowedYears.includes(year)) {
    notify(`${year} 年与当前年柱 ${yearPillar} 不一致`);
    render();
    return;
  }
  structuralRequestSerial += 1;
  state.pendingAnnualYear = null;
  workingSnapshot.mode = "experiment";
  workingSnapshot.birthYearHint = year;
  workingSnapshot.luckIndex = null;
  workingSnapshot.draftNodes = [];

  if (workingSnapshot.gender === "unknown") {
    mutate(() => {
      state.snapshot = workingSnapshot;
      state.drawMode = false;
      state.lens = null;
      state.preview = null;
      state.pillarEdit = null;
    }, `${year} 年已与 ${yearPillar} 绑定；确认乾造或坤造后定位大运`);
    return;
  }

  state.compiling = true;
  const requestSerial = structuralRequestSerial;
  notify(`${year} 年正在与完整四柱反查`);
  render();
  try {
    const payload = await requestTargetCompile(variant.pillars, workingSnapshot, {
      cycleYearAnchor: year,
    });
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    mutate(() => {
      workingSnapshot.variant = payload.variant;
      workingSnapshot.targetDraftId = payload.resolution.target_draft_id;
      workingSnapshot.constraintResolution = payload.resolution;
      workingSnapshot.birthYearHint = payload.resolution.cycle_year_anchor;
      state.snapshot = workingSnapshot;
      state.drawMode = false;
      state.lens = null;
      state.preview = null;
      state.pillarEdit = null;
    }, `${year} 年已锚定；${timingMessage(payload.variant)}`);
  } catch (error) {
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    notify(`出生年份锚定失败：${String(error).replace(/^Error:\s*/, "")}`);
    render();
  }
}

function loadFormal() {
  structuralRequestSerial += 1;
  state.compiling = false;
  stopPlayback();
  state.snapshot = formalSnapshot();
  state.selectedKey = "";
  state.lens = null;
  state.preview = null;
  state.history = [];
  state.future = [];
  state.drawMode = false;
  state.compareActive = false;
  state.playCueIndex = -1;
  state.playing = false;
  state.temporalStage = 2;
  state.playSource = "system";
  state.pillarEdit = null;
  state.pendingAnnualYear = null;
  state.targetResolution = null;
  render();
}

function currentRenderSnapshot() {
  if (state.compareActive && state.saved.a && state.saved.b) {
    return state.compareRatio < 50 ? state.saved.a : state.saved.b;
  }
  return state.snapshot;
}

function selectNode(key) {
  pausePlayback(true);
  if (state.drawMode) return addDraftNode(key);
  if (state.pillarEdit && !key.startsWith(`${state.pillarEdit.slot}_`)) {
    state.pillarEdit = null;
  }
  state.selectedKey = key;
  state.preview = null;
  state.lens = null;
  render();
}

function stepIndependentPillar(key, direction) {
  if (!/^(year|day)_(stem|branch)$/.test(key) || ![-1, 1].includes(direction) || state.compiling) return;
  const slot = key.split("_")[0];
  const workingSnapshot = state.snapshot.mode === "formal"
    ? experimentSnapshot()
    : cloneSnapshot(state.snapshot);
  const activeSession = state.pillarEdit?.slot === slot ? state.pillarEdit : null;
  const nextSession = activeSession
    ? model.stepPillarEditSession(activeSession, key, direction)
    : model.beginPillarEditSession(workingSnapshot, key, direction);
  const pillarEdit = {
    ...nextSession,
    sessionId: activeSession?.sessionId || `pillar-edit:${++pillarEditSessionSerial}`,
  };
  state.pillarEdit = pillarEdit;
  state.selectedKey = key;
  state.lens = null;
  state.preview = null;
  return applyPillarEditSession(pillarEdit, key, workingSnapshot);
}

function endPillarEditSession() {
  if (!state.pillarEdit) return;
  cancelPillarEditExit();
  const slot = state.pillarEdit.slot;
  state.pillarEdit = null;
  if (state.selectedKey.startsWith(`${slot}_`) && !state.drawMode) state.selectedKey = "";
  render();
}

function schedulePillarEditExit(clientX, clientY) {
  cancelPillarEditExit();
  pillarEditExitTimer = window.setTimeout(() => {
    pillarEditExitTimer = null;
    if (!state.pillarEdit) return;
    const target = Number.isFinite(clientX) && Number.isFinite(clientY)
      ? document.elementFromPoint(clientX, clientY)
      : document.activeElement;
    const pillar = target instanceof Element ? target.closest(".pillar-column") : null;
    if (pillar?.dataset.slot === state.pillarEdit.slot) return;
    endPillarEditSession();
  }, 180);
}

function cancelPillarEditExit() {
  if (!pillarEditExitTimer) return;
  window.clearTimeout(pillarEditExitTimer);
  pillarEditExitTimer = null;
}

async function applyPillarEditSession(pillarEdit, key, preparedSnapshot = null) {
  const workingSnapshot = preparedSnapshot || (state.snapshot.mode === "formal"
    ? experimentSnapshot()
    : cloneSnapshot(state.snapshot));
  const selectedPillars = [...model.variantFor(workingSnapshot).pillars];
  const axis = pillarEdit.slot;
  selectedPillars[axis === "year" ? 0 : 2] = pillarEdit.previewPillar;
  return compileVisibleTarget({
    key,
    axis,
    selectedPillars,
    workingSnapshot,
    preservePillarEdit: pillarEdit,
  });
}

function stepDependentPillar(nodeKey, direction) {
  const match = /^(month|hour)_(stem|branch)$/.exec(nodeKey || "");
  if (!match || ![-1, 1].includes(direction) || state.compiling) return;
  const axis = match[1];
  const options = model.dependentPillarOptions(axis, state.snapshot);
  if (!options.length) return;
  const variant = model.variantFor(state.snapshot);
  const current = variant.pillars[axis === "month" ? 1 : 3];
  const currentIndex = Math.max(0, options.indexOf(current));
  const pillar = options[(currentIndex + direction + options.length) % options.length];
  return selectDependentPillar(axis, pillar, nodeKey);
}

async function selectDependentPillar(axis, pillar, selectedKey = `${axis}_stem`) {
  if (!["month", "hour"].includes(axis) || state.compiling) return;
  const workingSnapshot = state.snapshot.mode === "formal"
    ? experimentSnapshot()
    : cloneSnapshot(state.snapshot);
  if (!model.dependentPillarOptions(axis, workingSnapshot).includes(pillar)) return;
  const selectedPillars = [...model.variantFor(workingSnapshot).pillars];
  selectedPillars[axis === "month" ? 1 : 3] = pillar;
  return compileVisibleTarget({
    key: selectedKey,
    axis,
    selectedPillars,
    workingSnapshot,
  });
}

async function compileVisibleTarget({
  key,
  axis,
  selectedPillars,
  workingSnapshot,
  preservePillarEdit = null,
}) {
  const requestSerial = ++structuralRequestSerial;
  state.pendingAnnualYear = null;
  state.compiling = true;
  state.selectedKey = key;
  state.pillarEdit = preservePillarEdit;
  render();
  try {
    const payload = await requestTargetCompile(selectedPillars, workingSnapshot);
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    if (!payload.variant) {
      holdTargetResolution(payload, {
        workingSnapshot,
        key,
        axis,
        preservePillarEdit,
      });
      return;
    }
    mutate(() => {
      workingSnapshot.mode = "experiment";
      workingSnapshot.axis = axis;
      workingSnapshot.variant = payload.variant;
      workingSnapshot.targetDraftId = payload.resolution.target_draft_id;
      workingSnapshot.constraintResolution = payload.resolution;
      workingSnapshot.birthYearHint = payload.resolution.cycle_year_anchor;
      workingSnapshot.luckIndex = null;
      workingSnapshot.draftNodes = [];
      state.snapshot = workingSnapshot;
      state.drawMode = false;
      state.selectedKey = key;
      state.lens = null;
      state.preview = null;
      state.pillarEdit = preservePillarEdit?.sessionId
        && state.pillarEdit?.sessionId === preservePillarEdit.sessionId
        ? preservePillarEdit
        : null;
    }, null);
    if (preservePillarEdit?.sessionId && state.pillarEdit?.sessionId === preservePillarEdit.sessionId) {
      window.requestAnimationFrame(() => {
        root.querySelector(`button.node[data-node-key="${key}"]`)?.focus({ preventScroll: true });
      });
    }
  } catch (error) {
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    if (!preservePillarEdit?.sessionId || state.pillarEdit?.sessionId === preservePillarEdit.sessionId) {
      state.pillarEdit = null;
    }
    notify(`结构重算失败：${String(error).replace(/^Error:\s*/, "")}`);
    render();
  }
}

async function requestTargetCompile(selectedPillars, snapshot, overrides = {}) {
  const response = await fetch("/api/v50/experience/onecanvas/target-compile", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(model.targetCompileRequest(selectedPillars, snapshot, overrides)),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `target_compile_http_${response.status}`);
  return payload;
}

function holdTargetResolution(payload, flow = {}) {
  state.compiling = false;
  state.targetResolution = {
    resolution: payload.resolution || {},
    targetDraft: payload.resolution?.target_draft || flow.targetDraft || {},
    targetDraftId: payload.resolution?.target_draft_id || flow.targetDraftId || "",
    workingSnapshot: cloneSnapshot(flow.workingSnapshot || state.snapshot),
    key: flow.key || "",
    axis: flow.axis || "day",
  };
  state.pillarEdit = null;
  state.lens = null;
  render();
  window.requestAnimationFrame(() => {
    root.querySelector(".target-resolution-dialog")?.focus({ preventScroll: true });
  });
}

async function selectTargetVariant(variantRef) {
  if (!variantRef || !state.targetResolution || state.compiling) return;
  await resolveTargetFlow(state.targetResolution, { selectedVariantId: variantRef });
}

async function releaseTargetConstraint(path) {
  if (!state.targetResolution || state.compiling) return;
  const [slot, field] = String(path || "").split(".");
  if (!["year", "month", "day", "hour"].includes(slot)
      || !["pillar", "stem", "branch"].includes(field)) return;
  const targetDraft = cloneTargetDraft(state.targetResolution.targetDraft);
  targetDraft[slot][field] = "";
  await resolveTargetFlow({
    ...state.targetResolution,
    targetDraft,
  });
}

async function resolveTargetFlow(flow, { selectedVariantId = "" } = {}) {
  const requestSerial = ++structuralRequestSerial;
  state.compiling = true;
  render();
  try {
    const payload = await requestTargetCompile(null, flow.workingSnapshot, {
      targetDraft: flow.targetDraft,
      targetDraftId: flow.targetDraftId,
      selectedVariantId,
    });
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    if (!payload.variant) {
      holdTargetResolution(payload, flow);
      return;
    }
    const workingSnapshot = cloneSnapshot(flow.workingSnapshot);
    mutate(() => {
      workingSnapshot.mode = "experiment";
      workingSnapshot.axis = flow.axis || "day";
      workingSnapshot.variant = payload.variant;
      workingSnapshot.targetDraftId = payload.resolution.target_draft_id;
      workingSnapshot.constraintResolution = payload.resolution;
      workingSnapshot.birthYearHint = payload.resolution.cycle_year_anchor;
      workingSnapshot.luckIndex = null;
      workingSnapshot.draftNodes = [];
      state.snapshot = workingSnapshot;
      state.targetResolution = null;
      state.drawMode = false;
      state.selectedKey = flow.key || "";
      state.lens = null;
      state.preview = null;
      state.pillarEdit = null;
    }, selectedVariantId ? "完整四柱已选择；正式命盘保持不变" : "冲突条件已放开；实验命盘已更新");
  } catch (error) {
    if (requestSerial !== structuralRequestSerial) return;
    state.compiling = false;
    notify(`命盘求解失败：${String(error).replace(/^Error:\s*/, "")}`);
    render();
  }
}

function cloneTargetDraft(value = {}) {
  return Object.fromEntries(["year", "month", "day", "hour"].map((slot) => [
    slot,
    {
      pillar: String(value[slot]?.pillar || ""),
      stem: String(value[slot]?.stem || ""),
      branch: String(value[slot]?.branch || ""),
    },
  ]));
}

function cancelTargetResolution() {
  structuralRequestSerial += 1;
  state.compiling = false;
  state.targetResolution = null;
  state.pillarEdit = null;
  notify("本次选择已取消；当前命盘未改变");
  render();
}

async function openReviewTargetIfRequested() {
  const task = new URLSearchParams(window.location.search).get("r1ReviewTask");
  if (!task || !["4", "5"].includes(task)) return;
  try {
    const response = await fetch("./review-targets.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`review_targets_http_${response.status}`);
    const entry = (await response.json()).targets?.[task];
    if (!entry?.target_draft) throw new Error("review_target_missing");
    await resolveTargetFlow({
      targetDraft: cloneTargetDraft(entry.target_draft),
      targetDraftId: entry.target_draft_id || `r1-review-${Date.now()}`,
      workingSnapshot: experimentSnapshot(),
      key: "",
      axis: "day",
    });
  } catch (error) {
    notify(`审阅场景未能载入：${String(error).replace(/^Error:\s*/, "")}`);
    render();
  }
}

function cancelPreview() {
  state.preview = null;
  state.pillarEdit = null;
  state.lens = null;
  state.selectedKey = "";
  render();
}

function mutate(operation, message = "实验已更新") {
  structuralRequestSerial += 1;
  state.compiling = false;
  state.pendingAnnualYear = null;
  pausePlayback(true);
  state.history.push(cloneSnapshot(state.snapshot));
  state.future = [];
  operation();
  state.compareActive = false;
  if (message) notify(message);
  render();
}

function undo() {
  const previous = state.history.pop();
  if (!previous) return;
  structuralRequestSerial += 1;
  state.compiling = false;
  state.pendingAnnualYear = null;
  state.future.push(cloneSnapshot(state.snapshot));
  state.snapshot = previous;
  state.pillarEdit = null;
  state.targetResolution = null;
  closeLens();
  notify("已撤销上一步实验");
  render();
}

function redo() {
  const next = state.future.pop();
  if (!next) return;
  structuralRequestSerial += 1;
  state.compiling = false;
  state.pendingAnnualYear = null;
  state.history.push(cloneSnapshot(state.snapshot));
  state.snapshot = next;
  state.pillarEdit = null;
  state.targetResolution = null;
  closeLens();
  notify("已恢复下一步实验");
  render();
}

function resetExperiment() {
  if (state.snapshot.mode === "formal") return;
  mutate(() => {
    state.snapshot = experimentSnapshot();
    state.pillarEdit = null;
    state.targetResolution = null;
    closeLens();
  }, "实验已恢复到正式盘基线");
}

function toggleDrawMode() {
  if (state.snapshot.mode === "formal") {
    createExperiment();
    state.drawMode = true;
    notify("已进入连线模式；请选择起点");
    render();
    return;
  }
  if (state.drawMode) return finishDraftPath();
  state.drawMode = true;
  state.lens = null;
  state.selectedKey = "";
  notify(state.snapshot.draftNodes.length
    ? "从当前终点继续连线；再点终点或按 Enter 完成"
    : "请选择起点，再依次点击节点；再点终点即可完成");
  render();
}

function addDraftNode(key) {
  if (state.snapshot.draftNodes.at(-1) === key) {
    if (state.snapshot.draftNodes.length >= 2) finishDraftPath();
    return;
  }
  mutate(() => {
    const draft = [...state.snapshot.draftNodes, key];
    state.snapshot.draftNodes = draft.slice(-6);
  }, draftFeedback(key));
}

function finishDraftPath() {
  if (!state.drawMode) return;
  state.drawMode = false;
  state.selectedKey = "";
  state.lens = null;
  if (state.snapshot.draftNodes.length < 2) {
    state.snapshot.draftNodes = [];
    notify("尚未形成连线，已退出画线模式");
  } else {
    notify("路径草稿已完成；需要时可点击“继续画线”追加节点");
  }
  render();
}

function draftFeedback(nextKey) {
  const previous = state.snapshot.draftNodes.at(-1);
  if (!previous) return "已选起点；继续选择下一节点";
  const result = model.relationBetween(state.snapshot, previous, nextKey);
  if (result.status === "available") return `${result.relation.label} · 正向关系存在；继续点节点，或再点终点完成`;
  if (result.status === "reverse") return `${result.relation.label} · 关系存在但方向相反；继续点节点，或再点终点完成`;
  return "当前没有可用关系，该段以断点保留；继续点节点，或再点终点完成";
}

function clearDraft() {
  if (!state.snapshot.draftNodes.length) return;
  mutate(() => { state.snapshot.draftNodes = []; }, "用户路径已清空");
}

function saveSnapshot(slot) {
  if (state.snapshot.mode === "formal") return notify("先建立实验，再保存 A/B");
  state.saved[slot] = cloneSnapshot(state.snapshot);
  notify(`实验 ${slot.toUpperCase()} 已保存`);
  render();
}

function toggleCompare() {
  if (!state.saved.a || !state.saved.b) return notify("请先分别保存实验 A 和 B");
  pausePlayback(true);
  state.compareActive = !state.compareActive;
  state.preview = null;
  state.lens = null;
  state.selectedKey = "";
  state.drawMode = false;
  render();
}

async function selectAnnualYear(year) {
  if (!Number.isInteger(year) || state.compiling) return;
  const allowed = model.annualObservations().some((item) => item.year === year);
  if (!allowed) return;
  const workingSnapshot = state.snapshot.mode === "formal"
    ? experimentSnapshot()
    : cloneSnapshot(state.snapshot);
  const selectedPillars = model.variantFor(workingSnapshot).pillars;
  const requestSerial = ++structuralRequestSerial;
  state.pendingAnnualYear = year;
  render();
  try {
    const payload = await requestTargetCompile(selectedPillars, workingSnapshot, { analysisYear: year });
    if (requestSerial !== structuralRequestSerial) return;
    workingSnapshot.mode = "experiment";
    workingSnapshot.analysisYear = year;
    workingSnapshot.variant = payload.variant;
    workingSnapshot.targetDraftId = payload.resolution.target_draft_id;
    workingSnapshot.constraintResolution = payload.resolution;
    workingSnapshot.birthYearHint = payload.resolution.cycle_year_anchor;
    workingSnapshot.luckIndex = null;
    state.pendingAnnualYear = null;
    mutate(() => {
      state.snapshot = workingSnapshot;
      state.selectedKey = "annual_stem";
      state.lens = null;
      state.pillarEdit = null;
    }, null);
  } catch (error) {
    if (requestSerial !== structuralRequestSerial) return;
    state.pendingAnnualYear = null;
    notify(`流年载入失败：${String(error).replace(/^Error:\s*/, "")}`);
    render();
  }
}

function stepLuck(direction) {
  if (![-1, 1].includes(direction)) return;
  const sequence = model.variantFor(state.snapshot).timing_recalculation.luck_sequence || [];
  if (!sequence.length) return notify("请先确认乾造或坤造，系统才能排出大运");
  const current = Number.isInteger(state.snapshot.luckIndex)
    ? state.snapshot.luckIndex
    : model.currentLuckIndex(state.snapshot);
  const next = current < 0
    ? direction > 0 ? 0 : sequence.length - 1
    : (current + direction + sequence.length) % sequence.length;
  observeLuck(next, true);
}

function observeLuck(index, direct = false) {
  const sequence = model.variantFor(state.snapshot).timing_recalculation.luck_sequence || [];
  if (!sequence[index]) return;
  observeTemporal(() => {
    state.snapshot.luckIndex = index;
    state.selectedKey = "luck_stem";
    state.lens = direct ? null : { type: "luck", key: "luck_stem" };
  }, `当前观察大运已切换为 ${sequence[index].pillar}；未提供的路径作用不会补写`);
}

function openLuckLens() {
  const timing = model.variantFor(state.snapshot).timing_recalculation || {};
  if (!(timing.luck_sequence || []).length) {
    return notify("请先确认乾造或坤造，系统才能排出大运顺逆序列");
  }
  pausePlayback(true);
  state.selectedKey = "";
  state.lens = { type: "luck", key: "luck_stem" };
  notify(timing.current_luck_status === "resolved" || timing.current_luck_status === "resolved_from_birth_year"
    ? `当前大运已定位为 ${timing.luck_pillar}`
    : "大运顺逆序列已排出；请选择出生年份定位当前大运");
  render();
}

function observeTemporal(operation, message) {
  pausePlayback(true);
  operation();
  notify(message);
  render();
}

function playPath() {
  if (state.playing) return pausePlayback(true);
  const cues = currentPlaybackCues();
  if (!cues.length) return notify("当前没有可播放的路径");
  if (state.playCueIndex >= cues.length - 1) state.playCueIndex = -1;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) {
    state.playCueIndex = cues.length - 1;
    state.temporalStage = cues.at(-1)?.temporal_stage ?? 2;
    state.playing = false;
    render();
    return;
  }
  state.playing = true;
  if (state.playCueIndex < 0) state.temporalStage = 0;
  advancePlayback();
}

function stopPlayback() {
  if (playTimer) window.clearTimeout(playTimer);
  playTimer = null;
  state.playCueIndex = -1;
  state.playing = false;
  state.temporalStage = 2;
}

function pausePlayback(preservePosition = true) {
  if (playTimer) window.clearTimeout(playTimer);
  playTimer = null;
  state.playing = false;
  if (!preservePosition) {
    state.playCueIndex = -1;
    state.temporalStage = 2;
  }
  render();
}

function advancePlayback() {
  const cues = currentPlaybackCues();
  if (!state.playing || !cues.length) return;
  const nextIndex = state.playCueIndex + 1;
  if (nextIndex >= cues.length) {
    state.playing = false;
    playTimer = null;
    render();
    return;
  }
  state.playCueIndex = nextIndex;
  const cue = cues[nextIndex];
  state.temporalStage = cue.temporal_stage;
  render();
  if (cue.action === "block_path") {
    state.playing = false;
    playTimer = null;
    notify("关系缺失，演时已在断点停止");
    render();
    return;
  }
  playTimer = window.setTimeout(advancePlayback, cue.action.startsWith("enter_") ? 980 : 760);
}

function setPlaySource(source) {
  pausePlayback(false);
  state.playSource = source === "draft" && state.snapshot.draftNodes.length > 1 ? "draft" : "system";
  render();
}

function closeLens() {
  state.selectedKey = "";
  state.lens = null;
  state.preview = null;
  state.pillarEdit = null;
}

function closeLensAndRender() {
  closeLens();
  render();
}

function notify(message) {
  state.toast = message;
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    state.toast = "";
    render();
  }, 3200);
}

function render() {
  const snapshot = currentRenderSnapshot();
  const variant = model.variantFor(snapshot);
  const nodes = model.nodesFor(snapshot);
  const nodeMap = new Map(nodes.map((node) => [node.node_key, node]));
  const systemPath = model.pathFor(snapshot);
  const draftSegments = model.draftSegments(snapshot, snapshot.draftNodes || []);
  const compare = compareModel();
  const xiangRatio = Math.max(0, Math.min(1, state.expressionRatio / 100));
  const expressionClass = state.expressionRatio >= 58 ? "xiang-dominant" : state.expressionRatio > 8 ? "expression-mixed" : "li-dominant";

  root.innerHTML = `
    <section class="onecanvas-shell ${expressionClass} ${state.drawMode ? "drawing" : ""} ${state.playing ? "scene-playing" : "scene-paused"}" style="--xiang-ratio:${xiangRatio};--li-ratio:${1 - xiangRatio}">
      ${renderHeader(snapshot)}
      <div class="canvas-wrap">
        ${renderCanvasHeading(snapshot, variant)}
        ${renderOneCanvasStage({
          layerMarkup: {
            background: `<div class="scene-backdrop" aria-hidden="true"></div>`,
            "structural-nodes": `<div class="pillar-grid">${SLOT_ORDER.map((slot) => renderPillar(slot, nodeMap, compare, snapshot, variant)).join("")}</div>`,
            "system-path": renderPathSvg(systemPath, draftSegments, compare),
          },
          overlay: state.targetResolution
            ? renderTargetResolution({
                resolution: state.targetResolution.resolution,
                compiling: state.compiling,
              })
            : renderLens(nodeMap, snapshot),
          extra: `${renderDrawingGuide()}${renderSceneCue()}${renderTemporalStageTrack(snapshot)}${renderCompareControl(compare)}`,
        })}
        ${renderCanvasFooter(snapshot, variant, systemPath, draftSegments)}
      </div>
      ${state.toast ? `<div class="toast" role="status">${escapeHtml(state.toast)}</div>` : ""}
    </section>`;
}

function renderHeader(snapshot) {
  const experiment = snapshot.mode === "experiment";
  return `
    <header class="tool-header">
      <div class="brand-lockup">
        <span class="brand-seal">六</span>
        <div><strong>六柱命局</strong><small>OneCanvas</small></div>
      </div>
      <div class="authority-status ${experiment ? "experimental" : "formal"}" role="status">
        <i aria-hidden="true"></i>
        <strong>${experiment ? "实验中" : "正式盘"}</strong>
        <span>${experiment ? "正式档案未改" : "LifeCase"}</span>
      </div>
      <div class="tool-actions">
        ${renderUndoRedoControl({ canUndo: Boolean(state.history.length), canRedo: Boolean(state.future.length), canReset: experiment })}
      </div>
    </header>`;
}

function renderCanvasHeading(snapshot, variant) {
  return `
    <div class="canvas-heading">
      ${renderGenderControl(snapshot)}
      <div class="scene-dimensions">
        <label class="expression-control">
          <strong>理</strong>
          <input type="range" min="0" max="100" value="${state.expressionRatio}" data-action="expression-ratio" aria-label="理象连续表达">
          <strong>象</strong>
        </label>
        ${renderPlaybackControl()}
      </div>
    </div>`;
}

function renderGenderControl(snapshot) {
  const current = snapshot.gender || "unknown";
  return `<div class="gender-control" role="group" aria-label="选择乾造或坤造">
    <small>命造</small>
    <button data-action="gender-select" data-intent="gender:select" data-gender="male" class="${current === "male" ? "active" : ""}" aria-pressed="${current === "male"}">乾造</button>
    <button data-action="gender-select" data-intent="gender:select" data-gender="female" class="${current === "female" ? "active" : ""}" aria-pressed="${current === "female"}">坤造</button>
    ${current === "unknown" ? "<em>大运待确认</em>" : ""}
  </div>`;
}

function renderPlaybackControl() {
  const hasDraft = state.snapshot.draftNodes.length > 1;
  const label = state.playing ? "暂停" : state.playCueIndex >= 0 ? "继续" : "演时";
  return `<div class="playback-control">
    ${hasDraft ? `<span class="path-source-switch" aria-label="演时路径来源">
      <button data-action="play-source-system" class="${state.playSource === "system" ? "active" : ""}" title="播放 LifeCase 已提交的正式主路径">正式</button>
      <button data-action="play-source-draft" class="${state.playSource === "draft" ? "active" : ""}">我的</button>
    </span>` : ""}
    <button class="play-command ${state.playing ? "active" : ""}" data-action="${state.playing ? "pause-play" : "play"}">
      <span>${state.playing ? "Ⅱ" : "▶"}</span>${label}
    </button>
  </div>`;
}

function renderSceneCue() {
  const cue = currentPlaybackCue();
  if (!cue) return "";
  return `<div class="scene-cue-caption ${state.playing ? "playing" : "paused"}" role="status">
    <span>${state.playing ? "演时" : "已暂停"}</span>
    <strong>${escapeHtml(cue.label)}</strong>
  </div>`;
}

function renderTemporalStageTrack(snapshot) {
  if (state.playCueIndex < 0 && !state.playing) return "";
  const labels = ["原局", model.luckObservationFor(snapshot) ? "大运进入" : "大运待定", "流年进入"];
  return `<ol class="temporal-stage-track" aria-label="当前时间阶段">
    ${labels.map((label, index) => `<li class="${index === state.temporalStage ? "current" : ""} ${index < state.temporalStage ? "reached" : ""}"><i></i><span>${label}</span></li>`).join("")}
  </ol>`;
}

function renderPillar(slot, nodeMap, compare, snapshot, variant) {
  const stem = nodeMap.get(`${slot}_stem`);
  const branch = nodeMap.get(`${slot}_branch`);
  const capability = model.fixture.r1_contract.slot_capabilities[slot] || {};
  const renderer = slot === "luck" || slot === "annual" ? renderTemporalNode : null;
  const luckMissing = slot === "luck" && !stem && !branch;
  const genderMissing = luckMissing && snapshot.gender === "unknown";
  const unresolvedLuckStem = genderMissing
    ? '<span class="node-empty temporal-missing"><b>待</b><small>乾坤</small></span>'
    : '<button class="node-empty temporal-missing inspectable" data-action="open-luck" aria-label="查看大运序列；当前大运待定位"><b>当前</b><small>大运</small></button>';
  const unresolvedLuckBranch = genderMissing
    ? '<span class="node-empty temporal-missing"><b>定</b><small>大运</small></span>'
    : '<button class="node-empty temporal-missing inspectable" data-action="open-luck" aria-label="查看大运序列；当前大运待定位"><b>待</b><small>定位</small></button>';
  return renderPillarSlot({
    slot,
    stemMarkup: luckMissing ? unresolvedLuckStem : renderNode(stem, compare, renderer, capability),
    branchMarkup: luckMissing ? unresolvedLuckBranch : renderNode(branch, compare, renderer, capability),
    hiddenMarkup: branch && !state.pillarEdit && state.selectedKey === branch.node_key ? renderHiddenStems(branch) : "",
    titleExtra: slot === "year"
      ? renderBirthYearAnchor(snapshot, variant)
      : slot === "annual"
          ? renderAnnualSelect(snapshot, variant)
          : "",
    temporalClass: temporalSlotClass(slot),
    capability,
    editablePillar: ["year", "day"].includes(slot),
    editSessionActive: state.pillarEdit?.slot === slot,
    editAnchorComponent: state.pillarEdit?.slot === slot
      ? state.pillarEdit.anchorComponent
      : "",
  });
}

function renderBirthYearAnchor(snapshot, variant) {
  const yearPillar = variant.pillars[0];
  const years = model.cycleYearChoicesForPillar(
    yearPillar,
    model.fixture.formal.analysis_year,
  );
  const selected = Number.isInteger(snapshot.birthYearHint) && years.includes(snapshot.birthYearHint)
    ? snapshot.birthYearHint
    : null;
  return `<label class="birth-year-anchor ${selected ? "anchored" : "unresolved"}" title="干支纪年锚点">
    <span class="sr-only">干支纪年锚点</span>
    <select data-action="birth-year-anchor" data-intent="temporal:anchor" aria-label="为年柱 ${escapeHtml(yearPillar)} 选择纪年锚点" ${state.compiling || !years.length ? "disabled" : ""}>
      <option value="" ${selected ? "" : "selected"} disabled>纪年</option>
      ${years.map((year) => `<option value="${year}" ${year === selected ? "selected" : ""}>${year}</option>`).join("")}
    </select>
  </label>`;
}

function renderAnnualSelect(snapshot, variant) {
  const timingYear = Number(variant.timing_recalculation?.analysis_year);
  const currentYear = Number.isInteger(state.pendingAnnualYear)
    ? state.pendingAnnualYear
    : Number.isInteger(snapshot.analysisYear)
      ? snapshot.analysisYear
      : Number.isInteger(timingYear)
        ? timingYear
        : model.fixture.formal.analysis_year;
  return renderAnnualYearSelect({
    items: model.annualObservations(),
    currentYear,
    disabled: false,
  });
}

function renderNode(node, compare, temporalRenderer = null, capability = {}) {
  if (!node) return renderStemNode({ node: null });
  const selected = state.selectedKey === node.node_key;
  const cue = currentPlaybackCue();
  const playActive = cue?.node_keys?.includes(node.node_key);
  const draft = state.snapshot.draftNodes.includes(node.node_key);
  const draftEndpoint = state.drawMode && state.snapshot.draftNodes.at(-1) === node.node_key;
  const reachable = state.drawMode && isReachable(node.node_key);
  const ghost = compare?.ghostNodes?.get(node.node_key);
  const renderer = temporalRenderer || (node.node_type === "stem" ? renderStemNode : renderBranchNode);
  const pillarEdit = state.pillarEdit?.slot === node.node_key.split("_")[0]
    ? state.pillarEdit
    : null;
  const component = node.node_key.endsWith("_stem") ? "stem" : "branch";
  const editRole = pillarEdit
    ? component === pillarEdit.anchorComponent ? "anchor" : "counterpart"
    : "";
  const previewLabel = pillarEdit
    ? component === pillarEdit.anchorComponent ? pillarEdit.anchorValue : pillarEdit.counterpartValue
    : "";
  return renderer({
    node,
    selected,
    playActive,
    draft,
    draftEndpoint,
    reachable,
    ghost,
    ghostOpacity: compare?.ghostOpacity || 0,
    cueAction: cue?.action || "",
    capability,
    stepper: stepperForNode(node),
    previewLabel,
    editRole,
  });
}

function stepperForNode(node) {
  if (state.drawMode) return null;
  const slot = node.node_key.split("_")[0];
  if (["year", "day"].includes(slot)) {
    return {
      action: "step-independent-pillar",
      intent: "pillar:edit-independent",
      previousLabel: `上一个${node.node_type === "stem" ? "天干" : "地支"}`,
      nextLabel: `下一个${node.node_type === "stem" ? "天干" : "地支"}`,
      compiling: state.compiling,
    };
  }
  if (["month", "hour"].includes(slot)) {
    if (node.node_type !== "stem") return null;
    return {
      action: "step-dependent-pillar",
      intent: "pillar:select-dependent",
      previousLabel: `上一组${SLOT_LABELS[slot]}`,
      nextLabel: `下一组${SLOT_LABELS[slot]}`,
      compiling: state.compiling,
    };
  }
  if (slot === "luck") {
    if (node.node_type !== "stem") return null;
    return {
      action: "step-luck",
      intent: "temporal:observe",
      previousLabel: "观察上一柱大运",
      nextLabel: "观察下一柱大运",
      compiling: state.compiling,
    };
  }
  return null;
}

function renderHiddenStems(node) {
  if (!node.hidden_stems?.length) return `<div class="hidden-stems empty">此支未提供藏干节点</div>`;
  return `<div class="hidden-stems" aria-label="藏干">${node.hidden_stems.map((item) => `
    <span class="hidden-stem element-${item.element}">
      <strong>${escapeHtml(item.stem)}</strong><small>${TEN_GOD_LABELS[item.ten_god] || ""}</small>
    </span>`).join("")}</div>`;
}

function renderPathSvg(systemPath, draftSegments, compare) {
  const cue = currentPlaybackCue();
  const system = pathSegmentsToSvg(systemPath.segments || [], "system", systemPath.epistemic_status, state.playSource === "system" ? cue : null);
  const draft = pathSegmentsToSvg(draftSegments.map((item) => ({
    from_key: item.from_key,
    to_key: item.to_key,
    label: item.relation?.label || "缺少关系",
    relation_type: item.relation?.relation_type || "missing",
    status: item.status,
  })), "draft", "user_draft", state.playSource === "draft" ? cue : null);
  const compareGhost = compare ? pathSegmentsToSvg(compare.ghostPath.segments || [], "compare-ghost", compare.ghostPath.epistemic_status, null, compare.ghostOpacity) : "";
  return `<svg class="path-layer" viewBox="0 0 1200 470" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <marker id="arrow-system" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z"></path></marker>
      <marker id="arrow-draft" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z"></path></marker>
    </defs>
    ${compareGhost}${system}${draft}
  </svg>`;
}

function pathSegmentsToSvg(segments, kind, epistemic, cue, opacity = 1) {
  return segments.map((segment, index) => {
    const from = nodePoint(segment.from_key || segment.from_anchor);
    const to = nodePoint(segment.to_key || segment.to_anchor);
    if (!from || !to) return "";
    const bend = from.y === to.y ? (from.y < 230 ? -55 : 55) : 0;
    const c1x = from.x + (to.x - from.x) * .42;
    const c2x = from.x + (to.x - from.x) * .58;
    const d = `M ${from.x} ${from.y} C ${c1x} ${from.y + bend}, ${c2x} ${to.y + bend}, ${to.x} ${to.y}`;
    const status = segment.status || "available";
    const cueMatches = cue && cue.segment_index === index && (cue.action === "trace_path" || cue.action === "block_path");
    const active = cueMatches ? (cue.action === "block_path" ? "playing blocked-cue" : "playing") : "";
    const midX = (from.x + to.x) / 2;
    const midY = (from.y + to.y) / 2 + bend * .72;
    return `<g class="path-segment ${kind} ${epistemic || ""} ${status} ${active}" style="opacity:${opacity}">
      <path d="${d}" marker-end="url(#arrow-${kind === "draft" ? "draft" : "system"})"></path>
      <text x="${midX}" y="${midY}">${escapeHtml(relationShortLabel(segment))}</text>
    </g>`;
  }).join("");
}

function renderLens(nodeMap, snapshot) {
  if (!state.lens) return "";
  if (state.lens.type === "luck") return renderLuckLens(snapshot);
  return "";
}

function renderLuckLens(snapshot) {
  const timing = model.variantFor(snapshot).timing_recalculation;
  const selectedIndex = Number.isInteger(snapshot.luckIndex)
    ? snapshot.luckIndex
    : model.currentLuckIndex(snapshot);
  return renderLuckObservation({
    timing,
    sequence: timing.luck_sequence || [],
    selectedIndex,
  });
}

function renderCompareControl(compare) {
  if (!compare) return "";
  return `<div class="compare-control" aria-label="实验 A B 擦除比较">
    <span>A</span><input type="range" min="0" max="100" value="${state.compareRatio}" data-action="compare-ratio"><span>B</span>
    <small>${compare.changedKeys.length} 个节点变化 · 同一空间叠加</small>
  </div>`;
}

function renderCanvasFooter(snapshot, variant, systemPath, draftSegments) {
  const changes = variant.diff.changed_pillars || [];
  const timing = variant.timing_recalculation;
  const recompute = recomputeViewModel(timing);
  const hasDraft = state.snapshot.draftNodes.length > 0;
  const birthYearSummary = Number.isInteger(snapshot.birthYearHint)
    ? `${snapshot.birthYearHint} 生`
    : "出生年份待定";
  const changeSummary = snapshot.mode === "formal"
    ? `${GENDER_LABELS[snapshot.gender] || GENDER_LABELS.unknown} · ${birthYearSummary}`
    : changes.length
      ? `${changes.map((item) => `${SLOT_LABELS[item.slot]} ${item.before}→${item.after}`).join(" · ")} · ${birthYearSummary}`
      : Number.isInteger(snapshot.birthYearHint)
        ? `四柱未改 · ${birthYearSummary}`
        : "实验盘与正式盘相同";
  const pathSummary = draftSegments.length
    ? `我的路径 ${draftSegments.length} 段`
    : systemPath.node_keys.length
      ? `正式路径 ${systemPath.node_keys.length} 节点`
      : "路径待形成";
  return `<footer class="canvas-footer">
    <p><i aria-hidden="true"></i><strong>${escapeHtml(changeSummary)}</strong><span>${escapeHtml(recompute.title)}</span></p>
    <nav aria-label="路径操作">
      ${state.drawMode
        ? `<button data-action="finish-path" data-intent="path:complete" class="active" title="完成路径"><span>✓</span>完成</button>`
        : `<button data-action="draw-path" data-intent="path:start" title="${hasDraft ? "继续画路径" : "画路径"}"><span>⌁</span>${hasDraft ? "续画" : "画路"}</button>`}
      ${hasDraft ? `<button data-action="clear-draft" title="清空我的路径"><span>×</span></button>` : ""}
      <small>${escapeHtml(pathSummary)}</small>
    </nav>
  </footer>`;
}

function renderDrawingGuide() {
  if (!state.drawMode) return "";
  const count = state.snapshot.draftNodes.length;
  return `<div class="draw-session-guide" role="status">
    <span>连线中</span>
    <strong>${count ? `已选 ${count} 个节点` : "请选择起点"}</strong>
    <small>${count >= 2 ? "继续点节点；再点当前终点完成" : "选择下一节点形成第一段"}</small>
  </div>`;
}

function currentPlaybackPath() {
  const snapshot = currentRenderSnapshot();
  if (state.playSource !== "draft" || snapshot.draftNodes.length < 2) return model.pathFor(snapshot);
  const segments = model.draftSegments(snapshot, snapshot.draftNodes).map((item) => ({
    from_key: item.from_key,
    to_key: item.to_key,
    label: item.relation?.label || "缺少关系",
    relation_type: item.relation?.relation_type || "missing",
    status: item.status,
    epistemic_status: "user_draft",
  }));
  return {
    authority: "user_path_draft",
    epistemic_status: "user_draft",
    warning: "用户路径草稿，不写入正式认知",
    node_keys: [...snapshot.draftNodes],
    segments,
  };
}

function currentPlaybackCues() {
  const nodeKeys = new Set(model.nodesFor(currentRenderSnapshot()).map((node) => node.node_key));
  return compileOneCanvasCues(currentPlaybackPath(), {
    luckAvailable: nodeKeys.has("luck_stem") && nodeKeys.has("luck_branch"),
    annualAvailable: nodeKeys.has("annual_stem") && nodeKeys.has("annual_branch"),
  });
}

function currentPlaybackCue() {
  if (state.playCueIndex < 0) return null;
  return currentPlaybackCues()[state.playCueIndex] || null;
}

function temporalSlotClass(slot) {
  if (slot === "luck" && state.temporalStage < 1) return "awaiting-entry";
  if (slot === "annual" && state.temporalStage < 2) return "awaiting-entry";
  if (slot === "luck" && state.temporalStage === 1) return "stage-entering";
  if (slot === "annual" && state.temporalStage === 2 && state.playCueIndex >= 0) return "stage-entering";
  return "stage-present";
}

function updateExpressionPresentation() {
  const shell = root.querySelector(".onecanvas-shell");
  if (!shell) return;
  const ratio = Math.max(0, Math.min(1, state.expressionRatio / 100));
  shell.style.setProperty("--xiang-ratio", String(ratio));
  shell.style.setProperty("--li-ratio", String(1 - ratio));
  shell.classList.toggle("li-dominant", state.expressionRatio <= 8);
  shell.classList.toggle("expression-mixed", state.expressionRatio > 8 && state.expressionRatio < 58);
  shell.classList.toggle("xiang-dominant", state.expressionRatio >= 58);
}

function compareModel() {
  if (!state.compareActive || !state.saved.a || !state.saved.b) return null;
  const main = state.compareRatio < 50 ? state.saved.a : state.saved.b;
  const ghost = state.compareRatio < 50 ? state.saved.b : state.saved.a;
  const changedKeys = model.changedNodeKeys(state.saved.a, state.saved.b);
  const changedSet = new Set(changedKeys);
  return {
    main,
    ghost,
    ghostNodes: new Map(model.nodesFor(ghost).filter((node) => changedSet.has(node.node_key)).map((node) => [node.node_key, node])),
    ghostPath: model.pathFor(ghost),
    ghostOpacity: Math.abs(50 - state.compareRatio) / 100 + .18,
    changedKeys,
  };
}

function isReachable(key) {
  const previous = state.snapshot.draftNodes.at(-1);
  if (!previous || previous === key) return false;
  return model.relationBetween(state.snapshot, previous, key).status !== "missing";
}

function nodePoint(key) {
  if (!key) return null;
  const [slot, kind] = key.split("_");
  const slotIndex = SLOT_ORDER.indexOf(slot);
  if (slotIndex < 0) return null;
  return {
    x: 100 + slotIndex * 200,
    y: kind === "stem" ? 138 : 332,
  };
}

function relationShortLabel(segment) {
  if (segment.status === "missing" || segment.relation_type === "missing") return "断点";
  if (segment.status === "reverse") return "逆向";
  return RELATION_LABELS[segment.relation_type] || segment.label || "关系";
}

function timingMessage(candidate) {
  const recompute = recomputeViewModel(candidate.timing_recalculation);
  return `${recompute.title}${recompute.detail ? `：${recompute.detail}` : ""}`;
}

function isNatalKey(key) {
  return /^(year|month|day|hour)_(stem|branch)$/.test(key);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
