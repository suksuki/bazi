const root = document.querySelector("#labRoot");
if (!root) throw new Error("mingli_lab_root_missing");

const TEN_GOD_LABELS = {
  day_master: "日主",
  bi_jian: "比肩",
  jie_cai: "劫财",
  shi_shen: "食神",
  shang_guan: "伤官",
  pian_cai: "偏财",
  zheng_cai: "正财",
  qi_sha: "七杀",
  zheng_guan: "正官",
  pian_yin: "偏印",
  zheng_yin: "正印",
};

const ELEMENTS = {
  甲: "wood", 乙: "wood", 寅: "wood", 卯: "wood",
  丙: "fire", 丁: "fire", 巳: "fire", 午: "fire",
  戊: "earth", 己: "earth", 辰: "earth", 戌: "earth", 丑: "earth", 未: "earth",
  庚: "metal", 辛: "metal", 申: "metal", 酉: "metal",
  壬: "water", 癸: "water", 子: "water", 亥: "water",
};

const POSITION_LABELS = {
  year_stem: "年干", year_branch: "年支",
  month_stem: "月干", month_branch: "月支",
  day_stem: "日干", day_branch: "日支",
  hour_stem: "时干", hour_branch: "时支",
};

const PILLAR_LABELS = ["年柱", "月柱", "日柱", "时柱"];

let fixture = null;
let playTimer = null;

const state = {
  mode: "formal",
  activeSlot: "a",
  variantIndex: 0,
  yearIndex: 2,
  pathLens: "reference",
  draftNodes: [],
  selectedNode: "",
  hourPickerOpen: false,
  playStep: -1,
  abuOpen: !window.matchMedia("(max-width: 620px)").matches,
  dirty: false,
  history: [],
  future: [],
  saved: { a: null, b: null },
};

boot();

async function boot() {
  try {
    const response = await fetch("./fixture.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`fixture_http_${response.status}`);
    fixture = await response.json();
    state.variantIndex = fixture.baseline_variant_index;
    state.yearIndex = Math.max(0, fixture.year_dial.findIndex((item) => item.source_mode === "official"));
    render();
    bindRootEvents();
  } catch (error) {
    root.innerHTML = `<div class="empty-state"><h1>原型数据没有准备好</h1><p>${escapeHtml(String(error))}</p></div>`;
  }
}

function bindRootEvents() {
  root.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target.closest("[data-action]") : null;
    if (!target) return;
    const action = target.getAttribute("data-action") || "";
    handleAction(action, target);
  });
}

function handleAction(action, target) {
  if (action === "mode-formal") {
    loadFormal();
    return;
  }
  if (action === "mode-a") {
    openExperiment("a");
    return;
  }
  if (action === "mode-b") {
    openExperiment("b");
    return;
  }
  if (action === "mode-compare") {
    openCompare();
    return;
  }
  if (action === "create-experiment") {
    createExperiment("a");
    return;
  }
  if (action === "toggle-hour-picker") {
    if (state.mode === "formal") createExperiment("a");
    state.hourPickerOpen = !state.hourPickerOpen;
    render();
    return;
  }
  if (action === "select-hour") {
    const index = Number(target.getAttribute("data-index"));
    mutate(() => {
      state.variantIndex = index;
      state.draftNodes = [];
      state.selectedNode = "";
      state.hourPickerOpen = false;
    });
    return;
  }
  if (action === "select-year") {
    if (state.mode === "formal") return;
    const index = Number(target.getAttribute("data-index"));
    mutate(() => { state.yearIndex = index; });
    return;
  }
  if (action === "path-lens") {
    state.pathLens = target.getAttribute("data-lens") || "reference";
    state.playStep = -1;
    render();
    return;
  }
  if (action === "play-path") {
    playPath();
    return;
  }
  if (action === "toggle-abu") {
    state.abuOpen = !state.abuOpen;
    render();
    return;
  }
  if (action === "select-node") {
    const key = target.getAttribute("data-node-key") || "";
    state.selectedNode = key;
    if (state.pathLens === "draft" && state.mode !== "formal") addDraftNode(key);
    else render();
    return;
  }
  if (action === "start-draft") {
    if (state.mode === "formal") createExperiment("a");
    state.pathLens = "draft";
    state.draftNodes = [];
    render();
    return;
  }
  if (action === "clear-draft") {
    mutate(() => { state.draftNodes = []; });
    return;
  }
  if (action === "undo") {
    undo();
    return;
  }
  if (action === "redo") {
    redo();
    return;
  }
  if (action === "reset") {
    mutate(() => {
      state.variantIndex = fixture.baseline_variant_index;
      state.yearIndex = fixture.year_dial.findIndex((item) => item.source_mode === "official");
      state.draftNodes = [];
      state.selectedNode = "";
      state.pathLens = "reference";
    });
    return;
  }
  if (action === "save-a" || action === "save-b") {
    saveExperiment(action.slice(-1));
    return;
  }
}

