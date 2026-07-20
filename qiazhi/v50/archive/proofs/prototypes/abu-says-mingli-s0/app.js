import {
  ELEMENT_META,
  approvedStage,
  loadApprovedScene,
  scenePillars,
} from "../s0-shared/scene-runtime.js";

const TOTAL_SECONDS = 47;
const CUES = [
  { start: 0, end: 5.2, stage: "original", number: "01 · 序", title: "命理不是一份宿命宣判。", lead: "它是理解人生结构的一种入口。", transport: "第一幕 · 命理与选择", actor: "welcome" },
  { start: 5.2, end: 11.8, stage: "original", number: "02 · 底稿", title: "人生剧本有底稿，但结局没有写死。", lead: "看见角色、关系、节奏，也保留人的选择。", transport: "第二幕 · 人生剧本的底稿", actor: "idle" },
  { start: 11.8, end: 18.2, stage: "original", number: "03 · 看见", title: "同一张图，看见原局、运与年。", lead: "六柱进入同一个语义空间。", transport: "第三幕 · 六柱进入 OneCanvas", actor: "divination" },
  { start: 18.2, end: 25.6, stage: "original", number: "04 · 路径", title: "乙木生丁火，丁火作用于金结构。", lead: "正式主路径逐段出现。", transport: "第四幕 · 正式主路径", actor: "observe" },
  { start: 25.6, end: 32.5, stage: "luck", number: "05 · 庚子", title: "源端受制，路径支持减弱。", lead: "路径仍然存在，没有被演成中断。", transport: "第五幕 · 庚子源端受制", actor: "caution" },
  { start: 32.5, end: 39.6, stage: "year", number: "06 · 丙午", title: "火侧得助，路径重新获得支持。", lead: "增强只相对庚子阶段，不超过原局基线。", transport: "第六幕 · 丙午火侧得助", actor: "divination" },
  { start: 39.6, end: 47.01, stage: "year", number: "07 · 同一命局", title: "理成为骨架，象成为同一结构的意境。", lead: "阿布陪你读懂底稿，下一章仍由你书写。", transport: "第七幕 · 看见命局，也看见自己", actor: "welcome" },
];

const ACTOR_ASSETS = {
  welcome: "/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp",
  idle: "/assets/abu/v4-video-derived/web/abu_idle_blink_v4.webp",
  divination: "/assets/abu/v9-designer-taoist-divination/web/abu_taoist_divination_v9.webp",
  observe: "/assets/abu/v4-video-derived/web/abu_head_tilt_v4.webp",
  caution: "/assets/abu/v4-video-derived/web/abu_caution_ears_v4.webp",
};

const dom = {
  theater: document.querySelector("#theater"),
  stage: document.querySelector("#stage"),
  sceneNumber: document.querySelector("#sceneNumber"),
  sceneTitle: document.querySelector("#sceneTitle"),
  sceneLead: document.querySelector("#sceneLead"),
  canvasTitle: document.querySelector("#canvasTitle"),
  stageChip: document.querySelector("#stageChip"),
  pillars: document.querySelector("#pillars"),
  pathSvg: document.querySelector("#pathSvg"),
  approvedPathLine: document.querySelector("#approvedPathLine"),
  temporalEffectLine: document.querySelector("#temporalEffectLine"),
  metalStructure: document.querySelector("#metalStructure"),
  pathCaption: document.querySelector("#pathCaption"),
  subtitle: document.querySelector("#subtitle"),
  abuImage: document.querySelector("#abuImage"),
  abuRole: document.querySelector("#abuRole"),
  audio: document.querySelector("#narrationAudio"),
  playButton: document.querySelector("#playButton"),
  muteButton: document.querySelector("#muteButton"),
  restartButton: document.querySelector("#restartButton"),
  progress: document.querySelector("#progress"),
  timeLabel: document.querySelector("#timeLabel"),
  transportTitle: document.querySelector("#transportTitle"),
  sceneRail: document.querySelector("#sceneRail"),
};

let packageData = null;
let currentCueIndex = -1;
let fallbackTimer = null;
let fallbackStartedAt = 0;
let fallbackStartTime = 0;

boot();

async function boot() {
  try {
    packageData = await loadApprovedScene();
    renderPillars();
    renderRail();
    bindControls();
    const params = new URLSearchParams(location.search);
    const frameParam = params.get("frame");
    const timeParam = params.get("time");
    const requestedFrame = frameParam === null ? Number.NaN : Number(frameParam);
    const requestedTime = timeParam === null ? Number.NaN : Number(timeParam);
    const exportMode = params.get("export") === "1" || Number.isInteger(requestedFrame);
    document.body.classList.toggle("is-export", exportMode);
    let initialTime = 0;
    if (Number.isInteger(requestedFrame) && requestedFrame >= 1 && requestedFrame <= CUES.length) {
      const cue = CUES[requestedFrame - 1];
      initialTime = cue.start + (cue.end - cue.start) * 0.56;
    } else if (Number.isFinite(requestedTime)) {
      initialTime = clamp(requestedTime, 0, TOTAL_SECONDS);
    }
    setTime(initialTime, false);
    if (params.get("autoplay") === "1" && !exportMode) await play();
  } catch (error) {
    dom.sceneTitle.textContent = "小剧场没有载入批准场景";
    dom.sceneLead.textContent = String(error);
    dom.playButton.disabled = true;
  }
}

