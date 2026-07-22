import {ELEMENT_META, loadScene, scenePillars, stageFor} from "../../shared/s0-v12-shared/scene-runtime.js";

const TOTAL = 44.5;
const ACTIONS = {
  enter: {
    id: "abu_enter_and_notice_v1",
    video: "/assets/abu/v12-actor-pass/enter-and-notice/web/abu_enter_and_notice_v1.webm",
    image: "/assets/abu/v12-actor-pass/enter-and-notice/web/abu_enter_and_notice_v1.webp",
    poster: "/assets/abu/v12-actor-pass/enter-and-notice/posters/abu_enter_and_notice_v1.png",
    duration: 4,
    displayScale: 1.42,
  },
  turnAndPoint: {
    id: "abu_turn_and_point_v1",
    video: "/assets/abu/v12-actor-pass/turn-and-point/web/abu_turn_and_point_v1.webm",
    image: "/assets/abu/v12-actor-pass/turn-and-point/web/abu_turn_and_point_v1.webp",
    poster: "/assets/abu/v12-actor-pass/turn-and-point/posters/abu_turn_and_point_v1.png",
    duration: 1.933,
    displayScale: 1.08,
    playbackScale: .82,
  },
  tension: {
    id: "abu_notice_tension_v1",
    video: "/assets/abu/v12-actor-pass/notice-tension/web/abu_notice_tension_v1.webm",
    image: "/assets/abu/v12-actor-pass/notice-tension/web/abu_notice_tension_v1.webp",
    poster: "/assets/abu/v12-actor-pass/notice-tension/posters/abu_notice_tension_v1.png",
    duration: 2.067,
  },
  faceChange: {
    id: "abu_face_change_transition_v1",
    video: "/assets/abu/v12-actor-pass/face-change-transition/web/abu_face_change_transition_v1.webm",
    image: "/assets/abu/v12-actor-pass/face-change-transition/web/abu_face_change_transition_v1.webp",
    poster: "/assets/abu/v12-actor-pass/face-change-transition/posters/abu_face_change_transition_v1.png",
    duration: 9.067,
    displayScale: 1.25,
    fitToScene: true,
    playbackWindow: [1.2, 7.4],
  },
  ninja: {
    id: "abu_ninja_disappear_throw_v1",
    video: "/assets/abu/v12-actor-pass/ninja-disappear-throw/web/abu_ninja_disappear_throw_v1.webm",
    image: "/assets/abu/v12-actor-pass/ninja-disappear-throw/web/abu_ninja_disappear_throw_v1.webp",
    poster: "/assets/abu/v12-actor-pass/ninja-disappear-throw/posters/abu_ninja_disappear_throw_v1.png",
    duration: 10,
    displayScale: 1.16,
  },
  baseball: {
    id: "abu_baseball_swing_v1",
    video: "/assets/abu/v12-actor-pass/baseball-swing/web/abu_baseball_swing_v1.webm",
    image: "/assets/abu/v12-actor-pass/baseball-swing/web/abu_baseball_swing_v1.webp",
    poster: "/assets/abu/v12-actor-pass/baseball-swing/posters/abu_baseball_swing_v1.png",
    duration: 9.933,
    displayScale: 1.08,
  },
  pachinko: {
    id: "abu_pachinko_jackpot_v1",
    video: "/assets/abu/v12-actor-pass/pachinko-jackpot/web/abu_pachinko_jackpot_v1.webm",
    image: "/assets/abu/v12-actor-pass/pachinko-jackpot/web/abu_pachinko_jackpot_v1.webp",
    poster: "/assets/abu/v12-actor-pass/pachinko-jackpot/posters/abu_pachinko_jackpot_v1.png",
    duration: 10,
    displayScale: 1.04,
  },
  breakdance: {
    id: "abu_breakdance_v9",
    image: "/assets/abu/v9-designer-breakdance/web/abu_breakdance_v9.webp",
    duration: 10,
    displayScale: 1.12,
  },
  sleep: {
    id: "abu_sleep_breathe_v6",
    image: "/assets/abu/v6-designer-sleep/web/abu_sleep_breathe_v6.webp",
    duration: 3.867,
    displayScale: 1.12,
  },
  idle: {
    id: "abu_quiet_sit_reaction_v1",
    video: "/assets/abu/v12-actor-pass/quiet-sit-reaction/web/abu_quiet_sit_reaction_v1.webm",
    image: "/assets/abu/v12-actor-pass/quiet-sit-reaction/web/abu_quiet_sit_reaction_v1.webp",
    poster: "/assets/abu/v12-actor-pass/quiet-sit-reaction/posters/abu_quiet_sit_reaction_v1.png",
    duration: 10,
    displayScale: 1.45,
  },
  caution: {id: "abu_caution_ears_v4", image: "/assets/abu/v4-video-derived/web/abu_caution_ears_v4.webp"},
  confirm: {id: "abu_happy_tail_v4", image: "/assets/abu/v4-video-derived/web/abu_happy_tail_v4.webp"},
};
const FINALE_ACTIONS = ["breakdance", "faceChange", "ninja", "baseball", "pachinko"];
const FINALE_ACTION_WEIGHTS = Object.freeze({
  breakdance: 2,
  faceChange: 1,
  ninja: 2,
  baseball: 3,
  pachinko: 1,
});
const FINALE_SLEEP_AFTER_MS = 28000;
const FORCE_ALPHA_IMAGE_FALLBACK = new URLSearchParams(location.search).get("actorMedia") === "webp";
const USE_ALPHA_IMAGE_FALLBACK = FORCE_ALPHA_IMAGE_FALLBACK
  || /iPad|iPhone|iPod/.test(navigator.userAgent)
  || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
