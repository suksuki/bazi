import { createOneCanvasModel } from "./onecanvas-runtime.js";
import {
  ONECANVAS_LAYER_ORDER,
  renderAnnualYearSelect,
  renderBranchNode,
  renderRecomputeIndicator,
  renderStemNode,
  renderTemporalNode,
} from "./onecanvas-components.js";

const root = document.querySelector("#galleryRoot");

boot();

async function boot() {
  try {
    const response = await fetch("./fixture.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`fixture_http_${response.status}`);
    const fixture = await response.json();
    const model = createOneCanvasModel(fixture);
    renderGallery(model);
  } catch (error) {
    root.innerHTML = `<div class="fatal-state"><strong>组件陈列页未能载入</strong><p>${escapeHtml(String(error))}</p></div>`;
  }
}

function renderGallery(model) {
  const formalNodes = model.formalVariant().nodes;
  const candidateSource = model.fixture.candidate_families.year[0];
  const hypotheticalNodes = candidateSource.nodes;
  const formalStem = formalNodes.find((node) => node.node_type === "stem");
  const formalBranch = formalNodes.find((node) => node.node_type === "branch");
  const hypotheticalStem = hypotheticalNodes.find((node) => node.node_type === "stem");
  const luckStem = formalNodes.find((node) => node.node_key === "luck_stem");
  const monthStem = formalNodes.find((node) => node.node_key === "month_stem");
  const monthBranch = formalNodes.find((node) => node.node_key === "month_branch");
  const candidateStem = { ...formalStem, epistemic_status: "candidate" };
  const blockedStem = { ...formalStem, epistemic_status: "blocked" };
  const snapshot = {
    mode: "experiment",
    axis: "day",
    index: model.fixture.baseline_candidate_index.day,
    variant: null,
  };
  const pillarEdit = model.beginPillarEditSession(snapshot, "year_stem", 1);
  const dependentStepper = {
    action: "step-dependent-pillar",
    intent: "pillar:select-dependent",
    previousLabel: "上一组月柱",
    nextLabel: "下一组月柱",
  };

  root.innerHTML = `<header class="gallery-header">
      <div><span>Internal Visual Contract</span><h1>OneCanvas Component Gallery</h1></div>
      <p>固定状态用于视觉回归，不是第二套产品界面。</p>
    </header>
    <section class="gallery-section">
      <div class="gallery-section-heading"><span>01</span><div><h2>语义节点</h2><p>同一组件，不同来源、能力和认识论状态。</p></div></div>
      <div class="node-gallery">
        ${componentCard("正式", "canonical", renderStemNode({ node: formalStem }))}
        ${componentCard("实验", "hypothetical", renderStemNode({ node: hypotheticalStem }))}
        ${componentCard("选中", "selected", renderStemNode({ node: formalStem, selected: true }))}
        ${componentCard("地支", "canonical", renderBranchNode({ node: formalBranch }))}
        ${componentCard("大运 · 派生锁定", "derived", renderTemporalNode({ node: luckStem, capability: { derived: true, editable_in_experiment: false } }))}
        ${componentCard("候选", "candidate", renderStemNode({ node: candidateStem }))}
        ${componentCard("受阻", "blocked", renderStemNode({ node: blockedStem }))}
      </div>
    </section>
    <section class="gallery-section gallery-section-muted">
      <div class="gallery-section-heading"><span>02</span><div><h2>派生链状态</h2><p>改变、无变化、无法计算与处理中必须显式区分。</p></div></div>
      <div class="status-gallery">
        ${renderRecomputeIndicator({ status: "recalculating", detail: "选择已经生效，正在同步更新六柱" })}
        ${renderRecomputeIndicator({ status: "recalculated_changed", luck_pillar: "乙未", formal_reference: { luck_pillar: "甲午" } })}
        ${renderRecomputeIndicator({ status: "recalculated_unchanged", luck_pillar: "甲午" })}
        ${renderRecomputeIndicator({ status: "recalculation_unavailable", failure_reason: "缺少可验证的起运输入" })}
      </div>
    </section>
    <section class="gallery-section">
      <div class="gallery-section-heading"><span>03</span><div><h2>直接操作</h2><p>年日首操作自动定锚，月时整柱选择，流年只选公历年份。</p></div></div>
      <div class="node-gallery">
        ${componentCard("首操作锚点", pillarEdit.previewPillar, renderStemNode({ node: formalStem, previewLabel: pillarEdit.anchorValue, editRole: "anchor" }))}
        ${componentCard("合法配对侧", pillarEdit.legalCounterparts.join(""), renderBranchNode({ node: formalBranch, previewLabel: pillarEdit.counterpartValue, editRole: "counterpart" }))}
        ${componentCard("月柱整柱步进", "dependent", `<div class="gallery-pillar-pair">${renderStemNode({ node: monthStem, selected: true, stepper: dependentStepper })}${renderBranchNode({ node: monthBranch, selected: true, stepper: dependentStepper })}</div>`)}
        ${componentCard("流年", "gregorian", renderAnnualYearSelect({ items: model.annualObservations(), currentYear: model.fixture.formal.analysis_year }))}
      </div>
    </section>
    <section class="gallery-section gallery-section-dark">
      <div class="gallery-section-heading"><span>04</span><div><h2>固定图层</h2><p>R1 只实现必要层，后续层保留稳定顺序但不提前获得功能。</p></div></div>
      <ol class="layer-gallery">${ONECANVAS_LAYER_ORDER.map((layer, index) => `<li><span>${String(index + 1).padStart(2, "0")}</span><strong>${escapeHtml(layer)}</strong><em>${["background", "structural-nodes", "temporal-activation", "interaction-hints", "selection"].includes(layer) ? "R1" : "reserved"}</em></li>`).join("")}</ol>
    </section>`;
}

function componentCard(label, state, markup) {
  return `<article class="component-card" data-component-state="${escapeHtml(state)}"><header><strong>${escapeHtml(label)}</strong><small>${escapeHtml(state)}</small></header><div>${markup}</div></article>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
