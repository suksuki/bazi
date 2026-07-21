import type {
  ApprovedClaim,
  ApprovedReasoningStep,
  CaseWorkspaceEnvelope,
  CanvasContextPack,
  CanvasNode,
  CanvasRelation,
  CanvasSemanticSlot,
  ExperienceCaseSummary,
  MingliExperienceEnvelope,
  NarrationManifest,
  ReadOnlySixPillarCanvas,
} from "./contracts";
import type { ProductArea, UiState, WorkspaceSurface } from "./state";

export interface ExperienceViewModel {
  accountName: string;
  accountRole: string;
  cases: ExperienceCaseSummary[];
  activeCaseId: string;
  availableAreas: ProductArea[];
  availableSurfaces: WorkspaceSurface[];
  workspace: CaseWorkspaceEnvelope;
  envelope: MingliExperienceEnvelope;
  narrationManifest: NarrationManifest | null;
  canvas: ReadOnlySixPillarCanvas | null;
  canvasContext: CanvasContextPack | null;
  ui: UiState;
}

const elementLabel: Record<string, string> = {
  wood: "木",
  fire: "火",
  earth: "土",
  metal: "金",
  water: "水",
};

const polarityLabel: Record<string, string> = { yin: "阴", yang: "阳" };

export function renderExperience(view: ExperienceViewModel): string {
  const claim = view.envelope.approved_claims[0];
  const steps = view.envelope.approved_reasoning_steps;
  const fullThesis = claim?.approved_meaning || "命盘事实已经确认，正式整盘认知尚未提交。";
  const thesis = firstSentence(fullThesis);
  const pathSummary = steps[steps.length - 1]?.conclusion || "正式主路径仍在形成。";
  const condition = claim?.conditions[0] || "当前还没有足够依据写下成立条件。";
  const uncertainty = view.envelope.uncertainty.reasons[0] || "当前没有额外未决项。";
  return `<div class="deepbeing-shell" data-product-area-current="${escapeAttr(view.ui.productArea)}">
    ${renderProductSidebar(view)}
    <div class="deepbeing-stage">
      ${renderMobileHeader(view)}
      <main class="product-main">
        ${view.ui.productArea === "world" ? renderLifeWorld(view, thesis, fullThesis, pathSummary, condition, uncertainty) : ""}
        ${view.ui.productArea === "workbench" ? renderWorkbench(view) : ""}
        ${view.ui.productArea === "lab" ? renderMingliLab(view) : ""}
      </main>
    </div>
    ${renderMobileNavigation(view)}
    ${renderAbuDock(view)}
  </div>`;
}

function renderWorkbench(view: ExperienceViewModel): string {
  const claim = view.envelope.approved_claims[0];
  const steps = view.envelope.approved_reasoning_steps;
  const condition = claim?.conditions[0] || "当前还没有足够依据写下成立条件。";
  const uncertainty = view.envelope.uncertainty.reasons[0] || "当前没有额外未决项。";
  const pathSummary = steps[steps.length - 1]?.conclusion || "正式主路径仍在形成。";
  const fullThesis = claim?.approved_meaning || "命盘事实已经确认，正式整盘认知尚未提交。";
  const thesis = firstSentence(fullThesis);

  return `
    ${renderWorkspaceNavigation(view)}

    <div class="workbench-surface" data-workspace-current-surface="${escapeAttr(view.ui.workspaceSurface)}">
      ${view.ui.workspaceSurface === "overview" ? `<section class="opening-band" id="baseline-summary" data-anchor="baseline-summary">
        <div class="opening-copy">
          <p class="section-kicker">看见命局 · 当前基线</p>
          <h1>${escapeHtml(thesis)}</h1>
          <p class="opening-lede">先看最重要的四件事，不把整份命局一次塞给你。</p>
          <div class="opening-actions">
            <button class="primary-command" type="button" data-command="listen">
              ${view.ui.narrationStatus === "playing" ? "暂停阿布" : "听阿布讲"}
            </button>
            <button class="text-command" type="button" data-command="focus-pillars">先看四柱</button>
          </div>
        </div>
        <div class="scan-strip" aria-label="整盘快速摘要">
          ${summaryItem("主路径", pathSummary, "baseline-work-path")}
          ${summaryItem("成立条件", condition, "baseline-condition")}
          ${summaryItem("最大未决", uncertainty, "baseline-uncertainty")}
        </div>
      </section>

      ${renderCollapsibleSection({
        id: "pillars",
        anchor: "four-pillars",
        tone: "facts",
        eyebrow: "命盘事实",
        title: "四柱是这份命局的底图",
        summary: view.envelope.allowed_chart_facts.map((item) => item.stem + item.branch).join(" · "),
        expanded: view.ui.expandedSections.pillars,
        body: renderPillars(view.envelope, view.ui.selectedAnchor),
      })}

      ${renderCollapsibleSection({
        id: "path",
        anchor: "baseline-work-path",
        tone: "cognition",
        eyebrow: "整盘认知",
        title: "这张盘如何运行",
        summary: pathSummary,
        expanded: view.ui.expandedSections.path,
        body: renderPath(fullThesis, steps, view.ui.selectedAnchor),
      })}

      ${renderCollapsibleSection({
        id: "boundaries",
        anchor: "baseline-condition",
        tone: "boundaries",
        eyebrow: "条件与未决",
        title: "判断成立，也要知道边界在哪里",
        summary: condition,
        expanded: view.ui.expandedSections.boundaries,
        body: renderBoundaries(claim, view.envelope, view.ui.selectedAnchor),
      })}` : ""}

      ${view.ui.workspaceSurface === "onecanvas" && view.canvas ? `${renderCollapsibleSection({
        id: "canvas",
        anchor: "temporal-canvas",
        tone: "canvas",
        eyebrow: "时间结构",
        title: "看结构怎样进入当前时间",
        summary: `${view.canvas.source.luck_pillar}大运 · ${view.canvas.source.analysis_year || "当前"}${view.canvas.source.annual_pillar}流年`,
        expanded: view.ui.expandedSections.canvas ?? true,
        body: renderReadOnlyCanvas(view.canvas, view.ui, view.canvasContext, false),
      })}` : ""}

      ${view.ui.workspaceSurface === "theater" ? renderNarrationWorkspace(view, thesis) : ""}

      <section class="closing-band">
        <p>知命，而后知己</p>
        <span>只说已经有充分依据的部分，也保留仍需验证的地方。</span>
      </section>
    </div>
  `;
}