const SCENES = [
  {id: "opening", start: 0, end: 5.5, stage: "original", actor: "enter", facing: "right", position: {wide: 12, compact: 18}, travel: {duration: 1.65, from: {wide: 6, compact: 13}}},
  {id: "canvas", start: 5.5, end: 10.5, stage: "original", actor: "idle", facing: "left", position: {wide: 71, compact: 4}, travel: {duration: 1.65}},
  {id: "path", start: 10.5, end: 18, stage: "original", actor: "turnAndPoint", facing: "right", position: {wide: 1, compact: 0}, travel: {duration: 2.85, moveRatio: .66, settleFacing: "front", settleAt: .72}},
  {id: "tension", start: 18, end: 24, stage: "original", actor: "caution", facing: "left", position: {wide: 67, compact: 0}, travel: {duration: 1.65}},
  {id: "luck", start: 24, end: 31.5, stage: "luck", actor: "tension", facing: "front", position: {wide: 67, compact: 0}},
  {id: "year", start: 31.5, end: 38.5, stage: "year", actor: "confirm", facing: "right", position: {wide: 1, compact: 0}, travel: {duration: 1.65}},
  {id: "morph", start: 38.5, end: 43.5, stage: "year", actor: "faceChange", facing: "front", position: {wide: 1, compact: 0}},
  {id: "finale", start: 43.5, end: TOTAL, stage: "year", actor: "idle", facing: "right", position: {wide: 1, compact: 0}},
];

const theater = document.querySelector("#theater");
const audio = document.querySelector("#audio");
const playButton = document.querySelector("#playButton");
const playGlyph = document.querySelector("#playGlyph");
const muteButton = document.querySelector("#muteButton");
const soundLabel = document.querySelector("#soundLabel");
const startSoundButton = document.querySelector("#startSoundButton");
const startMutedButton = document.querySelector("#startMutedButton");
const progress = document.querySelector("#progress");
const timeLabel = document.querySelector("#timeLabel");
const subtitle = document.querySelector("#subtitleText");
const pillars = document.querySelector("#pillars");
const mobileNatalPillars = document.querySelector("#mobileNatalPillars");
const mobileTemporalPillars = document.querySelector("#mobileTemporalPillars");
const mobileTimeLabel = document.querySelector("#mobileTimeLabel");
const canvasHeadline = document.querySelector("#canvasHeadline");
const canvasStageLabel = document.querySelector("#canvasStageLabel");
const abuActor = document.querySelector("#abuActor");
const abuVideo = document.querySelector("#abuVideo");
const abuImage = document.querySelector("#abuImage");
const xiangfaHandoff = document.querySelector("#xiangfaHandoff");
const xiangfaFrame = document.querySelector("#xiangfaFrame");
let payload;
let currentTime = 0;
let animationFrame = 0;
let currentActorId = "";
let pendingActorTime = 0;
let pendingActorPlaybackRate = 1;
let xiangfaReady = false;
let previousSceneId = "";
let finaleModeActive = false;
let finaleSleeping = false;
let finaleActionKey = "";
let previousFinaleActionKey = "";
let finaleActionTimer = 0;
let finaleSleepTimer = 0;
let finaleActionToken = 0;
let finalePointerActivityAt = 0;
let fallbackPlaying = false;
let fallbackOriginTime = 0;
let fallbackStartedAt = 0;
let soundEnabled = true;
let audioAvailable = true;