function renderPillars() {
  dom.pillars.innerHTML = scenePillars(packageData.source).map((item, index) => {
    const [stem, branch] = [...item.pillar];
    const stemMeta = ELEMENT_META[stem];
    const branchMeta = ELEMENT_META[branch];
    const stemRef = semanticRefFor(item.slotRef, "stem");
    const branchRef = semanticRefFor(item.slotRef, "branch");
    const temporalClass = item.temporal ? " temporal" : "";
    return `
      <article class="pillar${temporalClass}" data-slot-ref="${item.slotRef}" style="--pillar-index:${index}">
        <span class="pillar-label">${item.label}</span>
        <button class="pillar-node element-${stemMeta.element} polarity-${stemMeta.polarity}" data-semantic-ref="${stemRef}" type="button">
          <span class="glyph">${stem}</span><span class="nature">${polarityLabel(stemMeta)}${elementLabel(stemMeta)}</span>
        </button>
        <span class="pillar-divider"></span>
        <button class="pillar-node element-${branchMeta.element} polarity-${branchMeta.polarity}" data-semantic-ref="${branchRef}" type="button">
          <span class="glyph">${branch}</span><span class="nature">${polarityLabel(branchMeta)}${elementLabel(branchMeta)}</span>
        </button>
      </article>`;
  }).join("");
}

function semanticRefFor(slotRef, type) {
  const map = {
    "slot-natal-year:stem": "node-stem-year-ding",
    "slot-natal-day:stem": "node-stem-day-yi",
    "slot-luck-gengzi:stem": "node-luck-geng",
    "slot-luck-gengzi:branch": "node-luck-zi",
    "slot-year-bingwu:stem": "node-year-bing",
    "slot-year-bingwu:branch": "node-year-wu",
  };
  return map[`${slotRef}:${type}`] || "";
}

function renderRail() {
  dom.sceneRail.innerHTML = CUES.map((cue, index) => `<li data-scene-index="${index}" title="${cue.transport}"></li>`).join("");
  dom.sceneRail.addEventListener("click", (event) => {
    const item = event.target.closest("[data-scene-index]");
    if (!item) return;
    const cue = CUES[Number(item.dataset.sceneIndex)];
    setTime(cue.start + 0.05, true);
  });
}

function bindControls() {
  dom.playButton.addEventListener("click", () => dom.audio.paused ? play() : pause());
  dom.restartButton.addEventListener("click", async () => { setTime(0, true); await play(); });
  dom.muteButton.addEventListener("click", () => {
    dom.audio.muted = !dom.audio.muted;
    dom.muteButton.textContent = dom.audio.muted ? "静" : "音";
  });
  dom.progress.addEventListener("input", () => setTime(Number(dom.progress.value) / 10, true));
  dom.audio.addEventListener("timeupdate", () => updateAt(dom.audio.currentTime));
  dom.audio.addEventListener("play", () => { dom.playButton.textContent = "Ⅱ"; stopFallback(); });
  dom.audio.addEventListener("pause", () => { dom.playButton.textContent = "▶"; });
  dom.audio.addEventListener("ended", () => { dom.playButton.textContent = "▶"; updateAt(TOTAL_SECONDS); });
  addEventListener("resize", () => requestAnimationFrame(drawOneCanvasPaths));
}

async function play() {
  if (dom.audio.currentTime >= TOTAL_SECONDS - 0.1) setTime(0, true);
  try {
    await dom.audio.play();
  } catch {
    startFallback();
  }
}

function pause() {
  dom.audio.pause();
  stopFallback();
  dom.playButton.textContent = "▶";
}

function setTime(seconds, syncAudio) {
  const next = clamp(seconds, 0, TOTAL_SECONDS);
  if (syncAudio && Number.isFinite(dom.audio.duration)) dom.audio.currentTime = next;
  updateAt(next);
}

