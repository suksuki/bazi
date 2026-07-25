import {loadScene, stageFor} from "../../shared/s0-v12-shared/scene-runtime.js";

const root = document.querySelector("#xiangfa");
const stageRange = document.querySelector("#stageRange");
const stageEyebrow = document.querySelector("#stageEyebrow");
const stageTitle = document.querySelector("#stageTitle");
const inspector = document.querySelector("#inspector");
const inspectorStatus = document.querySelector("#inspectorStatus");
const inspectorTitle = document.querySelector("#inspectorTitle");
const inspectorBody = document.querySelector("#inspectorBody");
const inspectorRef = document.querySelector("#inspectorRef");
const interactionHint = document.querySelector("#interactionHint");
const pageParams = new URLSearchParams(location.search);
const embeddedInTheater = pageParams.get("embed") === "theater";
let source;
let lastActivityNoticeAt = 0;

if (embeddedInTheater) root.dataset.embed = "theater";

const STAGES = ["original", "luck", "year"];
const HOTSPOT_COPY = {
  "node-stem-day-jia": {title: "甲木 · 生发主体", body: "这里对应日干甲木，也是观察主线的来源端。象法中的青木不是装饰，而是同一语义对象的视觉映射。"},
  "node-stem-month-ding": {title: "丁火 · 转化中心", body: "甲木生丁火，丁火承接来源端的作用，并继续指向庚金结构。"},
  "node-stem-year-geng": {title: "庚金 · 结构边界", body: "右侧不是成功终点，而是需要被作用和处理的结构边界。关闭的山门保留了压力感。"},
  "path-observed-jia-ding-geng": {title: "结构观察主线", body: "甲木生丁火，丁火进一步作用于庚金。这是一条由确定性五行关系组成的观察主线，不等于唯一格局或人生定论。"},
  "current-time-effect": {title: "当前时间作用", body: "时间层只显示来源合同批准的作用。大运中的压力与根气并存；丙午阶段只增加丙火对丁火的支持。"},
};

function setMode(mode) {
  root.dataset.mode = mode;
  document.querySelectorAll("[data-mode-button]").forEach((button) => button.setAttribute("aria-current", String(button.dataset.modeButton === mode)));
}

function setStage(stageId) {
  const index = STAGES.indexOf(stageId);
  if (!source || index < 0) return;
  const stage = stageFor(source, stageId);
  root.dataset.stage = stageId;
  stageRange.value = String(index);
  stageEyebrow.textContent = stage.label;
  stageTitle.textContent = stage.shortLabel.replace(`${stage.label}：`, "");
  document.querySelectorAll("[data-stage-button]").forEach((button) => button.setAttribute("aria-current", String(button.dataset.stageButton === stageId)));
  inspectorStatus.textContent = `${stageId === "original" ? "正式结构" : "正式时间投影"} · ${stage.label}`;
  if (!inspector.classList.contains("is-closed")) {
    inspectorTitle.textContent = stage.shortLabel;
    inspectorBody.textContent = stage.explanation;
    inspectorRef.textContent = stage.relationRefs.join(" · ");
  }
}

function inspect(ref, {notify = true, reveal = true} = {}) {
  const copy = HOTSPOT_COPY[ref];
  if (!copy) return;
  root.dataset.selectedRef = ref;
  document.querySelectorAll("[data-semantic-ref]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.semanticRef === ref)));
  if (reveal) {
    inspector.classList.remove("is-closed");
    inspectorTitle.textContent = copy.title;
    inspectorBody.textContent = copy.body;
    inspectorRef.textContent = ref;
  }
  interactionHint.classList.add("is-dismissed");
  if (notify) notifyTheater("hotspot", ref);
}

function notifyTheater(interaction, value) {
  if (!embeddedInTheater) return;
  root.dataset.lastParentNotice = `${interaction}:${value}`;
  window.parent.postMessage({type: "deepbazi:xiangfa-engaged", interaction, value}, location.origin);
}

function notifyTheaterActivity() {
  if (!embeddedInTheater) return;
  const now = Date.now();
  if (now - lastActivityNoticeAt < 700) return;
  lastActivityNoticeAt = now;
  window.parent.postMessage({type: "deepbazi:xiangfa-activity"}, location.origin);
}

async function init() {
  try {
    const payload = await loadScene();
    source = payload.source;
    setMode("xiangfa");
    const stage = STAGES.includes(pageParams.get("stage")) ? pageParams.get("stage") : "original";
    const mode = ["xiangfa", "skeleton", "overlay"].includes(pageParams.get("mode")) ? pageParams.get("mode") : "xiangfa";
    setMode(mode);
    setStage(stage);
    if (embeddedInTheater) inspector.classList.add("is-closed");
    if (embeddedInTheater) window.parent.postMessage({type: "deepbazi:xiangfa-ready"}, location.origin);
  } catch (error) {
    inspectorStatus.textContent = "场景不可用";
    inspectorTitle.textContent = "Scene Source 未能载入";
    inspectorBody.textContent = "请通过 HTTP 服务打开本页。";
    console.error(error);
  }
}

document.querySelectorAll("[data-mode-button]").forEach((button) => button.addEventListener("click", () => {
  setMode(button.dataset.modeButton);
  notifyTheater("mode", button.dataset.modeButton);
}));
document.querySelectorAll("[data-stage-button]").forEach((button) => button.addEventListener("click", () => {
  setStage(button.dataset.stageButton);
  notifyTheater("stage", button.dataset.stageButton);
}));
document.querySelectorAll("[data-semantic-ref]").forEach((button) => button.addEventListener("click", () => inspect(button.dataset.semanticRef)));
document.querySelector(".close-inspector").addEventListener("click", () => inspector.classList.add("is-closed"));
stageRange.addEventListener("input", () => {
  const stage = STAGES[Number(stageRange.value)];
  setStage(stage);
  notifyTheater("stage", stage);
});
["pointermove", "mousemove", "pointerover", "wheel", "touchmove", "pointerdown", "touchstart", "keydown"].forEach((eventName) => {
  window.addEventListener(eventName, notifyTheaterActivity, {passive: true});
});
window.addEventListener("focus", notifyTheaterActivity);
window.addEventListener("message", (event) => {
  if (!embeddedInTheater || event.origin !== location.origin || event.source !== window.parent) return;
  if (event.data?.type !== "deepbazi:xiangfa-state") return;
  const {mode, stage, selectedRef} = event.data;
  if (["xiangfa", "skeleton", "overlay"].includes(mode)) setMode(mode);
  if (STAGES.includes(stage)) setStage(stage);
  if (HOTSPOT_COPY[selectedRef]) inspect(selectedRef, {notify: false, reveal: false});
});
window.setXiangfaState = ({mode = root.dataset.mode, stage = root.dataset.stage} = {}) => { setMode(mode); setStage(stage); };
window.getXiangfaState = () => ({mode: root.dataset.mode, stage: root.dataset.stage});

init();
