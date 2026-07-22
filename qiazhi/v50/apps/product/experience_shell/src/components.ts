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
  WorkspaceCognitionState,
} from "./contracts";
import type { ProductArea, UiState, WorkspaceSurface } from "./state";
import type { DreamFeatureStatus } from "./dream_api";

export interface ExperienceViewModel {
  accountName: string;
  accountRole: string;
  cases: ExperienceCaseSummary[];
  activeCaseId: string;
  activeProfileId: string;
  availableAreas: ProductArea[];
  availableSurfaces: WorkspaceSurface[];
  workspace: CaseWorkspaceEnvelope | null;
  envelope: MingliExperienceEnvelope;
  cognition: WorkspaceCognitionState;
  narrationManifest: NarrationManifest | null;
  canvas: ReadOnlySixPillarCanvas | null;
  canvasContext: CanvasContextPack | null;
  ui: UiState;
  dreamStatus: DreamFeatureStatus | null;
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
  const fullThesis = claim?.approved_meaning || "四柱已经就绪，阿布正在理解整盘。";
  const thesis = firstSentence(fullThesis);
  const pathSummary = steps[steps.length - 1]?.conclusion || "先从确定性的四柱开始。";
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
  const hasFormalCognition = Boolean(claim);
  const steps = view.envelope.approved_reasoning_steps;
  const condition = claim?.conditions[0] || "当前还没有足够依据写下成立条件。";
  const uncertainty = view.envelope.uncertainty.reasons[0] || "当前没有额外未决项。";
  const pathSummary = steps[steps.length - 1]?.conclusion || "先从确定性的四柱开始。";
  const fullThesis = claim?.approved_meaning || "四柱已经就绪，阿布正在理解整盘。";
  const thesis = firstSentence(fullThesis);

  return `
    ${renderWorkspaceNavigation(view)}

    <div class="workbench-surface" data-workspace-current-surface="${escapeAttr(view.ui.workspaceSurface)}">
      ${view.ui.workspaceSurface === "overview" ? `<section class="opening-band" id="baseline-summary" data-anchor="baseline-summary">
        <div class="opening-copy">
          <p class="section-kicker">看见命局 · 当前基线</p>
          <h1>${escapeHtml(thesis)}</h1>
          <p class="opening-lede">${escapeHtml(view.cognition.message)}</p>
          <div class="opening-actions">
            <button class="primary-command" type="button" data-command="listen">
              ${view.ui.narrationStatus === "playing" ? "暂停阿布" : "听阿布讲"}
            </button>
            <button class="text-command" type="button" data-command="focus-pillars">先看四柱</button>
          </div>
        </div>
        ${hasFormalCognition ? `<div class="scan-strip" aria-label="整盘快速摘要">
          ${summaryItem("主路径", pathSummary, "baseline-work-path")}
          ${summaryItem("成立条件", condition, "baseline-condition")}
          ${summaryItem("最大未决", uncertainty, "baseline-uncertainty")}
        </div>` : `<div class="cognition-progress" data-cognition-status="${escapeAttr(view.cognition.status)}"><i></i><span><strong>命盘先到，认知随后</strong><small>四柱已确认；阿布只会补充依据充分的部分。</small></span></div>`}
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

      ${hasFormalCognition ? `${renderCollapsibleSection({
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
      ` : ""}