function updateAt(seconds) {
  const safeTime = clamp(seconds, 0, TOTAL_SECONDS);
  const index = Math.max(0, CUES.findIndex((cue) => safeTime >= cue.start && safeTime < cue.end));
  const cue = CUES[index < 0 ? CUES.length - 1 : index];
  const cueIndex = index < 0 ? CUES.length - 1 : index;
  const progress = clamp((safeTime - cue.start) / (cue.end - cue.start), 0, 1);
  dom.theater.dataset.scene = String(cueIndex + 1);
  dom.theater.dataset.stage = cue.stage;
  dom.theater.style.setProperty("--scene-progress", progress.toFixed(3));
  dom.theater.style.setProperty("--reveal-right", `${((1 - progress) * 100).toFixed(2)}%`);
  dom.sceneNumber.textContent = cue.number;
  dom.sceneTitle.textContent = cue.title;
  dom.sceneLead.textContent = cue.lead;
  dom.transportTitle.textContent = cue.transport;
  dom.progress.value = String(Math.round(safeTime * 10));
  dom.timeLabel.textContent = `${formatTime(safeTime)} / 0:47`;
  const narrationSegment = packageData?.narration?.segments?.[cueIndex];
  if (narrationSegment) dom.subtitle.textContent = narrationSegment.subtitle;
  const stage = approvedStage(packageData.source, cue.stage);
  dom.stageChip.textContent = stage.label;
  dom.canvasTitle.textContent = cue.stage === "original" ? "原局四柱、大运与流年" : `${stage.label}进入同一命局`;
  dom.pathCaption.textContent = cue.stage === "original" ? "正式主路径：乙木 → 丁火 → 金结构" : stage.shortLabel;
  dom.abuImage.src = ACTOR_ASSETS[cue.actor];
  dom.abuRole.textContent = cueIndex >= 4 ? "在解释当前变化" : "你的命理解释伙伴";
  [...dom.sceneRail.children].forEach((item, itemIndex) => item.classList.toggle("active", itemIndex <= cueIndex));
  if (currentCueIndex !== cueIndex) {
    currentCueIndex = cueIndex;
    requestAnimationFrame(drawOneCanvasPaths);
  } else if (cueIndex >= 3 && cueIndex <= 5) {
    requestAnimationFrame(drawOneCanvasPaths);
  }
}

function drawOneCanvasPaths() {
  const canvas = document.querySelector("#oneCanvas");
  if (!canvas || Number(dom.theater.dataset.scene) < 4 || Number(dom.theater.dataset.scene) > 6) return;
  const yi = canvas.querySelector('[data-semantic-ref="node-stem-day-yi"]');
  const ding = canvas.querySelector('[data-semantic-ref="node-stem-year-ding"]');
  const metal = dom.metalStructure;
  if (!yi || !ding || !metal) return;
  const base = canvas.getBoundingClientRect();
  const p1 = centerOf(yi, base);
  const p2 = centerOf(ding, base);
  const p3 = centerOf(metal, base);
  dom.pathSvg.setAttribute("viewBox", `0 0 ${base.width} ${base.height}`);
  dom.approvedPathLine.setAttribute("d", curvedPath([p1, p2, p3]));

  const stage = dom.theater.dataset.stage;
  const temporalRef = stage === "luck" ? "node-luck-geng" : "node-year-bing";
  const targetRef = stage === "luck" ? "node-stem-day-yi" : "node-stem-year-ding";
  const temporal = canvas.querySelector(`[data-semantic-ref="${temporalRef}"]`);
  const target = canvas.querySelector(`[data-semantic-ref="${targetRef}"]`);
  if (stage === "original" || !temporal || !target) {
    dom.temporalEffectLine.setAttribute("d", "");
    return;
  }
  dom.temporalEffectLine.setAttribute("d", curvedPath([centerOf(temporal, base), centerOf(target, base)]));
}

function centerOf(element, base) {
  const rect = element.getBoundingClientRect();
  return { x: rect.left - base.left + rect.width / 2, y: rect.top - base.top + rect.height / 2 };
}

function curvedPath(points) {
  if (points.length === 2) {
    const [a, b] = points;
    const midY = Math.min(a.y, b.y) - 38;
    return `M${a.x},${a.y} C${a.x},${midY} ${b.x},${midY} ${b.x},${b.y}`;
  }
  const [a, b, c] = points;
  return `M${a.x},${a.y} C${a.x - 20},${a.y - 70} ${b.x + 30},${b.y - 65} ${b.x},${b.y} S${c.x - 90},${c.y - 35} ${c.x},${c.y}`;
}

function startFallback() {
  stopFallback();
  fallbackStartTime = dom.audio.currentTime || 0;
  fallbackStartedAt = performance.now();
  dom.playButton.textContent = "Ⅱ";
  fallbackTimer = requestAnimationFrame(tickFallback);
}

function tickFallback(now) {
  const elapsed = (now - fallbackStartedAt) / 1000;
  const next = Math.min(TOTAL_SECONDS, fallbackStartTime + elapsed);
  updateAt(next);
  if (next < TOTAL_SECONDS) fallbackTimer = requestAnimationFrame(tickFallback);
  else dom.playButton.textContent = "▶";
}

function stopFallback() {
  if (fallbackTimer) cancelAnimationFrame(fallbackTimer);
  fallbackTimer = null;
}

function elementLabel(meta) {
  return { wood: "木", fire: "火", earth: "土", metal: "金", water: "水" }[meta.element];
}

function polarityLabel(meta) { return meta.polarity === "yang" ? "阳" : "阴"; }
function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }
function formatTime(seconds) { return `0:${String(Math.floor(seconds)).padStart(2, "0")}`; }
