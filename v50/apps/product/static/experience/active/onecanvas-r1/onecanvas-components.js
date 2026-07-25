import {
  ELEMENT_LABELS,
  SLOT_LABELS,
  TEN_GOD_LABELS,
  metaphorBindingFor,
  recomputeViewModel,
} from "./onecanvas-runtime.js";

export const ONECANVAS_LAYER_ORDER = Object.freeze([
  "background",
  "structural-nodes",
  "root-and-reveal",
  "relations",
  "temporal-activation",
  "system-path",
  "user-path",
  "diff",
  "interaction-hints",
  "selection",
]);

export function renderOneCanvasStage({ layerMarkup = {}, overlay = "", extra = "" } = {}) {
  return `<div class="canvas-field" aria-label="六柱一图交互画布">
    ${ONECANVAS_LAYER_ORDER.map((layer) => `<div class="onecanvas-layer layer-${layer}" data-layer="${layer}">${layerMarkup[layer] || ""}</div>`).join("")}
    ${extra}
    <div class="onecanvas-overlay-layer">${overlay}</div>
  </div>`;
}

export function renderPillarSlot({
  slot,
  stemMarkup,
  branchMarkup,
  hiddenMarkup = "",
  titleExtra = "",
  temporalClass = "",
  capability = {},
  editablePillar = false,
  editSessionActive = false,
  editAnchorComponent = "",
}) {
  const temporal = slot === "luck" || slot === "annual";
  const derivedBadge = capability.derived && slot === "luck"
    ? `<i class="slot-capability derived" aria-label="大运由系统派生">派生</i>`
    : "";
  return `<div class="pillar-column ${temporal ? "temporal" : "natal"} ${temporalClass} ${editablePillar ? "editable" : ""} ${editSessionActive ? `edit-session anchor-${escapeHtml(editAnchorComponent)}` : ""}" data-slot="${escapeHtml(slot)}">
    <div class="pillar-title"><span>${escapeHtml(SLOT_LABELS[slot] || slot)}</span>${titleExtra}${slot === "day" ? "<i>命主</i>" : ""}${derivedBadge}</div>
    ${stemMarkup}
    <span class="pillar-spine-zone">
      <span class="pillar-spine" aria-hidden="true"></span>
    </span>
    ${branchMarkup}
    ${hiddenMarkup}
  </div>`;
}

export function renderAnnualYearSelect({ items = [], currentYear = null, disabled = false } = {}) {
  return `<label class="annual-inline-select" title="选择流年">
    <select data-action="annual-year-select" data-intent="temporal:observe" aria-label="选择公历流年" ${disabled ? "disabled" : ""}>
      ${items.map((item) => `<option value="${item.year}" ${item.year === currentYear ? "selected" : ""}>${item.year}</option>`).join("")}
    </select>
  </label>`;
}

export function renderStemNode(viewModel) {
  return renderSemanticNode({ ...viewModel, nodeKind: "stem" });
}

export function renderBranchNode(viewModel) {
  return renderSemanticNode({ ...viewModel, nodeKind: "branch" });
}

export function renderTemporalNode(viewModel) {
  return renderSemanticNode({ ...viewModel, temporal: true });
}