function loadFormal() {
  stopPlayback();
  state.mode = "formal";
  state.variantIndex = fixture.baseline_variant_index;
  state.yearIndex = fixture.year_dial.findIndex((item) => item.source_mode === "official");
  state.pathLens = "reference";
  state.draftNodes = [];
  state.hourPickerOpen = false;
  state.history = [];
  state.future = [];
  state.dirty = false;
  render();
}

function createExperiment(slot) {
  stopPlayback();
  state.mode = "experiment";
  state.activeSlot = slot;
  state.variantIndex = fixture.baseline_variant_index;
  state.yearIndex = fixture.year_dial.findIndex((item) => item.source_mode === "official");
  state.pathLens = "reference";
  state.draftNodes = [];
  state.selectedNode = "";
  state.history = [];
  state.future = [];
  state.saved[slot] = snapshot();
  state.dirty = false;
  render();
}

function openExperiment(slot) {
  if (!state.saved[slot]) {
    const source = state.mode === "experiment" ? snapshot() : formalSnapshot();
    state.saved[slot] = source;
  }
  stopPlayback();
  state.mode = "experiment";
  state.activeSlot = slot;
  restoreSnapshot(state.saved[slot]);
  state.history = [];
  state.future = [];
  state.dirty = false;
  render();
}

function openCompare() {
  if (!state.saved.a) state.saved.a = formalSnapshot();
  if (!state.saved.b) state.saved.b = state.mode === "experiment" ? snapshot() : formalSnapshot();
  stopPlayback();
  state.mode = "compare";
  state.hourPickerOpen = false;
  render();
}

function saveExperiment(slot) {
  if (state.mode === "formal") return;
  state.saved[slot] = snapshot();
  state.activeSlot = slot;
  state.mode = "experiment";
  state.dirty = false;
  render();
}

function snapshot() {
  return {
    variantIndex: state.variantIndex,
    yearIndex: state.yearIndex,
    pathLens: state.pathLens,
    draftNodes: [...state.draftNodes],
    selectedNode: state.selectedNode,
  };
}

function formalSnapshot() {
  return {
    variantIndex: fixture.baseline_variant_index,
    yearIndex: fixture.year_dial.findIndex((item) => item.source_mode === "official"),
    pathLens: "reference",
    draftNodes: [],
    selectedNode: "",
  };
}

function restoreSnapshot(value) {
  state.variantIndex = value.variantIndex;
  state.yearIndex = value.yearIndex;
  state.pathLens = value.pathLens;
  state.draftNodes = [...value.draftNodes];
  state.selectedNode = value.selectedNode;
  state.hourPickerOpen = false;
}

function mutate(operation) {
  stopPlayback();
  state.history.push(snapshot());
  state.future = [];
  operation();
  if (state.mode !== "formal") state.dirty = true;
  render();
}

function undo() {
  const previous = state.history.pop();
  if (!previous) return;
  state.future.push(snapshot());
  restoreSnapshot(previous);
  state.dirty = true;
  render();
}

function redo() {
  const next = state.future.pop();
  if (!next) return;
  state.history.push(snapshot());
  restoreSnapshot(next);
  state.dirty = true;
  render();
}