function actionUsesVideo(action) {
  return Boolean(action.video) && !USE_ALPHA_IMAGE_FALLBACK;
}

function renderPillars(source) {
  const slots = scenePillars(source);
  const rendered = slots.map((slot, index) => {
    const [stem, branch] = [...slot.pillar];
    const temporalClass = slot.temporal ? `temporal ${index === 4 ? "luck" : "year"}` : "natal";
    return `<article class="pillar ${temporalClass}" data-slot-ref="${slot.slot_ref}">
      <label>${slot.label}</label>
      <span class="char stem" data-element="${ELEMENT_META[stem].element}" data-ref="node-${index < 4 ? "stem" : index === 4 ? "luck" : "year"}-${stem}">${stem}</span>
      <span class="char branch" data-element="${ELEMENT_META[branch].element}" data-ref="node-${index < 4 ? "branch" : index === 4 ? "luck" : "year"}-${branch}">${branch}</span>
    </article>`;
  });
  pillars.innerHTML = `<div class="pillar-group natal-group" aria-label="原局四柱">${rendered.slice(0, 4).join("")}</div>
    <div class="pillar-group temporal-group" aria-label="时间进入">${rendered.slice(4).join("")}</div>`;

  mobileNatalPillars.innerHTML = slots.slice(0, 4).map((slot, index) => renderMobilePillar(slot, index)).join("");
  mobileTemporalPillars.innerHTML = `${renderMobilePillar(slots[4], 4)}
    <span class="mobile-time-arrow" aria-hidden="true">›</span>
    ${renderMobilePillar(slots[5], 5)}`;
}

