import { compileSceneState, objectByRef } from "./scene-runtime.js";

const root = document.querySelector("#sceneRoot");
if (!root) throw new Error("mingli_scene_root_missing");

const PROFILE_LABELS = {
  lab: ["理图", "准确结构"],
  xiangfa: ["入象", "直观意象"],
  theater: ["演时", "动态路径"],
};

const TEN_GOD_LABELS = {
  day_master: "日主", bi_jian: "比肩", jie_cai: "劫财",
  shi_shen: "食神", shang_guan: "伤官", pian_cai: "偏财",
  zheng_cai: "正财", qi_sha: "七杀", zheng_guan: "正官",
  pian_yin: "偏印", zheng_yin: "正印",
};

const PILLAR_LABELS = ["年柱", "月柱", "日柱", "时柱"];
const ELEMENT_LABELS = { wood: "木", fire: "火", earth: "土", metal: "金", water: "水", temporal: "时" };

let fixture = null;
let scene = null;
let playTimer = null;

const state = {
  renderProfile: "lab",
  mode: "formal",
  variantIndex: 0,
  yearIndex: 2,
  pathLens: "formal",
  draftNodes: [],
  selectedSemanticRef: "node:day_stem",
  hourPickerOpen: false,
  drawing: false,
  cueIndex: -1,
  playing: false,
  abuOpen: !window.matchMedia("(max-width: 720px)").matches,
};

boot();