function addDraftNode(key) {
  if (!key || state.draftNodes.at(-1) === key) return;
  mutate(() => {
    if (state.draftNodes.length >= 4) state.draftNodes.shift();
    state.draftNodes.push(key);
  });
}

function stopPlayback() {
  if (playTimer) window.clearInterval(playTimer);
  playTimer = null;
  state.playStep = -1;
}

function playPath() {
  stopPlayback();
  const path = currentPathModel();
  if (!path.nodes.length) return;
  let step = 0;
  state.playStep = 0;
  render();
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  playTimer = window.setInterval(() => {
    step += 1;
    state.playStep = step;
    render();
    if (step >= path.nodes.length + path.segments.length - 1) stopPlayback();
  }, reduced ? 120 : 620);
}

function render() {
  if (!fixture) return;
  root.innerHTML = `
    <div class="lab-shell">
      ${renderHeader()}
      ${renderWorkspaceBar()}
      <div class="lab-main">
        ${state.mode === "compare" ? renderCompare() : renderWorkbench()}
      </div>
      ${renderAbu()}
    </div>`;
}

function renderHeader() {
  return `<header class="lab-header">
    <div class="header-inner">
      <img class="brand-logo" src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi">
      <div class="header-title">
        <p class="eyebrow">Mingli Lab · C2A Prototype</p>
        <h1>命局实验台</h1>
        <p>不是观看一张命盘，而是亲手验证结构为何改变。</p>
      </div>
      <span class="boundary-badge">实验副本不改正式盘</span>
    </div>
  </header>`;
}

function renderWorkspaceBar() {
  const canEdit = state.mode === "experiment";
  return `<nav class="workspace-bar" aria-label="实验工作区">
    <div class="workspace-inner">
      <div class="mode-tabs" role="tablist">
        ${modeButton("formal", "正式盘", state.mode === "formal")}
        ${modeButton("a", "实验 A", state.mode === "experiment" && state.activeSlot === "a", Boolean(state.saved.a))}
        ${modeButton("b", "实验 B", state.mode === "experiment" && state.activeSlot === "b", Boolean(state.saved.a))}
        ${modeButton("compare", "A/B 比较", state.mode === "compare", Boolean(state.saved.a))}
      </div>
      <div class="tool-actions" aria-label="实验操作">
        ${state.mode === "formal" ? '<button class="text-command primary" aria-label="创建实验副本" data-action="create-experiment"><span class="label-full">创建实验副本</span><span class="label-compact">新实验</span></button>' : ""}
        <button class="icon-button" title="撤销" aria-label="撤销" data-action="undo" ${canEdit && state.history.length ? "" : "disabled"}>↶</button>
        <button class="icon-button" title="重做" aria-label="重做" data-action="redo" ${canEdit && state.future.length ? "" : "disabled"}>↷</button>
        <button class="icon-button" title="恢复正式盘" aria-label="恢复正式盘" data-action="reset" ${canEdit ? "" : "disabled"}>↺</button>
        <button class="text-command" aria-label="存为 A" data-action="save-a" ${canEdit ? "" : "disabled"}><span class="label-full">存为 A</span><span class="label-compact">存 A</span></button>
        <button class="text-command" aria-label="存为 B" data-action="save-b" ${canEdit ? "" : "disabled"}><span class="label-full">存为 B</span><span class="label-compact">存 B</span></button>
        <button class="text-command accent" aria-label="比较 A/B" data-action="mode-compare" ${state.saved.a ? "" : "disabled"}><span class="label-full">比较 A/B</span><span class="label-compact">比较</span></button>
      </div>
    </div>
  </nav>`;
}

function modeButton(mode, label, active, enabled = true) {
  return `<button type="button" role="tab" class="mode-tab ${active ? "active" : ""}" aria-selected="${active}" data-action="mode-${mode}" ${enabled ? "" : "disabled"}>${label}</button>`;
}

function renderWorkbench() {
  const variant = currentVariant();
  return `
    ${renderStatusRibbon(variant)}
    ${renderPillarStage(variant)}
    <div class="lab-grid">
      ${renderPathWorkspace(variant)}
      ${renderInsightPanel(variant)}
    </div>
    ${renderYearPanel()}`;
}