function renderWorkspaceNavigation(view: ExperienceViewModel): string {
  const labels: Record<string, string> = {
    overview: "命局概览",
    onecanvas: "结构",
    theater: "阿布讲解",
  };
  const detail = view.ui.workspaceSurface === "onecanvas"
    ? "原局、大运与流年沿同一组语义对象展开"
    : view.ui.workspaceSurface === "theater"
      ? "文字先到，阿布沿同一份正式认知讲解"
      : "先看整盘重心，再按需展开结构与边界";
  return `<header class="workbench-header">
    <div><p>命盘工作台 · ${escapeHtml(activeCaseName(view))}</p><h1>${labels[view.ui.workspaceSurface]}</h1><span>${detail}</span></div>
    <nav class="workspace-navigation" aria-label="命盘工作台视图">
      <div class="workspace-tabs">${view.availableSurfaces.map((surface) => `<button type="button" data-workspace-surface="${surface}" aria-pressed="${surface === view.ui.workspaceSurface}" class="${surface === view.ui.workspaceSurface ? "active" : ""}">${labels[surface]}</button>`).join("")}</div>
    </nav>
  </header>`;
}

function renderLifeWorld(
  view: ExperienceViewModel,
  thesis: string,
  fullThesis: string,
  pathSummary: string,
  condition: string,
  uncertainty: string,
): string {
  const pillars = view.envelope.allowed_chart_facts
    .filter((item) => item.fact_type === "pillar")
    .map((item) => item.stem + item.branch)
    .join(" · ");
  return `<div class="life-world">
    <section class="world-hero" data-anchor="baseline-summary">
      <div class="world-copy">
        <p class="section-kicker">我的生命世界 · ${escapeHtml(activeCaseName(view))}</p>
        <h1>${escapeHtml(thesis)}</h1>
        <p>${escapeHtml(firstSentence(pathSummary))}</p>
        <div class="world-actions">
          <button class="primary-command" type="button" data-command="listen">${view.ui.narrationStatus === "playing" ? "暂停阿布" : "听阿布讲"}</button>
          <button class="text-command" type="button" data-product-area="workbench">打开命盘</button>
        </div>
      </div>
      <div class="life-tree" aria-label="命、事、人的生命脉络">
        <span class="tree-line tree-line-left" aria-hidden="true"></span>
        <span class="tree-line tree-line-right" aria-hidden="true"></span>
        <button type="button" class="tree-node tree-nature" data-product-area="workbench">
          <small>命</small><strong>${escapeHtml(pillars || "四柱待确认")}</strong><span>先天底图</span>
        </button>
        <button type="button" class="tree-node tree-events" data-select-anchor="baseline-work-path" data-message="${escapeAttr(pathSummary)}">
          <small>事</small><strong>${escapeHtml(firstSentence(pathSummary))}</strong><span>${escapeHtml(view.workspace.state.selected_period)}</span>
        </button>
        <button type="button" class="tree-node tree-growth" data-command="toggle-abu">
          <small>人</small><strong>${escapeHtml(firstSentence(condition))}</strong><span>当前行动条件</span>
        </button>
        <div class="tree-trunk" aria-hidden="true"><i></i><i></i><i></i></div>
        <img src="/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp" alt="阿布在生命树旁等待">
      </div>
    </section>
    <section class="world-ledger" aria-label="生命记录">
      <header><p>生命记录</p><h2>命是起点，现实让理解继续生长</h2></header>
      <div class="world-ledger-flow">
        <button type="button" data-product-area="workbench"><span>命盘基线</span><strong>${escapeHtml(pillars || "等待建档")}</strong><small>${escapeHtml(view.envelope.source.life_case_version || "命盘事实")}</small></button>
        <button type="button" data-select-anchor="baseline-work-path" data-message="${escapeAttr(fullThesis)}"><span>当前认知</span><strong>${escapeHtml(thesis)}</strong><small>来自正式 LifeCase</small></button>
        <button type="button" data-command="toggle-abu"><span>继续观察</span><strong>${escapeHtml(firstSentence(uncertainty))}</strong><small>与阿布一起验证</small></button>
      </div>
    </section>
  </div>`;
}