async function boot() {
  try {
    const response = await fetch("../mingli-lab-c2a/fixture.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`fixture_http_${response.status}`);
    fixture = await response.json();
    state.variantIndex = fixture.baseline_variant_index;
    state.yearIndex = Math.max(0, fixture.year_dial.findIndex((item) => item.source_mode === "official"));
    render();
    root.addEventListener("click", handleClick);
  } catch (error) {
    root.innerHTML = `<section class="empty-state"><h1>共享场景没有准备好</h1><p>${escapeHtml(String(error))}</p></section>`;
  }
}

function handleClick(event) {
  const target = event.target instanceof Element ? event.target.closest("[data-action]") : null;
  if (!target) return;
  const action = target.getAttribute("data-action") || "";

  if (action === "set-profile") {
    stopPlayback();
    state.renderProfile = target.getAttribute("data-profile") || "lab";
    render();
    return;
  }
  if (action === "create-experiment") {
    stopPlayback();
    state.mode = "experiment";
    state.hourPickerOpen = true;
    render();
    return;
  }
  if (action === "restore-formal") {
    stopPlayback();
    state.mode = "formal";
    state.variantIndex = fixture.baseline_variant_index;
    state.yearIndex = fixture.year_dial.findIndex((item) => item.source_mode === "official");
    state.pathLens = "formal";
    state.draftNodes = [];
    state.drawing = false;
    state.hourPickerOpen = false;
    render();
    return;
  }
  if (action === "toggle-hour-picker") {
    if (state.mode === "formal") state.mode = "experiment";
    state.hourPickerOpen = !state.hourPickerOpen;
    render();
    return;
  }
  if (action === "select-hour") {
    stopPlayback();
    state.mode = "experiment";
    state.variantIndex = Number(target.getAttribute("data-index"));
    state.hourPickerOpen = false;
    state.selectedSemanticRef = "node:hour_stem";
    render();
    return;
  }
  if (action === "select-year") {
    stopPlayback();
    if (state.mode === "formal") state.mode = "experiment";
    state.yearIndex = Number(target.getAttribute("data-index"));
    state.selectedSemanticRef = "temporal:year";
    render();
    return;
  }
  if (action === "set-path-lens") {
    stopPlayback();
    state.pathLens = target.getAttribute("data-lens") || "formal";
    state.drawing = state.pathLens === "draft";
    render();
    return;
  }
  if (action === "start-draft") {
    stopPlayback();
    if (state.mode === "formal") state.mode = "experiment";
    state.pathLens = "draft";
    state.drawing = true;
    state.draftNodes = [];
    render();
    return;
  }
  if (action === "clear-draft") {
    stopPlayback();
    state.draftNodes = [];
    state.pathLens = "draft";
    state.drawing = true;
    render();
    return;
  }
  if (action === "select-object") {
    const semanticRef = target.getAttribute("data-semantic-ref") || "";
    state.selectedSemanticRef = semanticRef;
    if (state.drawing && semanticRef.startsWith("node:")) {
      const nodeKey = semanticRef.slice(5);
      if (state.draftNodes.at(-1) !== nodeKey) {
        if (state.draftNodes.length >= 4) state.draftNodes.shift();
        state.draftNodes.push(nodeKey);
      }
    }
    render();
    return;
  }
  if (action === "play-scene") {
    state.renderProfile = "theater";
    startPlayback();
    return;
  }
  if (action === "stop-scene") {
    stopPlayback();
    render();
    return;
  }
  if (action === "toggle-abu") {
    state.abuOpen = !state.abuOpen;
    render();
  }
}

function currentInput() {
  return {
    renderProfile: state.renderProfile,
    mode: state.mode,
    variantIndex: state.variantIndex,
    yearIndex: state.yearIndex,
    pathLens: state.pathLens,
    draftNodes: state.draftNodes,
    selectedSemanticRef: state.selectedSemanticRef,
  };
}

function render() {
  if (!fixture) return;
  scene = compileSceneState(fixture, currentInput());
  state.selectedSemanticRef = scene.selected_semantic_ref;
  const variant = fixture.variants[state.variantIndex];
  root.innerHTML = `
    <div class="scene-shell" data-profile="${escapeHtml(state.renderProfile)}">
      ${renderHeader()}
      ${renderCommandBar()}
      <section class="semantic-stage" aria-label="共享命局场景">
        ${renderStatusRibbon(variant)}
        ${renderPillarRail(variant)}
        ${state.hourPickerOpen ? renderHourPicker() : ""}
        <div class="profile-layout">
          <div class="profile-surface">${renderProfile()}</div>
          ${renderInspector()}
        </div>
        ${renderYearDial()}
      </section>
      ${renderAbu()}
    </div>`;
}

function renderHeader() {
  return `<header class="scene-header">
    <div class="scene-header-inner">
      <img class="brand-logo" src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi">
      <div class="scene-title">
        <p>MINGLI SCENE · C1R PROTOTYPE</p>
        <h1>理、象、时，共用同一个命局</h1>
      </div>
      <span class="boundary-mark">共享语义，不共享猜测</span>
    </div>
  </header>`;
}

function renderCommandBar() {
  return `<nav class="command-bar" aria-label="理象时视图与实验操作">
    <div class="command-inner">
      <div class="profile-switch" role="tablist" aria-label="表现维度">
        ${Object.entries(PROFILE_LABELS).map(([profile, labels]) => `
          <button type="button" role="tab" aria-selected="${state.renderProfile === profile}"
            class="profile-tab ${state.renderProfile === profile ? "active" : ""}"
            data-action="set-profile" data-profile="${profile}">
            <strong>${labels[0]}</strong><span>${labels[1]}</span>
          </button>`).join("")}
      </div>
      <div class="mode-actions">
        ${state.mode === "formal"
          ? `<button class="command primary" type="button" data-action="create-experiment">创建实验副本</button>`
          : `<button class="command" type="button" data-action="restore-formal">返回正式盘</button>`}
        <button class="command accent" type="button" data-action="play-scene">播放当前路径</button>
      </div>
    </div>
  </nav>`;
}

function renderStatusRibbon(variant) {
  const continuity = variant.formal_path_reference.continuity_status;
  const continuityLabel = { preserved: "完整保留", partial: "部分保留", broken: "不再闭合" }[continuity];
  const source = state.mode === "formal" ? "正式盘" : "实验副本";
  return `<div class="status-ribbon">
    <p><strong>${source}</strong> · ${variant.pillars[3]}时柱 · 正式路径参考${continuityLabel}</p>
    <p><code>${escapeHtml(scene.scene_state_id)}</code></p>
  </div>`;
}

function renderPillarRail(variant) {
  const cards = variant.pillars.map((pillar, index) => {
    const [stem, branch] = [...pillar];
    const stemObject = scene.visual_objects.find((item) => item.slot === `${["year", "month", "day", "hour"][index]}_stem`);
    const branchObject = scene.visual_objects.find((item) => item.slot === `${["year", "month", "day", "hour"][index]}_branch`);
    const editable = index === 3;
    const changed = index === 3 && state.variantIndex !== fixture.baseline_variant_index;
    return `<article class="pillar-card ${editable ? "editable" : "locked"} ${changed ? "changed" : ""}">
      <span>${PILLAR_LABELS[index]} ${editable ? "" : "◆"}</span>
      <button type="button" class="glyph element-${stemObject?.element || "metal"} ${isSelected(stemObject?.semantic_ref)}"
        data-action="select-object" data-semantic-ref="${stemObject?.semantic_ref || ""}">${stem}</button>
      <button type="button" class="glyph element-${branchObject?.element || "earth"} ${isSelected(branchObject?.semantic_ref)}"
        data-action="select-object" data-semantic-ref="${branchObject?.semantic_ref || ""}">${branch}</button>
      <small>${TEN_GOD_LABELS[stemObject?.ten_god] || (index === 2 ? "日主" : "")}</small>
      ${editable ? `<button class="pillar-edit" type="button" data-action="toggle-hour-picker">校勘</button>` : ""}
    </article>`;
  }).join("");
  const year = fixture.year_dial[state.yearIndex];
  return `<section class="pillar-band" aria-labelledby="pillarTitle">
    <div class="band-heading">
      <div><p>共享结构坐标</p><h2 id="pillarTitle">一次修改，三个视图同步</h2></div>
      <span>${state.mode === "formal" ? "正式世界" : "Sandbox only"}</span>
    </div>
    <div class="pillar-rail">
      ${cards}
      <div class="time-separator" aria-hidden="true"></div>
      ${renderTimeCard("大运", fixture.formal.luck_pillar, "temporal:luck", "official")}
      ${renderTimeCard("流年", year.pillar, "temporal:year", year.source_mode)}
    </div>
  </section>`;
}

function renderTimeCard(label, pillar, semanticRef, sourceMode) {
  const [stem, branch] = [...pillar];
  return `<article class="time-card ${isSelected(semanticRef)}">
    <span>${label}</span>
    <button type="button" data-action="select-object" data-semantic-ref="${semanticRef}">
      <strong>${stem}</strong><strong>${branch}</strong>
    </button>
    <small>${sourceMode === "official" ? "正式时间材料" : "假设时间信号"}</small>
  </article>`;
}

function renderHourPicker() {
  return `<section class="hour-picker" aria-label="合法时柱选择">
    <div><p>锁定年、月、日</p><h3>扫描十二个历法合法时柱</h3></div>
    <div class="hour-options">
      ${fixture.variants.map((item, index) => `
        <button type="button" class="hour-option ${index === state.variantIndex ? "active" : ""}"
          data-action="select-hour" data-index="${index}">
          <strong>${item.pillars[3]}</strong><span>${branchHourLabel(item.pillars[3][1])}</span>
          <small>${pathStatusLabel(item.formal_path_reference.continuity_status)}</small>
        </button>`).join("")}
    </div>
  </section>`;
}

function renderProfile() {
  if (state.renderProfile === "xiangfa") return renderXiangfa();
  if (state.renderProfile === "theater") return renderTheater();
  return renderLab();
}

function renderLab() {
  return `<section class="lab-profile" aria-labelledby="labTitle">
    ${renderPathHeader("理图 · 做功路径", "准确关系先行，只展开当前路径。", "labTitle")}
    ${renderPathTrack(scene.active_path, "lab")}
    <section class="draft-studio">
      <div><p>PATH DRAFT</p><h3>${state.drawing ? "依次点击节点，画一条对照路径" : "亲手比较另一条路径"}</h3></div>
      <div class="draft-actions">
        <button type="button" class="command" data-action="start-draft">自己画路</button>
        ${state.draftNodes.length ? `<button type="button" class="text-link" data-action="clear-draft">清空</button>` : ""}
      </div>
      <div class="node-palette">
        ${scene.visual_objects.filter((item) => item.object_type === "stem" || item.object_type === "branch").map((item) => `
          <button type="button" class="palette-node element-${item.element} ${state.draftNodes.includes(item.slot) ? "in-draft" : ""} ${isSelected(item.semantic_ref)}"
            data-action="select-object" data-semantic-ref="${item.semantic_ref}" title="${item.slot_label}">${item.label}</button>`).join("")}
      </div>
      ${state.draftNodes.length ? renderDraftSummary() : ""}
    </section>
  </section>`;
}

function renderPathHeader(title, subtitle, id) {
  return `<div class="profile-heading">
    <div><p>SHARED SEMANTIC PATH</p><h2 id="${id}">${title}</h2><span>${subtitle}</span></div>
    <div class="path-lenses" role="tablist" aria-label="路径来源">
      ${[["formal", "正式参考"], ["candidate", "Graph 候选"], ["draft", "我的草稿"]].map(([lens, label]) => `
        <button type="button" role="tab" aria-selected="${state.pathLens === lens}"
          class="lens-tab ${state.pathLens === lens ? "active" : ""}"
          data-action="set-path-lens" data-lens="${lens}">${label}</button>`).join("")}
    </div>
  </div>`;
}

function renderPathTrack(path, context) {
  if (!path.node_refs.length) {
    return `<div class="path-empty"><p>还没有用户路径。点击“自己画路”后依次选择节点。</p></div>`;
  }
  const pieces = [];
  path.node_refs.forEach((semanticRef, index) => {
    const object = objectByRef(scene, semanticRef);
    const activeCue = currentCue()?.semantic_refs.includes(semanticRef);
    pieces.push(`<button type="button" class="path-node element-${object?.element || "metal"} ${isSelected(semanticRef)} ${activeCue ? "cue-active" : ""}"
      data-action="select-object" data-semantic-ref="${semanticRef}">
      <strong>${object?.label || path.node_labels[index] || "?"}</strong><span>${object?.slot_label || "节点"}</span>
    </button>`);
    const segment = path.segments[index];
    if (!segment) return;
    const segmentActive = currentCue()?.semantic_refs.includes(segment.from_ref) && currentCue()?.semantic_refs.includes(segment.to_ref);
    pieces.push(`<div class="path-segment ${segment.status} ${segmentActive ? "cue-active" : ""}">
      <span>${escapeHtml(segment.label)}</span><i aria-hidden="true"></i>
    </div>`);
  });
  return `<div class="path-viewport" data-context="${context}">
    <div class="path-track">${pieces.join("")}</div>
    <div class="path-meta">
      <span class="authority ${path.epistemic_status}">${escapeHtml(path.label)}</span>
      <span>${pathOutcome(path)}</span>
    </div>
  </div>`;
}

function renderDraftSummary() {
  const draft = scene.user_path_draft;
  const missing = draft.segments.filter((item) => item.status === "missing").length;
  const reverse = draft.segments.filter((item) => item.status === "draft_reverse").length;
  return `<p class="draft-summary">用户草稿 · ${draft.node_refs.length} 个节点 · ${missing} 处缺失${reverse ? ` · ${reverse} 处方向相反` : ""}。不会写回正式盘。</p>`;
}

function renderXiangfa() {
  const bindingByRef = new Map(scene.metaphor_bindings.map((item) => [item.semantic_ref, item]));
  const path = scene.active_path;
  return `<section class="xiang-profile" aria-labelledby="xiangTitle">
    ${renderPathHeader("象法场景 · 同一条路", "象只解释结构，不增加命理结论。", "xiangTitle")}
    <div class="xiang-world">
      <div class="xiang-haze" aria-hidden="true"></div>
      <div class="xiang-copy"><span>入象</span><p>节点没有消失，只是换成可追踪的视觉隐喻。</p></div>
      <div class="xiang-route">
        ${path.node_refs.map((semanticRef, index) => {
          const object = objectByRef(scene, semanticRef);
          const binding = bindingByRef.get(semanticRef);
          const segment = path.segments[index];
          return `<div class="xiang-step">
            <button type="button" class="motif motif-${object?.element || "metal"} ${isSelected(semanticRef)}"
              data-action="select-object" data-semantic-ref="${semanticRef}">
              <i aria-hidden="true"></i><strong>${binding?.motif || "结构标记"}</strong><span>${object?.label || "?"} · ${object?.slot_label || "节点"}</span>
            </button>
            ${segment ? `<div class="xiang-link ${segment.status}"><span>${escapeHtml(segment.label)}</span></div>` : ""}
          </div>`;
        }).join("")}
      </div>
      <button class="scene-play" type="button" data-action="play-scene">从当前路径开始演时 <span>→</span></button>
    </div>
  </section>`;
}

function renderTheater() {
  const cue = currentCue();
  return `<section class="theater-profile" aria-labelledby="theaterTitle">
    ${renderPathHeader("演时 · 路径如何发生", "播放的是同一份 SceneState，不是另一套结论。", "theaterTitle")}
    <div class="theater-world">
      <div class="theater-copy">
        <p>${cue ? `第 ${state.cueIndex + 1} 步` : "准备演时"}</p>
        <blockquote>${cue ? escapeHtml(cue.label) : "阿布会沿着当前路径逐节点讲解，遇到缺口就停下。"}</blockquote>
        <div class="theater-controls">
          <button type="button" class="command accent" data-action="play-scene">${state.playing ? "重新播放" : "播放路径"}</button>
          ${state.playing ? `<button type="button" class="command" data-action="stop-scene">暂停</button>` : ""}
        </div>
      </div>
      <div class="theater-actor">
        <span class="actor-light" aria-hidden="true"></span>
        <img src="/assets/abu/v9-designer-taoist-divination/web/abu_taoist_divination_v9.webp" alt="阿布正在演示命局路径">
      </div>
      <div class="theater-path">${renderPathTrack(scene.active_path, "theater")}</div>
      <ol class="cue-rail" aria-label="场景时间线">
        ${scene.cues.map((item, index) => `<li class="${index === state.cueIndex ? "active" : ""} ${index < state.cueIndex ? "done" : ""}">
          <span>${String(index + 1).padStart(2, "0")}</span><p>${escapeHtml(item.label)}</p>
        </li>`).join("")}
      </ol>
    </div>
  </section>`;
}

function renderInspector() {
  const selected = objectByRef(scene, scene.selected_semantic_ref);
  const binding = scene.metaphor_bindings.find((item) => item.semantic_ref === scene.selected_semantic_ref);
  const continuity = scene.diff_focus.continuity_status;
  return `<aside class="scene-inspector" aria-label="当前语义对象">
    <p class="inspector-kicker">当前选择 · 三视图共享</p>
    <div class="selected-object">
      <strong>${selected?.label || "路径"}</strong>
      <span>${selected?.slot_label || scene.active_path.label}</span>
    </div>
    ${selected ? `<dl>
      <div><dt>语义身份</dt><dd><code>${escapeHtml(selected.semantic_ref)}</code></dd></div>
      <div><dt>五行 / 阴阳</dt><dd>${ELEMENT_LABELS[selected.element] || "时间"} · ${selected.polarity === "yang" ? "阳" : selected.polarity === "yin" ? "阴" : "时序"}</dd></div>
      <div><dt>十神</dt><dd>${TEN_GOD_LABELS[selected.ten_god] || "不适用"}</dd></div>
      <div><dt>认识论</dt><dd>${selected.epistemic_status}</dd></div>
    </dl>` : ""}
    <section class="metaphor-disclosure">
      <span>象法绑定</span>
      <h3>${binding?.motif || "当前对象没有象法绑定"}</h3>
      <p>${binding?.mapping_explanation || "时间信号保持为时间材料，不额外生成场景判断。"}</p>
      <small>${binding ? binding.binding_type : "not_applicable"}</small>
    </section>
    <section class="diff-disclosure">
      <span>本次变化</span>
      <h3>${pathStatusLabel(continuity)}</h3>
      <p>正式路径参考保留 ${scene.diff_focus.preserved_segments}/${scene.diff_focus.total_segments} 段；新增 ${scene.diff_focus.added_relations}，移除 ${scene.diff_focus.removed_relations}。</p>
    </section>
  </aside>`;
}

function renderYearDial() {
  const selected = fixture.year_dial[state.yearIndex];
  return `<section class="year-dial" aria-labelledby="yearDialTitle">
    <div><p>时间信号</p><h2 id="yearDialTitle">流年进入，但不虚构作用</h2><span>${selected.source_mode === "official" ? "当前为正式时间材料" : "当前为假设时间信号"}</span></div>
    <div class="year-options">
      ${fixture.year_dial.map((item, index) => `<button type="button" class="year-option ${index === state.yearIndex ? "active" : ""}"
        data-action="select-year" data-index="${index}"><strong>${item.year}</strong><span>${item.pillar}</span><small>${item.source_mode === "official" ? "正式" : "假设"}</small></button>`).join("")}
    </div>
  </section>`;
}

function renderAbu() {
  const text = abuText();
  return `<div class="abu-guide ${state.abuOpen ? "open" : "collapsed"}">
    <button type="button" class="abu-toggle" data-action="toggle-abu" aria-label="${state.abuOpen ? "收起阿布" : "打开阿布"}" aria-expanded="${state.abuOpen}">
      <img src="/assets/abu/v4-video-derived/web/abu_idle_blink_v4.webp" alt="阿布">
    </button>
    ${state.abuOpen ? `<p aria-live="polite">${escapeHtml(text)}</p>` : ""}
  </div>`;
}

function startPlayback() {
  stopPlayback();
  state.renderProfile = "theater";
  scene = compileSceneState(fixture, currentInput());
  if (!scene.cues.length) { render(); return; }
  state.playing = true;
  state.cueIndex = 0;
  state.selectedSemanticRef = scene.cues[0].semantic_refs[0] || state.selectedSemanticRef;
  render();
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  playTimer = window.setInterval(() => {
    scene = compileSceneState(fixture, currentInput());
    if (state.cueIndex >= scene.cues.length - 1) {
      stopPlayback();
      render();
      return;
    }
    state.cueIndex += 1;
    const cue = scene.cues[state.cueIndex];
    state.selectedSemanticRef = cue.semantic_refs.at(-1) || state.selectedSemanticRef;
    render();
  }, reduced ? 180 : 1050);
}

function stopPlayback() {
  if (playTimer) window.clearInterval(playTimer);
  playTimer = null;
  state.playing = false;
  state.cueIndex = -1;
}

function currentCue() {
  return state.cueIndex >= 0 ? scene?.cues?.[state.cueIndex] || null : null;
}

function pathOutcome(path) {
  if (path.epistemic_status === "candidate") return "候选路径，不自动提升";
  if (path.epistemic_status === "user_draft") return "用户草稿，不写回正式盘";
  return `${pathStatusLabel(path.continuity_status)} · ${path.segments.filter((item) => item.status !== "missing").length}/${path.segments.length} 段`;
}

function abuText() {
  if (state.renderProfile === "xiangfa") return "你现在看到的是同一批命理对象的象法表达。点击水路、灯火或金石，右侧仍会定位到同一个语义节点。";
  if (state.renderProfile === "theater") return currentCue()?.label || "点播放后，我会沿当前路径推进；遇到缺失关系时会停下，不替系统补路。";
  if (state.drawing) return "依次点选结构节点。我会告诉你连接存在、方向相反，还是中间缺了一段。";
  if (scene.diff_focus.continuity_status === "partial") return "这次时柱变化后，正式路径参考只剩一段。切到“入象”或“演时”，断点仍会保持在同一个位置。";
  return "先改一个合法时柱，再在理、象、时之间切换。你的选择和路径不会丢。";
}

function isSelected(semanticRef) {
  return semanticRef && semanticRef === scene?.selected_semantic_ref ? "selected" : "";
}

function pathStatusLabel(status) {
  return { preserved: "完整保留", partial: "部分保留", broken: "不再闭合", candidate: "结构候选", open: "尚未闭合", complete: "草稿闭合", empty: "等待绘制" }[status] || status;
}

function branchHourLabel(branch) {
  return `${branch || "?"}时`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[char]));
}