function renderStatusRibbon(variant) {
  const formal = state.mode === "formal";
  const year = fixture.year_dial[state.yearIndex];
  const copy = formal
    ? "这是正式 ChartVersion 与 LifeCase 已提交路径。先创建实验副本，才能改变出生时辰。"
    : `当前草稿来自实验 ${state.activeSlot.toUpperCase()}：${variant.time_range} · ${year.source_mode === "official" ? "正式流年材料" : "假设流年信号"}${state.dirty ? " · 有未保存调整" : ""}。`;
  return `<div class="status-ribbon">
    <span><strong>${formal ? "正式盘" : "结构实验"}</strong>　${copy}</span>
    <span>匿名真实案例 · ${escapeHtml(fixture.source.case_ref)}</span>
  </div>`;
}

function renderPillarStage(variant) {
  const year = fixture.year_dial[state.yearIndex];
  const pillars = [
    ...variant.pillars.map((pillar, index) => ({ pillar, label: PILLAR_LABELS[index], position: ["year", "month", "day", "hour"][index], time: false })),
    { pillar: fixture.formal.luck_pillar, label: "大运", position: "luck", time: true },
    { pillar: year.pillar, label: "流年", position: "year-time", time: true },
  ];
  return `<section class="pillar-stage" aria-labelledby="pillarTitle">
    <div class="stage-heading">
      <div>
        <p class="eyebrow">结构坐标</p>
        <h2 id="pillarTitle">四柱为原局，运年作为时间信号进入</h2>
        <p>年、月、日已锁定；点击时柱可扫描十二个合法时辰。</p>
      </div>
      <button class="text-command" data-action="toggle-hour-picker">${state.hourPickerOpen ? "收起时辰" : "校勘时柱"}</button>
    </div>
    <div class="pillar-strip">
      ${pillars.map((item, index) => `${index === 4 ? '<span class="time-divider" aria-hidden="true"></span>' : ""}${renderPillar(item, variant, index)}`).join("")}
    </div>
    ${state.hourPickerOpen ? renderHourPicker() : ""}
  </section>`;
}

function renderPillar(item, variant, index) {
  const stem = item.pillar[0] || "—";
  const branch = item.pillar[1] || "—";
  const editable = item.position === "hour";
  const changed = index === 3 && variant.pillars[3] !== fixture.formal.pillars[3];
  const nodeStem = variant.nodes.find((node) => node.node_key === `${item.position}_stem`);
  const nodeBranch = variant.nodes.find((node) => node.node_key === `${item.position}_branch`);
  const hidden = item.time ? [] : (nodeBranch?.hidden_stems || []);
  const tenGod = item.time ? "时间材料" : tenGodLabel(nodeStem?.ten_god);
  const attrs = editable ? 'data-action="toggle-hour-picker" role="button" tabindex="0"' : "";
  return `<article class="pillar ${editable ? "editable" : ""} ${changed ? "changed" : ""} ${item.time ? "time-slot" : ""}" ${attrs}>
    <div class="pillar-label">${item.label}${!item.time && !editable ? '<span class="lock-mark" title="已锁定">◆</span>' : ""}</div>
    <div class="stem-branch">
      <strong class="node-${ELEMENTS[stem] || "earth"}">${stem}</strong>
      <strong class="branch node-${ELEMENTS[branch] || "earth"}">${branch}</strong>
    </div>
    <div class="ten-god">${escapeHtml(tenGod || "")}</div>
    <div class="hidden-stems">${hidden.length ? `藏 ${hidden.map((entry) => entry.stem).join(" · ")}` : item.time ? "时间层" : ""}</div>
  </article>`;
}