function renderMobilePillar(slot, index) {
  const [stem, branch] = [...slot.pillar];
  const slotClass = index < 4 ? "natal" : index === 4 ? "luck" : "year";
  const shortLabel = slot.label.replace("柱", "");
  return `<article class="mobile-pillar ${slotClass}" data-slot-ref="${slot.slot_ref}">
    <label>${shortLabel}</label>
    <span class="mobile-char stem" data-element="${ELEMENT_META[stem].element}" data-ref="mobile-${slot.slot_ref}-stem">${stem}</span>
    <i aria-hidden="true"></i>
    <span class="mobile-char branch" data-element="${ELEMENT_META[branch].element}" data-ref="mobile-${slot.slot_ref}-branch">${branch}</span>
  </article>`;
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

function timelinePlaying() {
  return !audio.paused || fallbackPlaying;
}

function timelineTime() {
  if (!audio.paused) return audio.currentTime;
  if (!fallbackPlaying) return currentTime;
  return Math.min(TOTAL, fallbackOriginTime + ((window.performance.now() - fallbackStartedAt) / 1000));
}

function resetFallbackClock(time = currentTime) {
  fallbackOriginTime = Math.max(0, Math.min(TOTAL, Number(time) || 0));
  fallbackStartedAt = window.performance.now();
}

function updateTransport() {
  const playing = timelinePlaying();
  playGlyph.textContent = playing ? "Ⅱ" : "▶";
  playButton.setAttribute("aria-label", playing ? "暂停" : "播放");
  playButton.setAttribute("title", playing ? "暂停" : "播放");
  soundLabel.textContent = soundEnabled ? "声音开" : "声音关";
  muteButton.setAttribute("aria-label", soundEnabled ? "关闭声音" : "开启声音");
  muteButton.setAttribute("aria-pressed", String(soundEnabled));
  muteButton.setAttribute("title", soundEnabled ? "关闭声音" : "开启声音");
  theater.dataset.sound = soundEnabled ? "on" : "off";
  theater.dataset.playing = String(playing);
}

function markStarted() {
  theater.dataset.started = "true";
}

async function playTimeline({sound = soundEnabled} = {}) {
  markStarted();
  if (currentTime >= TOTAL - .1) applyTime(0, {syncAudio: true});
  soundEnabled = Boolean(sound);
  audio.muted = !soundEnabled;
  audio.currentTime = currentTime;
  try {
    await audio.play();
    fallbackPlaying = false;
    audioAvailable = true;
  } catch (error) {
    fallbackPlaying = true;
    resetFallbackClock(currentTime);
    audioAvailable = false;
    soundEnabled = false;
    audio.muted = true;
    console.warn("s0_audio_unavailable_using_visual_clock", error);
  }
  updateTransport();
  applyTime(currentTime);
}

function pauseTimeline() {
  const pausedAt = timelineTime();
  fallbackPlaying = false;
  if (!audio.paused) audio.pause();
  applyTime(pausedAt, {syncAudio: true});
  updateTransport();
}

function seekTimeline(time) {
  const wasFallbackPlaying = fallbackPlaying;
  applyTime(time, {syncAudio: true});
  if (wasFallbackPlaying) resetFallbackClock(currentTime);
}

async function setSoundEnabled(enabled) {
  soundEnabled = Boolean(enabled);
  audio.muted = !soundEnabled;
  if (soundEnabled && fallbackPlaying) {
    audio.currentTime = currentTime;
    try {
      await audio.play();
      fallbackPlaying = false;
      audioAvailable = true;
    } catch (error) {
      soundEnabled = false;
      audio.muted = true;
      audioAvailable = false;
      console.warn("s0_audio_retry_failed", error);
    }
  }
  updateTransport();
}

function actorLayoutProfile() {
  return window.matchMedia("(max-width: 720px), (orientation: portrait)").matches ? "compact" : "wide";
}

function scenePosition(scene, profile) {
  return scene.position[profile];
}

function previousScenePosition(scene, profile) {
  const sceneIndex = SCENES.indexOf(scene);
  if (scene.travel?.from) return scene.travel.from[profile];
  return sceneIndex > 0 ? scenePosition(SCENES[sceneIndex - 1], profile) : scenePosition(scene, profile);
}

function clearFinaleActionTimer() {
  if (!finaleActionTimer) return;
  window.clearTimeout(finaleActionTimer);
  finaleActionTimer = 0;
}

function clearFinaleSleepTimer() {
  if (!finaleSleepTimer) return;
  window.clearTimeout(finaleSleepTimer);
  finaleSleepTimer = 0;
}

function finaleActorPosition() {
  return actorLayoutProfile() === "compact" ? 0 : 1;
}

function showFinaleActor(actionKey) {
  if (!finaleModeActive) return;
  const action = ACTIONS[actionKey];
  finaleActionKey = actionKey;
  finaleActionToken += 1;
  currentActorId = action.id;
  abuActor.dataset.actionId = action.id;
  abuActor.dataset.finaleAction = actionKey;
  abuActor.dataset.facing = "front";
  abuActor.dataset.locomotion = "false";
  abuActor.style.setProperty("--actor-scale", String(action.displayScale || 1));
  abuActor.style.left = `${finaleActorPosition()}%`;
  abuActor.style.removeProperty("right");

  if (actionUsesVideo(action)) {
    abuImage.hidden = true;
    abuVideo.hidden = false;
    abuVideo.loop = false;
    abuVideo.src = action.video;
    abuVideo.poster = action.poster;
    abuVideo.load();
    if (abuVideo.readyState >= 1) {
      abuVideo.currentTime = 0;
      abuVideo.playbackRate = 1;
      void abuVideo.play().catch(() => {});
    }
    return;
  }

  abuVideo.pause();
  abuVideo.hidden = true;
  abuImage.hidden = false;
  abuActor.dataset.mediaMode = USE_ALPHA_IMAGE_FALLBACK ? "animated-webp" : "image";
  const replayToken = actionKey === "idle" ? "" : `?play=${Date.now()}`;
  abuImage.src = `${action.image}${replayToken}`;
}

function pickRandomFinaleAction() {
  const available = FINALE_ACTIONS.filter((key) => key !== previousFinaleActionKey);
  const weighted = available.flatMap((key) => Array(FINALE_ACTION_WEIGHTS[key] || 1).fill(key));
  return weighted[Math.floor(Math.random() * weighted.length)] || FINALE_ACTIONS[0];
}

function scheduleRandomFinaleAction(delay = 4200) {
  clearFinaleActionTimer();
  if (!finaleModeActive || finaleSleeping) return;
  const token = finaleActionToken;
  finaleActionTimer = window.setTimeout(() => {
    if (!finaleModeActive || finaleSleeping || token !== finaleActionToken) return;
    const actionKey = pickRandomFinaleAction();
    previousFinaleActionKey = actionKey;
    showFinaleActor(actionKey);
    const actionToken = finaleActionToken;
    finaleActionTimer = window.setTimeout(() => {
      if (!finaleModeActive || finaleSleeping || actionToken !== finaleActionToken) return;
      showFinaleActor("idle");
      scheduleRandomFinaleAction(3600 + Math.floor(Math.random() * 3200));
    }, Math.ceil(ACTIONS[actionKey].duration * 1000) + 120);
  }, delay);
}

function armFinaleSleepTimer() {
  clearFinaleSleepTimer();
  if (!finaleModeActive) return;
  const reviewDelay = Number(new URLSearchParams(location.search).get("finaleSleepAfterMs"));
  const sleepAfterMs = Number.isFinite(reviewDelay) && reviewDelay > 0
    ? Math.max(1200, Math.min(reviewDelay, FINALE_SLEEP_AFTER_MS))
    : FINALE_SLEEP_AFTER_MS;
  finaleSleepTimer = window.setTimeout(() => {
    if (!finaleModeActive) return;
    finaleSleeping = true;
    clearFinaleActionTimer();
    showFinaleActor("sleep");
  }, sleepAfterMs);
}

function startFinaleMode() {
  if (theater.classList.contains("capture") || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (finaleModeActive) return;
  finaleModeActive = true;
  finaleSleeping = false;
  showFinaleActor("idle");
  const reviewAction = new URLSearchParams(location.search).get("finaleAction");
  if (FINALE_ACTIONS.includes(reviewAction)) showFinaleActor(reviewAction);
  else scheduleRandomFinaleAction(700);
  armFinaleSleepTimer();
}

function stopFinaleMode() {
  if (!finaleModeActive) return;
  finaleModeActive = false;
  finaleSleeping = false;
  finaleActionKey = "";
  finaleActionToken += 1;
  clearFinaleActionTimer();
  clearFinaleSleepTimer();
  abuVideo.pause();
  delete abuActor.dataset.finaleAction;
}

function registerFinaleActivity() {
  if (!finaleModeActive) return;
  armFinaleSleepTimer();
  if (!finaleSleeping) return;
  finaleSleeping = false;
  showFinaleActor("idle");
  scheduleRandomFinaleAction(450);
}

function registerFinalePointerActivity() {
  const now = Date.now();
  if (!finaleSleeping && now - finalePointerActivityAt < 800) return;
  finalePointerActivityAt = now;
  registerFinaleActivity();
}

function applyActor(scene) {
  if (scene.id === "finale" && finaleModeActive) {
    abuActor.style.left = `${finaleActorPosition()}%`;
    return;
  }
  const localTime = Math.max(0, currentTime - scene.start);
  const sceneDuration = scene.end - scene.start;
  const profile = actorLayoutProfile();
  const targetPosition = scenePosition(scene, profile);
  const travelDuration = scene.travel?.duration || 0;
  const isTravelling = travelDuration > 0 && localTime < travelDuration;
  const travelProgress = isTravelling ? Math.min(1, localTime / travelDuration) : 1;
  const movementProgress = isTravelling
    ? Math.min(1, travelProgress / (scene.travel?.moveRatio || 1))
    : 1;
  const easedTravel = 1 - ((1 - movementProgress) ** 2);
  const fromPosition = previousScenePosition(scene, profile);
  const actorPosition = fromPosition + (targetPosition - fromPosition) * easedTravel;
  const effectiveActor = isTravelling ? "enter" : scene.actor;
  const action = ACTIONS[effectiveActor];
  const actionLocalTime = isTravelling || scene.actor === "enter" ? localTime : Math.max(0, localTime - travelDuration);
  const actionDuration = isTravelling ? travelDuration : Math.max(.001, sceneDuration - travelDuration);
  const sceneProgress = Math.min(actionDuration, actionLocalTime) / actionDuration;
  const actorTime = action.playbackWindow
    ? action.playbackWindow[0] + sceneProgress * (action.playbackWindow[1] - action.playbackWindow[0])
    : action.fitToScene
      ? sceneProgress * action.duration
      : actionLocalTime * (action.playbackScale || 1);
  abuActor.dataset.actionId = action.id;
  const travelFacing = targetPosition >= fromPosition ? "right" : "left";
  const hasSettledFacing = isTravelling
    && scene.travel?.settleFacing
    && travelProgress >= (scene.travel.settleAt || 1);
  abuActor.dataset.facing = isTravelling
    ? (hasSettledFacing ? scene.travel.settleFacing : travelFacing)
    : scene.facing;
  abuActor.dataset.locomotion = String(isTravelling);
  abuActor.style.setProperty("--actor-scale", String(action.displayScale || 1));
  abuActor.style.left = `${actorPosition}%`;
  abuActor.style.removeProperty("right");

  if (actionUsesVideo(action)) {
    abuVideo.hidden = false;
    abuImage.hidden = true;
    abuActor.dataset.mediaMode = "webm-alpha";
    const actorChanged = currentActorId !== action.id;
    if (actorChanged) {
      currentActorId = action.id;
      abuVideo.src = action.video;
      abuVideo.poster = action.poster;
      abuVideo.load();
    }
    pendingActorTime = Math.min(action.duration - .067, actorTime);
    pendingActorPlaybackRate = action.playbackWindow
      ? (action.playbackWindow[1] - action.playbackWindow[0]) / actionDuration
      : action.fitToScene
        ? action.duration / actionDuration
        : (action.playbackScale || 1);
    const livePlayback = timelinePlaying() && !theater.classList.contains("capture");
    if (abuVideo.readyState >= 1) {
      abuVideo.playbackRate = pendingActorPlaybackRate;
      const driftLimit = livePlayback ? .24 : .025;
      if (actorChanged || Math.abs(abuVideo.currentTime - pendingActorTime) > driftLimit) {
        abuVideo.currentTime = pendingActorTime;
      }
      if (livePlayback && pendingActorTime < action.duration - .1) {
        void abuVideo.play().catch(() => {});
      } else {
        abuVideo.pause();
      }
    }
    return;
  }

  abuVideo.pause();
  abuVideo.hidden = true;
  abuImage.hidden = false;
  abuActor.dataset.mediaMode = USE_ALPHA_IMAGE_FALLBACK ? "animated-webp" : "image";
  if (currentActorId !== action.id) {
    currentActorId = action.id;
    abuImage.src = action.image;
  }
}

async function waitForActorFrame() {
  if (abuVideo.hidden) return;
  if (abuVideo.readyState < 1) {
    await new Promise((resolve) => {
      const timeout = window.setTimeout(resolve, 500);
      abuVideo.addEventListener("loadedmetadata", () => {
        window.clearTimeout(timeout);
        resolve();
      }, {once: true});
    });
  }
  if (abuVideo.readyState >= 1 && Math.abs(abuVideo.currentTime - pendingActorTime) > .025) {
    abuVideo.currentTime = pendingActorTime;
  }
  if (!abuVideo.seeking) return;
  await new Promise((resolve) => {
    const timeout = window.setTimeout(resolve, 220);
    abuVideo.addEventListener("seeked", () => {
      window.clearTimeout(timeout);
      resolve();
    }, {once: true});
  });
}

function syncXiangfaFrame() {
  if (!xiangfaReady) return;
  xiangfaFrame.contentWindow?.postMessage({
    type: "deepbazi:xiangfa-state",
    stage: "year",
    mode: "xiangfa",
  }, location.origin);
}

async function waitForXiangfaFrame(scene) {
  if (scene.id !== "finale" || xiangfaReady) return;
  await new Promise((resolve) => {
    const timeout = window.setTimeout(resolve, 1200);
    xiangfaFrame.addEventListener("load", () => {
      window.clearTimeout(timeout);
      resolve();
    }, {once: true});
  });
}

function applyTime(time, {syncAudio = false} = {}) {
  currentTime = Math.max(0, Math.min(TOTAL, Number(time) || 0));
  const scene = sceneAt(currentTime);
  const narration = narrationAt(currentTime);
  const stage = stageFor(payload.source, scene.stage);
  theater.dataset.scene = scene.id;
  theater.dataset.stage = scene.stage;
  const xiangfaInteractive = scene.id === "finale";
  if (xiangfaInteractive && previousSceneId !== "finale") startFinaleMode();
  if (!xiangfaInteractive && previousSceneId === "finale") stopFinaleMode();
  xiangfaHandoff.setAttribute("aria-hidden", String(!xiangfaInteractive));
  xiangfaHandoff.inert = !xiangfaInteractive;
  xiangfaFrame.tabIndex = xiangfaInteractive ? 0 : -1;
  if (xiangfaInteractive && previousSceneId !== "finale") {
    theater.classList.remove("xiangfa-engaged");
    syncXiangfaFrame();
  }
  if (!xiangfaInteractive) theater.classList.remove("xiangfa-engaged");
  previousSceneId = scene.id;
  subtitle.textContent = narration.narration;
  subtitle.parentElement.dataset.segmentId = narration.segment_id;
  canvasStageLabel.textContent = stage.label;
  canvasHeadline.textContent = stage.shortLabel;
  mobileTimeLabel.textContent = scene.stage === "original"
    ? "尚未加入"
    : scene.stage === "luck"
      ? "庚寅大运"
      : "庚寅大运 · 丙午流年";
  applyActor(scene);
  document.querySelectorAll("[data-stage-button]").forEach((button) => {
    button.setAttribute("aria-current", String(button.dataset.stageButton === scene.stage));
  });
  progress.value = String(Math.round(currentTime * 10));
  timeLabel.textContent = `${formatTime(currentTime)} / 0:44`;
  if (syncAudio && Math.abs(audio.currentTime - currentTime) > .08) audio.currentTime = currentTime;
  if (syncAudio && fallbackPlaying) resetFallbackClock(currentTime);
}

function tick() {
  if (timelinePlaying()) {
    const nextTime = timelineTime();
    applyTime(nextTime);
    if (nextTime >= TOTAL) {
      fallbackPlaying = false;
      if (!audio.paused) audio.pause();
      applyTime(TOTAL, {syncAudio: true});
      updateTransport();
    }
  }
  animationFrame = requestAnimationFrame(tick);
}

function seekToStage(stageId) {
  const time = stageId === "original" ? 10.6 : stageId === "luck" ? 24.2 : 31.7;
  seekTimeline(time);
}

async function init() {
  try {
    payload = await loadScene();
    renderPillars(payload.source);
    const params = new URLSearchParams(location.search);
    const format = params.get("format");
    if (format === "portrait" || format === "landscape") theater.dataset.format = format;
    if (params.get("capture") === "1") {
      theater.classList.add("capture");
      markStarted();
    }
    const initial = params.has("time") ? Number(params.get("time")) : 0;
    applyTime(initial, {syncAudio: true});
    if (params.get("paused") !== "1" && params.get("autoplay") === "1") {
      await playTimeline({sound: params.get("muted") !== "1"});
    }
    updateTransport();
  } catch (error) {
    subtitle.textContent = "场景资料暂时无法载入。";
    console.error(error);
  }
  animationFrame = requestAnimationFrame(tick);
}

playButton.addEventListener("click", async () => {
  if (timelinePlaying()) pauseTimeline();
  else await playTimeline({sound: soundEnabled});
});

startSoundButton.addEventListener("click", () => playTimeline({sound: true}));
startMutedButton.addEventListener("click", () => playTimeline({sound: false}));
muteButton.addEventListener("click", () => setSoundEnabled(!soundEnabled));

progress.addEventListener("input", () => seekTimeline(Number(progress.value) / 10));
document.querySelectorAll("[data-stage-button]").forEach((button) => button.addEventListener("click", () => seekToStage(button.dataset.stageButton)));
audio.addEventListener("ended", () => {
  fallbackPlaying = false;
  applyTime(TOTAL, {syncAudio: true});
  updateTransport();
});
abuVideo.addEventListener("loadedmetadata", () => {
  if (finaleModeActive && finaleActionKey && actionUsesVideo(ACTIONS[finaleActionKey])) {
    abuVideo.currentTime = 0;
    abuVideo.playbackRate = 1;
    void abuVideo.play().catch(() => {});
    return;
  }
  abuVideo.currentTime = Math.min(Math.max(0, pendingActorTime), Math.max(0, abuVideo.duration - .067));
  abuVideo.playbackRate = pendingActorPlaybackRate;
  if (timelinePlaying() && !theater.classList.contains("capture") && pendingActorTime < abuVideo.duration - .1) {
    void abuVideo.play().catch(() => {});
  } else {
    abuVideo.pause();
  }
});
audio.addEventListener("play", () => {
  fallbackPlaying = false;
  audioAvailable = true;
  applyTime(audio.currentTime);
  updateTransport();
});
audio.addEventListener("pause", () => {
  if (fallbackPlaying) return;
  abuVideo.pause();
  applyTime(audio.currentTime);
  updateTransport();
});
audio.addEventListener("error", () => {
  audioAvailable = false;
  if (!timelinePlaying()) updateTransport();
});
xiangfaFrame.addEventListener("load", () => {
  xiangfaReady = true;
  xiangfaHandoff.classList.add("is-ready");
  if (theater.dataset.scene === "finale") syncXiangfaFrame();
});
window.addEventListener("message", (event) => {
  if (event.origin !== location.origin || event.source !== xiangfaFrame.contentWindow) return;
  if (event.data?.type === "deepbazi:xiangfa-ready") {
    xiangfaReady = true;
    xiangfaHandoff.classList.add("is-ready");
    syncXiangfaFrame();
  }
  if (event.data?.type === "deepbazi:xiangfa-engaged") {
    theater.classList.add("xiangfa-engaged");
    registerFinaleActivity();
  }
  if (event.data?.type === "deepbazi:xiangfa-activity") registerFinalePointerActivity();
});
window.setTheaterTime = async (time) => {
  applyTime(time, {syncAudio: true});
  await Promise.all([waitForActorFrame(), waitForXiangfaFrame(sceneAt(currentTime))]);
};
window.getTheaterState = () => ({
  time: currentTime,
  scene: theater.dataset.scene,
  stage: theater.dataset.stage,
  finaleAction: finaleActionKey,
  finaleSleeping,
  playing: timelinePlaying(),
  soundEnabled,
  audioAvailable,
  playbackClock: fallbackPlaying ? "visual_fallback" : "audio",
});
["pointerdown", "touchstart", "keydown"].forEach((eventName) => {
  window.addEventListener(eventName, registerFinaleActivity, {passive: true});
});
["pointermove", "mousemove", "pointerover", "wheel"].forEach((eventName) => {
  window.addEventListener(eventName, registerFinalePointerActivity, {passive: true});
});
xiangfaFrame.addEventListener("pointerenter", registerFinalePointerActivity, {passive: true});
window.addEventListener("resize", () => {
  if (finaleModeActive) abuActor.style.left = `${finaleActorPosition()}%`;
});
window.addEventListener("beforeunload", () => {
  cancelAnimationFrame(animationFrame);
  stopFinaleMode();
});

init();