      ${view.ui.workspaceSurface === "onecanvas" ? `${renderCollapsibleSection({
        id: "canvas",
        anchor: "temporal-canvas",
        tone: "canvas",
        eyebrow: "时间结构",
        title: "看结构怎样进入当前时间",
        summary: view.canvas
          ? `${view.canvas.source.luck_pillar}大运 · ${view.canvas.source.analysis_year || "当前"}${view.canvas.source.annual_pillar}流年`
          : "四柱骨架已经就绪",
        expanded: view.ui.expandedSections.canvas ?? true,
        body: view.canvas
          ? renderReadOnlyCanvas(
              view.canvas,
              view.ui,
              view.canvasContext,
              view.cognition.status === "preparing",
            )
          : renderDeterministicCanvasSkeleton(view.envelope, view.cognition),
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
          ${view.dreamStatus?.enabled && view.dreamStatus.available ? `<button class="dream-entry-command" type="button" data-command="enter-dream">${view.dreamStatus.resumable ? "继续上次的梦" : "随阿布入梦"}</button>` : ""}
        </div>
        ${renderDreamConsent(view)}
      </div>
      <div class="life-tree" aria-label="命、事、人的生命脉络">
        <span class="tree-line tree-line-left" aria-hidden="true"></span>
        <span class="tree-line tree-line-right" aria-hidden="true"></span>
        <button type="button" class="tree-node tree-nature" data-product-area="workbench">
          <small>命</small><strong>${escapeHtml(pillars || "四柱待确认")}</strong><span>先天底图</span>
        </button>
        <button type="button" class="tree-node tree-events" data-select-anchor="baseline-work-path" data-message="${escapeAttr(pathSummary)}">
          <small>事</small><strong>${escapeHtml(firstSentence(pathSummary))}</strong><span>${escapeHtml(view.workspace?.state.selected_period || "当前阶段")}</span>
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


function renderDreamConsent(view: ExperienceViewModel): string {
  const status = view.dreamStatus;
  if (!status?.enabled || status.consent_state === "case_unavailable") return "";
  if (status.consent_state === "active") {
    return `<div class="dream-consent-control is-active">
      <div><strong>当前档案已匿名授权入梦</strong><span>仅用于本地封闭三树体验，可随时撤回。</span></div>
      <button type="button" data-command="withdraw-dream-consent">撤回授权</button>
    </div>`;
  }
  const changed = status.consent_state === "source_changed";
  return `<div class="dream-consent-control">
    <div><strong>${changed ? "命盘版本已变化，请重新确认" : "让这棵生命树进入封闭梦境"}</strong><span>匿名展示确定性命盘与只读树象；不公开身份，不默认用于训练，授权后仍可撤回。</span></div>
    <button type="button" data-command="grant-dream-consent">${changed ? "重新授权" : "授权当前档案"}</button>
  </div>`;
}

function renderMingliLab(view: ExperienceViewModel): string {
  if (!view.canvas) return `<section class="lab-empty"><p>Mingli Lab</p><h1>四柱已经就绪</h1><span>研究镜头只在正式关系投影可用时按需展开，不会为 Lab 另算一套命盘。</span></section>`;
  const stage = view.canvas.stages[view.ui.canvasStage];
  const potentialCount = stage.spec.relations.filter((item) => item.relation_state === "potential").length;
  const sourceCount = new Set(stage.spec.relations.flatMap((item) => item.trace.source_refs)).size;
  const hiddenCount = stage.spec.nodes.filter((item) => item.node_type.includes("hidden")).length;
  return `<div class="mingli-lab">
    <header class="lab-header">
      <div><p>Mingli Lab · ${escapeHtml(activeCaseName(view))}</p><h1>同一命局的研究镜头</h1><span>候选关系与证据留在研究层；正式 Case 不在这里被改写。</span></div>
      <code>${escapeHtml((view.workspace?.state.scene_source_hash || view.envelope.source.source_hash).slice(0, 18))}</code>
    </header>
    <div class="lab-evidence-rail" aria-label="当前研究范围">
      <span><small>潜在关系</small><strong>${potentialCount}</strong></span>
      <span><small>藏干节点</small><strong>${hiddenCount}</strong></span>
      <span><small>来源引用</small><strong>${sourceCount}</strong></span>
      <span><small>正式写入</small><strong>关闭</strong></span>
    </div>
    <section class="lab-canvas"><p class="lab-lens-label">命理师 Lens · 潜在关系场</p>${renderReadOnlyCanvas(view.canvas, view.ui, view.canvasContext, view.cognition.status === "preparing")}</section>
  </div>`;
}

function renderProductSidebar(view: ExperienceViewModel): string {
  return `<aside class="product-sidebar">
    <a class="brand" href="/experience" aria-label="DeepBeing 首页"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence"><span>DeepBeing</span></a>
    ${renderProductNavigation(view, "sidebar")}
    <div class="sidebar-context">${renderProfileSelector(view.cases, view.activeProfileId)}<small>${escapeHtml(view.envelope.source.life_case_version || "命盘事实")}</small></div>
    <div class="sidebar-account"><span>${escapeHtml(view.accountName)}</span><button type="button" data-command="manage-profiles">档案</button></div>
  </aside>`;
}

function renderMobileHeader(view: ExperienceViewModel): string {
  const labels: Record<ProductArea, string> = { world: "我的生命世界", workbench: "命盘工作台", lab: "Mingli Lab" };
  return `<header class="mobile-header"><a href="/experience"><img src="/assets/deepbazi_symbol.png" alt="DeepBazi"></a><strong>${labels[view.ui.productArea]}</strong><div class="mobile-header-actions">${renderProfileSelector(view.cases, view.activeProfileId)}<button type="button" data-command="manage-profiles" aria-label="管理档案" title="管理档案">档</button></div></header>`;
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
  return view.cases.find((item) => item.profile_id === view.activeProfileId)?.display_name || "当前命盘";
}

function renderNarrationWorkspace(view: ExperienceViewModel, thesis: string): string {
  const segments = view.narrationManifest?.segments || [];
  return `<section class="narration-workspace" data-anchor="abu-narration">
    <header><p>阿布讲解</p><h1>${escapeHtml(thesis)}</h1><span>${segments.length ? "从整盘重心开始，沿四柱、路径、条件与未决逐段展开。" : "文字已经可读；点播放后才准备声音，不阻塞当前页面。"}</span></header>
    <div class="narration-workspace-actions">
      <button class="primary-command" type="button" data-command="listen">${view.ui.narrationStatus === "playing" ? "暂停" : "从头听"}</button>
      ${view.ui.narrationStatus !== "idle" ? '<button class="text-command" type="button" data-command="stop">停止</button>' : ""}
    </div>
    ${segments.length ? `<ol>${segments.map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><small>${String(index + 1).padStart(2, "0")}</small><span><strong>${escapeHtml(item.title)}</strong><em>${escapeHtml(item.text)}</em></span><b aria-hidden="true">▶</b></button></li>`).join("")}</ol>` : `<div class="narration-pending"><i></i><p>${escapeHtml(view.cognition.message)}</p></div>`}
  </section>`;
}