function renderHourPicker() {
  return `<div class="hour-picker">
    <div class="hour-picker-head">
      <div><h3>选择一个合法出生时辰</h3><p>系统重新排出时柱并重建 Graph；正式命盘保持不变。</p></div>
      <span class="status-chip hypothetical">Sandbox only</span>
    </div>
    <div class="hour-options">
      ${fixture.variants.map((item, index) => `<button class="hour-option ${index === state.variantIndex ? "active" : ""} ${index === fixture.baseline_variant_index ? "baseline" : ""}" data-action="select-hour" data-index="${index}">
        <strong>${escapeHtml(item.pillars[3])}</strong>
        <span>${escapeHtml(item.time_range.split(" · ")[0])}</span>
      </button>`).join("")}
    </div>
  </div>`;
}

function renderPathWorkspace(variant) {
  const path = currentPathModel();
  return `<section class="path-workspace" aria-labelledby="pathTitle">
    <div class="path-heading">
      <div><p class="eyebrow">Path Studio</p><h2 id="pathTitle">做功路径工作室</h2><p>先看一条路径，再按需展开节点；完整关系网留给内部 Inspector。</p></div>
      <button class="text-command" data-action="play-path" ${path.nodes.length ? "" : "disabled"}>播放路径</button>
    </div>
    <div class="path-tabs" role="tablist">
      ${pathLensButton("reference", "正式路径参考")}
      ${pathLensButton("candidate", "Graph 候选")}
      ${pathLensButton("draft", "我的路径")}
    </div>
    <div class="path-canvas">
      ${renderPathTrack(path)}
      ${renderPathMeta(path, variant)}
    </div>
    ${renderNodePalette(variant)}
  </section>`;
}

function pathLensButton(lens, label) {
  return `<button type="button" class="path-tab ${state.pathLens === lens ? "active" : ""}" data-action="path-lens" data-lens="${lens}" aria-selected="${state.pathLens === lens}">${label}</button>`;
}

function currentPathModel(forSnapshot = null) {
  const variant = forSnapshot ? fixture.variants[forSnapshot.variantIndex] : currentVariant();
  const lens = forSnapshot ? forSnapshot.pathLens : state.pathLens;
  const draftNodes = forSnapshot ? forSnapshot.draftNodes : state.draftNodes;
  if (lens === "candidate") return candidatePathModel(variant);
  if (lens === "draft") return draftPathModel(variant, draftNodes);
  return referencePathModel(variant);
}

function referencePathModel(variant) {
  const ordered = fixture.formal.path.ordered_nodes;
  const nodes = ordered.map((entry) => {
    const current = variant.nodes.find((node) => node.node_key === entry.anchor);
    return { key: entry.anchor, label: current?.label || entry.label, subtitle: POSITION_LABELS[entry.anchor] || entry.anchor, element: current?.element || ELEMENTS[entry.label] || "" };
  });
  const segments = [];
  for (let index = 0; index < ordered.length - 1; index += 1) {
    const from = ordered[index].anchor;
    const to = ordered[index + 1].anchor;
    const continuity = variant.formal_path_reference.segments.find((item) => item.baseline.from_anchor === from && item.baseline.to_anchor === to);
    const preserved = continuity?.status === "preserved";
    segments.push({
      label: preserved
        ? continuity.variant_relation.label
        : `原关系已断：${continuity?.baseline?.relation_label || "缺少结构关系"}`,
      status: preserved ? "committed" : "missing",
    });
  }
  return { authority: "committed-reference", nodes, segments, empty: false };
}

function candidatePathModel(variant) {
  const path = variant.graph_candidate;
  if (!path) return { authority: "candidate", nodes: [], segments: [], empty: true };
  return {
    authority: "candidate",
    nodes: path.node_keys.map((key, index) => {
      const node = variant.nodes.find((item) => item.node_key === key);
      return { key, label: path.node_labels[index], subtitle: POSITION_LABELS[key] || key, element: node?.element || ELEMENTS[path.node_labels[index]] || "" };
    }),
    segments: path.segments.map((item) => ({ label: item.label, status: "candidate" })),
    empty: false,
  };
}