function renderMingliLab(view: ExperienceViewModel): string {
  if (!view.canvas) return `<section class="lab-empty"><p>Mingli Lab</p><h1>这份命盘尚未形成可研究的结构投影</h1></section>`;
  const stage = view.canvas.stages[view.ui.canvasStage];
  const potentialCount = stage.spec.relations.filter((item) => item.relation_state === "potential").length;
  const sourceCount = new Set(stage.spec.relations.flatMap((item) => item.trace.source_refs)).size;
  const hiddenCount = stage.spec.nodes.filter((item) => item.node_type.includes("hidden")).length;
  return `<div class="mingli-lab">
    <header class="lab-header">
      <div><p>Mingli Lab · ${escapeHtml(activeCaseName(view))}</p><h1>同一命局的研究镜头</h1><span>候选关系与证据留在研究层；正式 Case 不在这里被改写。</span></div>
      <code>${escapeHtml(view.workspace.state.scene_source_hash.slice(0, 18))}</code>
    </header>
    <div class="lab-evidence-rail" aria-label="当前研究范围">
      <span><small>潜在关系</small><strong>${potentialCount}</strong></span>
      <span><small>藏干节点</small><strong>${hiddenCount}</strong></span>
      <span><small>来源引用</small><strong>${sourceCount}</strong></span>
      <span><small>正式写入</small><strong>关闭</strong></span>
    </div>
    <section class="lab-canvas"><p class="lab-lens-label">命理师 Lens · 潜在关系场</p>${renderReadOnlyCanvas(view.canvas, view.ui, view.canvasContext, true)}</section>
  </div>`;
}

function renderProductSidebar(view: ExperienceViewModel): string {
  return `<aside class="product-sidebar">
    <a class="brand" href="/experience" aria-label="DeepBeing 首页"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence"><span>DeepBeing</span></a>
    ${renderProductNavigation(view, "sidebar")}
    <div class="sidebar-context">${renderCaseSelector(view.cases, view.activeCaseId)}<small>${escapeHtml(view.envelope.source.life_case_version || "命盘事实")}</small></div>
    <div class="sidebar-account"><span>${escapeHtml(view.accountName)}</span><a href="/app">档案</a></div>
  </aside>`;
}

function renderMobileHeader(view: ExperienceViewModel): string {
  const labels: Record<ProductArea, string> = { world: "我的生命世界", workbench: "命盘工作台", lab: "Mingli Lab" };
  return `<header class="mobile-header"><a href="/experience"><img src="/assets/deepbazi_symbol.png" alt="DeepBazi"></a><strong>${labels[view.ui.productArea]}</strong>${renderCaseSelector(view.cases, view.activeCaseId)}</header>`;
}

function renderMobileNavigation(view: ExperienceViewModel): string {
  return `<nav class="mobile-product-navigation" aria-label="DeepBeing 主要区域">${renderProductNavigation(view, "mobile")}</nav>`;
}

function renderProductNavigation(view: ExperienceViewModel, placement: "sidebar" | "mobile"): string {
  const items: Array<{ area: ProductArea; index: string; label: string; detail: string }> = [
    { area: "world", index: "01", label: "我的生命世界", detail: "生命树与现实记录" },
    { area: "workbench", index: "02", label: "命盘工作台", detail: "概览、结构与阿布" },
    { area: "lab", index: "03", label: "Mingli Lab", detail: "候选、反例与证据" },
  ];
  return `<div class="product-navigation is-${placement}">${items.filter((item) => view.availableAreas.includes(item.area)).map((item) => `<button type="button" data-product-area="${item.area}" aria-current="${view.ui.productArea === item.area ? "page" : "false"}" class="${view.ui.productArea === item.area ? "active" : ""}"><i>${item.index}</i><span><strong>${item.label}</strong><small>${item.detail}</small></span></button>`).join("")}</div>`;
}

function activeCaseName(view: ExperienceViewModel): string {
  return view.cases.find((item) => item.case_id === view.activeCaseId)?.display_name || "当前命盘";
}

