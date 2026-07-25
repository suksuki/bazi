import {ELEMENT_META, loadScene, scenePillars, stageFor} from "../s0-v11-shared/scene-runtime.js";

const TOTAL = 44.5;
const SCENES = [
  {id: "opening", start: 0, end: 5.5, stage: "original", image: "/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp"},
  {id: "canvas", start: 5.5, end: 10.5, stage: "original", image: "/assets/abu/v4-video-derived/web/abu_head_tilt_v4.webp"},
  {id: "path", start: 10.5, end: 18, stage: "original", image: "/assets/abu/v4-video-derived/web/abu_head_tilt_v4.webp"},
  {id: "tension", start: 18, end: 24, stage: "original", image: "/assets/abu/v4-video-derived/web/abu_caution_ears_v4.webp"},
  {id: "luck", start: 24, end: 31.5, stage: "luck", image: "/assets/abu/v4-video-derived/web/abu_caution_ears_v4.webp"},
  {id: "year", start: 31.5, end: 38.5, stage: "year", image: "/assets/abu/v4-video-derived/web/abu_head_tilt_v4.webp"},
  {id: "morph", start: 38.5, end: 41.4, stage: "year", image: "/assets/abu/v4-video-derived/web/abu_head_tilt_v4.webp"},
  {id: "finale", start: 41.4, end: TOTAL, stage: "year", image: "/assets/abu/v4-video-derived/web/abu_idle_blink_v4.webp"},
];

const theater = document.querySelector("#theater");
const audio = document.querySelector("#audio");
const playButton = document.querySelector("#playButton");
const muteButton = document.querySelector("#muteButton");
const progress = document.querySelector("#progress");
const timeLabel = document.querySelector("#timeLabel");
const subtitle = document.querySelector("#subtitle span");
const pillars = document.querySelector("#pillars");
const canvasHeadline = document.querySelector("#canvasHeadline");
const canvasStageLabel = document.querySelector("#canvasStageLabel");
const abuImage = document.querySelector("#abuImage");
let payload;
let currentTime = 0;
let animationFrame = 0;

function renderPillars(source) {
  pillars.innerHTML = scenePillars(source).map((slot, index) => {
    const [stem, branch] = [...slot.pillar];
    const temporalClass = slot.temporal ? `temporal ${index === 4 ? "luck" : "year"}` : "natal";
    return `<article class="pillar ${temporalClass}" data-slot-ref="${slot.slot_ref}">
      <label>${slot.label}</label>
      <span class="char stem" data-element="${ELEMENT_META[stem].element}" data-ref="node-${index < 4 ? "stem" : index === 4 ? "luck" : "year"}-${stem}">${stem}</span>
      <span class="char branch" data-element="${ELEMENT_META[branch].element}" data-ref="node-${index < 4 ? "branch" : index === 4 ? "luck" : "year"}-${branch}">${branch}</span>
    </article>`;
  }).join("");
}

function sceneAt(time) {
  return SCENES.find((scene) => time >= scene.start && time < scene.end) || SCENES.at(-1);
}

function narrationAt(time) {
  return payload.narration.segments.find((segment) => time >= segment.start && time < segment.end) || payload.narration.segments.at(-1);
}

function formatTime(seconds) {
  return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
}

function applyTime(time, {syncAudio = false} = {}) {
  currentTime = Math.max(0, Math.min(TOTAL, Number(time) || 0));
  const scene = sceneAt(currentTime);
  const narration = narrationAt(currentTime);
  const stage = stageFor(payload.source, scene.stage);
  theater.dataset.scene = scene.id;
  theater.dataset.stage = scene.stage;
  subtitle.textContent = narration.subtitle;
  canvasStageLabel.textContent = stage.label;
  canvasHeadline.textContent = stage.shortLabel;
  abuImage.src = scene.image;
  document.querySelectorAll("[data-stage-button]").forEach((button) => {
    button.setAttribute("aria-current", String(button.dataset.stageButton === scene.stage));
  });
  progress.value = String(Math.round(currentTime * 10));
  timeLabel.textContent = `${formatTime(currentTime)} / 0:44`;
  if (syncAudio && Math.abs(audio.currentTime - currentTime) > .08) audio.currentTime = currentTime;
}

function tick() {
  if (!audio.paused) {
    applyTime(audio.currentTime);
    if (audio.currentTime >= TOTAL) {
      audio.pause();
      playButton.textContent = "▶";
    }
  }
  animationFrame = requestAnimationFrame(tick);
}

function seekToStage(stageId) {
  const time = stageId === "original" ? 10.6 : stageId === "luck" ? 24.2 : 31.7;
  applyTime(time, {syncAudio: true});
}

async function init() {
  try {
    payload = await loadScene();
    renderPillars(payload.source);
    const params = new URLSearchParams(location.search);
    if (params.get("capture") === "1") theater.classList.add("capture");
    const initial = params.has("time") ? Number(params.get("time")) : 0;
    applyTime(initial, {syncAudio: true});
    if (params.get("paused") !== "1" && params.get("autoplay") === "1") {
      await audio.play();
      playButton.textContent = "Ⅱ";
    }
  } catch (error) {
    subtitle.textContent = "场景资料暂时无法载入。";
    console.error(error);
  }
  animationFrame = requestAnimationFrame(tick);
}

playButton.addEventListener("click", async () => {
  if (audio.paused) {
    if (audio.currentTime >= TOTAL - .1) audio.currentTime = 0;
    await audio.play();
    playButton.textContent = "Ⅱ";
  } else {
    audio.pause();
    playButton.textContent = "▶";
  }
});

muteButton.addEventListener("click", () => {
  audio.muted = !audio.muted;
  muteButton.textContent = audio.muted ? "静音" : "声音";
});

progress.addEventListener("input", () => applyTime(Number(progress.value) / 10, {syncAudio: true}));
document.querySelectorAll("[data-stage-button]").forEach((button) => button.addEventListener("click", () => seekToStage(button.dataset.stageButton)));
audio.addEventListener("ended", () => { playButton.textContent = "▶"; applyTime(TOTAL); });
window.setTheaterTime = (time) => applyTime(time, {syncAudio: true});
window.getTheaterState = () => ({time: currentTime, scene: theater.dataset.scene, stage: theater.dataset.stage});
window.addEventListener("beforeunload", () => cancelAnimationFrame(animationFrame));

init();