function draftPathModel(variant, draftNodes) {
  const nodes = draftNodes.map((key) => {
    const node = variant.nodes.find((item) => item.node_key === key);
    return { key, label: node?.label || "?", subtitle: POSITION_LABELS[key] || key, element: node?.element || "" };
  });
  const segments = [];
  for (let index = 0; index < draftNodes.length - 1; index += 1) {
    const from = draftNodes[index];
    const to = draftNodes[index + 1];
    const exact = variant.relations.find((item) => item.from_key === from && item.to_key === to);
    const reverse = variant.relations.find((item) => item.from_key === to && item.to_key === from);
    segments.push({
      label: exact?.label || (reverse ? `方向相反：${reverse.label}` : "此处没有可用关系"),
      status: exact ? "draft" : "missing",
    });
  }
  return { authority: "user-draft", nodes, segments, empty: !nodes.length };
}

function renderPathTrack(path) {
  if (path.empty) {
    return `<div class="empty-state"><h3>${state.pathLens === "draft" ? "从下方选择节点，画出你的路径" : "当前没有可展示的结构路径"}</h3><p>${state.pathLens === "draft" ? "系统只查验相邻节点是否存在已编译关系，不替你补线。" : "不会从文字判断中猜测连线。"}</p></div>`;
  }
  return `<div class="path-track">
    ${path.nodes.map((node, index) => {
      const nodePlaying = state.playStep >= index * 2;
      const segment = path.segments[index];
      const segmentPlaying = segment && state.playStep >= index * 2 + 1;
      return `${renderPathNode(node, nodePlaying)}${segment ? renderPathSegment(segment, segmentPlaying) : ""}`;
    }).join("")}
  </div>`;
}

function renderPathNode(node, playing) {
  return `<button class="path-node node-${node.element || ELEMENTS[node.label] || "earth"} ${playing ? "active" : ""}" data-action="select-node" data-node-key="${escapeAttr(node.key)}">
    <strong>${escapeHtml(node.label)}</strong><span>${escapeHtml(node.subtitle)}</span>
  </button>`;
}

function renderPathSegment(segment, playing) {
  const type = segment.status === "committed" ? "" : segment.status;
  return `<div class="path-segment ${type} ${playing ? "playing" : ""}">
    <span>${escapeHtml(segment.label)}</span>${segment.status === "missing" ? '<i class="break-mark" aria-hidden="true"></i>' : ""}
  </div>`;
}

function renderPathMeta(path, variant) {
  if (path.empty) return "";
  const missing = path.segments.filter((item) => item.status === "missing").length;
  const labels = {
    "committed-reference": '<span class="status-chip committed">LifeCase 正式路径参考</span>',
    candidate: '<span class="status-chip candidate">Graph 实验候选</span>',
    "user-draft": '<span class="status-chip hypothetical">用户草稿</span>',
  };
  const note = state.pathLens === "reference" && state.mode !== "formal"
    ? `${variant.formal_path_reference.preserved_segments}/${variant.formal_path_reference.total_segments} 段结构关系仍存在`
    : missing ? `${missing} 段缺少可用关系` : "当前路径各段均有结构关系";
  return `<div class="path-meta">${labels[path.authority] || ""}<span>${escapeHtml(note)}</span></div>`;
}

function renderNodePalette(variant) {
  const draft = state.pathLens === "draft";
  return `<div class="node-palette">
    <div class="node-palette-head">
      <div><h3>${draft ? "依次选择节点" : "结构节点"}</h3><p>${draft ? "最多保留四个节点；顺序决定连接方向。" : "点击可查看五行、十神与来源。"}</p></div>
      ${draft ? '<button class="text-command" data-action="clear-draft">清空草稿</button>' : '<button class="text-command" data-action="start-draft">自己画一条</button>'}
    </div>
    <div class="node-list">
      ${variant.nodes.filter((node) => node.node_type === "stem" || node.node_type === "branch").map((node) => `<button class="node-token node-${node.element} ${state.draftNodes.includes(node.node_key) ? "selected" : ""}" data-action="select-node" data-node-key="${escapeAttr(node.node_key)}" title="${escapeAttr(POSITION_LABELS[node.node_key] || node.node_key)}">${escapeHtml(node.label)}</button>`).join("")}
    </div>
  </div>`;
}