export function renderSemanticNode({
  node,
  nodeKind = "",
  selected = false,
  playActive = false,
  draft = false,
  draftEndpoint = false,
  reachable = false,
  ghost = null,
  ghostOpacity = 0,
  cueAction = "",
  temporal = false,
  capability = {},
  stepper = null,
  previewLabel = "",
  editRole = "",
} = {}) {
  if (!node) return `<span class="node-empty">—</span>`;
  const metaphor = metaphorBindingFor(node);
  const classes = [
    "node",
    nodeKind ? `node-${nodeKind}` : "",
    temporal ? "temporal-node" : "",
    `element-${node.element}`,
    `polarity-${node.polarity}`,
    selected ? "selected" : "",
    playActive ? "play-active" : "",
    draft ? "draft-node" : "",
    draftEndpoint ? "draft-endpoint" : "",
    reachable ? "reachable" : "",
    node.source_mode === "hypothetical" ? "hypothetical" : "",
    playActive && cueAction ? `cue-${cueAction}` : "",
    capability.editable_in_experiment === false ? "not-editable" : "",
    capability.derived ? "derived-node" : "",
    editRole ? `edit-${editRole}` : "",
    node.epistemic_status ? `epistemic-${node.epistemic_status}` : "",
  ].filter(Boolean).join(" ");
  const tenGod = node.node_type === "branch"
    ? node.hidden_stems?.length ? `藏 ${node.hidden_stems.map((item) => item.stem).join(" · ")}` : "地支"
    : TEN_GOD_LABELS[node.ten_god] || "十神待定";
  const polarity = node.polarity === "yang" ? "阳" : node.polarity === "yin" ? "阴" : "";
  const capabilityLabel = temporal && capability.derived
    ? `<span class="node-capability-label">${capability.editable_in_experiment === false ? "派生" : ""}</span>`
    : "";
  const visibleLabel = previewLabel || node.label;
  const nodeMarkup = `<button class="${classes}" data-action="select-node" data-intent="node:select" data-node-key="${escapeHtml(node.node_key)}" data-semantic-ref="${escapeHtml(node.semantic_ref || "")}" aria-label="${escapeHtml(visibleLabel)}，${editRole === "anchor" ? "本次编辑锚点，可连续调整" : editRole === "counterpart" ? "合法配对侧，可连续调整" : `${polarity}${ELEMENT_LABELS[node.element] || ""}，${escapeHtml(tenGod)}`}">
    ${ghost ? `<span class="ghost-glyph" style="--ghost-opacity:${Number(ghostOpacity) || 0}">${escapeHtml(ghost.label)}</span>` : ""}
    ${editRole === "anchor" ? '<span class="edit-anchor-badge" aria-hidden="true"><i></i></span>' : ""}
    ${editRole === "counterpart" ? '<span class="edit-counterpart-hint" aria-hidden="true"></span>' : ""}
    ${capabilityLabel}
    <span class="node-glyph-layer">
      <strong>${escapeHtml(visibleLabel)}</strong>
      <span>${polarity}${ELEMENT_LABELS[node.element] || ""}</span>
      <small>${escapeHtml(tenGod)}</small>
    </span>
    <span class="node-motif-layer" aria-hidden="true">
      <i class="motif-symbol motif-${escapeHtml(node.element)}"><b></b></i>
      <em>${escapeHtml(metaphor.motif)}</em>
      <small>${escapeHtml(visibleLabel)}</small>
    </span>
  </button>`;
  if (!stepper?.action) return nodeMarkup;
  const stepperScope = ["step-dependent-pillar", "step-luck"].includes(stepper.action) ? "whole-pillar-stepper" : "component-stepper";
  return `<div class="node-control ${stepperScope} ${selected ? "selected" : ""} ${stepper.compiling ? "compiling" : ""}" data-node-control="${escapeHtml(node.node_key)}">
    <button class="node-step node-step-previous" data-action="${escapeHtml(stepper.action)}" data-intent="${escapeHtml(stepper.intent || "temporal:observe")}" data-node-key="${escapeHtml(node.node_key)}" data-direction="-1" aria-label="${escapeHtml(stepper.previousLabel || "上一个合法值")}" ${stepper.compiling ? "disabled" : ""}><span aria-hidden="true">‹</span></button>
    ${nodeMarkup}
    <button class="node-step node-step-next" data-action="${escapeHtml(stepper.action)}" data-intent="${escapeHtml(stepper.intent || "temporal:observe")}" data-node-key="${escapeHtml(node.node_key)}" data-direction="1" aria-label="${escapeHtml(stepper.nextLabel || "下一个合法值")}" ${stepper.compiling ? "disabled" : ""}><span aria-hidden="true">›</span></button>
  </div>`;
}