function renderNarrationWorkspace(view: ExperienceViewModel, thesis: string): string {
  const segments = view.narrationManifest?.segments || [];
  return `<section class="narration-workspace" data-anchor="abu-narration">
    <header><p>阿布讲解</p><h1>${escapeHtml(thesis)}</h1><span>从整盘重心开始，沿四柱、路径、条件与未决逐段展开。</span></header>
    <div class="narration-workspace-actions">
      <button class="primary-command" type="button" data-command="listen">${view.ui.narrationStatus === "playing" ? "暂停" : "从头听"}</button>
      ${view.ui.narrationStatus !== "idle" ? '<button class="text-command" type="button" data-command="stop">停止</button>' : ""}
    </div>
    <ol>${segments.map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><small>${String(index + 1).padStart(2, "0")}</small><span><strong>${escapeHtml(item.title)}</strong><em>${escapeHtml(item.text)}</em></span><b aria-hidden="true">▶</b></button></li>`).join("")}</ol>
  </section>`;
}

function renderReadOnlyCanvas(
  canvas: ReadOnlySixPillarCanvas,
  ui: UiState,
  context: CanvasContextPack | null,
  researchLens: boolean,
): string {
  const stage = canvas.stages[ui.canvasStage];
  const exposedRelations = researchLens
    ? stage.spec.relations
    : stage.spec.relations.filter((item) => item.relation_state !== "potential");
  const exposedRelationRefs = new Set(exposedRelations.map((item) => item.relation_ref));
  const displayLayers = stage.layers.map((item) => {
    const relationRefs = item.relation_refs.filter((ref) => exposedRelationRefs.has(ref));
    return { ...item, relation_refs: relationRefs, count: relationRefs.length, available: relationRefs.length > 0 };
  });
  const layer = displayLayers.find((item) => item.layer_id === ui.canvasLayer && item.available)
    || displayLayers.find((item) => item.layer_id === stage.default_layer_id && item.available)
    || displayLayers.find((item) => item.available)
    || displayLayers[0];
  const visibleRelations = new Set(layer?.relation_refs || []);
  const nodesByRef = new Map(stage.spec.nodes.map((item) => [item.node_ref, item]));
  const selected = ui.selectedCanvasObject || stage.spec.semantic_slots[0]?.slot_ref || "";
  const activeRelations = exposedRelations.filter((item) => visibleRelations.has(item.relation_ref));
  const range = canvas.source.luck_year_range.length === 2
    ? `${canvas.source.luck_year_range[0]}–${canvas.source.luck_year_range[1]}`
    : "当前阶段";

  return `<div class="temporal-viewer" data-canvas-stage-root="${escapeAttr(ui.canvasStage)}">
    <div class="temporal-toolbar">
      <div class="stage-switch" role="tablist" aria-label="查看时间阶段">
        ${canvas.stage_order.map((item, index) => {
          const projection = canvas.stages[item];
          return `<button type="button" role="tab" data-canvas-stage="${item}" aria-selected="${item === ui.canvasStage}" class="${item === ui.canvasStage ? "active" : ""}">
            <small>0${index + 1}</small><span>${escapeHtml(projection.title)}</span>
          </button>`;
        }).join("")}
      </div>
      <div class="temporal-status">
        <span>${escapeHtml(ui.canvasStage === "natal" ? "原局基线" : ui.canvasStage === "luck" ? range : `${canvas.source.analysis_year || "当前"}年`)}</span>
        <strong>${escapeHtml(stage.summary)}</strong>
      </div>
    </div>

    <div class="layer-switch" role="tablist" aria-label="关系图层">
      ${displayLayers.map((item) => `<button type="button" role="tab" data-canvas-layer="${escapeAttr(item.layer_id)}" aria-selected="${item.layer_id === layer?.layer_id}" class="${item.layer_id === layer?.layer_id ? "active" : ""}"${item.available ? "" : " disabled"}>
        <span>${escapeHtml(item.label)}</span><small>${item.count}</small>
      </button>`).join("")}
    </div>

    <div class="canvas-board" data-layer="${escapeAttr(layer?.layer_id || "")}">
      <div class="six-pillar-scroll">
        <div class="six-pillar-rail" style="--pillar-count:${stage.spec.semantic_slots.length}">
          ${stage.spec.semantic_slots.map((slot) => renderCanvasPillar(slot, nodesByRef, selected, researchLens)).join("")}
        </div>
        ${renderCanvasRelations(stage.spec.semantic_slots, stage.spec.nodes, activeRelations, stage.spec.paths.flatMap((item) => item.relation_refs), selected)}
      </div>
      <p class="layer-caption"><strong>${escapeHtml(layer?.label || "当前图层")}</strong>${escapeHtml(layer?.description || "当前没有可显示的关系。")}</p>
    </div>

    <div class="canvas-reading-grid">
      ${renderCanvasChanges(stage.change_groups, selected, ui.canvasStage)}
      ${renderCanvasInspector(stage.spec, selected, context, ui.canvasContextStatus)}
    </div>

    <div class="canvas-boundary ${canvas.path_availability.status === "available" ? "is-ready" : "is-limited"}">
      <span>${canvas.path_availability.status === "available" ? "主路径已对齐" : "主路径未补画"}</span>
      <p>${escapeHtml(canvas.path_availability.message)}</p>
      <small>当前查看只读取正式案例，不修改原局，也不调用 LLM。</small>
    </div>
  </div>`;
}

function renderCanvasPillar(
  slot: CanvasSemanticSlot,
  nodesByRef: Map<string, CanvasNode>,
  selected: string,
  showHiddenStems: boolean,
): string {
  const nodes = [...nodesByRef.values()].filter((item) => item.semantic_slot_ref === slot.slot_ref);
  const stemNode = nodes.find((item) => item.node_type.includes("stem") && !item.node_type.includes("hidden"));
  const branchNode = nodes.find((item) => item.node_type.includes("branch"));
  const temporal = slot.slot_type === "luck" || slot.slot_type === "year";
  return `<article class="canvas-pillar${temporal ? " is-temporal" : ""}${selected === slot.slot_ref ? " is-selected" : ""}" data-slot-type="${escapeAttr(slot.slot_type)}">
    <button type="button" class="canvas-pillar-label" data-canvas-object="${escapeAttr(slot.slot_ref)}"><span>${escapeHtml(slot.label)}</span>${slot.immutable ? "<small>原局</small>" : "<small>时间</small>"}</button>
    <button type="button" class="canvas-character element-${escapeAttr(stemNode?.element || "")}${selected === stemNode?.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr(stemNode?.polarity || "")}" data-canvas-object="${escapeAttr(stemNode?.node_ref || slot.slot_ref)}" aria-label="${escapeAttr(`${slot.label}天干${slot.stem}`)}">
      <small>${escapeHtml(stemNode?.ten_god === "day_master" ? "日主" : tenGodLabel(stemNode?.ten_god || "天干"))}</small><strong>${escapeHtml(slot.stem)}</strong>
    </button>
    <i aria-hidden="true"></i>
    <button type="button" class="canvas-character element-${escapeAttr(branchNode?.element || "")}${selected === branchNode?.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr(branchNode?.polarity || "")}" data-canvas-object="${escapeAttr(branchNode?.node_ref || slot.slot_ref)}" aria-label="${escapeAttr(`${slot.label}地支${slot.branch}`)}">
      <small>地支</small><strong>${escapeHtml(slot.branch)}</strong>
    </button>
    ${showHiddenStems ? `<div class="canvas-hidden-stems"><span>藏干</span>${slot.hidden_stems.map((item) => `<b>${escapeHtml(item)}</b>`).join("") || "<em>无</em>"}</div>` : ""}
  </article>`;
}

function renderCanvasRelations(
  slots: CanvasSemanticSlot[],
  nodes: CanvasNode[],
  relations: CanvasRelation[],
  pathRelationRefs: string[],
  selected: string,
): string {
  const slotIndex = new Map(slots.map((item, index) => [item.slot_ref, index]));
  const nodesByRef = new Map(nodes.map((item) => [item.node_ref, item]));
  const pathRefs = new Set(pathRelationRefs);
  const width = 1200;
  const count = Math.max(slots.length, 1);
  const x = (index: number): number => ((index + 0.5) * width) / count;
  const y = (node: CanvasNode | undefined): number => node?.node_type.includes("branch") ? 132 : 44;
  const paths = relations.flatMap((relation, index) => {
    const source = nodesByRef.get(relation.from_node_ref);
    const target = nodesByRef.get(relation.to_node_ref);
    const sourceIndex = source ? slotIndex.get(source.semantic_slot_ref) : undefined;
    const targetIndex = target ? slotIndex.get(target.semantic_slot_ref) : undefined;
    if (sourceIndex === undefined || targetIndex === undefined) return [];
    const x1 = x(sourceIndex);
    const x2 = x(targetIndex);
    const y1 = y(source);
    const y2 = y(target);
    const lift = 30 + (index % 4) * 15;
    const controlY = Math.max(12, Math.min(y1, y2) - lift);
    const d = sourceIndex === targetIndex
      ? `M ${x1 - 7} ${y1} C ${x1 - 70} ${controlY}, ${x1 + 70} ${controlY}, ${x2 + 7} ${y2}`
      : `M ${x1} ${y1} C ${x1} ${controlY}, ${x2} ${controlY}, ${x2} ${y2}`;
    const midX = (x1 + x2) / 2;
    const classes = [
      "canvas-relation",
      `state-${relation.semantic_state}`,
      pathRefs.has(relation.relation_ref) ? "is-work-path" : "",
      selected === relation.relation_ref ? "is-selected" : "",
    ].filter(Boolean).join(" ");
    return [`<g class="${classes}">
      <path d="${d}" marker-end="url(#canvas-arrow)" data-canvas-object="${escapeAttr(relation.relation_ref)}"></path>
      <text x="${midX}" y="${Math.max(18, controlY - 5)}" text-anchor="middle" tabindex="0" role="button" data-canvas-object="${escapeAttr(relation.relation_ref)}" aria-label="${escapeAttr(relation.label)}">${escapeHtml(relation.label)}</text>
    </g>`];
  }).join("");
  if (!paths) return `<div class="relation-empty"><span>此图层在当前阶段没有已披露关系</span><small>页面不会为了填满画面而补线。</small></div>`;
  return `<svg class="relation-map" viewBox="0 0 ${width} 170" preserveAspectRatio="xMidYMid meet" aria-label="当前关系图">
    <defs><marker id="canvas-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker></defs>
    ${paths}
  </svg>`;
}

function renderCanvasChanges(
  groups: ReadOnlySixPillarCanvas["stages"]["natal"]["change_groups"],
  selected: string,
  stage: string,
): string {
  const visible = groups.filter((item) => item.count > 0);
  return `<section class="canvas-diff-panel" aria-label="阶段变化">
    <header><span>阶段差异</span><strong>${stage === "natal" ? "这是比较基线" : "只列合同已经给出的变化"}</strong></header>
    ${visible.length ? `<div class="change-list">${visible.map((group) => `<div class="change-group change-${escapeAttr(group.change_type)}">
      <span><b>${escapeHtml(group.label)}</b><em>${group.count}</em></span>
      ${group.items.slice(0, 5).map((item) => `<button type="button" data-canvas-object="${escapeAttr(item.target_ref)}" class="${selected === item.target_ref ? "is-selected" : ""}">${escapeHtml(item.label)}</button>`).join("")}
    </div>`).join("")}</div>` : `<div class="baseline-diff"><b>原局</b><p>先建立四柱、关系与正式主路径的比较起点。</p></div>`}
    <details><summary>八种变化语义</summary><p>${groups.map((item) => `${item.label} ${item.count}`).join(" · ")}</p></details>
  </section>`;
}

function renderCanvasInspector(
  spec: ReadOnlySixPillarCanvas["stages"]["natal"]["spec"],
  selected: string,
  context: CanvasContextPack | null,
  status: UiState["canvasContextStatus"],
): string {
  const slot = spec.semantic_slots.find((item) => item.slot_ref === selected);
  const node = spec.nodes.find((item) => item.node_ref === selected);
  const relation = spec.relations.find((item) => item.relation_ref === selected);
  const path = spec.paths.find((item) => item.path_ref === selected);
  const cluster = spec.clusters.find((item) => item.cluster_ref === selected);
  const item = slot || node || relation || path || cluster;
  if (!item) return `<section class="canvas-inspector"><p>点击一柱、一个干支或一条关系，查看它在当前正式状态中的位置。</p></section>`;
  const trace = item.trace;
  const label = slot ? `${slot.label} ${slot.stem}${slot.branch}` : item.label;
  const type = slot ? "语义柱位" : node ? nodeTypeLabel(node.node_type) : relation ? "结构关系" : path ? "命局路径" : "结构候选";
  const semanticState = relation?.semantic_state || path?.semantic_state || trace.epistemic_status;
  const contextMatches = context?.selected_object_refs.includes(selected);
  return `<section class="canvas-inspector" aria-label="对象解释">
    <header><span>${escapeHtml(type)}</span><b class="epistemic-${escapeAttr(trace.epistemic_status)}">${escapeHtml(epistemicLabel(trace.epistemic_status))}</b></header>
    <h3>${escapeHtml(label)}</h3>
    <p>${status === "loading" ? "正在取回这个对象的受控上下文。" : contextMatches ? objectExplanation(slot, node, relation, path) : "选择已定位；受控上下文将在这里显示。"}</p>
    <dl><div><dt>当前状态</dt><dd>${escapeHtml(stateLabel(semanticState))}</dd></div><div><dt>来源</dt><dd>${trace.source_refs.length} 条可追溯引用</dd></div><div><dt>当前阶段</dt><dd>${escapeHtml(spec.stage)}</dd></div></dl>
    ${(trace.uncertainty.length || trace.rejection_or_block_reasons.length) ? `<div class="inspector-caution"><span>仍需保留</span><p>${escapeHtml([...trace.uncertainty, ...trace.rejection_or_block_reasons][0])}</p></div>` : ""}
    <details><summary>查看来源</summary><ul>${trace.source_refs.map((ref) => `<li>${escapeHtml(ref)}</li>`).join("")}</ul></details>
  </section>`;
}

function objectExplanation(
  slot: CanvasSemanticSlot | undefined,
  node: CanvasNode | undefined,
  relation: CanvasRelation | undefined,
  path: ReadOnlySixPillarCanvas["stages"]["natal"]["spec"]["paths"][number] | undefined,
): string {
  if (slot) return slot.immutable ? "这是原局固定柱位；视觉重排不会改变它的年、月、日、时身份。" : "这是正式历法时间柱；出现不等于已经形成现实事件判断。";
  if (node) return `${node.label}属于${elementLabel[node.element] || "未标注五行"}${node.ten_god ? `，当前十神标记为${tenGodLabel(node.ten_god)}` : ""}。`;
  if (relation) return `${relation.label}由 Compiler 提供，页面只负责定位与显示。`;
  if (path) return path.label;
  return "这是当前角色获准查看的结构候选。";
}

function epistemicLabel(value: string): string {
  return ({ fact: "正式事实", derived: "结构推导", candidate: "候选", committed: "已提交", blocked: "已阻止", hypothetical: "假设", presentation_only: "仅展示" } as Record<string, string>)[value] || value;
}

function stateLabel(value: string): string {
  return ({ latent: "潜在", active: "参与中", reinforced: "获得支持", weakened: "受到制约", blocked: "无法闭合", fact: "事实", derived: "推导", candidate: "候选", committed: "已提交" } as Record<string, string>)[value] || value;
}

function nodeTypeLabel(value: string): string {
  if (value.includes("hidden")) return "藏干节点";
  if (value.includes("stem")) return "天干节点";
  if (value.includes("branch")) return "地支节点";
  return "结构节点";
}

function tenGodLabel(value: string): string {
  return ({
    day_master: "日主", bi_jian: "比肩", jie_cai: "劫财", shi_shen: "食神", shang_guan: "伤官",
    pian_cai: "偏财", zheng_cai: "正财", qi_sha: "七杀", zheng_guan: "正官", pian_yin: "偏印", zheng_yin: "正印",
  } as Record<string, string>)[value] || value;
}

export function renderLoading(message: string): string {
  return `<main class="system-state"><div class="state-mark"></div><p>看见命局</p><h1>${escapeHtml(message)}</h1></main>`;
}

export function renderUnavailable(title: string, detail: string, actionLabel: string): string {
  return `
    <main class="system-state unavailable">
      <img src="/assets/abu/v11-designer-sad-tears/web/abu_sad_tears_v11.webp" alt="阿布正在等待">
      <p>阿布在这里</p>
      <h1>${escapeHtml(title)}</h1>
      <span>${escapeHtml(detail)}</span>
      <a class="primary-command" href="/app">${escapeHtml(actionLabel)}</a>
    </main>`;
}

function renderCaseSelector(cases: ExperienceCaseSummary[], activeCaseId: string): string {
  if (cases.length <= 1) {
    const active = cases.find((item) => item.case_id === activeCaseId);
    return `<span class="active-case"><i></i>${escapeHtml(active?.display_name || "当前命盘")}</span>`;
  }
  return `<label class="case-select-label"><span>当前命盘</span><select data-case-select>${cases
    .map((item) => `<option value="${escapeAttr(item.case_id)}"${item.case_id === activeCaseId ? " selected" : ""}>${escapeHtml(item.display_name)}</option>`)
    .join("")}</select></label>`;
}

function summaryItem(label: string, value: string, anchor: string): string {
  return `<button type="button" class="scan-item" data-select-anchor="${escapeAttr(anchor)}" data-message="${escapeAttr(value)}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></button>`;
}