function renderInsightPanel(variant) {
  const selected = variant.nodes.find((node) => node.node_key === state.selectedNode);
  const continuity = variant.formal_path_reference.continuity_status;
  const title = state.mode === "formal"
    ? "正式主路径依赖时柱壬午"
    : continuity === "preserved"
      ? "原正式路径的结构关系完整保留"
      : continuity === "partial"
        ? "原正式路径只保留了一部分"
        : "原正式路径在这个时辰不再闭合";
  const copy = state.mode === "formal"
    ? "这条路径已由 LifeCase 提交，并由 typed Graph 证据唯一定位。"
    : "这只是对原正式路径的结构连续性检查；变体尚未形成新的专业命理判断。";
  return `<aside class="insight-panel" aria-label="变化解释">
    <section class="panel-section">
      <p class="panel-kicker">本次实验回答</p>
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(copy)}</p>
      <ul class="change-list">
        <li><strong>时柱</strong><span>${fixture.formal.pillars[3]} → ${variant.pillars[3]}</span></li>
        <li><strong>路径</strong><span>保留 ${variant.formal_path_reference.preserved_segments}/${variant.formal_path_reference.total_segments} 段</span></li>
        <li><strong>关系</strong><span>新增 ${variant.diff.added_relation_count} · 移除 ${variant.diff.removed_relation_count}</span></li>
      </ul>
    </section>
    <section class="panel-section">
      <p class="panel-kicker">${selected ? "选中节点" : "认识论边界"}</p>
      ${selected ? renderSelectedNode(selected) : `<h3>正式、候选与草稿不会混在一起</h3><p>正式路径来自 LifeCase；Graph 只给结构候选；你画的路径始终是用户草稿。</p>`}
    </section>
    <section class="panel-section">
      <details class="source-details">
        <summary>查看来源与边界</summary>
        <code>${escapeHtml(state.pathLens === "reference" ? "source: committed LifeCase + deterministic structural comparison" : state.pathLens === "candidate" ? "source: experimental Graph path explorer" : "source: user draft + compiled relation lookup")}</code>
      </details>
    </section>
  </aside>`;
}

function renderSelectedNode(node) {
  const hidden = node.hidden_stems?.length
    ? `藏干：${node.hidden_stems.map((item) => `${item.stem}${tenGodLabel(item.ten_god) ? `（${tenGodLabel(item.ten_god)}）` : ""}`).join("、")}`
    : "此节点没有藏干展开。";
  return `<h3>${escapeHtml(node.label)} · ${escapeHtml(POSITION_LABELS[node.node_key] || node.position)}</h3>
    <p>五行：${elementLabel(node.element)}　阴阳：${node.polarity === "yin" ? "阴" : node.polarity === "yang" ? "阳" : "—"}<br>${escapeHtml(tenGodLabel(node.ten_god) || "地支角色需从藏干展开")}<br>${escapeHtml(hidden)}</p>`;
}

function renderYearPanel() {
  const current = fixture.year_dial[state.yearIndex];
  return `<section class="year-panel" aria-labelledby="yearTitle">
    <div class="year-panel-head">
      <div><h2 id="yearTitle">流年拨盘</h2><p>选择其他年份只加入假设时间信号；当前 Fixture 没有正式的路径激活或受阻结论。</p></div>
      <span class="status-chip ${current.source_mode === "official" ? "committed" : "hypothetical"}">${current.source_mode === "official" ? "正式时间材料" : "假设流年"}</span>
    </div>
    <div class="year-dial">
      ${fixture.year_dial.map((item, index) => `<button class="year-stop ${index === state.yearIndex ? "active" : ""}" data-action="select-year" data-index="${index}" ${state.mode === "formal" && item.source_mode !== "official" ? "disabled" : ""}>
        <i class="year-dot" aria-hidden="true"></i><strong>${item.year}</strong><span>${item.pillar}</span><em>${item.source_mode === "official" ? "正式" : ""}</em>
      </button>`).join("")}
    </div>
  </section>`;
}