export function renderRecomputeIndicator(value = {}) {
  const model = value.status && value.tone && value.title ? value : recomputeViewModel(value);
  return `<div class="recompute-indicator tone-${escapeHtml(model.tone || "unavailable")}" role="status" data-recompute-status="${escapeHtml(model.status || "recalculation_unavailable")}">
    <i aria-hidden="true"></i>
    <div><strong>${escapeHtml(model.title || "当前输入不足，无法可靠重算")}</strong><small>${escapeHtml(model.detail || "")}</small></div>
  </div>`;
}

export function renderContextPopover({ className = "", ariaLabel = "上下文", kicker = "", body = "" } = {}) {
  return `<aside class="context-lens context-popover ${escapeHtml(className)}" tabindex="-1" aria-label="${escapeHtml(ariaLabel)}">
    <button class="lens-close" data-action="close-lens" data-intent="candidate:cancel" aria-label="关闭">×</button>
    ${kicker ? `<span class="lens-kicker">${escapeHtml(kicker)}</span>` : ""}
    ${body}
  </aside>`;
}

export function renderUndoRedoControl({ canUndo = false, canRedo = false, canReset = false } = {}) {
  return `<span class="undo-redo-control" aria-label="实验历史">
    <button data-action="undo" data-intent="history:undo" class="icon-button" title="撤销" ${canUndo ? "" : "disabled"}>↶</button>
    <button data-action="redo" data-intent="history:redo" class="icon-button" title="重做" ${canRedo ? "" : "disabled"}>↷</button>
    <button data-action="reset" data-intent="canvas:reset" class="icon-button" title="恢复正式盘" ${canReset ? "" : "disabled"}>↺</button>
  </span>`;
}

export function renderLuckObservation({ timing = {}, sequence = [], selectedIndex = -1 } = {}) {
  const recompute = recomputeViewModel(timing);
  const hasSequence = sequence.length > 0;
  const currentResolved = ["resolved", "resolved_from_birth_year"].includes(timing.current_luck_status) && selectedIndex >= 0;
  return renderContextPopover({
    className: "temporal-lens luck-lens",
    ariaLabel: "大运派生结果",
    kicker: "大运序列 · 自动推导，不可手工改写",
    body: `${renderRecomputeIndicator(recompute)}
      ${hasSequence && !currentResolved ? `<p class="candidate-boundary">这里只确定了顺逆序列，没有自动认定当前大运。请选择出生年份，系统会用完整四柱反查定位；也可以暂时选择其中一步进行假设观察。</p>` : ""}
      <div class="luck-sequence" role="listbox" aria-label="切换观察大运">
        ${sequence.map((item, index) => `<button role="option" aria-selected="${index === selectedIndex}" class="${index === selectedIndex ? "current" : ""}" data-action="luck-observe" data-intent="temporal:observe" data-index="${index}">
          <strong>${escapeHtml(item.pillar)}</strong><small>${item.start_year && item.end_year ? `${item.start_year}–${item.end_year}` : `第 ${item.sequence_index || index + 1} 步 · 时间待定`}</small><em>${index === selectedIndex ? (currentResolved ? "当前大运" : "假设观察中") : "观察"}</em>
        </button>`).join("") || `<p class="candidate-empty">请先确认乾造或坤造；系统不会猜测大运顺逆。</p>`}
      </div>
      <p>选择只改变当前画布的观察步骤，不会把它写成正式当前大运。缺少 typed temporal path effect 时，关系与路径不会被补写。</p>`,
  });
}

