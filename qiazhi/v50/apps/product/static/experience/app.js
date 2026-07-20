// apps/product/experience_shell/src/api.ts
async function requestJson(url, init) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...init?.headers || {} },
    ...init
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(String(payload.detail || `request_failed_${response.status}`));
  }
  return response.json();
}
async function loadAccount() {
  const payload = await requestJson(
    "/api/v50/product/auth/me"
  );
  return payload.account;
}
async function loadCases() {
  const payload = await requestJson(
    "/api/v50/experience/cases"
  );
  return payload.cases;
}
function loadEnvelope(caseId) {
  return requestJson(`/api/v50/experience/cases/${encodeURIComponent(caseId)}/baseline`);
}
function loadReadOnlyCanvas(caseId) {
  return requestJson(`/api/v50/experience/cases/${encodeURIComponent(caseId)}/canvas`);
}
async function loadCanvasContext(caseId, stage, selectedObjectRef, layer) {
  const params = new URLSearchParams({ stage, selected: selectedObjectRef, layer });
  const payload = await requestJson(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/canvas/context?${params.toString()}`
  );
  return payload.context;
}
async function loadNarration(caseId) {
  const payload = await requestJson(`/api/v50/narration/cases/${encodeURIComponent(caseId)}/baseline`);
  return { manifest: payload.manifest, speechAssets: payload.speech_assets };
}
async function prepareNarrationSegment(caseId, segmentId) {
  const payload = await requestJson(
    `/api/v50/narration/cases/${encodeURIComponent(caseId)}/baseline/segments/${encodeURIComponent(segmentId)}`,
    { method: "POST" }
  );
  return payload.speech_asset;
}

// apps/product/experience_shell/src/audio.ts
var NarrationTimeline = class {
  constructor(caseId, manifest, statuses, events) {
    this.caseId = caseId;
    this.manifest = manifest;
    this.statuses = statuses;
    this.events = events;
  }
  audio = null;
  index = -1;
  cueTimers = [];
  stopped = false;
  async play() {
    if (this.audio?.paused && this.index >= 0) {
      await this.audio.play();
      this.scheduleCues(this.manifest.segments[this.index]);
      return;
    }
    this.stopped = false;
    this.index = this.index >= 0 ? this.index : 0;
    await this.playIndex(this.index);
  }
  pause() {
    this.clearCues();
    this.audio?.pause();
    const segment = this.manifest.segments[this.index];
    if (segment) this.events.onPaused(segment, this.index);
  }
  stop() {
    this.stopped = true;
    this.clearCues();
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
    }
    this.index = -1;
  }
  async playSegment(index) {
    this.stop();
    this.stopped = false;
    this.index = index;
    await this.playIndex(index);
  }
  async playIndex(index) {
    const segment = this.manifest.segments[index];
    if (!segment || this.stopped) {
      this.events.onComplete();
      return;
    }
    try {
      this.events.onPreparing(segment, index);
      const audioUrl = await this.resolveAudioUrl(segment);
      if (this.stopped) return;
      this.audio = new Audio(audioUrl);
      this.audio.preload = "auto";
      this.audio.addEventListener("play", () => {
        this.events.onPlaying(segment, index);
        this.scheduleCues(segment);
      });
      this.audio.addEventListener("ended", () => {
        this.clearCues();
        this.index = index + 1;
        void this.playIndex(this.index);
      });
      this.audio.addEventListener("error", () => this.events.onError(new Error("audio_playback_failed")));
      await this.audio.play();
    } catch (error) {
      this.events.onError(error instanceof Error ? error : new Error(String(error)));
    }
  }
  async resolveAudioUrl(segment) {
    const status = this.statuses[segment.segment_id];
    if (status?.status === "ready" && status.audio_url) return status.audio_url;
    const asset = await prepareNarrationSegment(this.caseId, segment.segment_id);
    const opus = asset.media.playback_variants.find((item) => item.format === "opus");
    return opus?.audio_url || asset.media.audio_url;
  }
  scheduleCues(segment) {
    this.clearCues();
    for (const cue of segment.visual_cues || []) {
      const remaining = Math.max(0, cue.at_ms - Math.round((this.audio?.currentTime || 0) * 1e3));
      this.cueTimers.push(window.setTimeout(() => this.events.onCue(cue.target), remaining));
    }
  }
  clearCues() {
    this.cueTimers.forEach((timer) => window.clearTimeout(timer));
    this.cueTimers = [];
  }
};

// apps/product/experience_shell/src/components.ts
var elementLabel = {
  wood: "\u6728",
  fire: "\u706B",
  earth: "\u571F",
  metal: "\u91D1",
  water: "\u6C34"
};
var polarityLabel = { yin: "\u9634", yang: "\u9633" };
function renderExperience(view) {
  const claim = view.envelope.approved_claims[0];
  const steps = view.envelope.approved_reasoning_steps;
  const condition = claim?.conditions[0] || "\u5F53\u524D\u8FD8\u6CA1\u6709\u8DB3\u591F\u4F9D\u636E\u5199\u4E0B\u6210\u7ACB\u6761\u4EF6\u3002";
  const uncertainty = view.envelope.uncertainty.reasons[0] || "\u5F53\u524D\u6CA1\u6709\u989D\u5916\u672A\u51B3\u9879\u3002";
  const pathSummary = steps[steps.length - 1]?.conclusion || "\u6B63\u5F0F\u4E3B\u8DEF\u5F84\u4ECD\u5728\u5F62\u6210\u3002";
  const fullThesis = claim?.approved_meaning || "\u547D\u76D8\u4E8B\u5B9E\u5DF2\u7ECF\u786E\u8BA4\uFF0C\u6B63\u5F0F\u6574\u76D8\u8BA4\u77E5\u5C1A\u672A\u63D0\u4EA4\u3002";
  const thesis = firstSentence(fullThesis);
  return `
    <header class="site-header">
      <a class="brand" href="/experience" aria-label="DeepBazi \u770B\u89C1\u547D\u5C40">
        <img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence">
      </a>
      <div class="case-context">
        ${renderCaseSelector(view.cases, view.activeCaseId)}
        <span class="case-version">${escapeHtml(view.envelope.source.life_case_version || "\u4EC5\u547D\u76D8\u4E8B\u5B9E")}</span>
      </div>
      <div class="account-context">
        <span>${escapeHtml(view.accountName)}</span>
        <a href="/app" title="\u8FD4\u56DE\u5F53\u524D\u6863\u6848\u4E0E\u963F\u5E03\u5165\u53E3">\u6863\u6848</a>
      </div>
    </header>

    <main>
      <section class="opening-band" id="baseline-summary" data-anchor="baseline-summary">
        <nav class="journey-nav" aria-label="\u547D\u5C40\u9605\u8BFB\u7AE0\u8282">
          <a href="#baseline-summary" class="active">\u6574\u76D8\u91CD\u5FC3</a>
          <a href="#four-pillars">\u56DB\u67F1</a>
          ${view.canvas ? '<a href="#temporal-canvas">\u65F6\u95F4\u7ED3\u6784</a>' : ""}
          <a href="#baseline-work-path">\u8FD0\u884C\u8DEF\u5F84</a>
          <a href="#baseline-condition">\u6761\u4EF6\u4E0E\u672A\u51B3</a>
        </nav>
        <div class="opening-copy">
          <p class="section-kicker">\u770B\u89C1\u547D\u5C40 \xB7 \u5F53\u524D\u57FA\u7EBF</p>
          <h1>${escapeHtml(thesis)}</h1>
          <p class="opening-lede">\u5148\u770B\u6700\u91CD\u8981\u7684\u56DB\u4EF6\u4E8B\uFF0C\u4E0D\u628A\u6574\u4EFD\u547D\u5C40\u4E00\u6B21\u585E\u7ED9\u4F60\u3002</p>
          <div class="opening-actions">
            <button class="primary-command" type="button" data-command="listen">
              ${view.ui.narrationStatus === "playing" ? "\u6682\u505C\u963F\u5E03" : "\u542C\u963F\u5E03\u8BB2"}
            </button>
            <button class="text-command" type="button" data-command="focus-pillars">\u5148\u770B\u56DB\u67F1</button>
          </div>
        </div>
        <div class="scan-strip" aria-label="\u6574\u76D8\u5FEB\u901F\u6458\u8981">
          ${summaryItem("\u4E3B\u8DEF\u5F84", pathSummary, "baseline-work-path")}
          ${summaryItem("\u6210\u7ACB\u6761\u4EF6", condition, "baseline-condition")}
          ${summaryItem("\u6700\u5927\u672A\u51B3", uncertainty, "baseline-uncertainty")}
        </div>
      </section>

      ${renderCollapsibleSection({
    id: "pillars",
    anchor: "four-pillars",
    tone: "facts",
    eyebrow: "\u547D\u76D8\u4E8B\u5B9E",
    title: "\u56DB\u67F1\u662F\u8FD9\u4EFD\u547D\u5C40\u7684\u5E95\u56FE",
    summary: view.envelope.allowed_chart_facts.map((item) => item.stem + item.branch).join(" \xB7 "),
    expanded: view.ui.expandedSections.pillars,
    body: renderPillars(view.envelope, view.ui.selectedAnchor)
  })}

      ${view.canvas ? renderCollapsibleSection({
    id: "canvas",
    anchor: "temporal-canvas",
    tone: "canvas",
    eyebrow: "\u64CD\u4F5C\u547D\u5C40 \xB7 \u53EA\u8BFB",
    title: "\u770B\u7ED3\u6784\u600E\u6837\u8FDB\u5165\u5F53\u524D\u65F6\u95F4",
    summary: `${view.canvas.source.luck_pillar}\u5927\u8FD0 \xB7 ${view.canvas.source.analysis_year || "\u5F53\u524D"}${view.canvas.source.annual_pillar}\u6D41\u5E74`,
    expanded: view.ui.expandedSections.canvas ?? true,
    body: renderReadOnlyCanvas(view.canvas, view.ui, view.canvasContext)
  }) : ""}

      ${renderCollapsibleSection({
    id: "path",
    anchor: "baseline-work-path",
    tone: "cognition",
    eyebrow: "\u6574\u76D8\u8BA4\u77E5",
    title: "\u8FD9\u5F20\u76D8\u5982\u4F55\u8FD0\u884C",
    summary: pathSummary,
    expanded: view.ui.expandedSections.path,
    body: renderPath(fullThesis, steps, view.ui.selectedAnchor)
  })}

      ${renderCollapsibleSection({
    id: "boundaries",
    anchor: "baseline-condition",
    tone: "boundaries",
    eyebrow: "\u6761\u4EF6\u4E0E\u672A\u51B3",
    title: "\u5224\u65AD\u6210\u7ACB\uFF0C\u4E5F\u8981\u77E5\u9053\u8FB9\u754C\u5728\u54EA\u91CC",
    summary: condition,
    expanded: view.ui.expandedSections.boundaries,
    body: renderBoundaries(claim, view.envelope, view.ui.selectedAnchor)
  })}

      <section class="closing-band">
        <p>\u77E5\u547D\uFF0C\u800C\u540E\u77E5\u5DF1</p>
        <span>\u8FD9\u4EFD\u9875\u9762\u53EA\u663E\u793A\u5DF2\u7ECF\u8FDB\u5165 LifeCase \u7684\u6B63\u5F0F\u8BA4\u77E5\u3002</span>
      </section>
    </main>

    ${renderAbuDock(view)}
  `;
}
function renderReadOnlyCanvas(canvas2, ui2, context) {
  const stage = canvas2.stages[ui2.canvasStage];
  const layer = stage.layers.find((item) => item.layer_id === ui2.canvasLayer) || stage.layers.find((item) => item.layer_id === stage.default_layer_id) || stage.layers[0];
  const visibleRelations = new Set(layer?.relation_refs || []);
  const nodesByRef = new Map(stage.spec.nodes.map((item) => [item.node_ref, item]));
  const selected = ui2.selectedCanvasObject || stage.spec.semantic_slots[0]?.slot_ref || "";
  const activeRelations = stage.spec.relations.filter((item) => visibleRelations.has(item.relation_ref));
  const range = canvas2.source.luck_year_range.length === 2 ? `${canvas2.source.luck_year_range[0]}\u2013${canvas2.source.luck_year_range[1]}` : "\u5F53\u524D\u9636\u6BB5";
  return `<div class="temporal-viewer" data-canvas-stage-root="${escapeAttr(ui2.canvasStage)}">
    <div class="temporal-toolbar">
      <div class="stage-switch" role="tablist" aria-label="\u67E5\u770B\u65F6\u95F4\u9636\u6BB5">
        ${canvas2.stage_order.map((item, index) => {
    const projection = canvas2.stages[item];
    return `<button type="button" role="tab" data-canvas-stage="${item}" aria-selected="${item === ui2.canvasStage}" class="${item === ui2.canvasStage ? "active" : ""}">
            <small>0${index + 1}</small><span>${escapeHtml(projection.title)}</span>
          </button>`;
  }).join("")}
      </div>
      <div class="temporal-status">
        <span>${escapeHtml(ui2.canvasStage === "natal" ? "\u539F\u5C40\u57FA\u7EBF" : ui2.canvasStage === "luck" ? range : `${canvas2.source.analysis_year || "\u5F53\u524D"}\u5E74`)}</span>
        <strong>${escapeHtml(stage.summary)}</strong>
      </div>
    </div>

    <div class="layer-switch" role="tablist" aria-label="\u5173\u7CFB\u56FE\u5C42">
      ${stage.layers.map((item) => `<button type="button" role="tab" data-canvas-layer="${escapeAttr(item.layer_id)}" aria-selected="${item.layer_id === layer?.layer_id}" class="${item.layer_id === layer?.layer_id ? "active" : ""}"${item.available ? "" : " disabled"}>
        <span>${escapeHtml(item.label)}</span><small>${item.count}</small>
      </button>`).join("")}
    </div>

    <div class="canvas-board" data-layer="${escapeAttr(layer?.layer_id || "")}">
      <div class="six-pillar-scroll">
        <div class="six-pillar-rail" style="--pillar-count:${stage.spec.semantic_slots.length}">
          ${stage.spec.semantic_slots.map((slot) => renderCanvasPillar(slot, nodesByRef, selected)).join("")}
        </div>
        ${renderCanvasRelations(stage.spec.semantic_slots, stage.spec.nodes, activeRelations, stage.spec.paths.flatMap((item) => item.relation_refs), selected)}
      </div>
      <p class="layer-caption"><strong>${escapeHtml(layer?.label || "\u5F53\u524D\u56FE\u5C42")}</strong>${escapeHtml(layer?.description || "\u5F53\u524D\u6CA1\u6709\u53EF\u663E\u793A\u7684\u5173\u7CFB\u3002")}</p>
    </div>

    <div class="canvas-reading-grid">
      ${renderCanvasChanges(stage.change_groups, selected, ui2.canvasStage)}
      ${renderCanvasInspector(stage.spec, selected, context, ui2.canvasContextStatus)}
    </div>

    <div class="canvas-boundary ${canvas2.path_availability.status === "available" ? "is-ready" : "is-limited"}">
      <span>${canvas2.path_availability.status === "available" ? "\u4E3B\u8DEF\u5F84\u5DF2\u5BF9\u9F50" : "\u4E3B\u8DEF\u5F84\u672A\u8865\u753B"}</span>
      <p>${escapeHtml(canvas2.path_availability.message)}</p>
      <small>\u5F53\u524D\u67E5\u770B\u53EA\u8BFB\u53D6\u6B63\u5F0F\u6848\u4F8B\uFF0C\u4E0D\u4FEE\u6539\u539F\u5C40\uFF0C\u4E5F\u4E0D\u8C03\u7528 LLM\u3002</small>
    </div>
  </div>`;
}
function renderCanvasPillar(slot, nodesByRef, selected) {
  const nodes = [...nodesByRef.values()].filter((item) => item.semantic_slot_ref === slot.slot_ref);
  const stemNode = nodes.find((item) => item.node_type.includes("stem") && !item.node_type.includes("hidden"));
  const branchNode = nodes.find((item) => item.node_type.includes("branch"));
  const temporal = slot.slot_type === "luck" || slot.slot_type === "year";
  return `<article class="canvas-pillar${temporal ? " is-temporal" : ""}${selected === slot.slot_ref ? " is-selected" : ""}" data-slot-type="${escapeAttr(slot.slot_type)}">
    <button type="button" class="canvas-pillar-label" data-canvas-object="${escapeAttr(slot.slot_ref)}"><span>${escapeHtml(slot.label)}</span>${slot.immutable ? "<small>\u539F\u5C40</small>" : "<small>\u65F6\u95F4</small>"}</button>
    <button type="button" class="canvas-character element-${escapeAttr(stemNode?.element || "")}${selected === stemNode?.node_ref ? " is-selected" : ""}" data-canvas-object="${escapeAttr(stemNode?.node_ref || slot.slot_ref)}" aria-label="${escapeAttr(`${slot.label}\u5929\u5E72${slot.stem}`)}">
      <small>${escapeHtml(stemNode?.ten_god === "day_master" ? "\u65E5\u4E3B" : tenGodLabel(stemNode?.ten_god || "\u5929\u5E72"))}</small><strong>${escapeHtml(slot.stem)}</strong>
    </button>
    <i aria-hidden="true"></i>
    <button type="button" class="canvas-character element-${escapeAttr(branchNode?.element || "")}${selected === branchNode?.node_ref ? " is-selected" : ""}" data-canvas-object="${escapeAttr(branchNode?.node_ref || slot.slot_ref)}" aria-label="${escapeAttr(`${slot.label}\u5730\u652F${slot.branch}`)}">
      <small>\u5730\u652F</small><strong>${escapeHtml(slot.branch)}</strong>
    </button>
    <div class="canvas-hidden-stems"><span>\u85CF\u5E72</span>${slot.hidden_stems.map((item) => `<b>${escapeHtml(item)}</b>`).join("") || "<em>\u65E0</em>"}</div>
  </article>`;
}
function renderCanvasRelations(slots, nodes, relations, pathRelationRefs, selected) {
  const slotIndex = new Map(slots.map((item, index) => [item.slot_ref, index]));
  const nodesByRef = new Map(nodes.map((item) => [item.node_ref, item]));
  const pathRefs = new Set(pathRelationRefs);
  const width = 1200;
  const count = Math.max(slots.length, 1);
  const x = (index) => (index + 0.5) * width / count;
  const y = (node) => node?.node_type.includes("branch") ? 132 : 44;
  const paths = relations.flatMap((relation, index) => {
    const source = nodesByRef.get(relation.from_node_ref);
    const target = nodesByRef.get(relation.to_node_ref);
    const sourceIndex = source ? slotIndex.get(source.semantic_slot_ref) : void 0;
    const targetIndex = target ? slotIndex.get(target.semantic_slot_ref) : void 0;
    if (sourceIndex === void 0 || targetIndex === void 0) return [];
    const x1 = x(sourceIndex);
    const x2 = x(targetIndex);
    const y1 = y(source);
    const y2 = y(target);
    const lift = 30 + index % 4 * 15;
    const controlY = Math.max(12, Math.min(y1, y2) - lift);
    const d = sourceIndex === targetIndex ? `M ${x1 - 7} ${y1} C ${x1 - 70} ${controlY}, ${x1 + 70} ${controlY}, ${x2 + 7} ${y2}` : `M ${x1} ${y1} C ${x1} ${controlY}, ${x2} ${controlY}, ${x2} ${y2}`;
    const midX = (x1 + x2) / 2;
    const classes = [
      "canvas-relation",
      `state-${relation.semantic_state}`,
      pathRefs.has(relation.relation_ref) ? "is-work-path" : "",
      selected === relation.relation_ref ? "is-selected" : ""
    ].filter(Boolean).join(" ");
    return [`<g class="${classes}">
      <path d="${d}" marker-end="url(#canvas-arrow)" data-canvas-object="${escapeAttr(relation.relation_ref)}"></path>
      <text x="${midX}" y="${Math.max(18, controlY - 5)}" text-anchor="middle" tabindex="0" role="button" data-canvas-object="${escapeAttr(relation.relation_ref)}" aria-label="${escapeAttr(relation.label)}">${escapeHtml(relation.label)}</text>
    </g>`];
  }).join("");
  if (!paths) return `<div class="relation-empty"><span>\u6B64\u56FE\u5C42\u5728\u5F53\u524D\u9636\u6BB5\u6CA1\u6709\u5DF2\u62AB\u9732\u5173\u7CFB</span><small>\u9875\u9762\u4E0D\u4F1A\u4E3A\u4E86\u586B\u6EE1\u753B\u9762\u800C\u8865\u7EBF\u3002</small></div>`;
  return `<svg class="relation-map" viewBox="0 0 ${width} 170" preserveAspectRatio="xMidYMid meet" aria-label="\u5F53\u524D\u5173\u7CFB\u56FE">
    <defs><marker id="canvas-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker></defs>
    ${paths}
  </svg>`;
}
function renderCanvasChanges(groups, selected, stage) {
  const visible = groups.filter((item) => item.count > 0);
  return `<section class="canvas-diff-panel" aria-label="\u9636\u6BB5\u53D8\u5316">
    <header><span>\u9636\u6BB5\u5DEE\u5F02</span><strong>${stage === "natal" ? "\u8FD9\u662F\u6BD4\u8F83\u57FA\u7EBF" : "\u53EA\u5217\u5408\u540C\u5DF2\u7ECF\u7ED9\u51FA\u7684\u53D8\u5316"}</strong></header>
    ${visible.length ? `<div class="change-list">${visible.map((group) => `<div class="change-group change-${escapeAttr(group.change_type)}">
      <span><b>${escapeHtml(group.label)}</b><em>${group.count}</em></span>
      ${group.items.slice(0, 5).map((item) => `<button type="button" data-canvas-object="${escapeAttr(item.target_ref)}" class="${selected === item.target_ref ? "is-selected" : ""}">${escapeHtml(item.label)}</button>`).join("")}
    </div>`).join("")}</div>` : `<div class="baseline-diff"><b>\u539F\u5C40</b><p>\u5148\u5EFA\u7ACB\u56DB\u67F1\u3001\u5173\u7CFB\u4E0E\u6B63\u5F0F\u4E3B\u8DEF\u5F84\u7684\u6BD4\u8F83\u8D77\u70B9\u3002</p></div>`}
    <details><summary>\u516B\u79CD\u53D8\u5316\u8BED\u4E49</summary><p>${groups.map((item) => `${item.label} ${item.count}`).join(" \xB7 ")}</p></details>
  </section>`;
}
function renderCanvasInspector(spec, selected, context, status) {
  const slot = spec.semantic_slots.find((item2) => item2.slot_ref === selected);
  const node = spec.nodes.find((item2) => item2.node_ref === selected);
  const relation = spec.relations.find((item2) => item2.relation_ref === selected);
  const path = spec.paths.find((item2) => item2.path_ref === selected);
  const cluster = spec.clusters.find((item2) => item2.cluster_ref === selected);
  const item = slot || node || relation || path || cluster;
  if (!item) return `<section class="canvas-inspector"><p>\u70B9\u51FB\u4E00\u67F1\u3001\u4E00\u4E2A\u5E72\u652F\u6216\u4E00\u6761\u5173\u7CFB\uFF0C\u67E5\u770B\u5B83\u5728\u5F53\u524D\u6B63\u5F0F\u72B6\u6001\u4E2D\u7684\u4F4D\u7F6E\u3002</p></section>`;
  const trace = item.trace;
  const label = slot ? `${slot.label} ${slot.stem}${slot.branch}` : item.label;
  const type = slot ? "\u8BED\u4E49\u67F1\u4F4D" : node ? nodeTypeLabel(node.node_type) : relation ? "\u7ED3\u6784\u5173\u7CFB" : path ? "\u547D\u5C40\u8DEF\u5F84" : "\u7ED3\u6784\u5019\u9009";
  const semanticState = relation?.semantic_state || path?.semantic_state || trace.epistemic_status;
  const contextMatches = context?.selected_object_refs.includes(selected);
  return `<section class="canvas-inspector" aria-label="\u5BF9\u8C61\u89E3\u91CA">
    <header><span>${escapeHtml(type)}</span><b class="epistemic-${escapeAttr(trace.epistemic_status)}">${escapeHtml(epistemicLabel(trace.epistemic_status))}</b></header>
    <h3>${escapeHtml(label)}</h3>
    <p>${status === "loading" ? "\u6B63\u5728\u53D6\u56DE\u8FD9\u4E2A\u5BF9\u8C61\u7684\u53D7\u63A7\u4E0A\u4E0B\u6587\u3002" : contextMatches ? objectExplanation(slot, node, relation, path) : "\u9009\u62E9\u5DF2\u5B9A\u4F4D\uFF1B\u53D7\u63A7\u4E0A\u4E0B\u6587\u5C06\u5728\u8FD9\u91CC\u663E\u793A\u3002"}</p>
    <dl><div><dt>\u5F53\u524D\u72B6\u6001</dt><dd>${escapeHtml(stateLabel(semanticState))}</dd></div><div><dt>\u6765\u6E90</dt><dd>${trace.source_refs.length} \u6761\u53EF\u8FFD\u6EAF\u5F15\u7528</dd></div><div><dt>\u5F53\u524D\u9636\u6BB5</dt><dd>${escapeHtml(spec.stage)}</dd></div></dl>
    ${trace.uncertainty.length || trace.rejection_or_block_reasons.length ? `<div class="inspector-caution"><span>\u4ECD\u9700\u4FDD\u7559</span><p>${escapeHtml([...trace.uncertainty, ...trace.rejection_or_block_reasons][0])}</p></div>` : ""}
    <details><summary>\u67E5\u770B\u6765\u6E90</summary><ul>${trace.source_refs.map((ref) => `<li>${escapeHtml(ref)}</li>`).join("")}</ul></details>
  </section>`;
}
function objectExplanation(slot, node, relation, path) {
  if (slot) return slot.immutable ? "\u8FD9\u662F\u539F\u5C40\u56FA\u5B9A\u67F1\u4F4D\uFF1B\u89C6\u89C9\u91CD\u6392\u4E0D\u4F1A\u6539\u53D8\u5B83\u7684\u5E74\u3001\u6708\u3001\u65E5\u3001\u65F6\u8EAB\u4EFD\u3002" : "\u8FD9\u662F\u6B63\u5F0F\u5386\u6CD5\u65F6\u95F4\u67F1\uFF1B\u51FA\u73B0\u4E0D\u7B49\u4E8E\u5DF2\u7ECF\u5F62\u6210\u73B0\u5B9E\u4E8B\u4EF6\u5224\u65AD\u3002";
  if (node) return `${node.label}\u5C5E\u4E8E${elementLabel[node.element] || "\u672A\u6807\u6CE8\u4E94\u884C"}${node.ten_god ? `\uFF0C\u5F53\u524D\u5341\u795E\u6807\u8BB0\u4E3A${tenGodLabel(node.ten_god)}` : ""}\u3002`;
  if (relation) return `${relation.label}\u7531 Compiler \u63D0\u4F9B\uFF0C\u9875\u9762\u53EA\u8D1F\u8D23\u5B9A\u4F4D\u4E0E\u663E\u793A\u3002`;
  if (path) return path.label;
  return "\u8FD9\u662F\u5F53\u524D\u89D2\u8272\u83B7\u51C6\u67E5\u770B\u7684\u7ED3\u6784\u5019\u9009\u3002";
}
function epistemicLabel(value) {
  return { fact: "\u6B63\u5F0F\u4E8B\u5B9E", derived: "\u7ED3\u6784\u63A8\u5BFC", candidate: "\u5019\u9009", committed: "\u5DF2\u63D0\u4EA4", blocked: "\u5DF2\u963B\u6B62", hypothetical: "\u5047\u8BBE", presentation_only: "\u4EC5\u5C55\u793A" }[value] || value;
}
function stateLabel(value) {
  return { latent: "\u6F5C\u5728", active: "\u53C2\u4E0E\u4E2D", reinforced: "\u83B7\u5F97\u652F\u6301", weakened: "\u53D7\u5230\u5236\u7EA6", blocked: "\u65E0\u6CD5\u95ED\u5408", fact: "\u4E8B\u5B9E", derived: "\u63A8\u5BFC", candidate: "\u5019\u9009", committed: "\u5DF2\u63D0\u4EA4" }[value] || value;
}
function nodeTypeLabel(value) {
  if (value.includes("hidden")) return "\u85CF\u5E72\u8282\u70B9";
  if (value.includes("stem")) return "\u5929\u5E72\u8282\u70B9";
  if (value.includes("branch")) return "\u5730\u652F\u8282\u70B9";
  return "\u7ED3\u6784\u8282\u70B9";
}
function tenGodLabel(value) {
  return {
    day_master: "\u65E5\u4E3B",
    bi_jian: "\u6BD4\u80A9",
    jie_cai: "\u52AB\u8D22",
    shi_shen: "\u98DF\u795E",
    shang_guan: "\u4F24\u5B98",
    pian_cai: "\u504F\u8D22",
    zheng_cai: "\u6B63\u8D22",
    qi_sha: "\u4E03\u6740",
    zheng_guan: "\u6B63\u5B98",
    pian_yin: "\u504F\u5370",
    zheng_yin: "\u6B63\u5370"
  }[value] || value;
}
function renderLoading(message) {
  return `<main class="system-state"><div class="state-mark"></div><p>\u770B\u89C1\u547D\u5C40</p><h1>${escapeHtml(message)}</h1></main>`;
}
function renderUnavailable(title, detail, actionLabel) {
  return `
    <main class="system-state unavailable">
      <img src="/assets/abu/v11-designer-sad-tears/web/abu_sad_tears_v11.webp" alt="\u963F\u5E03\u6B63\u5728\u7B49\u5F85">
      <p>\u963F\u5E03\u5728\u8FD9\u91CC</p>
      <h1>${escapeHtml(title)}</h1>
      <span>${escapeHtml(detail)}</span>
      <a class="primary-command" href="/app">${escapeHtml(actionLabel)}</a>
    </main>`;
}
function renderCaseSelector(cases2, activeCaseId2) {
  if (cases2.length <= 1) {
    const active = cases2.find((item) => item.case_id === activeCaseId2);
    return `<span class="active-case"><i></i>${escapeHtml(active?.display_name || "\u5F53\u524D\u547D\u76D8")}</span>`;
  }
  return `<label class="case-select-label"><span>\u5F53\u524D\u547D\u76D8</span><select data-case-select>${cases2.map((item) => `<option value="${escapeAttr(item.case_id)}"${item.case_id === activeCaseId2 ? " selected" : ""}>${escapeHtml(item.display_name)}</option>`).join("")}</select></label>`;
}
function summaryItem(label, value, anchor) {
  return `<button type="button" class="scan-item" data-select-anchor="${escapeAttr(anchor)}" data-message="${escapeAttr(value)}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></button>`;
}
function renderCollapsibleSection(input) {
  return `
    <section class="experience-section tone-${escapeAttr(input.tone)}${input.expanded ? " is-expanded" : " is-collapsed"}" id="${escapeAttr(input.anchor)}" data-anchor="${escapeAttr(input.anchor)}">
      <button class="section-heading" type="button" data-toggle-section="${escapeAttr(input.id)}" aria-expanded="${input.expanded}">
        <span><small>${escapeHtml(input.eyebrow)}</small><strong>${escapeHtml(input.title)}</strong><em>${escapeHtml(input.summary)}</em></span>
        <b aria-hidden="true">${input.expanded ? "\u2212" : "+"}</b>
      </button>
      <div class="section-body"${input.expanded ? "" : " hidden"}>${input.body}</div>
    </section>`;
}
function renderPillars(envelope2, selectedAnchor) {
  const pillars = envelope2.allowed_chart_facts.filter((item) => item.fact_type === "pillar");
  if (!pillars.length) return `<p class="empty-note">\u56DB\u67F1\u4E8B\u5B9E\u5C1A\u672A\u8FDB\u5165\u8FD9\u4EFD\u4F53\u9A8C\u3002</p>`;
  return `<div class="pillar-stage">${pillars.map((pillar) => {
    const message = `${pillar.pillar_label}\u662F${pillar.stem}${pillar.branch}\u3002${pillar.visible_ten_god ? `\u5929\u5E72\u5173\u7CFB\u4E3A${pillar.visible_ten_god}\u3002` : ""}${pillar.hidden_stems.length ? `\u5730\u652F\u85CF${pillar.hidden_stems.map((item) => item.stem).join("\u3001")}\u3002` : ""}`;
    return `<button type="button" class="pillar${selectedAnchor === pillar.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr(pillar.visual_anchor)}" data-message="${escapeAttr(message)}">
      <span class="pillar-label">${escapeHtml(pillar.pillar_label)}</span>
      <span class="ten-god">${escapeHtml(pillar.visible_ten_god || "\u5929\u5E72")}</span>
      <strong class="stem element-${escapeAttr(pillar.stem_element)}" data-polarity="${escapeAttr(pillar.stem_polarity)}">${escapeHtml(pillar.stem)}</strong>
      <strong class="branch element-${escapeAttr(pillar.branch_element)}" data-polarity="${escapeAttr(pillar.branch_polarity)}">${escapeHtml(pillar.branch)}</strong>
      <span class="nature">${polarityLabel[pillar.stem_polarity] || ""}${elementLabel[pillar.stem_element] || ""} \xB7 ${polarityLabel[pillar.branch_polarity] || ""}${elementLabel[pillar.branch_element] || ""}</span>
      <span class="hidden-stems">${pillar.hidden_stems.map((item) => `<i class="element-${escapeAttr(item.element)}"><b>${escapeHtml(item.stem)}</b><em>${escapeHtml(item.ten_god)}</em></i>`).join("")}</span>
    </button>`;
  }).join("")}</div>`;
}
function renderPath(fullThesis, steps, selectedAnchor) {
  if (!steps.length) return `<p class="empty-note">\u4E3B\u8DEF\u5F84\u4ECD\u5728\u53EF\u9760\u6027\u95E8\u7981\u5185\uFF0C\u6CA1\u6709\u88AB\u5305\u88C5\u6210\u786E\u5B9A\u7ED3\u8BBA\u3002</p>`;
  return `<button type="button" class="baseline-thesis${selectedAnchor === "baseline-summary" ? " is-selected" : ""}" data-select-anchor="baseline-summary" data-message="${escapeAttr(fullThesis)}">
    <span>\u6574\u76D8\u603B\u65AD</span><strong>${escapeHtml(fullThesis)}</strong>
  </button><div class="path-stage">${steps.map((step, index) => {
    const message = `${step.premise}\uFF0C\u56E0\u6B64\u5F53\u524D\u5F97\u5230\u7684\u5224\u65AD\u662F\uFF1A${step.conclusion}`;
    return `<button type="button" class="path-step${selectedAnchor === step.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr(step.visual_anchor)}" data-message="${escapeAttr(message)}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <small>${escapeHtml(step.premise)}</small>
      <strong>${escapeHtml(step.conclusion)}</strong>
    </button>`;
  }).join('<span class="path-arrow" aria-hidden="true">\u2192</span>')}</div>`;
}
function firstSentence(value) {
  const match = value.match(/^.*?[。！？](?:[”’"])?/u);
  return match?.[0] || value;
}
function renderBoundaries(claim, envelope2, selectedAnchor) {
  const condition = claim?.conditions[0] || "\u6B63\u5F0F\u6761\u4EF6\u5C1A\u672A\u63D0\u4EA4\u3002";
  const uncertainty = envelope2.uncertainty.reasons[0] || "\u5F53\u524D\u6CA1\u6709\u989D\u5916\u672A\u51B3\u9879\u3002";
  const counter = claim?.counter_signals[0] || envelope2.competing_hypotheses[0]?.approved_meaning || "\u5C1A\u65E0\u5DF2\u63D0\u4EA4\u7684\u53CD\u5411\u4FE1\u53F7\u3002";
  return `<div class="boundary-grid">
    ${boundaryItem("\u6210\u7ACB\u6761\u4EF6", condition, "baseline-condition", selectedAnchor)}
    ${boundaryItem("\u6700\u5927\u672A\u51B3", uncertainty, "baseline-uncertainty", selectedAnchor)}
    ${boundaryItem("\u53CD\u5411\u4FE1\u53F7", counter, "baseline-counter-signal", selectedAnchor)}
  </div>`;
}
function boundaryItem(label, text, anchor, selectedAnchor) {
  return `<button type="button" class="boundary-item${selectedAnchor === anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr(anchor)}" data-message="${escapeAttr(text)}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(text)}</strong></button>`;
}
function renderAbuDock(view) {
  const segment = view.narrationManifest?.segments[view.ui.narrationIndex];
  const isBusy = view.ui.narrationStatus === "preparing";
  return `<aside class="abu-dock${view.ui.abuExpanded ? " is-open" : ""}${isBusy ? " is-thinking" : ""}" aria-label="\u963F\u5E03\u540C\u6B65\u8BBA\u547D">
    <button class="abu-avatar" type="button" data-command="toggle-abu" aria-label="${view.ui.abuExpanded ? "\u6536\u8D77\u963F\u5E03" : "\u6253\u5F00\u963F\u5E03"}">
      <img src="${isBusy ? "/assets/abu/v9-designer-taoist-divination/web/abu_taoist_divination_v9.webp" : "/assets/abu/v4-video-derived/web/abu_idle_blink_v4.webp"}" alt="\u963F\u5E03">
    </button>
    <div class="abu-bubble" role="status"><span>${segment ? escapeHtml(segment.title) : "\u963F\u5E03"}</span><p>${escapeHtml(view.ui.abuMessage)}</p></div>
    <div class="abu-panel"${view.ui.abuExpanded ? "" : " hidden"}>
      <div class="abu-panel-heading"><span>\u963F\u5E03\u540C\u6B65\u8BBA\u547D</span><button type="button" data-command="toggle-abu" aria-label="\u6536\u8D77">\xD7</button></div>
      <p>${escapeHtml(view.ui.abuMessage)}</p>
      <div class="narration-controls">
        <button type="button" class="primary-command compact" data-command="listen">${view.ui.narrationStatus === "playing" ? "\u6682\u505C" : "\u7EE7\u7EED\u542C"}</button>
        <button type="button" class="text-command" data-command="stop">\u505C\u6B62</button>
      </div>
      <ol class="chapter-list">${(view.narrationManifest?.segments || []).map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><span>${escapeHtml(item.title)}</span><small>${escapeHtml(item.text)}</small></button></li>`).join("")}</ol>
    </div>
  </aside>`;
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character] || character);
}
function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

// apps/product/experience_shell/src/state.ts
var initialUiState = {
  selectedAnchor: "baseline-summary",
  expandedSections: {
    baseline: true,
    pillars: true,
    canvas: true,
    path: true,
    boundaries: true
  },
  abuExpanded: false,
  narrationStatus: "idle",
  narrationIndex: -1,
  abuMessage: "\u6211\u5148\u966A\u4F60\u770B\u6574\u76D8\u91CD\u5FC3\u3002\u60F3\u542C\u7684\u65F6\u5019\uFF0C\u70B9\u6211\u5C31\u597D\u3002",
  canvasStage: "natal",
  canvasLayer: "work_path",
  selectedCanvasObject: "",
  canvasContextStatus: "idle"
};
function reduceUi(state, action) {
  switch (action.type) {
    case "select":
      return { ...state, selectedAnchor: action.anchor, abuMessage: action.message };
    case "toggle-section":
      return {
        ...state,
        expandedSections: {
          ...state.expandedSections,
          [action.section]: !state.expandedSections[action.section]
        }
      };
    case "toggle-abu":
      return { ...state, abuExpanded: action.expanded ?? !state.abuExpanded };
    case "narration":
      return {
        ...state,
        narrationStatus: action.status,
        narrationIndex: action.index ?? state.narrationIndex,
        abuMessage: action.message ?? state.abuMessage
      };
    case "canvas-stage":
      return {
        ...state,
        canvasStage: action.stage,
        canvasLayer: action.layer,
        selectedCanvasObject: action.selected,
        canvasContextStatus: "ready"
      };
    case "canvas-layer":
      return { ...state, canvasLayer: action.layer };
    case "canvas-select":
      return {
        ...state,
        selectedCanvasObject: action.selected,
        canvasContextStatus: action.status
      };
    case "canvas-context-status":
      return { ...state, canvasContextStatus: action.status };
  }
}

// apps/product/experience_shell/src/main.ts
var rootElement = document.querySelector("#experienceRoot");
if (!rootElement) throw new Error("experience_root_missing");
var root = rootElement;
var account = { display_name: "", role: "member" };
var cases = [];
var activeCaseId = "";
var envelope = null;
var canvas = null;
var canvasContext = null;
var narrationManifest = null;
var narrationAssets = {};
var timeline = null;
var ui = structuredClone(initialUiState);
void boot();
async function boot() {
  root.innerHTML = renderLoading("\u6B63\u5728\u53D6\u56DE\u4F60\u7684\u6B63\u5F0F\u547D\u5C40\u8BA4\u77E5");
  try {
    account = await loadAccount();
    cases = await loadCases();
    if (!cases.length) {
      root.innerHTML = renderUnavailable(
        "\u8FD8\u6CA1\u6709\u53EF\u4EE5\u9605\u8BFB\u7684\u547D\u5C40",
        "\u5148\u8BA9\u963F\u5E03\u5E2E\u4F60\u5EFA\u7ACB\u51FA\u751F\u6863\u6848\uFF0C\u5E76\u5B8C\u6210\u7B2C\u4E00\u4EFD\u6574\u76D8\u57FA\u7EBF\u3002",
        "\u53BB\u627E\u963F\u5E03\u5EFA\u6863"
      );
      return;
    }
    const requested = new URLSearchParams(location.search).get("case") || "";
    const selected = cases.find((item) => item.case_id === requested) || cases.find((item) => item.baseline_available) || cases[0];
    await openCase(selected.case_id);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const unauthenticated = message.includes("authentication_required");
    root.innerHTML = renderUnavailable(
      unauthenticated ? "\u5148\u548C\u963F\u5E03\u6253\u4E2A\u62DB\u547C" : "\u8FD9\u4EFD\u547D\u5C40\u6682\u65F6\u6CA1\u6709\u51C6\u5907\u597D",
      unauthenticated ? "\u767B\u5F55\u540E\uFF0C\u963F\u5E03\u4F1A\u7EE7\u7EED\u4F60\u5DF2\u7ECF\u5EFA\u7ACB\u7684 LifeCase\u3002" : humanizeError(message),
      unauthenticated ? "\u767B\u5F55\u6216\u6CE8\u518C" : "\u8FD4\u56DE\u963F\u5E03\u5165\u53E3"
    );
  }
}
async function openCase(caseId) {
  timeline?.stop();
  activeCaseId = caseId;
  envelope = await loadEnvelope(caseId);
  try {
    canvas = await loadReadOnlyCanvas(caseId);
    const initialStage = canvas.default_stage;
    const initialProjection = canvas.stages[initialStage];
    canvasContext = initialProjection.context;
    ui = reduceUi(ui, {
      type: "canvas-stage",
      stage: initialStage,
      layer: initialProjection.default_layer_id,
      selected: initialProjection.context.selected_object_refs[0] || initialProjection.spec.semantic_slots[0]?.slot_ref || ""
    });
  } catch {
    canvas = null;
    canvasContext = null;
  }
  try {
    const narration = await loadNarration(caseId);
    narrationManifest = narration.manifest;
    narrationAssets = narration.speechAssets;
  } catch {
    narrationManifest = null;
    narrationAssets = {};
  }
  timeline = narrationManifest ? createTimeline(caseId, narrationManifest, narrationAssets) : null;
  history.replaceState({}, "", `/experience?case=${encodeURIComponent(caseId)}`);
  render();
}
function createTimeline(caseId, manifest, statuses) {
  return new NarrationTimeline(caseId, manifest, statuses, {
    onPreparing(segment, index) {
      dispatch({ type: "narration", status: "preparing", index, message: `\u6211\u6B63\u5728\u51C6\u5907\u201C${segment.title}\u201D\u3002\u9875\u9762\u53EF\u4EE5\u5148\u770B\uFF0C\u4E0D\u7528\u7B49\u6211\u3002` });
    },
    onPlaying(segment, index) {
      dispatch({ type: "narration", status: "playing", index, message: segment.text });
      focusAnchor(segment.visual_anchor_ids[0] || "baseline-summary", false);
    },
    onPaused(segment, index) {
      dispatch({ type: "narration", status: "paused", index, message: `\u505C\u5728\u201C${segment.title}\u201D\u3002\u4F60\u53EF\u4EE5\u5148\u770B\u9875\u9762\uFF0C\u4E5F\u53EF\u4EE5\u7EE7\u7EED\u542C\u3002` });
    },
    onComplete() {
      dispatch({ type: "narration", status: "complete", index: -1, message: "\u8FD9\u6B21\u5148\u8BB2\u5230\u8FD9\u91CC\u3002\u4F60\u53EF\u4EE5\u70B9\u56DB\u67F1\u3001\u8DEF\u5F84\u6216\u672A\u51B3\u9879\u7EE7\u7EED\u95EE\u3002" });
    },
    onError(error) {
      dispatch({ type: "narration", status: "error", message: `\u58F0\u97F3\u6682\u65F6\u6CA1\u6709\u51C6\u5907\u597D\uFF1A${humanizeError(error.message)}\u3002\u6587\u5B57\u5185\u5BB9\u4ECD\u7136\u5B8C\u6574\u53EF\u8BFB\u3002` });
    },
    onCue(anchor) {
      focusAnchor(anchor, false);
    }
  });
}
function render() {
  if (!envelope) return;
  root.innerHTML = renderExperience({
    accountName: account.display_name,
    accountRole: account.role,
    cases,
    activeCaseId,
    envelope,
    narrationManifest,
    canvas,
    canvasContext,
    ui
  });
  bindInteractions();
  requestAnimationFrame(() => applyActiveAnchor(ui.selectedAnchor));
}
function bindInteractions() {
  root.querySelectorAll("[data-select-anchor]").forEach((element) => {
    element.addEventListener("click", () => {
      const anchor = element.dataset.selectAnchor || "baseline-summary";
      const message = element.dataset.message || "\u8FD9\u4E00\u5904\u6765\u81EA\u6B63\u5F0F\u547D\u5C40\u8BA4\u77E5\u3002";
      dispatch({ type: "select", anchor, message });
      focusAnchor(anchor);
    });
  });
  root.querySelectorAll("[data-toggle-section]").forEach((button) => {
    button.addEventListener("click", () => dispatch({ type: "toggle-section", section: button.dataset.toggleSection || "baseline" }));
  });
  root.querySelectorAll("[data-command]").forEach((button) => {
    button.addEventListener("click", () => void handleCommand(button.dataset.command || ""));
  });
  root.querySelectorAll("[data-play-segment]").forEach((button) => {
    button.addEventListener("click", () => void timeline?.playSegment(Number(button.dataset.playSegment || 0)));
  });
  root.querySelectorAll("[data-canvas-stage]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!canvas) return;
      const stage = button.dataset.canvasStage || "natal";
      const projection = canvas.stages[stage];
      canvasContext = projection.context;
      ui = reduceUi(ui, {
        type: "canvas-stage",
        stage,
        layer: projection.default_layer_id,
        selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || ""
      });
      render();
    });
  });
  root.querySelectorAll("[data-canvas-layer]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!canvas || button.disabled) return;
      const layer = button.dataset.canvasLayer || "generation_control";
      ui = reduceUi(ui, { type: "canvas-layer", layer });
      render();
      if (ui.selectedCanvasObject) void refreshCanvasContext(ui.selectedCanvasObject);
    });
  });
  root.querySelectorAll("[data-canvas-object]").forEach((element) => {
    element.addEventListener("click", () => {
      const selected = element.getAttribute("data-canvas-object") || "";
      if (selected) void refreshCanvasContext(selected);
    });
    element.addEventListener("keydown", (event) => {
      if (event instanceof KeyboardEvent && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        const selected = element.getAttribute("data-canvas-object") || "";
        if (selected) void refreshCanvasContext(selected);
      }
    });
  });
  root.querySelector("[data-case-select]")?.addEventListener("change", (event) => {
    const select = event.currentTarget;
    root.innerHTML = renderLoading("\u6B63\u5728\u5207\u6362\u547D\u76D8");
    void openCase(select.value);
  });
}
async function refreshCanvasContext(selected) {
  if (!canvas) return;
  ui = reduceUi(ui, { type: "canvas-select", selected, status: "loading" });
  render();
  try {
    canvasContext = await loadCanvasContext(activeCaseId, ui.canvasStage, selected, ui.canvasLayer);
    ui = reduceUi(ui, { type: "canvas-context-status", status: "ready" });
  } catch {
    canvasContext = null;
    ui = reduceUi(ui, { type: "canvas-context-status", status: "error" });
  }
  render();
}
async function handleCommand(command) {
  if (command === "toggle-abu") {
    dispatch({ type: "toggle-abu" });
    return;
  }
  if (command === "listen") {
    dispatch({ type: "toggle-abu", expanded: true });
    if (!timeline) {
      dispatch({ type: "narration", status: "error", message: "\u8FD9\u4EFD\u6848\u4F8B\u6682\u65F6\u6CA1\u6709\u53EF\u64AD\u653E\u7684\u6B63\u5F0F\u8BB2\u89E3\u3002" });
    } else if (ui.narrationStatus === "playing") {
      timeline.pause();
    } else {
      await timeline.play();
    }
    return;
  }
  if (command === "stop") {
    timeline?.stop();
    dispatch({ type: "narration", status: "idle", index: -1, message: "\u5DF2\u505C\u6B62\u3002\u4F60\u53EF\u4EE5\u70B9\u4EFB\u610F\u547D\u7406\u5BF9\u8C61\uFF0C\u8BA9\u6211\u4ECE\u90A3\u91CC\u7EE7\u7EED\u3002" });
    return;
  }
  if (command === "focus-pillars") focusAnchor("four-pillars");
}
function dispatch(action) {
  ui = reduceUi(ui, action);
  render();
}
function focusAnchor(anchor, scroll = true) {
  ui = reduceUi(ui, { type: "select", anchor, message: ui.abuMessage });
  applyActiveAnchor(anchor);
  if (scroll) document.querySelector(`[data-anchor="${CSS.escape(anchor)}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
}
function applyActiveAnchor(anchor) {
  document.querySelectorAll(".narration-active").forEach((element) => element.classList.remove("narration-active"));
  document.querySelectorAll(`[data-anchor="${CSS.escape(anchor)}"], [data-select-anchor="${CSS.escape(anchor)}"]`).forEach((element) => element.classList.add("narration-active"));
}
function humanizeError(message) {
  return message.replace(/^formal_life_case_not_available$/, "\u6B63\u5F0F\u6574\u76D8\u8BA4\u77E5\u5C1A\u672A\u901A\u8FC7\u53EF\u9760\u6027\u95E8\u7981\u3002").replace(/^experience_case_not_found$/, "\u6CA1\u6709\u627E\u5230\u8FD9\u4EFD\u6848\u4F8B\uFF0C\u6216\u5B83\u4E0D\u5C5E\u4E8E\u5F53\u524D\u8D26\u6237\u3002").replace(/^canvas_official_timing_required$/, "\u8FD9\u4EFD\u6848\u4F8B\u8FD8\u6CA1\u6709\u5B8C\u6574\u7684\u5927\u8FD0\u4E0E\u6D41\u5E74\u8BA1\u7B97\u3002").replace(/_/g, " ");
}