function renderCompare() {
  const a = state.saved.a || formalSnapshot();
  const b = state.saved.b || formalSnapshot();
  const va = fixture.variants[a.variantIndex];
  const vb = fixture.variants[b.variantIndex];
  const ya = fixture.year_dial[a.yearIndex];
  const yb = fixture.year_dial[b.yearIndex];
  return `<section class="compare-board" aria-labelledby="compareTitle">
    <div class="compare-heading"><div><p class="eyebrow">A/B Compare</p><h2 id="compareTitle">两个实验状态，差异直接放在中间</h2><p>比较的是结构存在性，不是吉凶分数。</p></div></div>
    <div class="compare-grid">
      ${renderCompareSide("实验 A", va, ya)}
      <div class="compare-center">
        <h3>结构差异</h3>
        <ul class="change-list">
          <li><strong>时柱</strong><span>${va.pillars[3]} → ${vb.pillars[3]}</span></li>
          <li><strong>流年</strong><span>${ya.year} ${ya.pillar} → ${yb.year} ${yb.pillar}</span></li>
          <li><strong>路径 A</strong><span>${continuityLabel(va.formal_path_reference.continuity_status)}</span></li>
          <li><strong>路径 B</strong><span>${continuityLabel(vb.formal_path_reference.continuity_status)}</span></li>
          <li><strong>关系差</strong><span>B 新增 ${vb.diff.added_relation_count}，移除 ${vb.diff.removed_relation_count}</span></li>
        </ul>
      </div>
      ${renderCompareSide("实验 B", vb, yb)}
    </div>
  </section>`;
}

function renderCompareSide(label, variant, year) {
  const pillars = [...variant.pillars, fixture.formal.luck_pillar, year.pillar];
  return `<div class="compare-side"><h3>${label}</h3>
    <div class="mini-pillars">${pillars.map((pillar, index) => `<div class="mini-pillar"><strong class="node-${ELEMENTS[pillar[0]]}">${pillar[0]}</strong><span class="node-${ELEMENTS[pillar[1]]}">${pillar[1]}</span><small>${[...PILLAR_LABELS, "大运", "流年"][index]}</small></div>`).join("")}</div>
    <div class="panel-section" style="padding-left:0;padding-right:0;margin-top:18px"><p class="panel-kicker">正式路径参考</p><h3>${continuityLabel(variant.formal_path_reference.continuity_status)}</h3><p>保留 ${variant.formal_path_reference.preserved_segments}/${variant.formal_path_reference.total_segments} 段。变体结果不自动成为正式判断。</p></div>
  </div>`;
}

function renderAbu() {
  const variant = currentVariant();
  const message = state.mode === "compare"
    ? "A/B 只比较结构差异，不把实验结果写回正式盘。"
    : state.mode === "formal"
      ? "先创建一个实验副本，再试着换一个时辰。正式盘不会动。"
      : variant.formal_path_reference.continuity_status === "preserved"
        ? "这个时辰保留了正式路径的两段结构关系。"
        : variant.formal_path_reference.continuity_status === "partial"
          ? "这里很有意思：路径只剩下一段。点“播放路径”看看断在哪里。"
          : "原路径在这个时辰不再闭合。可以看看 Graph 候选，或自己画一条。";
  return `<div class="abu-guide ${state.abuOpen ? "open" : "collapsed"}">
    <button class="abu-avatar" type="button" data-action="toggle-abu" aria-label="${state.abuOpen ? "收起阿布解释" : "展开阿布解释"}" aria-expanded="${state.abuOpen}">
      <img src="/assets/abu/v4-video-derived/web/abu_idle_blink_v4.webp" alt="阿布">
    </button>
    <div class="abu-bubble" aria-live="polite" ${state.abuOpen ? "" : "hidden"}>${escapeHtml(message)}</div>
  </div>`;
}

function currentVariant() {
  return fixture.variants[state.variantIndex];
}

function tenGodLabel(value) {
  return TEN_GOD_LABELS[value] || value || "";
}

function elementLabel(value) {
  return { wood: "木", fire: "火", earth: "土", metal: "金", water: "水" }[value] || "—";
}

function continuityLabel(value) {
  return { preserved: "结构完整保留", partial: "部分保留", broken: "不再闭合" }[value] || "未比较";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