function renderCollapsibleSection(input: {
  id: string;
  anchor: string;
  tone: string;
  eyebrow: string;
  title: string;
  summary: string;
  expanded: boolean;
  body: string;
}): string {
  return `
    <section class="experience-section tone-${escapeAttr(input.tone)}${input.expanded ? " is-expanded" : " is-collapsed"}" id="${escapeAttr(input.anchor)}" data-anchor="${escapeAttr(input.anchor)}">
      <button class="section-heading" type="button" data-toggle-section="${escapeAttr(input.id)}" aria-expanded="${input.expanded}">
        <span><small>${escapeHtml(input.eyebrow)}</small><strong>${escapeHtml(input.title)}</strong><em>${escapeHtml(input.summary)}</em></span>
        <b aria-hidden="true">${input.expanded ? "−" : "+"}</b>
      </button>
      <div class="section-body"${input.expanded ? "" : " hidden"}>${input.body}</div>
    </section>`;
}

function renderPillars(envelope: MingliExperienceEnvelope, selectedAnchor: string): string {
  const pillars = envelope.allowed_chart_facts.filter((item) => item.fact_type === "pillar");
  if (!pillars.length) return `<p class="empty-note">四柱事实尚未进入这份体验。</p>`;
  return `<div class="pillar-stage">${pillars.map((pillar) => {
    const message = `${pillar.pillar_label}是${pillar.stem}${pillar.branch}。${pillar.visible_ten_god ? `天干关系为${pillar.visible_ten_god}。` : ""}${pillar.hidden_stems.length ? `地支藏${pillar.hidden_stems.map((item) => item.stem).join("、")}。` : ""}`;
    return `<button type="button" class="pillar${selectedAnchor === pillar.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr(pillar.visual_anchor)}" data-message="${escapeAttr(message)}">
      <span class="pillar-label">${escapeHtml(pillar.pillar_label)}</span>
      <span class="ten-god">${escapeHtml(pillar.visible_ten_god || "天干")}</span>
      <strong class="stem element-${escapeAttr(pillar.stem_element)}" data-polarity="${escapeAttr(pillar.stem_polarity)}">${escapeHtml(pillar.stem)}</strong>
      <strong class="branch element-${escapeAttr(pillar.branch_element)}" data-polarity="${escapeAttr(pillar.branch_polarity)}">${escapeHtml(pillar.branch)}</strong>
      <span class="nature">${polarityLabel[pillar.stem_polarity] || ""}${elementLabel[pillar.stem_element] || ""} · ${polarityLabel[pillar.branch_polarity] || ""}${elementLabel[pillar.branch_element] || ""}</span>
      <span class="hidden-stems">${pillar.hidden_stems.map((item) => `<i class="element-${escapeAttr(item.element)}"><b>${escapeHtml(item.stem)}</b><em>${escapeHtml(item.ten_god)}</em></i>`).join("")}</span>
    </button>`;
  }).join("")}</div>`;
}