export function renderTargetResolution({ resolution = {}, compiling = false } = {}) {
  const status = String(resolution.status || "");
  if (!status || status === "single_solution") return "";
  const multiple = status === "multiple_solutions";
  const candidates = Array.isArray(resolution.legal_variants) ? resolution.legal_variants : [];
  const conflicts = Array.isArray(resolution.conflict_reasons) ? resolution.conflict_reasons : [];
  const releasable = Array.isArray(resolution.releasable_constraints)
    ? resolution.releasable_constraints
    : [];
  const title = multiple
    ? `有 ${Number(resolution.candidate_count) || candidates.length} 个完整命盘符合条件`
    : "这组条件不能同时成立";
  const body = multiple
    ? `<p class="target-resolution-intro">请选择一个完整四柱。候选顺序只便于查看，不代表专业排序。</p>
      <div class="target-candidate-grid" role="list" aria-label="合法完整命盘候选">
        ${candidates.map((candidate) => renderTargetCandidate(candidate, compiling)).join("")}
      </div>
      ${resolution.candidates_truncated ? '<p class="target-resolution-note">候选较多，当前仅显示服务器返回的安全范围。</p>' : ""}`
    : `<ul class="target-conflict-list">
        ${conflicts.map((item) => `<li><strong>${escapeHtml(conflictTitle(item.reason))}</strong><span>${escapeHtml(item.detail || "当前锁定条件彼此冲突。")}</span></li>`).join("") || "<li><strong>没有合法完整命盘</strong><span>请放开一个冲突条件后重新计算。</span></li>"}
      </ul>
      <div class="target-release-actions" aria-label="可放开的冲突条件">
        ${releasable.map((path) => `<button data-action="release-target-constraint" data-constraint-path="${escapeHtml(path)}" ${compiling ? "disabled" : ""}>${escapeHtml(releaseLabel(path))}</button>`).join("")}
      </div>`;
  return `<div class="target-resolution-overlay" data-resolution-status="${escapeHtml(status)}">
    <section class="target-resolution-dialog" role="dialog" aria-modal="true" aria-labelledby="targetResolutionTitle" tabindex="-1">
      <button class="target-resolution-close" data-action="cancel-target-resolution" aria-label="取消本次选择">×</button>
      <span class="target-resolution-kicker">实验盘 · 正式档案未改</span>
      <h2 id="targetResolutionTitle">${escapeHtml(title)}</h2>
      ${body}
      <footer><button data-action="cancel-target-resolution" ${compiling ? "disabled" : ""}>取消，保留当前命盘</button></footer>
    </section>
  </div>`;
}

function renderTargetCandidate(candidate, compiling) {
  const pillars = Array.isArray(candidate.pillars) ? candidate.pillars : [];
  return `<article class="target-candidate" role="listitem">
    <div class="target-candidate-pillars" aria-label="完整四柱">
      ${["年", "月", "日", "时"].map((label, index) => `<span><small>${label}柱</small><strong>${escapeHtml(pillars[index] || "—")}</strong></span>`).join("")}
    </div>
    <button data-action="select-target-variant" data-variant-ref="${escapeHtml(candidate.variant_ref || "")}" ${compiling || !candidate.variant_ref ? "disabled" : ""}>使用这个完整命盘</button>
  </article>`;
}

function conflictTitle(reason) {
  const labels = {
    month_pillar_not_legal_for_year: "年柱与月柱不能同时成立",
    hour_pillar_not_legal_for_day: "日柱与时柱不能同时成立",
    year_pillar_not_in_cycle: "年柱不是合法六十甲子",
    day_pillar_not_in_cycle: "日柱不是合法六十甲子",
  };
  return labels[String(reason || "")] || "当前约束没有合法完整命盘";
}

function releaseLabel(path) {
  const labels = {
    "year.pillar": "放开年柱条件",
    "year.stem": "放开年干条件",
    "year.branch": "放开年支条件",
    "month.pillar": "让月柱重新选择",
    "month.stem": "放开月干条件",
    "month.branch": "放开月支条件",
    "day.pillar": "放开日柱条件",
    "day.stem": "放开日干条件",
    "day.branch": "放开日支条件",
    "hour.pillar": "让时柱重新选择",
    "hour.stem": "放开时干条件",
    "hour.branch": "放开时支条件",
  };
  return labels[String(path || "")] || "放开这个条件";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