function renderDeterministicCanvasSkeleton(
  envelope: MingliExperienceEnvelope,
  cognition: WorkspaceCognitionState,
): string {
  const pillars = envelope.allowed_chart_facts.filter((item) => item.fact_type === "pillar");
  return `<div class="deterministic-canvas-skeleton">
    <header><span>确定性命盘</span><strong>四柱先显示，关系按正式来源逐步进入</strong></header>
    <div class="skeleton-pillar-rail">${pillars.map((pillar) => `<article>
      <small>${escapeHtml(pillar.pillar_label)}</small>
      <b class="element-${escapeAttr(pillar.stem_element)}" data-polarity="${escapeAttr(pillar.stem_polarity)}">${escapeHtml(pillar.stem)}</b>
      <i></i>
      <b class="element-${escapeAttr(pillar.branch_element)}" data-polarity="${escapeAttr(pillar.branch_polarity)}">${escapeHtml(pillar.branch)}</b>
      <em>${escapeHtml(pillar.visible_ten_god || "命盘事实")}</em>
    </article>`).join("")}</div>
    <p><i></i>${escapeHtml(cognition.message)}</p>
  </div>`;
}

export function renderReadOnlyCanvas(
  canvas: ReadOnlySixPillarCanvas,
  ui: UiState,
  context: CanvasContextPack | null,
  pathTaskRunning: boolean,
): string {
  const stage = canvas.stages[ui.canvasStage];
  const allowedVisibility = canvas.renderer_policy.available_visibility_layers;
  const requestedVisibility = ui.canvasVisibilityLayer;
  const visibility = allowedVisibility.includes(requestedVisibility)
    ? requestedVisibility
    : canvas.renderer_policy.default_visibility_layer;
  const selected = ui.selectedCanvasObject || stage.scene_slots[0]?.slot_ref || "";
  const displayLayers = stage.layers.map((item) => {
    const relationRefs = visibility === "lab_audit"
      ? item.relation_refs
      : item.formal_relation_refs;
    const pathRefs = visibility === "lab_audit"
      ? item.path_refs
      : item.formal_path_refs;
    const focusedRelationRefs = visibility === "focus"
      ? focusRelationRefs(stage.spec, relationRefs, selected)
      : relationRefs;
    const focusedPathRefs = visibility === "focus"
      ? focusPathRefs(stage.spec, pathRefs, selected)
      : pathRefs;
    return {
      ...item,
      relation_refs: focusedRelationRefs,
      path_refs: focusedPathRefs,
      count: focusedRelationRefs.length,
      available: focusedRelationRefs.length > 0 || focusedPathRefs.length > 0,
    };
  });
  const layer = displayLayers.find((item) => item.layer_id === ui.canvasLayer)
    || displayLayers.find((item) => item.layer_id === stage.default_layer_id)
    || displayLayers[0];
  const visibleRelationRefs = new Set(layer?.relation_refs || []);
  const visiblePathRefs = new Set(layer?.path_refs || []);
  const activeRelations = stage.spec.relations.filter((item) => visibleRelationRefs.has(item.relation_ref));
  const activePaths = stage.spec.paths.filter((item) => visiblePathRefs.has(item.path_ref));
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

    <div class="canvas-lens-controls">
      <div class="layer-switch" role="tablist" aria-label="命局观察镜头">
        ${displayLayers.map((item) => `<button type="button" role="tab" data-canvas-layer="${escapeAttr(item.layer_id)}" aria-selected="${item.layer_id === layer?.layer_id}" class="${item.layer_id === layer?.layer_id ? "active" : ""}"${item.available || item.layer_id === "overview" || item.layer_id === "work_path" ? "" : " disabled"}>
          <span>${escapeHtml(item.label)}</span>${item.count > 0 ? `<small>${item.count}</small>` : ""}
        </button>`).join("")}
      </div>
      <div class="visibility-switch" role="tablist" aria-label="关系披露层">
        ${allowedVisibility.map((item) => `<button type="button" role="tab" data-canvas-visibility="${item}" aria-selected="${item === visibility}" class="${item === visibility ? "active" : ""}">${visibilityLabel(item)}</button>`).join("")}
      </div>
    </div>

    <div class="canvas-board" data-layer="${escapeAttr(layer?.layer_id || "")}" data-visibility="${escapeAttr(visibility)}">
      <div class="six-pillar-scroll">
        ${renderCanonicalCanvasScene(
          stage.scene_slots,
          stage.spec.nodes,
          activeRelations,
          activePaths,
          selected,
          visibility === "lab_audit",
        )}
      </div>
      <p class="layer-caption"><strong>${escapeHtml(layer?.label || "当前图层")}</strong>${escapeHtml(layer?.description || "当前没有可显示的关系。")}</p>
    </div>

    <div class="canvas-reading-grid">
      ${renderCanvasChanges(stage.change_groups, selected, ui.canvasStage)}
      ${renderCanvasInspector(stage.spec, selected, context, ui.canvasContextStatus)}
    </div>

    <div class="canvas-boundary ${canvas.path_availability.status === "available" ? "is-ready" : "is-limited"}">
      <span>${canvas.path_availability.status === "available"
        ? "正式路径已确认"
        : pathTaskRunning
          ? "正式主路径正在形成"
          : "当前暂无已确认主路径"}</span>
      <p>${escapeHtml(
        canvas.path_availability.status !== "available" && pathTaskRunning
          ? "后台正在形成最小整盘主线，已经确认的结构会自动出现。"
          : canvas.path_availability.message,
      )}</p>
      ${canvas.path_availability.disclosure_level === "audit" && canvas.path_availability.diagnostic
        ? `<small>${escapeHtml(pathDiagnosticLabel(canvas.path_availability.diagnostic.rejection_reason))}</small>`
        : ""}
      ${visibility === "lab_audit" && canvas.path_availability.diagnostic
        ? `<code>${escapeHtml(canvas.path_availability.diagnostic.rejection_reason)}</code>`
        : ""}
    </div>
  </div>`;
}

function renderCanonicalCanvasScene(
  slots: ReadOnlySixPillarCanvas["stages"]["natal"]["scene_slots"],
  nodes: CanvasNode[],
  relations: CanvasRelation[],
  paths: ReadOnlySixPillarCanvas["stages"]["natal"]["spec"]["paths"],
  selected: string,
  showHiddenStems: boolean,
): string {
  const nodesByRef = new Map(nodes.map((item) => [item.node_ref, item]));
  const anchors = canvasAnchorRegistry(slots, nodes);
  const pathRelationRefs = new Set(paths.flatMap((item) => item.relation_refs));
  const requiredNodeRefs = new Set([
    ...relations.flatMap((item) => [
      item.from_node_ref,
      item.to_node_ref,
      ...item.participant_node_refs,
    ]),
    ...paths.flatMap((item) => item.node_refs),
  ]);
  const relationMarkup = relations.flatMap((relation, index) => {
    const source = anchors.get(relation.from_node_ref);
    const target = anchors.get(relation.to_node_ref);
    if (!source || !target) return [];
    const route = routeCanvasRelation(source, target, index);
    const classes = [
      "canvas-relation",
      `state-${relation.semantic_state}`,
      pathRelationRefs.has(relation.relation_ref) ? "is-work-path" : "",
      selected === relation.relation_ref ? "is-selected" : "",
    ].filter(Boolean).join(" ");
    return [`<g class="${classes}">
      <path d="${route.d}" marker-end="url(#canvas-arrow)" data-canvas-object="${escapeAttr(relation.relation_ref)}"></path>
      <text x="${route.labelX}" y="${route.labelY}" text-anchor="middle" tabindex="0" role="button" data-canvas-object="${escapeAttr(relation.relation_ref)}" aria-label="${escapeAttr(relation.label)}">${escapeHtml(shortRelationLabel(relation))}</text>
    </g>`];
  }).join("");
  const pathMarkup = paths.map((path, pathIndex) => renderCanvasPath(path, anchors, selected, pathIndex)).join("");
  const nodeMarkup = slots.map((slot) => renderCanvasSceneSlot(
    slot,
    nodesByRef,
    anchors,
    selected,
    showHiddenStems,
    requiredNodeRefs,
  )).join("");
  return `<svg class="canonical-canvas-scene" viewBox="0 0 1320 640" preserveAspectRatio="xMidYMid meet" aria-label="六柱同一命局场景">
    <defs>
      <marker id="canvas-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker>
      <marker id="canvas-path-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z"></path></marker>
    </defs>
    <g class="canvas-scene-tracks" aria-hidden="true"><line x1="44" y1="185" x2="1276" y2="185"></line><line x1="44" y1="390" x2="1276" y2="390"></line><text x="46" y="171">天干</text><text x="46" y="376">地支</text></g>
    <g class="canvas-scene-relations">${relationMarkup}</g>
    <g class="canvas-scene-paths">${pathMarkup}</g>
    <g class="canvas-scene-nodes">${nodeMarkup}</g>
    ${!relationMarkup && !pathMarkup ? `<g class="canvas-scene-empty"><text x="660" y="292" text-anchor="middle">此镜头没有已披露关系</text><text x="660" y="315" text-anchor="middle">页面不会为了填满画面而补线</text></g>` : ""}
  </svg>`;
}

interface CanvasAnchor {
  x: number;
  y: number;
  level: "stem" | "branch" | "hidden";
  slotIndex: number;
}

function canvasAnchorRegistry(
  slots: ReadOnlySixPillarCanvas["stages"]["natal"]["scene_slots"],
  nodes: CanvasNode[],
): Map<string, CanvasAnchor> {
  const anchors = new Map<string, CanvasAnchor>();
  slots.forEach((slot, index) => {
    const x = 110 + (index * 220);
    if (slot.stem_node_ref) anchors.set(slot.stem_node_ref, { x, y: 185, level: "stem", slotIndex: index });
    if (slot.branch_node_ref) anchors.set(slot.branch_node_ref, { x, y: 390, level: "branch", slotIndex: index });
    const hiddenNodes = orderedHiddenStemNodes(slot, nodes);
    const offsets = hiddenNodes.length === 1
      ? [0]
      : hiddenNodes.length === 2
        ? [-30, 30]
        : [-44, 0, 44];
    hiddenNodes.forEach((node, hiddenIndex) => {
      anchors.set(node.node_ref, {
        x: x + (offsets[hiddenIndex] ?? ((hiddenIndex - 1) * 44)),
        y: 515,
        level: "hidden",
        slotIndex: index,
      });
    });
  });
  return anchors;
}

function orderedHiddenStemNodes(
  slot: ReadOnlySixPillarCanvas["stages"]["natal"]["scene_slots"][number],
  nodes: CanvasNode[],
): CanvasNode[] {
  return nodes
    .filter((item) => item.node_type === "hidden_stem" && item.semantic_slot_ref === slot.slot_ref)
    .sort((left, right) => {
      const leftIndex = slot.hidden_stems.indexOf(left.label);
      const rightIndex = slot.hidden_stems.indexOf(right.label);
      if (leftIndex !== rightIndex) return leftIndex - rightIndex;
      return left.node_ref.localeCompare(right.node_ref);
    });
}

function renderCanvasSceneSlot(
  slot: ReadOnlySixPillarCanvas["stages"]["natal"]["scene_slots"][number],
  nodesByRef: Map<string, CanvasNode>,
  anchors: Map<string, CanvasAnchor>,
  selected: string,
  showHiddenStems: boolean,
  requiredNodeRefs: Set<string>,
): string {
  const x = 110 + (slot.position_index * 220);
  const temporal = slot.slot_type === "luck" || slot.slot_type === "year";
  const active = slot.state === "active";
  const stemNode = nodesByRef.get(slot.stem_node_ref);
  const branchNode = nodesByRef.get(slot.branch_node_ref);
  const slotAction = active ? ` tabindex="0" role="button" data-canvas-object="${escapeAttr(slot.slot_ref)}"` : "";
  return `<g class="canvas-scene-slot${temporal ? " is-temporal" : ""} state-${slot.state}" transform="translate(${x} 0)">
    <g class="canvas-slot-label${selected === slot.slot_ref ? " is-selected" : ""}"${slotAction}>
      <text x="0" y="70" text-anchor="middle">${escapeHtml(slot.label)}</text>
      <text class="canvas-slot-state" x="0" y="91" text-anchor="middle">${slot.state === "active" ? (slot.immutable ? "原局" : "时间进入") : slot.state === "inactive" ? "尚未进入" : "未载入"}</text>
    </g>
    <line class="canvas-column-guide" x1="0" y1="117" x2="0" y2="548"></line>
    ${renderCanvasSceneNode(slot, stemNode, anchors.get(slot.stem_node_ref), selected, "stem")}
    ${renderCanvasSceneNode(slot, branchNode, anchors.get(slot.branch_node_ref), selected, "branch")}
    ${active ? renderCanvasHiddenStemNodes(
      slot,
      [...nodesByRef.values()],
      anchors,
      selected,
      showHiddenStems,
      requiredNodeRefs,
    ) : ""}
  </g>`;
}

function renderCanvasHiddenStemNodes(
  slot: ReadOnlySixPillarCanvas["stages"]["natal"]["scene_slots"][number],
  nodes: CanvasNode[],
  anchors: Map<string, CanvasAnchor>,
  selected: string,
  showAll: boolean,
  requiredNodeRefs: Set<string>,
): string {
  const hiddenNodes = orderedHiddenStemNodes(slot, nodes)
    .filter((item) => showAll || requiredNodeRefs.has(item.node_ref));
  if (!hiddenNodes.length) return "";
  const slotX = 110 + (slot.position_index * 220);
  return `<g class="canvas-hidden-stems">
    <text class="canvas-hidden-label" x="0" y="474" text-anchor="middle">藏干</text>
    ${hiddenNodes.map((node) => {
      const anchor = anchors.get(node.node_ref);
      if (!anchor) return "";
      return `<g class="canvas-hidden-node element-${escapeAttr(node.element)}${selected === node.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr(node.polarity)}" transform="translate(${anchor.x - slotX} 515)" tabindex="0" role="button" data-canvas-object="${escapeAttr(node.node_ref)}" aria-label="${escapeAttr(`${slot.label}藏干${node.label}`)}">
        <circle r="21"></circle>
        <text text-anchor="middle" dominant-baseline="central">${escapeHtml(node.label)}</text>
      </g>`;
    }).join("")}
  </g>`;
}

function renderCanvasSceneNode(
  slot: ReadOnlySixPillarCanvas["stages"]["natal"]["scene_slots"][number],
  node: CanvasNode | undefined,
  anchor: CanvasAnchor | undefined,
  selected: string,
  level: "stem" | "branch",
): string {
  const y = level === "stem" ? 185 : 390;
  const value = level === "stem" ? slot.stem : slot.branch;
  if (!node || !anchor) {
    return `<g class="canvas-scene-node is-inactive" transform="translate(0 ${y})"><text class="canvas-node-character" text-anchor="middle" dominant-baseline="central">${escapeHtml(value || "·")}</text></g>`;
  }
  const label = level === "stem"
    ? node.ten_god === "day_master" ? "日主" : tenGodLabel(node.ten_god || "天干")
    : "地支";
  return `<g class="canvas-scene-node element-${escapeAttr(node.element)}${selected === node.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr(node.polarity)}" transform="translate(0 ${y})" tabindex="0" role="button" data-canvas-object="${escapeAttr(node.node_ref)}" aria-label="${escapeAttr(`${slot.label}${label}${value}`)}">
    <rect x="-56" y="-58" width="112" height="116" rx="6"></rect>
    <text class="canvas-node-role" x="0" y="-33" text-anchor="middle">${escapeHtml(label)}</text>
    <text class="canvas-node-character" x="0" y="11" text-anchor="middle" dominant-baseline="central">${escapeHtml(value)}</text>
  </g>`;
}

function routeCanvasRelation(source: CanvasAnchor, target: CanvasAnchor, index: number): { d: string; labelX: number; labelY: number } {
  const lane = index % 4;
  const sameLevel = source.level === target.level;
  const sameSlot = source.slotIndex === target.slotIndex;
  if (sameSlot && !sameLevel) {
    const side = source.slotIndex % 2 === 0 ? -70 : 70;
    const x = source.x + side;
    return {
      d: `M ${source.x} ${source.y} C ${x} ${source.y}, ${x} ${target.y}, ${target.x} ${target.y}`,
      labelX: x,
      labelY: (source.y + target.y) / 2,
    };
  }
  if (sameLevel) {
    const trackY = source.level === "stem"
      ? 118 - (lane * 15)
      : source.level === "branch"
        ? 457 + (lane * 15)
        : 570 + (lane * 15);
    return {
      d: `M ${source.x} ${source.y} C ${source.x} ${trackY}, ${target.x} ${trackY}, ${target.x} ${target.y}`,
      labelX: (source.x + target.x) / 2,
      labelY: trackY + (source.level === "stem" ? -7 : 15),
    };
  }
  const middleY = ((source.y + target.y) / 2) + ((lane - 1.5) * 13);
  return {
    d: `M ${source.x} ${source.y} C ${source.x} ${middleY}, ${target.x} ${middleY}, ${target.x} ${target.y}`,
    labelX: (source.x + target.x) / 2,
    labelY: middleY - 7,
  };
}

function renderCanvasPath(
  path: ReadOnlySixPillarCanvas["stages"]["natal"]["spec"]["paths"][number],
  anchors: Map<string, CanvasAnchor>,
  selected: string,
  pathIndex: number,
): string {
  const points = path.node_refs.flatMap((ref) => {
    const anchor = anchors.get(ref);
    return anchor ? [anchor] : [];
  });
  if (points.length < 2) return "";
  const segments = points.slice(0, -1).map((source, index) => {
    const target = points[index + 1];
    const laneY = 286 + (pathIndex * 18);
    return `<path d="M ${source.x} ${source.y} C ${source.x} ${laneY}, ${target.x} ${laneY}, ${target.x} ${target.y}" marker-end="url(#canvas-path-arrow)"></path>`;
  }).join("");
  const candidate = path.trace.epistemic_status !== "committed";
  return `<g class="canvas-work-path${candidate ? " is-candidate" : ""}${selected === path.path_ref ? " is-selected" : ""}" tabindex="0" role="button" data-canvas-object="${escapeAttr(path.path_ref)}" aria-label="${escapeAttr(path.label)}">
    ${segments}
    <text x="${points[Math.floor(points.length / 2)].x}" y="${274 + (pathIndex * 18)}" text-anchor="middle">${candidate ? "候选路径" : "正式主路径"}</text>
  </g>`;
}

function focusRelationRefs(
  spec: ReadOnlySixPillarCanvas["stages"]["natal"]["spec"],
  relationRefs: string[],
  selected: string,
): string[] {
  if (!selected) return [];
  const selectedRefs = focusNodeRefs(spec, selected);
  return relationRefs.filter((ref) => {
    const relation = spec.relations.find((item) => item.relation_ref === ref);
    return relation && (
      relation.relation_ref === selected
      || relation.participant_node_refs.some((nodeRef) => selectedRefs.has(nodeRef))
    );
  });
}

function focusPathRefs(
  spec: ReadOnlySixPillarCanvas["stages"]["natal"]["spec"],
  pathRefs: string[],
  selected: string,
): string[] {
  if (!selected) return [];
  const selectedRefs = focusNodeRefs(spec, selected);
  return pathRefs.filter((ref) => {
    const path = spec.paths.find((item) => item.path_ref === ref);
    return path && (
      path.path_ref === selected
      || path.node_refs.some((nodeRef) => selectedRefs.has(nodeRef))
      || path.relation_refs.includes(selected)
    );
  });
}

function focusNodeRefs(
  spec: ReadOnlySixPillarCanvas["stages"]["natal"]["spec"],
  selected: string,
): Set<string> {
  const refs = new Set<string>();
  const node = spec.nodes.find((item) => item.node_ref === selected);
  if (node) refs.add(node.node_ref);
  spec.nodes.filter((item) => item.semantic_slot_ref === selected).forEach((item) => refs.add(item.node_ref));
  const relation = spec.relations.find((item) => item.relation_ref === selected);
  relation?.participant_node_refs.forEach((item) => refs.add(item));
  const path = spec.paths.find((item) => item.path_ref === selected);
  path?.node_refs.forEach((item) => refs.add(item));
  return refs;
}

function shortRelationLabel(relation: CanvasRelation): string {
  return ({
    generates: "生",
    controls: "克",
    same_element_support: "同气",
    stores: "藏",
    roots: "根",
    forms_half_combination: "半合",
    forms_triple_combination: "三合",
    clashes: "冲",
    harmonizes: "合",
    harms: "害",
    breaks: "破",
    punishes: "刑",
    position_link: "同柱",
  } as Record<string, string>)[relation.relation_type] || relation.label;
}

function visibilityLabel(value: string): string {
  return ({ formal: "正式", focus: "聚焦", lab_audit: "审计" } as Record<string, string>)[value] || value;
}

function pathDiagnosticLabel(value: string): string {
  return ({
    none: "当前路径的节点、关系与权限引用均已闭合。",
    no_cognitive_path: "当前认知记录尚未形成做功路径。",
    natural_language_only: "目前只有文字描述，还没有结构化路径引用。",
    candidate_not_committed: "已有结构候选，但尚未提交为正式路径。",
    missing_path_ref: "正式断言缺少可投影的路径身份。",
    invalid_node_ref: "路径引用的节点未能落到当前场景。",
    invalid_relation_ref: "路径引用的关系未能落到当前场景。",
    relation_still_potential: "路径组成关系仍是潜在状态，不能进入正式层。",
    authority_not_allowed: "当前路径状态没有正式投影权限。",
    role_visibility_filtered: "正式路径不在当前角色的披露范围内。",
    timing_scope_mismatch: "路径的时间作用域与当前阶段不一致。",
  } as Record<string, string>)[value] || "当前没有可投影的正式路径。";
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
      <a class="primary-command" href="/experience?manage=1">${escapeHtml(actionLabel)}</a>
    </main>`;
}

function renderProfileSelector(cases: ExperienceCaseSummary[], activeProfileId: string): string {
  if (cases.length <= 1) {
    const active = cases.find((item) => item.profile_id === activeProfileId);
    return `<span class="active-case"><i></i>${escapeHtml(active?.display_name || "当前命盘")}</span>`;
  }
  return `<label class="case-select-label"><span>当前命盘</span><select data-profile-select>${cases
    .map((item) => `<option value="${escapeAttr(item.profile_id)}"${item.profile_id === activeProfileId ? " selected" : ""}>${escapeHtml(item.display_name)}</option>`)
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
      <img class="${isBusy ? "" : "abu-avatar-standard"}" src="${isBusy ? "/assets/abu/v9-designer-taoist-divination/web/abu_taoist_divination_v9.webp" : "/assets/abu/v12-actor-pass/quiet-sit-reaction/web/abu_quiet_sit_reaction_v1.webp"}" alt="阿布">
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