function renderPath(fullThesis: string, steps: ApprovedReasoningStep[], selectedAnchor: string): string {
  if (!steps.length) return `<p class="empty-note">主路径仍在可靠性门禁内，没有被包装成确定结论。</p>`;
  return `<button type="button" class="baseline-thesis${selectedAnchor === "baseline-summary" ? " is-selected" : ""}" data-select-anchor="baseline-summary" data-message="${escapeAttr(fullThesis)}">
    <span>整盘总断</span><strong>${escapeHtml(fullThesis)}</strong>
  </button><div class="path-stage">${steps.map((step, index) => {
    const message = `${step.premise}，因此当前得到的判断是：${step.conclusion}`;
    return `<button type="button" class="path-step${selectedAnchor === step.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr(step.visual_anchor)}" data-message="${escapeAttr(message)}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <small>${escapeHtml(step.premise)}</small>
      <strong>${escapeHtml(step.conclusion)}</strong>
    </button>`;
  }).join('<span class="path-arrow" aria-hidden="true">→</span>')}</div>`;
}

function firstSentence(value: string): string {
  const match = value.match(/^.*?[。！？](?:[”’"])?/u);
  return match?.[0] || value;
}

function renderBoundaries(
  claim: ApprovedClaim | undefined,
  envelope: MingliExperienceEnvelope,
  selectedAnchor: string,
): string {
  const condition = claim?.conditions[0] || "正式条件尚未提交。";
  const uncertainty = envelope.uncertainty.reasons[0] || "当前没有额外未决项。";
  const counter = claim?.counter_signals[0] || envelope.competing_hypotheses[0]?.approved_meaning || "尚无已提交的反向信号。";
  return `<div class="boundary-grid">
    ${boundaryItem("成立条件", condition, "baseline-condition", selectedAnchor)}
    ${boundaryItem("最大未决", uncertainty, "baseline-uncertainty", selectedAnchor)}
    ${boundaryItem("反向信号", counter, "baseline-counter-signal", selectedAnchor)}
  </div>`;
}

function boundaryItem(label: string, text: string, anchor: string, selectedAnchor: string): string {
  return `<button type="button" class="boundary-item${selectedAnchor === anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr(anchor)}" data-message="${escapeAttr(text)}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(text)}</strong></button>`;
}

function renderAbuDock(view: ExperienceViewModel): string {
  const segment = view.narrationManifest?.segments[view.ui.narrationIndex];
  const isBusy = view.ui.narrationStatus === "preparing";
  return `<aside class="abu-dock${view.ui.abuExpanded ? " is-open" : ""}${isBusy ? " is-thinking" : ""}" aria-label="阿布同步论命">
    <button class="abu-avatar" type="button" data-command="toggle-abu" aria-label="${view.ui.abuExpanded ? "收起阿布" : "打开阿布"}">
      <img src="${isBusy ? "/assets/abu/v9-designer-taoist-divination/web/abu_taoist_divination_v9.webp" : "/assets/abu/v4-video-derived/web/abu_idle_blink_v4.webp"}" alt="阿布">
    </button>
    <div class="abu-bubble" role="status"><span>${segment ? escapeHtml(segment.title) : "阿布"}</span><p>${escapeHtml(view.ui.abuMessage)}</p></div>
    <div class="abu-panel"${view.ui.abuExpanded ? "" : " hidden"}>
      <div class="abu-panel-heading"><span>阿布同步论命</span><button type="button" data-command="toggle-abu" aria-label="收起">×</button></div>
      <p>${escapeHtml(view.ui.abuMessage)}</p>
      <div class="narration-controls">
        <button type="button" class="primary-command compact" data-command="listen">${view.ui.narrationStatus === "playing" ? "暂停" : "继续听"}</button>
        <button type="button" class="text-command" data-command="stop">停止</button>
      </div>
      <ol class="chapter-list">${(view.narrationManifest?.segments || []).map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><span>${escapeHtml(item.title)}</span><small>${escapeHtml(item.text)}</small></button></li>`).join("")}</ol>
    </div>
  </aside>`;
}

function escapeHtml(value: unknown): string {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character] || character);
}

function escapeAttr(value: unknown): string {
  return escapeHtml(value).replace(/`/g, "&#96;");
}
