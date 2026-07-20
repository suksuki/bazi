const API = {
  agent: "/api/v50/agent",
  narration: "/api/v50/narration",
  voiceValidation: "/api/v50/narration/validation",
  product: "/api/v50/product",
};

const VOICE_STUDY_ENABLED = new URLSearchParams(window.location.search).get("voice_study") === "1";

const ABU_MOTION_ROOT = "/assets/abu/v4-video-derived";
const ABU_MOTION_REGISTRY = window.DeepBaziAbuMotionRegistry || {
  motions: {
    idle_blink: {
      animation: `${ABU_MOTION_ROOT}/web/abu_idle_blink_v4.webp?v=motion-fallback`,
      poster: `${ABU_MOTION_ROOT}/posters/abu_idle_blink_v4.png?v=motion-fallback`,
      durationMs: 2133,
      displayScale: 1,
      stageProfile: "standard",
      playback: "loop",
    },
  },
  stateMapping: {},
  ambientMoments: [],
};
const ABU_MOTIONS = ABU_MOTION_REGISTRY.motions;
const ABU_STATE_MOTION = ABU_MOTION_REGISTRY.stateMapping;
const ABU_AMBIENT_MOMENTS = ABU_MOTION_REGISTRY.ambientMoments;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const OPENING_SCENE_SESSION_KEY = "deepbazi.opening_scene_v10.seen";
const OPENING_SCENE_BACKGROUND = "/assets/abu/v10-opening-scene/transition/abu_opening_background_v10.webp";

const STEM_META = {
  "甲": { element: "wood", polarity: "yang", nature: "阳木" },
  "乙": { element: "wood", polarity: "yin", nature: "阴木" },
  "丙": { element: "fire", polarity: "yang", nature: "阳火" },
  "丁": { element: "fire", polarity: "yin", nature: "阴火" },
  "戊": { element: "earth", polarity: "yang", nature: "阳土" },
  "己": { element: "earth", polarity: "yin", nature: "阴土" },
  "庚": { element: "metal", polarity: "yang", nature: "阳金" },
  "辛": { element: "metal", polarity: "yin", nature: "阴金" },
  "壬": { element: "water", polarity: "yang", nature: "阳水" },
  "癸": { element: "water", polarity: "yin", nature: "阴水" },
};
const BRANCH_META = {
  "子": { element: "water", polarity: "yang", nature: "阳水", hidden: ["癸"] },
  "丑": { element: "earth", polarity: "yin", nature: "阴土", hidden: ["己", "癸", "辛"] },
  "寅": { element: "wood", polarity: "yang", nature: "阳木", hidden: ["甲", "丙", "戊"] },
  "卯": { element: "wood", polarity: "yin", nature: "阴木", hidden: ["乙"] },
  "辰": { element: "earth", polarity: "yang", nature: "阳土", hidden: ["戊", "乙", "癸"] },
  "巳": { element: "fire", polarity: "yin", nature: "阴火", hidden: ["丙", "戊", "庚"] },
  "午": { element: "fire", polarity: "yang", nature: "阳火", hidden: ["丁", "己"] },
  "未": { element: "earth", polarity: "yin", nature: "阴土", hidden: ["己", "丁", "乙"] },
  "申": { element: "metal", polarity: "yang", nature: "阳金", hidden: ["庚", "壬", "戊"] },
  "酉": { element: "metal", polarity: "yin", nature: "阴金", hidden: ["辛"] },
  "戌": { element: "earth", polarity: "yang", nature: "阳土", hidden: ["戊", "辛", "丁"] },
  "亥": { element: "water", polarity: "yin", nature: "阴水", hidden: ["壬", "甲"] },
};

const state = {
  account: null,
  authMode: "login",
  birthDraft: readStoredJson("deepbazi.birth_draft"),
  profiles: [],
  activeProfile: null,
  profileFormMode: "intake",
  editingProfileId: "",
  caseId: localStorage.getItem("deepbazi.case_id") || "",
  jobId: localStorage.getItem("deepbazi.cognitive_job_id") || "",
  jobSequence: Number(localStorage.getItem("deepbazi.cognitive_job_sequence") || 0),
  progressive: {},
  thinkingPreviewGeneration: 0,
  thinkingPreviewLines: [],
  thinkingPreviewIndex: -1,
  thinkingPreviewTimer: null,
  primaryTypewriterGeneration: 0,
  pendingPrimaryTypewriter: false,
  journeyExpandedSteps: {},
  lastStartPayload: null,
  reading: null,
  narrationManifest: null,
  narrationManifestCaseId: "",
  narrationAssets: {},
  narrationAssetPromises: {},
  narrationAudio: null,
  narrationGeneration: 0,
  narrationIndex: -1,
  narrationStatus: "idle",
  narrationCueTimers: [],
  voiceValidationSession: null,
  voiceValidationStartedAt: 0,
  voiceValidationRequestStartedAt: 0,
  voiceValidationSegmentPlays: {},
  workspaceState: null,
  readOnlyCase: false,
  readOnlyReason: "",
  cognitionBlocked: false,
  activeMode: "guest",
  activeArtifact: localStorage.getItem("deepbazi.active_artifact") || "overview",
  activeDeliberationStage: "",
  pendingComposerIntent: "",
  busy: false,
  mobileCanvas: false,
  abuSurface: localStorage.getItem("deepbazi.abu_surface") === "collapsed" ? "collapsed" : "open",
  abuSurfaceReady: false,
  abuPeekTimer: null,
  abuPeekPinned: false,
  abuIdleTimer: null,
  abuPlayTimer: null,
  abuLastActivityAt: Date.now(),
  abuLastPlayAt: 0,
  abuLastAmbientState: "",
};

const ABU_SLEEP_DELAY_MS = 120000;
const ABU_PLAY_COOLDOWN_MS = 14000;
const ABU_PLAY_DELAY_MIN_MS = 9000;
const ABU_PLAY_DELAY_MAX_MS = 18000;

const el = (id) => document.getElementById(id);
const messageList = el("messageList");
const quickActions = el("quickActions");
const messageInput = el("messageInput");
const appShell = el("appShell");

document.addEventListener("DOMContentLoaded", async () => {
  syncAbuMotionAssets();
  reducedMotion.addEventListener?.("change", syncAbuMotionAssets);
  refreshIcons();
  bindEvents();
  setAbuState("welcome", "准备听你说");
  initializeAbuSurface();
  initializeOpeningScene();
  await restoreAccount();
  if (state.account) await refreshProfiles({ selectDefault: true });
  let restored = false;
  if (state.jobId) {
    state.jobSequence = 0;
    await watchCognitiveJob(state.jobId);
    restored = Boolean(state.reading);
  }
  else if (state.caseId) restored = await restoreCase(state.caseId, true);
  renderInitialAbuContext(restored);
});

function initializeOpeningScene() {
  const scene = el("openingScene");
  const video = el("openingSceneVideo");
  const skip = el("openingSceneSkip");
  const forceReplay = new URLSearchParams(window.location.search).get("opening") === "1";
  const alreadySeen = sessionStorage.getItem(OPENING_SCENE_SESSION_KEY) === "1";
  el("welcomeScene").style.backgroundImage = `url('${OPENING_SCENE_BACKGROUND}')`;

  if (!scene || !video || (!forceReplay && alreadySeen)) {
    scene?.setAttribute("hidden", "");
    el("openingAbuFlight")?.setAttribute("hidden", "");
    document.body.classList.remove("opening-pending");
    return;
  }

  let finishing = false;
  const finish = (fast = false) => {
    if (finishing) return;
    finishing = true;
    sessionStorage.setItem(OPENING_SCENE_SESSION_KEY, "1");
    completeOpeningScene({ fast }).catch(() => removeOpeningSceneImmediately());
  };
  skip.addEventListener("click", () => finish(true), { once: true });
  video.addEventListener("ended", () => finish(false), { once: true });
  video.addEventListener("error", () => finish(true), { once: true });
  window.setTimeout(() => finish(true), 15000);

  if (reducedMotion.matches) {
    window.setTimeout(() => finish(true), 320);
    return;
  }
  const playback = video.play();
  playback?.catch(() => finish(true));
}

async function completeOpeningScene({ fast = false } = {}) {
  const scene = el("openingScene");
  const video = el("openingSceneVideo");
  const flight = el("openingAbuFlight");
  if (!scene || !flight) return removeOpeningSceneImmediately();

  video?.pause();
  scene.classList.add("is-holding");
  setAbuState("welcome", "欢迎来到 DeepBazi");
  setAbuSurface("peek", { persist: false, message: "你好，我是阿布。我们从你的出生信息开始。" });
  await nextAnimationFrame();

  const source = openingCharacterRect();
  const target = openingDestinationRect();
  Object.assign(flight.style, rectStyles(source));
  flight.hidden = false;
  await nextAnimationFrame();
  scene.classList.add("is-revealing");

  const duration = reducedMotion.matches ? 1 : (fast ? 620 : 1450);
  const animation = flight.animate(
    [
      { ...rectStyles(source), opacity: 1, filter: "drop-shadow(0 22px 28px rgba(24, 48, 40, .16))" },
      { offset: .72, opacity: 1 },
      { ...rectStyles(target), opacity: 0, filter: "drop-shadow(0 8px 12px rgba(24, 48, 40, .10))" },
    ],
    { duration, easing: "cubic-bezier(.22,.78,.2,1)", fill: "forwards" },
  );
  await animation.finished.catch(() => {});
  scene.hidden = true;
  flight.hidden = true;
  document.body.classList.remove("opening-pending");
  setAbuSurface("peek", { persist: false, message: "你好，我是阿布。我们从你的出生信息开始。" });
  el("abuStage").focus({ preventScroll: true });
}

function openingCharacterRect() {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  if (viewportWidth / viewportHeight < .8) {
    const renderedWidth = viewportWidth * 1.75;
    const scale = renderedWidth / 1280;
    const renderedHeight = 720 * scale;
    const offsetX = viewportWidth * .5 - renderedWidth * .52;
    const offsetY = viewportHeight * .5 - renderedHeight * .5;
    return {
      left: offsetX + 540 * scale,
      top: offsetY + 218 * scale,
      width: 276 * scale,
      height: 450 * scale,
    };
  }
  const scale = Math.max(viewportWidth / 1280, viewportHeight / 720);
  const renderedWidth = 1280 * scale;
  const renderedHeight = 720 * scale;
  const offsetX = (viewportWidth - renderedWidth) * .5;
  const offsetY = (viewportHeight - renderedHeight) / 2;
  return {
    left: offsetX + 540 * scale,
    top: offsetY + 218 * scale,
    width: 276 * scale,
    height: 450 * scale,
  };
}

function openingDestinationRect() {
  const stage = el("abuStage")?.getBoundingClientRect();
  if (!stage || !stage.width) {
    const height = Math.min(94, window.innerWidth * .22);
    return { left: 22, top: window.innerHeight - height - 22, width: height * .66, height };
  }
  const height = stage.height * .84;
  const width = height * .66;
  return {
    left: stage.left + (stage.width - width) / 2,
    top: stage.top + (stage.height - height) / 2,
    width,
    height,
  };
}

function rectStyles(rect) {
  return {
    left: `${rect.left}px`,
    top: `${rect.top}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
  };
}

function nextAnimationFrame() {
  return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
}

function removeOpeningSceneImmediately() {
  el("openingScene")?.setAttribute("hidden", "");
  el("openingAbuFlight")?.setAttribute("hidden", "");
  document.body.classList.remove("opening-pending");
}

function bindEvents() {
  el("composer").addEventListener("submit", sendMessage);
  messageInput.addEventListener("input", autoSizeComposer);
  messageInput.addEventListener("focus", () => {
    if (!state.busy) setAbuState("listening", state.reading ? "在听你的问题" : "在听出生信息");
  });
  messageInput.addEventListener("blur", () => {
    if (!state.busy && !messageInput.value.trim()) setAbuState("idle", state.reading ? "在听你说" : "准备听你说");
  });
  el("structuredInputButton").addEventListener("click", openBirthDialog);
  el("accountButton").addEventListener("click", () => state.account ? openCasebook() : el("authDialog").showModal());
  el("casebookButton").addEventListener("click", openCasebook);
  el("closeCasebook").addEventListener("click", () => el("casebookDialog").close());
  el("brandButton").addEventListener("click", () => {
    showConversation();
    if (!state.busy) setAbuState("welcome", state.reading ? "又见面了" : "准备听你说");
  });
  el("abuStage").addEventListener("click", () => {
    if (state.abuSurface !== "open") setAbuSurface("open");
  });
  el("abuPanelMinimize").addEventListener("click", () => setAbuSurface("collapsed"));
  el("abuPeekOpen").addEventListener("click", () => setAbuSurface("open"));
  el("abuPanelScrim").addEventListener("click", () => setAbuSurface("collapsed"));
  el("mobileViewToggle").addEventListener("click", toggleMobileView);
  el("birthForm").addEventListener("submit", submitStructuredBirth);
  el("authForm").addEventListener("submit", submitAuth);
  el("retryReadingButton").addEventListener("click", () => state.lastStartPayload ? startCase(state.lastStartPayload) : openBirthDialog());
  el("editBirthFromFailureButton").addEventListener("click", openBirthDialog);
  el("birthDialog").addEventListener("close", () => {
    if (!state.busy && !["confirming", "boundary"].includes(el("abuStage").dataset.state)) {
      setAbuState("idle", state.reading ? "在听你说" : "准备听你说");
    }
  });
  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.addEventListener("click", () => setAuthMode(button.dataset.authMode));
  });
  el("readingTabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-artifact]");
    if (!button) return;
    showArtifact(button.dataset.artifact);
  });
  el("readingBackButton").addEventListener("click", () => {
    const target = el("readingBackButton").dataset.target || "overview";
    showArtifact(target);
  });
  document.addEventListener("pointerdown", noteAbuActivity, { passive: true });
  document.addEventListener("keydown", (event) => {
    noteAbuActivity();
    if (event.key === "Escape" && state.abuSurface === "open" && !document.querySelector("dialog[open]")) {
      setAbuSurface("collapsed");
    }
  });
}

async function sendMessage(event) {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message || state.busy) return;
  messageInput.value = "";
  autoSizeComposer();
  addMessage("user", message, "你");
  setQuickActions([]);
  const pendingComposerIntent = state.pendingComposerIntent;
  state.pendingComposerIntent = "";
  if (pendingComposerIntent === "reality.record") {
    setBusy(true, "正在保存现实记录");
    try {
      await recordRealityFromAbu(message);
    } finally {
      setBusy(false);
    }
    return;
  }
  if (executeLocalNavigationCommand(message)) return;
  setBusy(true, "正在理解你的问题");
  const routingLoader = addMessageLoading("正在理解你的问题");
  try {
    const body = await request(`${API.agent}/abu/resolve`, {
      method: "POST",
      body: JSON.stringify({
        message,
        has_case: Boolean(state.caseId && state.reading),
        has_profile: Boolean(state.activeProfile),
        active_mode: state.activeMode,
        active_domain: LIFE_DOMAIN_LABELS[state.activeArtifact] ? state.activeArtifact : "whole_chart",
      }),
    });
    routingLoader.remove();
    setBusy(false);
    await executeAbuCommand(body.plan, message);
  } catch (_) {
    routingLoader.remove();
    setBusy(false);
    if (!state.caseId || !state.reading) {
      if (state.activeProfile && !looksLikeBirthStatement(message)) handleProfileReadyMessage();
      else await handleBirthConversation(message);
    }
    else await continueMingliConversation(message);
  }
}

function executeLocalNavigationCommand(message) {
  if (!state.reading) return false;
  const normalized = message.replace(/\s+/g, "");
  const routes = [
    { matches: ["人生地图", "人生领域", "人生主题"], artifact: "domains", reply: "主题选择已经打开。一次只看一个你此刻真正关心的问题。" },
    { matches: ["八字依据", "看八字"], artifact: "bazi", reply: "八字依据已经打开。这里保留盘面重心、竞争解释和主作用路径。" },
    { matches: ["紫微视角", "看紫微"], artifact: "ziwei", reply: "紫微视角已经打开。这里用来观察人生舞台，不替代八字长期结构。" },
    { matches: ["回到综合", "看综合", "综合判断"], artifact: "overview", reply: "已经回到综合判断。" },
  ];
  const route = routes.find((item) => item.matches.some((term) => normalized.includes(term)));
  if (!route) return false;
  void executeProductAction("OPEN_LENS", { lens: route.artifact });
  void addTypedMessage("abu", route.reply, "Abu");
  setAbuState("wave", "已经为你打开");
  return true;
}

async function executeAbuCommand(plan, originalMessage) {
  const missing = plan.missing_requirements || [];
  if (missing.length) {
    void addTypedMessage("abu", plan.abu_message, "Abu");
    setQuickActions((plan.suggested_actions || []).map((label) => [label, actionForSuggestion(label)]));
    return;
  }
  switch (plan.capability_id) {
    case "profile.create":
      if (plan.slots?.open_form) {
        if (state.account) openProfileCreateDialog();
        else openBirthDialog();
        void addTypedMessage("abu", plan.abu_message, "Abu");
        return;
      }
      await handleBirthConversation(originalMessage);
      return;
    case "account.login":
      await executeProductAction(plan.action_type, plan.slots);
      setAbuState("listening", "还需要确认一件事");
      void addTypedMessage("abu", plan.abu_message, "Abu");
      return;
    case "account.register":
      await executeProductAction(plan.action_type, plan.slots);
      void addTypedMessage("abu", plan.abu_message, "Abu");
      return;
    case "account.logout":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      setQuickActions([["确认退出", logout], ["先不退出", () => setQuickActions([])]]);
      return;
    case "profile.list":
    case "reading.resume":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      await executeProductAction(plan.action_type, plan.slots);
      return;
    case "reading.select_domain":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      await executeProductAction(plan.action_type, plan.slots);
      return;
    case "reading.select_lens":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      await executeProductAction(plan.action_type, plan.slots);
      return;
    case "reading.explain":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      await executeProductAction(plan.action_type, plan.slots);
      return;
    case "interface.language":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      return;
    case "reality.record":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      await recordRealityFromAbu(plan.slots?.raw_event || originalMessage);
      return;
    case "timeline.select_period":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      await selectTimelinePeriod(resolveTimelinePeriod(plan.slots?.period || "current_month"));
      return;
    case "reading.start":
      void addTypedMessage("abu", plan.abu_message, "Abu");
      if (state.caseId) await restoreCase(state.caseId, true);
      else if (state.activeProfile) await startCase({ profile_id: state.activeProfile.profile_id });
      else setQuickActions([["直接说出生信息", () => focusComposer("例如：1990年10月19日下午三点，男，出生在广州，公历")], ["按表格填写", openBirthDialog]]);
      return;
    case "reading.ask":
      await continueMingliConversation(originalMessage);
      return;
    default:
      void addTypedMessage("abu", plan.abu_message, "Abu");
      setQuickActions((plan.suggested_actions || []).map((label) => [label, actionForSuggestion(label)]));
  }
}

async function executeProductAction(actionType, args = {}) {
  switch (actionType) {
    case "OPEN_DOMAIN":
      return selectDomain(args.domain);
    case "OPEN_LENS":
      return showArtifact(args.lens || "overview");
    case "OPEN_EVIDENCE":
      return showArtifact("evidence");
    case "OPEN_PROFILE_ARCHIVE":
      return openCasebook();
    case "CONTINUE_LAST_EXPLORATION":
      if (state.caseId && state.reading) return showArtifact(state.activeArtifact || "overview");
      if (state.caseId) return restoreCase(state.caseId, true);
      return state.account ? openCasebook() : showWelcome();
    case "OPEN_LOGIN":
      setAuthMode("login");
      el("authDialog").showModal();
      return;
    case "OPEN_REGISTER":
      setAuthMode("register");
      el("authDialog").showModal();
      return;
    case "START_BASELINE":
      if (args.birthDraft) return startCaseFromDraft(args.birthDraft);
      if (state.caseId) return restoreCase(state.caseId, true);
      if (state.activeProfile) return startCase({ profile_id: state.activeProfile.profile_id });
      return openBirthDialog();
    default:
      return undefined;
  }
}

function resolveTimelinePeriod(relative) {
  const now = new Date();
  const delta = relative === "previous_month" ? -1 : relative === "next_month" ? 1 : 0;
  return `${now.getFullYear()}-${String(now.getMonth() + 1 + delta).padStart(2, "0")}`.replace(
    /^(\d{4})-(00|13)$/,
    (_, year, month) => month === "00" ? `${Number(year) - 1}-12` : `${Number(year) + 1}-01`,
  );
}

async function selectTimelinePeriod(periodKey) {
  if (!state.caseId || !state.reading) return;
  setBusy(true, `正在打开 ${periodKey}`);
  setAbuState("thinking", "正在切换时间视角");
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/temporal/select`, {
      method: "POST",
      body: JSON.stringify({ period_key: periodKey, active_mode: state.activeMode }),
    });
    state.workspaceState = body.workspace_state;
    state.reading = body.reading;
    renderReading();
    const perspective = body.temporal_snapshot?.perspective;
    const language = perspective === "past" ? "复盘" : perspective === "future" ? "先验观察" : "当前观察";
    await addTypedMessage("abu", `${periodKey} 已经打开。这里是${language}，不会改写整盘基线。`, "Abu");
    setAbuState("wave", `${periodKey} 已打开`);
  } catch (error) {
    await addTypedMessage("abu", friendlyError(error, "这个月份暂时没有切换成功，当前命局不会受影响。"), "Abu");
    setAbuState("caution", "月份切换未完成");
  } finally {
    setBusy(false);
  }
}

async function recordRealityFromAbu(rawEvent) {
  if (!state.caseId || !state.reading) return;
  const summary = String(rawEvent || "").replace(/^(请)?(?:帮我)?(?:记录|记下)(?:一下|一件事)?[：:，,\s]*/, "").trim();
  if (!summary) {
    setQuickActions([["告诉 Abu 发生了什么", () => focusComposer("记录：", "reality.record")]]);
    return;
  }
  const period = state.workspaceState?.selected_period || state.reading?.workspace_state?.selected_period || resolveTimelinePeriod("current_month");
  const idempotencyKey = `abu:${period}:${stableClientHash(summary)}`;
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/reality-evidence`, {
      method: "POST",
      body: JSON.stringify({
        idempotency_key: idempotencyKey,
        source: "abu",
        summary,
        period_key: period,
        domain: state.reading?.workspace_state?.active_domain || "whole_chart",
        active_mode: state.activeMode,
      }),
    });
    const replay = body.created === false;
    state.workspaceState = {
      ...(state.workspaceState || state.reading?.workspace_state || {}),
      selected_period: period,
    };
    state.reading = {
      ...state.reading,
      workspace_state: state.workspaceState,
      temporal_state: {
        ...(state.reading?.temporal_state || {}),
        selected_period: period,
        selected_snapshot: body.temporal_snapshot,
      },
    };
    renderReading();
    await addTypedMessage("abu", replay ? "这件事已经记录过，我没有重复添加。" : `已经记在 ${period} 的现实记录里。它暂时只是事实，不会自动改写命局。`, "Abu");
    setAbuState("completed", replay ? "没有重复记录" : "现实记录已保存");
  } catch (error) {
    await addTypedMessage("abu", friendlyError(error, "这条现实记录暂时没有保存成功，原有判断没有被修改。"), "Abu");
  }
}

function stableClientHash(value) {
  let hash = 2166136261;
  for (const character of value) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function actionForSuggestion(label) {
  if (label.includes("当前档案") && label.includes("开始看盘")) return () => state.activeProfile ? startCase({ profile_id: state.activeProfile.profile_id }) : openBirthDialog();
  if (label.includes("切换命理档案") || label.includes("查看命理档案")) return openCasebook;
  if (label.includes("精确填写") || label.includes("表格填写")) return openBirthDialog;
  if (label.includes("出生信息") || label.includes("命盘")) return () => focusComposer("例如：1990年10月19日下午三点，男，出生在广州，公历");
  if (label === "登录") return () => { setAuthMode("login"); el("authDialog").showModal(); };
  if (label === "注册") return () => { setAuthMode("register"); el("authDialog").showModal(); };
  if (label.includes("八字") || label.includes("为什么")) return () => state.reading ? showArtifact("bazi") : sendQuickMessage("为什么这样判断");
  if (label.includes("紫微")) return () => state.reading ? showArtifact("ziwei") : sendQuickMessage("我想看紫微");
  const domainEntry = Object.entries(LIFE_DOMAIN_LABELS).find(([, name]) => label.includes(name.replace(/与.*/, "")));
  if (domainEntry && domainEntry[0] !== "whole_chart") return () => state.reading ? selectDomain(domainEntry[0]) : sendQuickMessage(`我想看${domainEntry[1]}`);
  if (label.includes("整盘")) return () => state.reading ? showArtifact("overview") : sendQuickMessage("先看整盘命局");
  return () => sendQuickMessage(label);
}

async function handleBirthConversation(message) {
  setBusy(true, "正在整理出生信息");
  try {
    const body = await request(`${API.agent}/intake`, {
      method: "POST",
      body: JSON.stringify({ message, current_draft: state.birthDraft }),
    });
    setBirthDraft(body.draft);
    if (body.status === "ready_for_confirmation") {
      setQuickActions([]);
      addMessage("abu", "我已经整理好了。请核对历法、日期、时间和地点；只有你确认后，我才会正式排盘。", "Abu");
      addBirthConfirmation(body.draft);
      setAbuState("confirming", "等你确认命盘");
    } else {
      addMessage("abu", body.draft.clarification_question || "还缺一项关键信息。你可以补充出生时间和地点吗？", "Abu");
      setAbuState("listening", "只差一项信息");
      setQuickActions([["改用表格填写", openBirthDialog]]);
    }
  } catch (error) {
    addMessage("abu", "这句话里的出生信息还不足以安全排盘。可以换一种说法，或改用表格填写；我不会猜测缺失信息。", "Abu");
    setAbuState("boundary", "不会猜测出生信息");
    setQuickActions([["按表格填写出生信息", openBirthDialog]]);
  } finally {
    setBusy(false);
  }
}

function addBirthConfirmation(draft) {
  const article = document.createElement("article");
  article.className = "message system birth-confirmation";
  const timeIsApproximate = draft.time_precision === "approximate";
  article.innerHTML = `<div class="message-author">盘</div><div class="message-body">
    <strong>${escapeHtml(draft.name || "我的命盘")}</strong><br>
    ${draft.calendar_type === "lunar" ? "农历" : "公历"} ${escapeHtml(draft.birth_date)} ${escapeHtml(draft.birth_time)}<br>
    ${draft.gender === "female" ? "女" : "男"} · ${escapeHtml(draft.birth_location)} · ${escapeHtml(draft.timezone)}<br>
    <span class="birth-confidence">出生时间：${timeIsApproximate ? "大约值，将保留不确定性" : "准确"}</span>
    <div class="quick-actions inline-actions">
      <button type="button" data-confirm-birth>确认，开始看盘</button>
      <button type="button" data-edit-birth>修改</button>
    </div>
  </div>`;
  article.querySelector("[data-confirm-birth]").addEventListener("click", (event) => {
    event.currentTarget.disabled = true;
    void executeProductAction("START_BASELINE", { birthDraft: draft });
  });
  article.querySelector("[data-edit-birth]").addEventListener("click", openBirthDialog);
  messageList.appendChild(article);
  scrollConversation();
}

async function submitStructuredBirth(event) {
  event.preventDefault();
  const data = new FormData(el("birthForm"));
  const draft = {
    name: data.get("name"),
    gender: data.get("gender"),
    calendar_type: data.get("calendar_type"),
    birth_date: data.get("birth_date"),
    birth_time: data.get("birth_time"),
    birth_location: data.get("birth_location"),
    timezone: data.get("timezone"),
    time_precision: data.get("time_precision") || "exact",
    missing_fields: [],
    clarification_question: "",
    ready_for_confirmation: true,
  };
  setBirthDraft(draft);
  el("birthFormError").textContent = "";
  if (["create", "edit"].includes(state.profileFormMode)) {
    await saveProfileFromDialog(draft);
    return;
  }
  el("birthDialog").close();
  setQuickActions([]);
  addMessage("user", `请按 ${state.birthDraft.birth_date} ${state.birthDraft.birth_time}，${state.birthDraft.birth_location} 建档。`, "你");
  addMessage("abu", "信息已经整理好。请先核对；确认后我会独立看盘，不先用现实经历套结论。", "Abu");
  addBirthConfirmation(state.birthDraft);
  setAbuState("confirming", "等你确认命盘");
}

async function startCaseFromDraft(draft) {
  const birthInput = birthInputFromDraft(draft);
  try {
    if (state.account) {
      const profile = await saveBirthProfile(birthInput);
      syncActiveProfile(profile);
      await startCase({ profile_id: profile.profile_id });
      return;
    }
    await startCase({ birth_input: birthInput });
  } catch (error) {
    setBusy(false);
    addMessage("abu", friendlyError(error, "这份出生信息暂时没有保存成功。信息还在当前页面里，可以稍后重试。"), "Abu");
    setQuickActions([["重新保存并看盘", () => startCaseFromDraft(draft)], ["检查出生信息", openBirthDialog]]);
  }
}

function birthInputFromDraft(draft) {
  return {
    birth_input_id: `abu-intake-${crypto.randomUUID()}`,
    name: draft.name || "我的命盘",
    gender: draft.gender,
    calendar_type: draft.calendar_type,
    birth_date: draft.birth_date,
    birth_time: draft.birth_time,
    birth_location: draft.birth_location,
    timezone: draft.timezone,
    true_solar_time_policy: "not_applied",
    lunar_leap_month: null,
    year_pillar: "",
    month_pillar: "",
    day_pillar: "",
    hour_pillar: "",
    input_quality: draft.time_precision === "exact" ? "user_confirmed" : "user_confirmed_approximate",
    warnings: draft.time_precision === "exact" ? [] : ["birth_time_approximate"],
  };
}

async function startDemoCase() {
  addMessage("user", "先用一个示例命盘让我体验。", "你");
  await startCase({
    birth_input: {
      birth_input_id: "demo-bridge-chart",
      name: "示例命盘",
      gender: "male",
      calendar_type: "solar",
      birth_date: "1987-05-12",
      birth_time: "18:00",
      birth_location: "上海",
      timezone: "Asia/Shanghai",
      true_solar_time_policy: "not_applied",
      lunar_leap_month: null,
      year_pillar: "丁巳",
      month_pillar: "乙巳",
      day_pillar: "乙丑",
      hour_pillar: "乙酉",
      input_quality: "explicit_pillars",
      warnings: ["demo_chart"],
    },
  });
}

async function startCase(payload) {
  state.lastStartPayload = JSON.parse(JSON.stringify(payload));
  state.readOnlyCase = false;
  state.readOnlyReason = "";
  state.cognitionBlocked = false;
  setBusy(true, "正在看盘");
  resetThinkingExperience();
  showThinking();
  await addTypedMessage("abu", "命盘已经确认。我会先独立看整盘，比较不同解释；形成判断后，再问你最有区分力的现实问题。", "Abu");
  try {
    payload.active_mode = state.activeMode;
    payload.progressive = true;
    const body = await request(`${API.agent}/cases`, { method: "POST", body: JSON.stringify(payload) });
    if (body.profile) {
      syncActiveProfile(body.profile);
      renderThinkingChartContext();
    }
    state.caseId = body.case_id;
    state.jobId = body.job_id;
    state.jobSequence = 0;
    state.progressive = {};
    localStorage.setItem("deepbazi.case_id", state.caseId);
    localStorage.setItem("deepbazi.cognitive_job_id", state.jobId);
    localStorage.setItem("deepbazi.cognitive_job_sequence", "0");
    await watchCognitiveJob(state.jobId);
  } catch (error) {
    showWelcome();
    addMessage("abu", friendlyError(error, "这次深度看盘没有完成，我不会拿模板结果敷衍你。可以稍后重试，出生信息仍保留在当前会话。"), "Abu");
    setQuickActions([["重新开始看盘", () => startCase(payload)], ["检查出生信息", openBirthDialog]]);
  }
}

async function watchCognitiveJob(jobId) {
  if (!jobId) return;
  state.jobId = jobId;
  setBusy(true, "正在形成第一眼判断");
  showThinking();
  let finished = false;
  let terminalStatus = "";
  while (!finished && state.jobId === jobId) {
    try {
      const body = await request(`${API.agent}/jobs/${jobId}?after=${state.jobSequence}`);
      for (const event of body.events || []) {
        state.jobSequence = Math.max(state.jobSequence, event.sequence || 0);
        localStorage.setItem("deepbazi.cognitive_job_sequence", String(state.jobSequence));
        handleCognitiveEvent(event);
      }
      finished = ["completed", "failed"].includes(body.status);
      if (finished) terminalStatus = body.status;
      if (!finished) await delay(2500);
    } catch (error) {
      if (error.status === 404) {
        const recovered = await restoreCase(state.caseId, true);
        state.jobId = "";
        localStorage.removeItem("deepbazi.cognitive_job_id");
        localStorage.removeItem("deepbazi.cognitive_job_sequence");
        if (recovered) {
          addMessage("abu", "看盘结果已经找回来了。你可以从整盘结论继续探索。", "Abu");
        } else {
          addMessage("abu", "上一次未完成的任务已经失效。出生信息仍在，你可以重新开始看盘。", "Abu");
          showWelcome();
        }
      } else {
        const recovered = await restoreCase(state.caseId, true);
        if (recovered) {
          state.jobId = "";
          localStorage.removeItem("deepbazi.cognitive_job_id");
          localStorage.removeItem("deepbazi.cognitive_job_sequence");
          addMessage("abu", "任务进度刚才短暂中断，但完整结果已经找回来了。", "Abu");
        } else {
          addMessage("abu", friendlyError(error, "我暂时没有读到认知任务的进度。已经完成的阶段仍然保留，可以稍后继续。"), "Abu");
          showCognitionFailure({ message: "暂时无法读取本轮看盘进度。你可以重新开始，命理档案不会丢失。" });
        }
      }
      setBusy(false);
      return;
    }
  }
  if (state.jobId === jobId && terminalStatus) {
    if (terminalStatus === "completed" && !state.reading) await restoreCase(state.caseId, true);
    state.jobId = "";
    localStorage.removeItem("deepbazi.cognitive_job_id");
    localStorage.removeItem("deepbazi.cognitive_job_sequence");
    setBusy(false);
  }
}

function handleCognitiveEvent(event) {
  const payload = event.payload || {};
  state.progressive[event.event_type] = payload;
  if (event.event_type === "chart_ready") renderThinkingChartContext();
  let previewLine = "";
  if (event.event_type === "chart_ready") {
    updateThinkingExperience(0, 18, "命盘已经确认", "正在一次完成整盘基线认知，不会提前生成各人生专题。", `四柱已确认：${(payload.pillars || []).join(" · ")}`);
    previewLine = `四柱已经确认：${(payload.pillars || []).join(" · ")}`;
    setAbuState("thinking", "正在观察盘面重心");
  } else if (event.event_type === "baseline_preview_ready") {
    updateThinkingExperience(1, 36, "第一眼正在形成", "这是尚未提交的事实安全预览；完整假设与反证仍在生成。", "暂定第一眼 · 尚未写入案例");
    previewLine = payload.preview_line || "";
    setAbuState("thinking", "正在比较相反解释");
  } else if (event.event_type === "baseline_draft_ready") {
    updateThinkingExperience(2, 72, "整盘基线已经初步形成", "这仍是草稿，正在检查事实引用、命盘版本和不确定性。", "初步认知尚未写入长期案例");
    previewLine = payload.first_look || payload.whole_chart_thesis || payload.primary_path || "";
    setAbuState("thinking", "正在校验整盘基线");
  } else if (event.event_type === "formal_insight_draft_ready") {
    updateThinkingExperience(2, 82, "已经看见命局主线", "草稿只用于当前预览，通过检查后才会保存。", "Draft Preview · 尚未提交");
    previewLine = payload.claim || "";
    setAbuState("thinking", "正在核对依据");
  } else if (event.event_type === "baseline_validated") {
    updateThinkingExperience(3, 94, "命理依据已经核对", "正在把通过检查的基线认知写入这份长期案例。", "事实与引用检查完成");
    setAbuState("thinking", "正在写入长期案例");
  } else if (event.event_type === "pattern_preview_ready") {
    updateThinkingExperience(1, 31, "第一眼已经出现", "Abu 正在把这条观察与相反解释继续比较。", "第一眼已经形成");
    previewLine = payload.preview_line || payload.whole_chart_thesis || "";
    setAbuState("thinking", "正在核对第一眼");
  } else if (event.event_type === "pattern_candidates_ready") {
    updateThinkingExperience(1, 38, "正在比较命局假设", "第一眼已经形成，但还要与相反解释逐一比较。", `已形成 ${payload.hypotheses?.length || 1} 个候选解释`);
    setAbuState("thinking", "正在比较命局假设");
    previewLine = payload.first_look || payload.whole_chart_thesis || "";
    state.pendingPrimaryTypewriter = true;
    void addTypedMessage("abu", "第一眼已经形成，我先把它交给你；主作用路径和紫微参看会继续补上。", "Abu");
  } else if (event.event_type === "work_path_ready") {
    updateThinkingExperience(2, 58, "主作用路径已经形成", "继续检查这条路径能否解释整盘，而不是只解释局部。", "八字主作用路径已形成");
    previewLine = payload.work_path?.path_statement || payload.portrait?.[0]?.claim || "";
    setAbuState("thinking", "正在用紫微看人生舞台");
  } else if (event.event_type === "work_path_unavailable") {
    updateThinkingExperience(2, 58, "先保留已确认的盘面重心", "继续从已经形成的判断向下展开。", "继续整理命局主线");
    setAbuState("thinking", "继续整理可确认的判断");
  } else if (event.event_type === "ziwei_lens_ready") {
    updateThinkingExperience(3, 76, "正在参看紫微人生舞台", "比较八字长期结构与紫微人生舞台的一致处和差异。", "紫微镜头已形成");
    previewLine = payload.integrated_thesis || payload.ziwei_first_look || "";
    setAbuState("thinking", "正在综合八字与紫微");
  } else if (event.event_type === "ziwei_unavailable") {
    updateThinkingExperience(3, 76, "本轮先以八字为主", "出生资料不足以可靠叠加紫微，因此不会强行补猜。", "紫微本轮未参与综合");
    previewLine = "本轮先沿八字主线继续展开，不用缺失的紫微信息补猜。";
    setAbuState("thinking", "继续完成八字判断");
  } else if (event.event_type === "prior_probe_ready") {
    updateThinkingExperience(4, 94, "正在形成现实判断", "把命局结构转成可被现实验证、也可能被推翻的判断。", "第一批先验判断已形成");
    previewLine = payload.prior_predictions?.[0]?.claim || payload.next_probe?.question || "";
    setAbuState("thinking", "正在完成整盘审查");
  } else if (event.event_type === "whole_chart_ready") {
    updateThinkingExperience(4, 98, "整盘核心已经形成", "正在整理成完整、可继续探索的命局理解。", "整盘核心认知已形成");
    previewLine = payload.first_look || payload.whole_chart_thesis || "";
  } else if (["baseline_committed", "reading_completed"].includes(event.event_type)) {
    updateThinkingExperience(4, 100, "第一轮看盘完成", "命局理解已经形成。", "整盘内容已整理完成");
    stopThinkingPreview();
    state.reading = payload.reading;
    state.cognitionBlocked = false;
    state.workspaceState = payload.reading?.workspace_state || state.workspaceState;
    state.progressive = {};
    state.pendingPrimaryTypewriter = true;
    renderReading();
    void addTypedMessage("abu", "整盘基线已经写入这份长期案例。先看命局主线和当前阶段，再选择一个真正关心的方向继续。", "Abu");
    setQuickActions([["选择人生主题", () => showArtifact("domains")], ["验证一个判断", () => document.querySelector(".probe-panel")?.scrollIntoView({ behavior: "smooth", block: "center" })]]);
    setAbuState("completed", "基线认知已形成");
    updateCaseHeader();
    return;
  } else if (event.event_type === "baseline_competing") {
    stopThinkingPreview();
    state.reading = payload.reading;
    state.cognitionBlocked = false;
    state.workspaceState = payload.reading?.workspace_state || state.workspaceState;
    state.progressive = {};
    renderReading();
    void addTypedMessage("abu", "这张盘目前有两种都能成立的解释。我不会装作已经选定；先把分歧和判断条件摊开。", "Abu");
    setQuickActions([["查看两种解释", () => showArtifact("overview")], ["重新独立看盘", () => state.lastStartPayload ? startCase(state.lastStartPayload) : openBirthDialog()]]);
    setAbuState("caution", "两种解释仍在竞争");
    updateCaseHeader();
    return;
  } else if (event.event_type === "baseline_blocked") {
    stopThinkingPreview();
    state.cognitionBlocked = true;
    addMessage("abu", "本轮发现了不能绕过的命盘事实或一致性问题，所以我没有把草稿写成正式判断。排盘和档案都保留。", "Abu");
    setQuickActions([["重新独立看盘", () => state.lastStartPayload ? startCase(state.lastStartPayload) : openBirthDialog()], ["检查出生信息", openBirthDialog]]);
    setAbuState("sad", "这次没能形成可靠判断");
    showCognitionFailure({
      failure_stage: "epistemic_review",
      message: "当前整盘认知没有通过一致性校验，因此暂不形成正式判断。命盘档案已经保存，可以重新分析。",
      outcome: payload.outcome,
    });
    return;
  } else if (event.event_type === "domain_baseline_reused") {
    const label = LIFE_DOMAIN_LABELS[payload.domain] || "这个专题";
    previewLine = payload.preview_line || "";
    setAbuLoadingPeek(`正在沿整盘基线推演${label}`, "没有重新生成另一套命局。");
    setAbuState("thinking", `正在沿基线看${label}`);
  } else if (event.event_type === "domain_preview_ready") {
    const label = LIFE_DOMAIN_LABELS[payload.domain] || "这个专题";
    previewLine = payload.preview_line || "";
    setAbuLoadingPeek(`${label}的第一条因果线已经出现`, "仍在补齐条件、反证与一致性检查。");
    setAbuState("thinking", `正在核对${label}依据`);
  } else if (event.event_type === "domain_cache_reused") {
    const label = LIFE_DOMAIN_LABELS[payload.domain] || "这个专题";
    setAbuLoadingPeek(`已经找回上次的${label}结果`, "命盘版本与问题完全一致，不重复计算。");
  } else if (event.event_type === "domain_committed") {
    stopThinkingPreview();
    state.reading = payload.reading;
    state.workspaceState = payload.reading?.workspace_state || state.workspaceState;
    state.pendingPrimaryTypewriter = !payload.cache_hit;
    showArtifact(payload.domain || "overview");
    void addTypedMessage("abu", `${LIFE_DOMAIN_LABELS[payload.domain] || "专题"}已经沿当前整盘基线形成，并通过一致性检查。`, "Abu");
    setAbuState("idle", "专题理解已经形成");
    return;
  } else if (["domain_competing", "domain_blocked", "domain_revision_candidate"].includes(event.event_type)) {
    stopThinkingPreview();
    state.reading = payload.reading || state.reading;
    state.workspaceState = payload.reading?.workspace_state || state.workspaceState;
    showDomainReliabilityOutcome(LIFE_DOMAIN_LABELS[payload.domain] || "这个专题", payload.domain_outcome || {});
    void addTypedMessage("abu", event.event_type === "domain_revision_candidate"
      ? "专题发现了一处可能需要修正整盘基线的分歧。我保留了修正候选，没有悄悄覆盖原判断。"
      : "这一专题目前没有形成可提交的单一判断，我保留了整盘基线和分歧。", "Abu");
    setAbuState(event.event_type === "domain_blocked" ? "sad" : "caution", event.event_type === "domain_blocked" ? "这个专题没有通过检查" : "专题暂未提交");
    return;
  } else if (event.event_type === "domain_failed") {
    stopThinkingPreview();
    void addTypedMessage("abu", payload.message || "这一专题暂时没有完成，整盘基线仍然保留。", "Abu");
    showArtifact("domains");
    setAbuState("sad", "这个专题暂时没有完成");
    return;
  } else if (event.event_type === "reading_failed") {
    stopThinkingPreview();
    addMessage("abu", payload.message || "本次深度认知没有完成，已经形成的部分会保留。", "Abu");
    setQuickActions([["重新开始看盘", () => state.lastStartPayload ? startCase(state.lastStartPayload) : openBirthDialog()], ["检查出生信息", openBirthDialog]]);
    setAbuState("sad", "这次看盘没有完成");
    showCognitionFailure(payload);
    return;
  }
  renderProgressiveCanvas();
  if (previewLine) void updateThinkingPreview(previewLine);
  else resumeThinkingPreview();
}

function renderProgressiveCanvas() {
  if (state.reading) return;
  const pattern = state.progressive.pattern_candidates_ready;
  const work = state.progressive.work_path_ready;
  const workUnavailable = state.progressive.work_path_unavailable;
  if (!pattern) {
    showThinking();
    return;
  }
  const dual = state.progressive.ziwei_lens_ready;
  const predictions = state.progressive.prior_probe_ready;
  const wholeReady = state.progressive.whole_chart_ready;
  const selected = pattern.hypotheses?.find((item) => item.hypothesis_id === pattern.selected_hypothesis_id) || pattern.hypotheses?.[0];
  const professional = ["practitioner", "research"].includes(state.activeMode);
  el("welcomeScene").hidden = true;
  el("thinkingScene").hidden = true;
  el("failureScene").hidden = true;
  el("readingCanvas").hidden = false;
  el("readingTabs").hidden = true;
  el("readingEyebrow").textContent = "已形成的判断";
  el("readingTitle").textContent = "这张命盘正在显出它的主线";
  el("artifactContent").innerHTML = `
    <section class="artifact-section public-reading-lead stream-section"><p class="eyebrow">Abu 第一眼</p><h3>${escapeHtml(cleanUserCopy(pattern.first_look))}</h3><p>${escapeHtml(cleanUserCopy(pattern.whole_chart_thesis))}</p></section>
    ${(pattern.salient_phenomena || []).length ? `<section class="artifact-section stream-section"><p class="eyebrow">为什么先看这里</p><div class="personal-observation-list">${pattern.salient_phenomena.slice(0, professional ? 3 : 2).map((item) => `<p>${escapeHtml(cleanUserCopy(professional ? `${item.observation}：${item.why_it_matters}` : item.observation))}</p>`).join("")}</div></section>` : ""}
    ${professional && pattern.hypotheses?.length ? `<section class="artifact-section stream-section"><p class="eyebrow">竞争解释</p><div class="hypothesis-list">${pattern.hypotheses.map(renderHypothesis).join("")}</div></section>` : selected ? `<section class="artifact-section stream-section"><p class="eyebrow">当前领先解释</p><h3>${escapeHtml(cleanUserCopy(selected.thesis))}</h3></section>` : ""}
    ${work ? `<section class="artifact-section stream-section newly-accepted"><p class="eyebrow">主作用路径</p><h3>${escapeHtml(cleanUserCopy(work.work_path?.path_statement || ""))}</h3><div class="causal-chain">${[...(work.work_path?.source || []), ...(work.work_path?.transformations || []), ...(work.work_path?.target || [])].map((step) => `<div class="causal-step">${escapeHtml(cleanUserCopy(step))}</div>`).join("")}</div></section>` : ""}
    ${dual ? `<section class="artifact-section stream-section newly-accepted"><p class="eyebrow">紫微复核</p><h3>${escapeHtml(cleanUserCopy(dual.integrated_thesis))}</h3>${dual.tensions?.[0] ? `<p>${escapeHtml(cleanUserCopy(dual.tensions[0]))}</p>` : ""}</section>` : ""}
    ${predictions?.prior_predictions?.length ? `<section class="artifact-section stream-section newly-accepted"><p class="eyebrow">可以在现实中验证</p><div class="personal-observation-list">${predictions.prior_predictions.slice(0, 3).map((item) => `<p>${escapeHtml(cleanUserCopy(item.claim))}</p>`).join("")}</div></section>` : ""}`;
  decoratePublicArtifact();
  resumeThinkingPreview();
  if (window.innerWidth <= 960) showCanvas();
  refreshIcons();
}

async function continueMingliConversation(message) {
  setBusy(true, "正在重新看这个问题");
  setAbuState("thinking", "正在思考");
  const replyLoader = addMessageLoading("正在结合这张命盘重新推演");
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/turn`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    const turn = body.turn;
    replyLoader.remove();
    await addTypedMessage("abu", turn.abu_message, "Abu");
    if (turn.canvas_focus) showArtifact(turn.canvas_focus);
    const actions = [];
    if (turn.next_probe) {
      actions.push(...turn.next_probe.options.slice(0, 2).map((label) => [label, () => sendQuickMessage(label)]));
    }
    actions.push(...(turn.suggested_actions || []).slice(0, Math.max(0, 3 - actions.length)).map((label) => [label, () => sendQuickMessage(label)]));
    setQuickActions(actions);
    state.reading = body.reading;
    state.workspaceState = body.reading?.workspace_state || state.workspaceState;
    renderReading();
  } catch (error) {
    replyLoader.remove();
    await addTypedMessage("abu", friendlyError(error, "我暂时没能把这个问题推演完整。原有判断没有被改写，你可以换一种说法再问。"), "Abu");
  } finally {
    replyLoader.remove();
    setBusy(false);
    setAbuState("idle", "在听你说");
  }
}

function renderReading() {
  if (!state.reading) return;
  state.activeMode = state.reading.experience_mode || state.activeMode;
  el("readingCanvas").dataset.mode = state.activeMode;
  updateModeTabs();
  el("welcomeScene").hidden = true;
  el("thinkingScene").hidden = true;
  el("failureScene").hidden = true;
  el("readingCanvas").hidden = false;
  el("readingTabs").hidden = ["guest", "member"].includes(state.activeMode);
  const publicHeadline = readingBaselineClaim(state.reading);
  const primaryHypothesis = state.reading.hypotheses?.find((item) => item.hypothesis_id === state.reading.selected_hypothesis_id) || state.reading.hypotheses?.[0];
  el("readingTitle").textContent = ["guest", "member"].includes(state.activeMode) ? publicHeadline : humanizeHypothesisName(primaryHypothesis?.name || state.reading.first_look);
  el("readingEyebrow").textContent = modeLabel(state.activeMode);
  showArtifact(state.activeArtifact);
  animateCanvasEntrance(el("readingCanvas"));
}

function showArtifact(name) {
  if (!state.reading) return;
  stopNarration({ silent: true });
  state.primaryTypewriterGeneration += 1;
  document.querySelectorAll(".reading-stream-marker, .reading-stream-caret").forEach((node) => node.remove());
  document.querySelectorAll(".primary-reading-stream").forEach((node) => {
    node.classList.remove("primary-reading-stream");
    node.style.minHeight = "";
  });
  state.activeArtifact = name;
  localStorage.setItem("deepbazi.active_artifact", name);
  updateReadingHeader(name);
  syncReadingNavigation(name);
  const domainSelected = Boolean(LIFE_DOMAIN_LABELS[name] && name !== "whole_chart");
  el("artifactContent").dataset.view = domainSelected ? "domain" : name;
  el("artifactContent").dataset.mode = state.activeMode;
  document.querySelectorAll("[data-artifact]").forEach((button) => button.classList.toggle("active", button.dataset.artifact === name || (button.dataset.artifact === "domains" && domainSelected)));
  const renderers = { overview: renderOverview, bazi: renderBazi, ziwei: renderZiwei, domains: renderDomainMap, evidence: renderEvidence };
  const artifact = domainSelected ? renderDomainExploration(name) : (renderers[name] || renderOverview)();
  const readOnlyNotice = state.readOnlyCase
    ? `<section class="historical-read-only-notice" role="status"><p class="eyebrow">历史命盘版本 · 只读</p><strong>${escapeHtml(state.readOnlyReason || "这份案例基于已经被替代的出生资料。")}</strong><p>你可以查看当时的正式判断，但不能继续测算、切换月份、记录现实事件或修改案例。</p></section>`
    : "";
  el("artifactContent").innerHTML = `${readOnlyNotice}${artifact}`;
  decoratePublicArtifact();
  bindArtifactActions();
  if (window.innerWidth <= 960) showCanvas();
  el("taskCanvas").scrollTop = 0;
  refreshIcons();
  animateCanvasEntrance(el("artifactContent"));
  if (name === "overview" && ["guest", "member"].includes(state.activeMode)) void hydrateNarrationWorkspace();
}

function decoratePublicArtifact() {
  const artifact = el("artifactContent");
  const isPublic = ["guest", "member"].includes(state.activeMode);
  artifact.classList.toggle("public-story-artifact", isPublic);
  artifact.classList.toggle("task-choice-artifact", isPublic && state.activeArtifact === "domains");
  if (!isPublic) return;
  artifact.querySelectorAll(".story-band, .story-command").forEach((node) => {
    node.classList.remove("story-band", "story-command", "story-day", "story-mist", "story-dusk", "story-night");
  });
  const children = Array.from(artifact.children);
  const storyNodes = children.filter((node) => !node.matches(".domain-back"));
  children.forEach((node) => {
    if (node.matches(".domain-back")) {
      node.classList.add("story-command");
      return;
    }
    node.classList.add("story-band");
    const storyIndex = storyNodes.indexOf(node);
    const ratio = storyNodes.length <= 1 ? 0 : storyIndex / (storyNodes.length - 1);
    const tone = ratio === 0 ? "day" : ratio < .45 ? "mist" : ratio < .78 ? "dusk" : "night";
    node.classList.add(`story-${tone}`);
  });
  if (state.activeArtifact !== "domains") applyStoryDisclosure(artifact);
  if (isPublic && state.pendingPrimaryTypewriter) {
    state.pendingPrimaryTypewriter = false;
    requestAnimationFrame(() => void typePrimaryReading(artifact));
  }
}

function applyStoryDisclosure(artifact) {
  artifact.querySelector(".story-continue")?.remove();
  const bands = Array.from(artifact.children).filter((node) => node.classList.contains("story-band"));
  const journeySteps = bands.filter((band) => band.classList.contains("journey-step"));
  if (journeySteps.length) applyJourneyAccordion(artifact, journeySteps);
}

function applyJourneyAccordion(artifact, steps) {
  const key = `${state.caseId || "guest"}:${state.activeMode}:${state.activeArtifact}:journey`;
  const hasSavedState = Object.prototype.hasOwnProperty.call(state.journeyExpandedSteps, key);
  const activeStep = hasSavedState ? state.journeyExpandedSteps[key] : steps[0]?.dataset.journeyStep;
  const sync = () => {
    steps.forEach((step) => {
      const expanded = step.dataset.journeyStep === state.journeyExpandedSteps[key];
      const button = step.querySelector("[data-journey-step-toggle]");
      const body = step.querySelector(".journey-step-body");
      step.classList.toggle("is-expanded", expanded);
      step.classList.toggle("is-collapsed", !expanded);
      button?.setAttribute("aria-expanded", String(expanded));
      body?.setAttribute("aria-hidden", String(!expanded));
      if (body) body.inert = !expanded;
      const action = button?.querySelector("[data-journey-toggle-label]");
      if (action) action.textContent = expanded ? "收起" : "展开";
    });
  };
  state.journeyExpandedSteps[key] = activeStep || "";
  steps.forEach((step) => {
    const button = step.querySelector("[data-journey-step-toggle]");
    if (!button) return;
    button.addEventListener("click", () => {
      const selected = step.dataset.journeyStep || "";
      state.journeyExpandedSteps[key] = state.journeyExpandedSteps[key] === selected ? "" : selected;
      sync();
      if (state.journeyExpandedSteps[key] && window.innerWidth <= 960) {
        step.scrollIntoView({ behavior: reducedMotion.matches ? "auto" : "smooth", block: "start" });
      }
    });
  });
  sync();
  refreshIcons();
}

async function typePrimaryReading(artifact) {
  if (!["guest", "member"].includes(state.activeMode)) return;
  const target = artifact.querySelector(".journey-step.is-expanded h3, .story-band:not([hidden]) h3");
  if (!target || !target.textContent.trim()) return;
  const fullText = target.textContent.trim();
  const generation = ++state.primaryTypewriterGeneration;
  if (reducedMotion.matches) return;
  const height = Math.ceil(target.getBoundingClientRect().height);
  target.style.minHeight = `${height}px`;
  target.classList.add("primary-reading-stream");
  target.setAttribute("aria-label", fullText);
  target.textContent = "";
  const marker = document.createElement("span");
  marker.className = "reading-stream-marker";
  marker.textContent = "Abu 刚刚形成";
  target.before(marker);
  const caret = document.createElement("span");
  caret.className = "reading-stream-caret";
  target.appendChild(caret);
  const characters = Array.from(fullText);
  const chunkSize = characters.length > 180 ? 3 : characters.length > 90 ? 2 : 1;
  try {
    for (let index = 0; index < characters.length; index += chunkSize) {
      if (generation !== state.primaryTypewriterGeneration || !target.isConnected) return;
      caret.before(document.createTextNode(characters.slice(index, index + chunkSize).join("")));
      await delay(characters[index] === "。" || characters[index] === "；" ? 30 : 12);
    }
    marker.classList.add("complete");
  } finally {
    caret.remove();
    target.classList.remove("primary-reading-stream");
    target.style.minHeight = "";
  }
}

function animateCanvasEntrance(node) {
  if (!node || reducedMotion.matches || typeof node.animate !== "function") return;
  node.animate(
    [{ opacity: .35, transform: "translateY(12px)" }, { opacity: 1, transform: "translateY(0)" }],
    { duration: 420, easing: "cubic-bezier(.22,.72,.25,1)" },
  );
}

function updateReadingHeader(name) {
  const reading = state.reading;
  if (!reading) return;
  const primary = reading.hypotheses?.find((item) => item.hypothesis_id === reading.selected_hypothesis_id) || reading.hypotheses?.[0];
  if (name === "overview") {
    const publicMode = ["guest", "member"].includes(state.activeMode);
    el("readingEyebrow").textContent = publicMode ? "整体理解" : modeLabel(state.activeMode);
    el("readingTitle").textContent = publicMode ? "这张命盘中的你" : humanizeHypothesisName(primary?.name || reading.first_look);
  } else if (name === "bazi") {
    el("readingEyebrow").textContent = ["guest", "member"].includes(state.activeMode) ? "长期模式" : "命局依据";
    el("readingTitle").textContent = ["guest", "member"].includes(state.activeMode) ? "你的长期结构" : "八字结构与主作用路径";
  } else if (name === "ziwei") {
    el("readingEyebrow").textContent = "人生舞台";
    el("readingTitle").textContent = ["guest", "member"].includes(state.activeMode) ? "你如何进入现实世界" : "紫微视角";
  } else if (name === "domains") {
    el("readingEyebrow").textContent = "你的命局";
    el("readingTitle").textContent = "人生主题";
  } else if (name === "evidence") {
    el("readingEyebrow").textContent = "为什么这样判断";
    el("readingTitle").textContent = ["guest", "member"].includes(state.activeMode) ? "判断依据与不确定性" : "证据、反证与竞争解释";
  } else if (LIFE_DOMAIN_LABELS[name]) {
    el("readingEyebrow").textContent = "人生主题";
    el("readingTitle").textContent = LIFE_DOMAIN_LABELS[name];
  }
}

function syncReadingNavigation(name) {
  const publicMode = ["guest", "member"].includes(state.activeMode);
  const overview = name === "overview";
  const domainSelected = Boolean(LIFE_DOMAIN_LABELS[name] && name !== "whole_chart");
  el("readingCanvas").classList.toggle("public-detail-view", publicMode && !overview);
  el("readingHeader").hidden = publicMode && overview;
  el("readingTabs").hidden = publicMode;
  el("readingBackButton").hidden = !publicMode || overview;
  el("readingBackButton").dataset.target = domainSelected ? "domains" : "overview";
  el("readingBackButton").querySelector("span").textContent = domainSelected ? "返回主题选择" : "返回当前命局";
}

function updateModeTabs() {
  const publicMode = ["guest", "member"].includes(state.activeMode);
  const labels = publicMode
    ? { overview: "你的命局", bazi: "长期结构", ziwei: "人生舞台", domains: "人生主题" }
    : { overview: "综合", bazi: "八字", ziwei: "紫微", domains: "人生地图" };
  document.querySelectorAll("[data-artifact]").forEach((button) => {
    if (labels[button.dataset.artifact]) button.textContent = labels[button.dataset.artifact];
  });
}

function renderOverview() {
  const r = state.reading;
  let content = "";
  if (state.activeMode === "guest") content = renderGuestOverview(r);
  else if (state.activeMode === "member") content = renderMemberOverview(r);
  else if (r.dual_lens) content = renderIntegratedOverview(r);
  else content = renderBazi();
  const professionalMode = ["practitioner", "research"].includes(state.activeMode);
  const reliability = renderReliabilityState(r);
  return professionalMode
    ? `${reliability}${r.deliberation ? renderDeliberationWorkspace() : ""}${renderProfessionalChangeLog(r)}${content}`
    : `${reliability}${content}`;
}

function renderReliabilityState(reading) {
  const reliability = reading?.reliability || {};
  if (reliability.state !== "competing") return "";
  const alternatives = reading.public_evidence?.alternative_explanations
    || reading.hypotheses?.filter((item) => item.hypothesis_id !== reading.selected_hypothesis_id)
    || [];
  const primary = reading.public_evidence?.primary_explanation
    || reading.hypotheses?.find((item) => item.hypothesis_id === reading.selected_hypothesis_id);
  return `<section class="artifact-section reliability-state competing">
    <p class="eyebrow">当前存在竞争解释</p>
    <h3>Abu 还没有足够依据只保留一种答案</h3>
    <div class="competing-explanation-grid">
      ${primary ? `<article><small>解释 A</small><strong>${escapeHtml(cleanUserCopy(primary.name || "当前领先解释"))}</strong><p>${escapeHtml(cleanUserCopy(primary.thesis || ""))}</p></article>` : ""}
      ${alternatives.slice(0, 2).map((item, index) => `<article><small>解释 ${String.fromCharCode(66 + index)}</small><strong>${escapeHtml(cleanUserCopy(item.name || "另一种解释"))}</strong><p>${escapeHtml(cleanUserCopy(item.thesis || ""))}</p></article>`).join("")}
    </div>
    <p class="boundary-copy">这些内容只作为未决理解保存，没有写成正式 Life Case 结论。</p>
  </section>`;
}

function renderProfessionalChangeLog(reading) {
  const evidenceRevision = reading.latest_revision || reading.life_case?.latest_case_revision;
  const deliberationRevision = reading.latest_deliberation_revision;
  if (!evidenceRevision && !deliberationRevision) return "";
  return `<details class="professional-change-log"><summary>最近案例变化</summary>${evidenceRevision ? `<div><strong>现实证据修正</strong><p>${escapeHtml(evidenceRevision.summary)}</p></div>` : ""}${deliberationRevision ? `<div><strong>专业研判修正</strong><p>${escapeHtml(deliberationRevision.summary)}</p></div>` : ""}<p class="boundary-copy">以上变化均未修改出生信息、原始命盘、系统理论或全局规则。</p></details>`;
}

function renderLatestDeliberationRevision(reading) {
  const revision = reading.latest_deliberation_revision;
  if (!revision || !["practitioner", "research"].includes(state.activeMode)) return "";
  return `<section class="case-revision deliberation-revision" aria-label="最新专业研判"><div><p class="eyebrow">案例研判已更新</p><h3>${escapeHtml(revision.summary)}</h3></div><details><summary>影响范围</summary><p>${escapeHtml((revision.changed_surfaces || []).map(deliberationSurfaceLabel).join("、"))}</p><p class="boundary-copy">没有修改出生信息、原始命盘、系统理论或全局规则。</p></details></section>`;
}

function renderLatestRevision(reading) {
  const revision = reading.latest_revision || reading.life_case?.latest_case_revision;
  if (!revision) return "";
  const publicMode = ["guest", "member"].includes(state.activeMode);
  const publicSummary = publicMode ? `${cleanUserCopy(revision.summary).split(/[。！？]/)[0]}。` : revision.summary;
  return `<details class="case-revision compact-revision" aria-label="最新认知修正"><summary><span><small>Abu 对你的理解已更新</small><strong>${escapeHtml(publicSummary)}</strong></span><b>查看变化</b></summary><div class="compact-revision-body"><p>${escapeHtml(cleanUserCopy(revision.interpretation))}</p><p class="boundary-copy">出生信息和原始命盘没有改变。</p></div></details>`;
}

function renderIntegratedOverview(r) {
  const dual = r.dual_lens;
  const firstAgreement = dual.agreements?.[0] || "两种视角正在形成同一个现实判断。";
  const tension = dual.tensions?.[0];
  return `
    <section class="artifact-section integrated-hero"><div class="lens-kicker"><span>八字</span><i data-lucide="plus"></i><span>紫微</span></div><h3>${escapeHtml(firstAgreement)}</h3><details class="reading-details"><summary>展开完整综合判断</summary><p>${escapeHtml(dual.integrated_thesis)}</p></details><div class="overview-actions"><button class="text-link" type="button" data-open-artifact="bazi">看八字依据</button><button class="text-link" type="button" data-open-artifact="ziwei">看紫微依据</button></div></section>
    ${tension ? `<section class="artifact-section tension-note"><p class="eyebrow">值得继续确认</p><h3>${escapeHtml(tension)}</h3><p>${escapeHtml(dual.current_stage_note)}</p></section>` : ""}
    ${r.probe_plan ? `<section class="artifact-section"><p class="eyebrow">先断后问</p><h3>让两种视角在现实中继续收敛</h3>${renderProbe(r.probe_plan)}</section>` : ""}`;
}

function renderBazi() {
  const r = state.reading;
  if (["guest", "member"].includes(state.activeMode)) return renderPublicBazi(r);
  return `<section class="artifact-section lens-intro bazi"><p class="eyebrow">八字 · 长期结构</p>${renderPillarSet(r.pillars)}<h3>${escapeHtml(r.first_look)}</h3><p>${escapeHtml(r.whole_chart_thesis)}</p></section>
    ${renderDeliberationWorkspace(["pattern", "useful_god", "work_path"])}
    <section class="artifact-section"><p class="eyebrow">盘面重心</p><h3>Abu 为什么先看这里</h3>${r.salient_phenomena.map((item) => `<div class="evidence-row"><strong>${escapeHtml(item.observation)}</strong><p>${escapeHtml(item.why_it_matters)}</p></div>`).join("")}</section>
    <section class="artifact-section"><p class="eyebrow">竞争解释</p><h3>不是看到一个标签就结束</h3><div class="hypothesis-list">${r.hypotheses.map(renderHypothesis).join("")}</div></section>
    <section class="artifact-section"><p class="eyebrow">主做功</p><h3>${escapeHtml(r.work_path.path_statement)}</h3><div class="causal-chain">${[...r.work_path.source, ...r.work_path.transformations, ...r.work_path.target].map((step) => `<div class="causal-step">${escapeHtml(step)}</div>`).join("")}</div><p class="warning-line">失效条件：${escapeHtml(r.work_path.failure_conditions.join("；"))}</p></section>`;
}

function renderPublicBazi(r) {
  const portrait = (r.portrait || []).slice(0, 3);
  const summary = readingBaselineClaim(r);
  return `${renderJourneyStep({ id: "bazi-structure", index: "01", title: "长期结构", summary, className: "public-reading-lead", body: `<h3>${escapeHtml(summary)}</h3><p>${escapeHtml(cleanUserCopy(r.whole_chart_thesis || ""))}</p>` })}
    ${renderJourneyStep({ id: "bazi-pillars", index: "02", title: "命盘底图", summary: "四柱与藏干构成这份命局的基础", className: "pillar-story-section", body: `<h3>四柱与藏干</h3>${renderPillarSet(r.pillars)}` })}
    ${portrait.length ? renderJourneyStep({ id: "bazi-reality", index: "03", title: "现实表现", summary: cleanUserCopy(portrait[0]?.claim || "这些结构如何落到你身上"), body: `<div class="personal-observation-list">${portrait.map((item) => `<p>${escapeHtml(cleanUserCopy(item.claim))}</p>`).join("")}</div>` }) : ""}`;
}

function renderPillarSet(pillars = []) {
  return renderPillarSetWithNarration(pillars, "");
}

function renderPillarSetWithNarration(pillars = [], narrationAnchorPrefix = "") {
  const labels = ["年柱", "月柱", "日柱", "时柱"];
  return `<div class="mingli-pillars" aria-label="八字四柱">${pillars.slice(0, 4).map((pillar, index) => {
    const characters = Array.from(String(pillar || ""));
    const stem = characters[0] || "-";
    const branch = characters[1] || "-";
    const stemMeta = STEM_META[stem] || { element: "unknown", polarity: "unknown", nature: "天干" };
    const branchMeta = BRANCH_META[branch] || { element: "unknown", polarity: "unknown", nature: "地支", hidden: [] };
    const hidden = branchMeta.hidden.map((item) => {
      const meta = STEM_META[item] || { element: "unknown", polarity: "unknown" };
      return `<span class="hidden-stem element-${meta.element} polarity-${meta.polarity}">${escapeHtml(item)}</span>`;
    }).join("");
    const narrationAnchor = narrationAnchorPrefix ? `${narrationAnchorPrefix}-${index}` : "";
    return `<article class="mingli-pillar" ${narrationAnchor ? `data-narration-anchor="${escapeAttr(narrationAnchor)}" data-narration-jump="baseline-thesis" role="button" tabindex="0"` : ""}>
      <header><strong>${labels[index]}</strong><small>${escapeHtml(stemMeta.nature)} · ${escapeHtml(branchMeta.nature)}</small></header>
      <div class="pillar-glyphs">
        <span class="pillar-glyph pillar-stem element-${stemMeta.element} polarity-${stemMeta.polarity}"><small>天干</small><b>${escapeHtml(stem)}</b></span>
        <span class="pillar-glyph pillar-branch element-${branchMeta.element} polarity-${branchMeta.polarity}"><small>地支</small><b>${escapeHtml(branch)}</b></span>
      </div>
      <div class="hidden-stems"><small>藏干</small><span>${hidden || "—"}</span></div>
    </article>`;
  }).join("")}</div>`;
}

function renderZiwei() {
  const r = state.reading;
  const profile = r.ziwei_profile || {};
  const dual = r.dual_lens;
  if (!r.lenses_available?.ziwei || !dual) {
    const mismatch = (profile.warnings || []).includes("ziwei_bazi_pillar_mismatch");
    return `<section class="artifact-section lens-boundary"><p class="eyebrow">紫微 · 等待可靠资料</p><h3>${mismatch ? "这张测试盘不能叠加紫微" : "确认准确出生时辰后，Abu 才会开启紫微镜头"}</h3><p>${mismatch ? "当前生日与手写四柱不对应。为了不制造一张错误星盘，本轮只保留八字判断。" : "紫微对出生时辰敏感。Abu 不会用默认时辰补猜，也不会把不可靠结果包装成完整测算。"}</p></section>`;
  }
  if (["guest", "member"].includes(state.activeMode)) {
    const identity = cleanUserCopy(dual.identity_axis);
    const current = cleanUserCopy(dual.current_stage_note || "当前阶段仍需结合时序继续理解");
    return `${renderJourneyStep({ id: "ziwei-stage", index: "01", title: "人生舞台", summary: identity, className: "public-reading-lead", body: `<h3>${escapeHtml(identity)}</h3>` })}
      ${renderJourneyStep({ id: "ziwei-current", index: "02", title: "当前阶段", summary: current, className: "current-stage", body: `<h3>${escapeHtml(current)}</h3><p class="boundary-copy">紫微在这里补充现实舞台与阶段，不替代八字的长期结构。</p>` })}`;
  }
  const meta = [["命宫", profile.life_palace], ["身宫", profile.body_palace], ["五行局", profile.five_elements_class], ["命主 / 身主", `${profile.soul_star || "-"} / ${profile.body_star || "-"}`]];
  return `<section class="artifact-section lens-intro ziwei"><p class="eyebrow">紫微 · 人生舞台</p><h3>${escapeHtml(dual.ziwei_first_look)}</h3><p>${escapeHtml(dual.identity_axis)}</p><div class="ziwei-meta">${meta.map(([label, value]) => `<div><small>${label}</small><strong>${escapeHtml(value || "待确认")}</strong></div>`).join("")}</div></section>
    ${renderDeliberationWorkspace(["ziwei_focus"])}
    <section class="artifact-section"><p class="eyebrow">关键宫位</p><h3>只看真正改变理解的部分</h3>${dual.palace_observations.map((item) => `<div class="evidence-row"><strong>${escapeHtml(item.claim)}</strong><p>${escapeHtml(item.why_it_matters)}</p>${item.counter_conditions?.length ? `<p class="warning-line">若出现相反情况：${escapeHtml(item.counter_conditions.join("；"))}</p>` : ""}</div>`).join("")}</section>
    <section class="artifact-section"><p class="eyebrow">当前阶段</p><h3>${escapeHtml(dual.current_stage_note)}</h3><p class="boundary-copy">紫微时序在这里用于理解舞台变化，不用于承诺某件事一定发生。</p></section>`;
}

function renderGuestOverview(r) {
  const baseline = r.life_case?.baseline;
  const claim = readingBaselineClaim(r);
  return `${renderJourneyStep({ id: "baseline", index: "01", title: "看见命局", summary: claim, className: "public-reading-lead", body: renderNarratedBaselineWorkspace(r, baseline, { guest: true }) })}
    ${renderLatestRevision(r)}
    ${renderCurrentTemporalState(r)}
    ${renderJourneyStep({ id: "explore", index: "03", title: "继续探索", summary: "选择一个现在真正关心的人生问题", body: `<h3>选择一个你现在真正关心的人生问题</h3><p>事业、财富和人生阶段会在你选择后单独推演，并沿用这份整盘基线。</p><button class="primary-button" type="button" data-open-artifact="domains">选择人生主题</button>${renderProbe(r.probe_plan)}` })}`;
}

function renderMemberOverview(r) {
  const baseline = r.life_case?.baseline;
  const claim = readingBaselineClaim(r);
  return `${renderJourneyStep({ id: "baseline", index: "01", title: "看见命局", summary: claim, className: "public-reading-lead", body: renderNarratedBaselineWorkspace(r, baseline) })}
    ${renderLatestRevision(r)}
    ${renderCurrentTemporalState(r)}
    ${renderJourneyStep({ id: "explore", index: "03", title: "继续探索", summary: "从一个具体人生问题继续", body: `<h3>从一个具体人生问题继续</h3><p>事业、财富和人生阶段会在你选择后单独推演，并沿用这份整盘基线。</p><button class="primary-button" type="button" data-open-artifact="domains">选择人生主题</button>${r.probe_plan ? renderProbe(r.probe_plan) : ""}` })}`;
}

function renderNarratedBaselineWorkspace(reading, baseline, { guest = false } = {}) {
  const claim = readingBaselineClaim(reading);
  const condition = cleanUserCopy(baseline?.conditions?.[0] || "");
  const uncertainty = cleanUserCopy(baseline?.uncertainty?.reasons?.[0] || "");
  const path = reading.work_path || reading.public_work_path || {};
  const baselineReasoning = Array.isArray(baseline?.reasoning_path) ? baseline.reasoning_path : [];
  const baselineWorkPath = [...baselineReasoning].reverse().find((step) => String(step?.premise || "").includes("→"))
    || baselineReasoning[baselineReasoning.length - 1]
    || {};
  const pathStatement = cleanUserCopy(path.path_statement || baselineWorkPath.conclusion || "");
  const pathSteps = [...(path.source || []), ...(path.transformations || []), ...(path.target || [])]
    .map(cleanUserCopy)
    .filter(Boolean);
  const chapters = [
    ["baseline-thesis", "整盘重心", true],
    ["baseline-work_path", "主路径", Boolean(pathStatement)],
    ["baseline-condition", "关键条件", Boolean(condition)],
    ["baseline-uncertainty", "仍未写满", Boolean(uncertainty)],
  ].filter(([, , available]) => available);
  const pathMarkup = pathStatement ? `<div class="narration-source-block" data-narration-anchor="baseline-work-path" data-narration-jump="baseline-work_path" role="button" tabindex="0"><small>这张盘如何运行</small><p>${escapeHtml(pathStatement)}</p>${pathSteps.length ? `<div class="narration-path" aria-label="命局主路径">${pathSteps.slice(0, 6).map((step, index) => `${index ? '<i data-lucide="arrow-right"></i>' : ""}<span>${escapeHtml(step)}</span>`).join("")}</div>` : ""}</div>` : "";
  const conditionMarkup = condition ? `<div class="narration-source-block" data-narration-anchor="baseline-condition" data-narration-jump="baseline-condition" role="button" tabindex="0"><small>关键成立条件</small><p>${escapeHtml(condition)}</p></div>` : "";
  const uncertaintyMarkup = uncertainty ? `<div class="narration-source-block uncertainty" data-narration-anchor="baseline-uncertainty" data-narration-jump="baseline-uncertainty" role="button" tabindex="0"><small>仍需确认</small><p>${escapeHtml(uncertainty)}</p></div>` : "";
  return `<div class="narrated-workspace" data-narrated-workspace>
    <div class="narration-toolbar">
      <div><p class="eyebrow">阿布同步论命</p><p data-narration-status aria-live="polite">页面先到，声音由你决定。</p></div>
      <div class="narration-controls">
        <button class="narration-play" type="button" data-narration-start><i data-lucide="volume-2"></i><span>听阿布讲</span><small>约 1 分钟</small></button>
        <button type="button" data-narration-toggle hidden>暂停</button>
        <button type="button" data-narration-stop hidden>结束</button>
      </div>
    </div>
    <nav class="narration-chapters" aria-label="选择阿布讲解段落">${chapters.map(([id, label]) => `<button type="button" data-narration-jump="${escapeAttr(id)}">${escapeHtml(label)}</button>`).join("")}</nav>
    <div class="narration-stage">
      <div class="narration-thesis" data-narration-anchor="baseline-summary" data-narration-jump="baseline-thesis" role="button" tabindex="0"><h3>${escapeHtml(claim)}</h3></div>
      ${renderPillarSetWithNarration(reading.pillars, "baseline-pillar")}
      <div class="narration-source-grid">${pathMarkup}${conditionMarkup}${uncertaintyMarkup}</div>
    </div>
    ${renderVoiceStudyPanel()}
  </div>
  ${guest ? '<p class="boundary-copy">这是在不知道你现实经历前形成的整盘基线，后续可以被现实证据修正。</p>' : ""}`;
}

function renderVoiceStudyPanel() {
  if (!VOICE_STUDY_ENABLED) return "";
  return `<details class="voice-study-panel" data-voice-study-panel>
    <summary>完成本轮理解任务</summary>
    <form data-voice-study-form>
      <p data-voice-study-arm>正在准备本轮对照条件…</p>
      <label><span>请用自己的话说出整盘重心</span><textarea name="whole_chart_summary" maxlength="1000" required></textarea></label>
      <label><span>主路径从哪里开始，又走向哪里？</span><textarea name="work_path_summary" maxlength="1000" required></textarea></label>
      <label><span>这条判断成立的关键条件是什么？</span><textarea name="key_condition_summary" maxlength="1000" required></textarea></label>
      <label><span>系统目前仍不确定什么？</span><textarea name="uncertainty_summary" maxlength="1000" required></textarea></label>
      <label><span>你现在最自然想追问什么？（可选）</span><textarea name="natural_followup_question" maxlength="1000"></textarea></label>
      <div class="voice-study-ratings">
        <label><span>理解过程有多疲劳？</span><select name="fatigue_score" required><option value="">请选择</option><option value="1">1 · 很轻松</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5 · 很疲劳</option></select></label>
        <label><span>专业信任感变化</span><select name="professional_trust_delta" required><option value="">请选择</option><option value="2">明显提高</option><option value="1">略有提高</option><option value="0">没有变化</option><option value="-1">略有下降</option><option value="-2">明显下降</option></select></label>
        <label><span>是否愿意长期听这个声音？</span><select name="abu_long_term_listening_score" required><option value="">请选择</option><option value="5">5 · 很愿意</option><option value="4">4</option><option value="3">3</option><option value="2">2</option><option value="1">1 · 不愿意</option></select></label>
      </div>
      <label class="voice-study-consent"><input type="checkbox" name="consent_confirmed" required><span>同意将本轮理解回答作为私有研究记录；不记录出生资料。</span></label>
      <button class="primary-button" type="submit">提交理解记录</button>
      <p class="voice-study-status" data-voice-study-status aria-live="polite"></p>
    </form>
  </details>`;
}

function renderCurrentTemporalState(reading) {
  const timing = reading.temporal_state || {};
  const timingReading = reading.domain_explorations?.life_timing?.reading;
  const luck = timing.luck_pillar ? `${timing.luck_pillar}大运` : "大运资料待确认";
  const annual = timing.annual_pillar ? `${timing.analysis_year || "当前"} · ${timing.annual_pillar}年` : "当前年份资料已建立";
  const material = `${luck} · ${annual}`;
  const interpretation = cleanUserCopy(timingReading?.stable_tendencies?.[0] || timingReading?.timing_note || "");
  const selectedPeriod = timing.selected_period || resolveTimelinePeriod("current_month");
  const systemPeriod = timing.system_period || resolveTimelinePeriod("current_month");
  const snapshot = timing.selected_snapshot;
  const summary = cleanUserCopy(snapshot?.summary || interpretation || material);
  const previous = shiftPeriodKey(selectedPeriod, -1);
  const next = shiftPeriodKey(selectedPeriod, 1);
  const periodControls = `<div class="timeline-period-controls" aria-label="选择查看月份">
    <button type="button" data-timeline-period="${escapeAttr(previous)}"><i data-lucide="chevron-left"></i><span>上月</span></button>
    <button type="button" class="timeline-current-period" data-timeline-period="${escapeAttr(systemPeriod)}"><strong>${escapeHtml(selectedPeriod)}</strong><small>${selectedPeriod === systemPeriod ? "当前月" : "返回当前月"}</small></button>
    <button type="button" data-timeline-period="${escapeAttr(next)}"><span>下月</span><i data-lucide="chevron-right"></i></button>
  </div>`;
  const snapshotContext = snapshot
    ? `<div class="temporal-snapshot-note" data-perspective="${escapeAttr(snapshot.perspective)}"><strong>${escapeHtml(cleanUserCopy(snapshot.observation_theme))}</strong><p>${escapeHtml(cleanUserCopy(snapshot.summary))}</p></div>`
    : "";
  const review = snapshot?.perspective === "past"
    ? `<details class="monthly-review-panel"><summary>复盘这个月</summary><p>先比较当时的观察主题与现实记录，再决定是否形成案例修正候选。</p><div class="monthly-review-options">${[
        ["supported", "支持"],
        ["partially_supported", "部分支持"],
        ["not_observed", "未观察到"],
        ["contradicted", "形成反证"],
        ["insufficient_evidence", "证据不足"],
      ].map(([value, label]) => `<button type="button" data-monthly-verdict="${value}">${label}</button>`).join("")}</div></details>`
    : "";
  const body = interpretation
    ? `${periodControls}${snapshotContext}<h3>${escapeHtml(interpretation)}</h3><p>${escapeHtml(material)}</p><p class="boundary-copy">这是条件性的阶段理解，不代表某件事必然发生。</p><div class="temporal-actions"><button class="secondary-button" type="button" data-select-domain="life_timing">继续看阶段变化</button><button class="text-link" type="button" data-reality-record>记录这个月发生的事</button></div>${review}`
    : `${periodControls}${snapshotContext}<h3>${escapeHtml(material)}</h3><p>时间位置已经计算完成。阶段含义会在你选择后按需推演，不会提前套一份流年报告。</p><div class="temporal-actions"><button class="primary-button" type="button" data-select-domain="life_timing">理解当前阶段</button><button class="text-link" type="button" data-reality-record>记录这个月发生的事</button></div>${review}`;
  return renderJourneyStep({ id: "temporal", index: "02", title: "现在处于哪里", summary, className: "current-stage", body });
}

function shiftPeriodKey(periodKey, delta) {
  const [year, month] = String(periodKey).split("-").map(Number);
  const shifted = new Date(year, month - 1 + delta, 1);
  return `${shifted.getFullYear()}-${String(shifted.getMonth() + 1).padStart(2, "0")}`;
}

function readingBaselineClaim(reading) {
  return cleanUserCopy(
    reading?.life_case?.baseline?.claim
    || reading?.whole_chart_thesis
    || reading?.first_look
    || reading?.portrait?.[0]?.claim
    || "这张命盘的整盘主线仍在形成",
  );
}

function renderPublicBaselineContext(baseline) {
  if (!baseline) return "";
  const condition = cleanUserCopy(baseline.conditions?.[0] || "");
  const uncertainty = cleanUserCopy(baseline.uncertainty?.reasons?.[0] || "");
  return `${condition ? `<p><strong>关键成立条件：</strong>${escapeHtml(condition)}</p>` : ""}${uncertainty ? `<p class="boundary-copy"><strong>仍需确认：</strong>${escapeHtml(uncertainty)}</p>` : ""}`;
}

function renderJourneyStep({ id, index, title, summary, body, className = "" }) {
  const bodyId = `journey-step-${id}-body`;
  return `<section class="artifact-section journey-step ${className}" data-journey-step="${escapeAttr(id)}">
    <button class="journey-step-toggle" type="button" data-journey-step-toggle aria-expanded="false" aria-controls="${escapeAttr(bodyId)}">
      <span class="journey-step-number">${escapeHtml(index)}</span>
      <span class="journey-step-heading"><strong>${escapeHtml(title)}</strong><small>${escapeHtml(cleanUserCopy(summary))}</small></span>
      <span class="journey-step-action"><b data-journey-toggle-label>展开</b><i data-lucide="chevron-down"></i></span>
    </button>
    <div class="journey-step-body" id="${escapeAttr(bodyId)}" aria-hidden="true"><div class="journey-step-body-inner">${body}</div></div>
  </section>`;
}

function renderHypothesis(item) {
  return `<article class="hypothesis ${item.status === "primary" ? "primary" : ""}"><header><strong>${escapeHtml(item.name)}</strong><small>${item.status === "primary" ? "当前主假设" : "替代解释"} · ${confidenceLabel(item.confidence)}</small></header><p>${escapeHtml(item.thesis)}</p>${item.rejection_reason ? `<p class="warning-line">${escapeHtml(item.rejection_reason)}</p>` : ""}</article>`;
}

function renderDomainExploration(domain) {
  const exploration = state.reading.domain_explorations?.[domain];
  const d = exploration?.reading || state.reading[domain];
  const label = LIFE_DOMAIN_LABELS[domain] || "人生专题";
  if (!d) return `<section class="artifact-section domain-loading"><p class="eyebrow">${escapeHtml(label)}</p><h3>这个专题还没有展开</h3><p>让 Abu 从整盘认知出发，单独推演这里的因果关系。</p><button class="primary-button" type="button" data-select-domain="${escapeAttr(domain)}">开始探索</button></section>`;
  const publicMode = ["guest", "member"].includes(state.activeMode);
  const present = (value) => publicMode ? cleanUserCopy(value) : String(value || "").trim();
  const stable = (d.stable_tendencies || []).map(present).filter(Boolean);
  const helpful = [...new Set([...(d.opportunity_conditions || []), ...(d.favorable_environments || [])].map(present).filter(Boolean))].slice(0, publicMode ? 2 : 3);
  const risks = [...new Set([...(d.risk_conditions || []), ...(d.adverse_environments || [])].map(present).filter(Boolean))].slice(0, publicMode ? 2 : 3);
  const actions = (d.prior_directions || []).map(present).filter(Boolean).slice(0, publicMode ? 2 : 3);
  const summary = stable[0] || actions[0] || cleanUserCopy(d.core_question);
  if (publicMode) {
    const conditions = helpful.length
      ? `<div class="condition-column"><p class="eyebrow">更容易成立</p>${helpful.map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</div>`
      : `<div class="condition-column"><p>还需要更多现实信息，才能确认有利条件。</p></div>`;
    const failures = risks.length
      ? `<div class="condition-column"><p class="eyebrow">容易受阻</p>${risks.map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</div>`
      : `<div class="condition-column"><p>目前没有足够证据形成具体风险判断。</p></div>`;
    const nextBody = `${d.timing_note ? `<p>${escapeHtml(present(d.timing_note))}</p>` : ""}${actions.length ? `<div class="action-list">${actions.map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</div>` : ""}${state.reading.probe_plan ? renderProbe(state.reading.probe_plan) : ""}${exploration?.boundary ? `<p class="domain-boundary">${escapeHtml(exploration.boundary)}</p>` : ""}`;
    return `${renderJourneyStep({ id: `domain-${domain}-core`, index: "01", title: "核心判断", summary, className: "public-reading-lead domain-personal-summary", body: `<h3>${escapeHtml(summary)}</h3>${stable.slice(1, 2).map((item) => `<p>${escapeHtml(item)}</p>`).join("")}` })}
      ${renderJourneyStep({ id: `domain-${domain}-conditions`, index: "02", title: "何时成立，何时受阻", summary: helpful[0] || risks[0] || "查看影响这条路径的现实条件", className: "domain-guidance", body: `<div class="domain-guidance-compact">${conditions}${failures}</div>` })}
      ${renderJourneyStep({ id: `domain-${domain}-next`, index: "03", title: "现实方向", summary: actions[0] || d.timing_note || "回答一个问题，让判断更贴近现实", className: "domain-next-step", body: nextBody })}`;
  }
  const professional = ["practitioner", "research"].includes(state.activeMode)
    ? `<details class="professional-details"><summary>${state.activeMode === "research" ? "查看研究审阅" : "查看专业依据"}</summary><div class="causal-chain">${(d.causal_chain || []).map((step) => `<div class="causal-step">${escapeHtml(step)}</div>`).join("")}</div>${(d.unknowns || []).length ? `<p class="warning-line">仍需确认：${escapeHtml(d.unknowns.join("；"))}</p>` : ""}${state.activeMode === "research" && exploration?.review ? `<p>审阅观察 ${exploration.review.issues?.length || 0} 条 · 事实引用率 ${Math.round((exploration.review.fact_traceability_rate || 0) * 100)}%</p>` : ""}</details>`
    : "";
  return `<button class="text-link back-link domain-back" type="button" data-open-artifact="domains"><i data-lucide="arrow-left"></i> 返回主题选择</button>
    <section class="artifact-section domain-personal-summary"><p class="eyebrow">这部分的核心模式</p><h3>${escapeHtml(summary)}</h3>${stable.slice(1, 3).map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</section>
    <section class="artifact-section domain-guidance"><div><p class="eyebrow">对你有帮助</p>${helpful.map((item) => `<p>${escapeHtml(item)}</p>`).join("") || "<p>还需要更多现实信息才能判断。</p>"}</div><div><p class="eyebrow">需要留意</p>${risks.map((item) => `<p>${escapeHtml(item)}</p>`).join("") || "<p>目前没有足够证据形成具体提醒。</p>"}</div></section>
    ${d.timing_note ? `<section class="artifact-section current-stage"><p class="eyebrow">结合你现在的阶段</p><p>${escapeHtml(present(d.timing_note))}</p></section>` : ""}
    ${actions.length ? `<section class="artifact-section"><p class="eyebrow">可以尝试</p><div class="action-list">${actions.map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</div></section>` : ""}
    ${["practitioner", "research"].includes(state.activeMode) ? renderDeliberationWorkspace(["domain_assertion"]) : ""}
    ${state.reading.probe_plan ? `<section class="artifact-section">${renderProbe(state.reading.probe_plan)}</section>` : ""}
    ${exploration?.boundary ? `<p class="domain-boundary">${escapeHtml(exploration.boundary)}</p>` : ""}${professional}`;
}

function renderDomainMap() {
  const domains = (state.reading.life_domains || []).filter((item) => item.domain !== "whole_chart");
  const explored = state.reading.domain_explorations || {};
  return `<section class="artifact-section domain-map-intro"><p class="eyebrow">继续探索</p><h3>你此刻真正想看清什么？</h3><p>一次选择一个主题。Abu 会沿着同一份整盘理解继续，不会重新套一份报告。</p></section><section class="domain-map" aria-label="人生主题">${domains.map((item) => {
    const done = Boolean(explored[item.domain]);
    const publicMode = ["guest", "member"].includes(state.activeMode);
    const available = !publicMode || item.publicly_available;
    const description = done ? "继续上次的理解" : item.user_jobs?.[0] || "开始探索";
    if (!available) {
      const status = item.readiness === "research" ? "研究中" : "逐步开放";
      return `<article class="domain-map-item locked" aria-disabled="true"><span>${escapeHtml(item.name_zh)}</span><small>${escapeHtml(status)} · ${escapeHtml(item.boundary || "当前还不能负责任地公开断言")}</small><i data-lucide="lock-keyhole"></i></article>`;
    }
    return `<button type="button" class="domain-map-item ${done ? "explored" : ""}" data-select-domain="${escapeAttr(item.domain)}"><span>${escapeHtml(item.name_zh)}</span><small>${escapeHtml(description)}</small><i data-lucide="arrow-up-right"></i></button>`;
  }).join("")}</section>`;
}

function renderEvidence() {
  const r = state.reading;
  if (["guest", "member"].includes(state.activeMode)) {
    const publicEvidence = r.public_evidence || {};
    const primary = publicEvidence.primary_explanation;
    const alternatives = publicEvidence.alternative_explanations || [];
    const observations = publicEvidence.observations || [];
    const uncertainty = publicEvidence.uncertainties || [];
    const primaryBody = primary
      ? `<h3>${escapeHtml(cleanUserCopy(primary.thesis))}</h3>${(primary.success_conditions || []).slice(0, 2).map((item) => `<p>${escapeHtml(cleanUserCopy(item))}</p>`).join("")}${(primary.failure_conditions || []).length ? `<p class="warning-line">这条解释可能失效：${escapeHtml(cleanUserCopy(primary.failure_conditions[0]))}</p>` : ""}`
      : `<h3>当前还没有形成足够可靠的主解释。</h3>`;
    const alternativeBody = alternatives.length
      ? alternatives.slice(0, 2).map((item) => `<div class="evidence-row"><strong>${escapeHtml(humanizeHypothesisName(item.name))}</strong><p>${escapeHtml(cleanUserCopy(item.thesis))}</p>${item.rejection_reason ? `<p class="warning-line">目前没有优先采用：${escapeHtml(cleanUserCopy(item.rejection_reason))}</p>` : ""}</div>`).join("")
      : `<p>当前没有保留下足够可靠的替代解释，系统不会用套话补齐。</p>`;
    return `${renderJourneyStep({ id: "evidence-observations", index: "01", title: "盘面依据", summary: cleanUserCopy(observations[0]?.observation || "查看这份判断首先关注的盘面线索"), className: "public-reading-lead", body: observations.length ? observations.map((item) => `<div class="evidence-row"><strong>${escapeHtml(cleanUserCopy(item.observation))}</strong><p>${escapeHtml(cleanUserCopy(item.why_it_matters))}</p></div>`).join("") : "<p>当前还没有形成足够可靠的盘面依据。</p>" })}
      ${renderJourneyStep({ id: "evidence-primary", index: "02", title: "当前解释", summary: cleanUserCopy(primary?.thesis || "当前还没有形成足够可靠的主解释"), body: primaryBody })}
      ${renderJourneyStep({ id: "evidence-alternatives", index: "03", title: "其他解释与未知", summary: cleanUserCopy(uncertainty[0] || alternatives[0]?.thesis || "查看还有哪些地方不能确定"), body: `${alternativeBody}${uncertainty.length ? `<div class="uncertainty-list"><p class="eyebrow">仍需确认</p>${uncertainty.map((item) => `<p>${escapeHtml(cleanUserCopy(item))}</p>`).join("")}</div>` : ""}` })}`;
  }
  return `<section class="artifact-section"><p class="eyebrow">盘面重心</p><h3>为什么先看这里</h3>${r.salient_phenomena.map((item) => `<div class="evidence-row"><strong>${escapeHtml(item.observation)}</strong><p>${escapeHtml(item.why_it_matters)}</p></div>`).join("")}</section>
    <section class="artifact-section"><p class="eyebrow">用神逻辑</p><h3>不是缺什么补什么</h3>${r.useful_god_reasoning.map((item) => `<div class="evidence-row"><strong>${escapeHtml(item.candidate)} · ${escapeHtml(item.role)}</strong><p>${escapeHtml(item.why_useful)}</p><p class="warning-line">反而有害：${escapeHtml(item.when_harmful)}</p></div>`).join("")}</section>
    <section class="artifact-section"><p class="eyebrow">仍然未知</p><h3>Abu 不会装作已经知道</h3>${r.unresolved_questions.map((x) => `<div class="evidence-row"><p>${escapeHtml(x)}</p></div>`).join("")}</section>`;
}

function renderDeliberationWorkspace(stageIds = null) {
  const view = state.reading?.deliberation;
  if (!view || !["practitioner", "research"].includes(state.activeMode)) return "";
  const stages = stageIds ? view.stages.filter((stage) => stageIds.includes(stage.stage_id)) : view.stages.filter((stage) => stage.status !== "unavailable");
  if (!stages.length) return "";
  let active = stages.find((stage) => stage.stage_id === state.activeDeliberationStage);
  if (!active) active = stages.find((stage) => stage.status === "available") || stages.find((stage) => stage.status === "completed") || stages[0];
  state.activeDeliberationStage = active.stage_id;
  const canUndo = (view.active_selections || []).length > 0;
  const completed = Math.max(0, Number(view.progress_completed) || 0);
  const total = Math.max(1, Number(view.progress_total) || stages.length || 1);
  const progressPercent = Math.min(100, Math.round((completed / total) * 100));
  return `<section class="deliberation-workspace" aria-label="专业研判工作台">
    <header class="deliberation-header"><div><p class="eyebrow">${state.activeMode === "research" ? "研究分支工作台" : "专业研判工作台"}</p><h3>让判断沿着证据逐步成立</h3><p>${escapeHtml(view.support_disclaimer)}</p></div><div class="deliberation-progress" aria-label="已完成 ${completed} 个，共 ${total} 个研判步骤"><span>研判进度</span><strong><b>${completed}</b><small>/ ${total}</small></strong><div class="deliberation-progress-track"><i style="width:${progressPercent}%"></i></div>${canUndo ? `<button type="button" class="text-link" data-deliberation-undo>撤销最近选择</button>` : ""}</div></header>
    <nav class="deliberation-stage-nav" aria-label="研判步骤">${stages.map((stage, index) => `<button type="button" data-deliberation-stage="${escapeAttr(stage.stage_id)}" class="${stage.stage_id === active.stage_id ? "active" : ""} ${stage.status}"><b>${String(index + 1).padStart(2, "0")}</b><span>${escapeHtml(stage.title)}</span><small>${deliberationStatusLabel(stage.status)}</small></button>`).join("")}</nav>
    ${renderDeliberationStage(active)}
  </section>`;
}

function renderDeliberationStage(stage) {
  if (stage.status === "locked") return `<div class="deliberation-stage locked"><p class="eyebrow">当前步骤尚未开放</p><h3>${escapeHtml(stage.title)}</h3><p>${escapeHtml(stage.blocked_reason)}</p></div>`;
  if (stage.status === "unavailable") return `<div class="deliberation-stage locked"><p class="eyebrow">当前没有可用候选</p><h3>${escapeHtml(stage.title)}</h3><p>${escapeHtml(stage.blocked_reason)}</p></div>`;
  return `<div class="deliberation-stage" data-stage-key="${escapeAttr(stage.stage_key)}"><div class="deliberation-question"><p class="eyebrow">Abu 当前请你判断</p><h3>${escapeHtml(stage.question)}</h3><p>系统优先项仍然保留。你的选择只作用于当前案例。</p></div><div class="deliberation-options">${stage.options.map((option) => renderDeliberationOption(stage, option)).join("")}</div><label class="deliberation-rationale"><span>补充专业理由（可选）</span><textarea rows="2" maxlength="600" data-deliberation-rationale placeholder="记录你为什么沿这条分支继续；理由不会自动成为证据。"></textarea></label></div>`;
}

function renderDeliberationOption(stage, option) {
  const selection = (state.reading.deliberation.active_selections || []).find((item) => item.stage_key === stage.stage_key && item.option_id === option.option_id && item.action !== "research_fork");
  const supportLabel = option.support_kind === "relative_probability" ? `当前相对支持 ${option.support_percent}%` : `独立支持度 ${option.support_percent}/100`;
  const tags = [option.system_preferred ? "系统优先" : "候选", option.professionally_selected ? "当前案例选择" : "", option.research_forked ? "研究分支" : ""].filter(Boolean);
  const evidence = state.activeMode === "research" && option.evidence_refs?.length ? `<details class="deliberation-evidence"><summary>查看证据引用</summary><p>${escapeHtml(option.evidence_refs.join(" · "))}</p></details>` : "";
  return `<article class="deliberation-option ${option.professionally_selected ? "selected" : ""}"><header><div>${tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div><strong>${escapeHtml(supportLabel)}</strong></header><h4>${escapeHtml(option.label)}</h4><p>${escapeHtml(option.thesis)}</p><div class="deliberation-why"><div><small>为什么支持</small>${(option.support_reasons || []).slice(0, 2).map((item) => `<p>${escapeHtml(item)}</p>`).join("") || "<p>当前支持仍有限。</p>"}</div><div><small>主要反证</small>${(option.counter_reasons || []).slice(0, 2).map((item) => `<p>${escapeHtml(item)}</p>`).join("") || "<p>尚未发现强反证。</p>"}</div></div><p class="deliberation-impact"><strong>选择后重审：</strong>${escapeHtml((option.downstream_impacts || []).map(deliberationSurfaceLabel).join("、"))}</p>${evidence}<div class="deliberation-actions">${renderDeliberationActions(stage, option, selection)}</div></article>`;
}

function renderDeliberationActions(stage, option, selection) {
  const buttons = [];
  if (["exclusive", "attention"].includes(stage.selection_type)) {
    buttons.push(`<button type="button" class="primary-button" data-deliberation-option="${escapeAttr(option.option_id)}" data-deliberation-action="select" data-deliberation-stage-id="${escapeAttr(stage.stage_id)}" ${selection?.action === "select" ? "disabled" : ""}>${selection?.action === "select" ? "当前案例分支" : "沿此分支继续"}</button>`);
  } else {
    [["support", "支持"], ["challenge", "挑战"], ["defer", "暂缓"]].forEach(([action, label]) => buttons.push(`<button type="button" class="${action === "support" ? "primary-button" : "secondary-button"}" data-deliberation-option="${escapeAttr(option.option_id)}" data-deliberation-action="${action}" data-deliberation-stage-id="${escapeAttr(stage.stage_id)}" ${selection?.action === action ? "disabled" : ""}>${selection?.action === action ? `已${label}` : label}</button>`));
  }
  if (state.activeMode === "research") buttons.push(`<button type="button" class="text-link" data-deliberation-option="${escapeAttr(option.option_id)}" data-deliberation-action="research_fork" data-deliberation-stage-id="${escapeAttr(stage.stage_id)}" ${option.research_forked ? "disabled" : ""}>${option.research_forked ? "已保留研究分支" : "保留为研究分支"}</button>`);
  return buttons.join("");
}

function deliberationStatusLabel(status) { return ({ available: "待判断", locked: "有前置步骤", completed: "已选择", unavailable: "暂无证据" })[status] || status; }
function deliberationSurfaceLabel(value) { return ({ case_hypothesis: "命局主假设", useful_god_review: "用神逻辑", work_path_review: "主做功", domain_reading: "领域判断", timing_review: "时序判断", client_explanation: "客户解释", cross_lens_focus: "八字紫微交叉重心", next_probe: "下一条鉴别问题" })[value] || value; }

function renderProbe(probe) {
  if (!probe) return "";
  const professionalMode = ["practitioner", "research"].includes(state.activeMode);
  const professional = probe.professional_note ? `<p class="probe-note">${escapeHtml(probe.professional_note)}</p>` : "";
  const updates = state.activeMode === "research"
    ? `<details class="probe-update-preview"><summary>查看选项如何影响当前假设</summary>${probe.options.map((option) => { const changes = { ...(option.hypothesis_updates || {}), ...(option.assertion_updates || {}) }; return `<small><strong>${escapeHtml(option.label)}</strong>：${Object.entries(changes).map(([id, delta]) => `${escapeHtml(id)} ${beliefDeltaLabel(delta)}`).join("；") || "保留为独立观察"}</small>`; }).join("")}</details>`
    : "";
  const timelineFields = probe.response_shape === "timeline_choice"
    ? `<div class="timeline-probe-fields"><label><span>大约年份</span><input type="number" min="1900" max="2100" inputmode="numeric" data-probe-year value="${escapeAttr(probe.time_anchors?.[0] || "")}" placeholder="例如 2021"></label><label><span>类似情况出现次数</span><select data-probe-recurrence><option value="">不确定</option><option value="0">没有发生</option><option value="1">1 次</option><option value="2">2—3 次</option><option value="4">反复发生</option></select></label><label class="wide"><span>一句话补充（可选）</span><input maxlength="300" data-probe-note placeholder="只写发生了什么，不必提供敏感细节"></label></div>`
    : "";
  const context = professionalMode
    ? `<details class="probe-context"><summary>查看鉴别目的</summary><p>${escapeHtml(probe.purpose)}</p>${professional}${updates}</details>`
    : "";
  return `<div class="probe-panel" data-mode="${escapeAttr(state.activeMode)}"><p class="eyebrow">${probeHeading(state.activeMode)}</p><h3>${escapeHtml(cleanUserCopy(probe.question))}</h3>${timelineFields}<div class="probe-options">${probe.options.map((option) => `<button type="button" data-probe-option="${escapeAttr(option.option_id)}">${escapeHtml(cleanUserCopy(option.label))}</button>`).join("")}</div>${context}</div>`;
}

async function hydrateNarrationWorkspace() {
  const workspace = document.querySelector("[data-narrated-workspace]");
  const caseId = state.caseId;
  if (!workspace || !caseId) return null;
  if (state.narrationManifest && state.narrationManifestCaseId === caseId) {
    syncNarrationWorkspaceUi();
    return state.narrationManifest;
  }
  setNarrationStatus("正在核对可讲解的正式认知…");
  try {
    const body = await request(`${API.narration}/cases/${caseId}/baseline`);
    if (caseId !== state.caseId || !document.querySelector("[data-narrated-workspace]")) return null;
    state.narrationManifest = body.manifest;
    state.narrationManifestCaseId = caseId;
    state.narrationAssets = {};
    state.narrationAssetPromises = {};
    Object.entries(body.speech_assets || {}).forEach(([segmentId, asset]) => {
      if (asset.status === "ready" && asset.audio_url) {
        state.narrationAssets[segmentId] = {
          speech_asset_id: asset.speech_asset_id,
          media: { audio_url: asset.audio_url },
          cache_hit: true,
        };
      }
    });
    syncNarrationWorkspaceUi();
    if (VOICE_STUDY_ENABLED) await initializeVoiceValidation();
    return state.narrationManifest;
  } catch (_) {
    setNarrationStatus("页面内容完整可读；阿布语音暂时没有接上。");
    return null;
  }
}

function syncNarrationWorkspaceUi() {
  const manifest = state.narrationManifest;
  const workspace = document.querySelector("[data-narrated-workspace]");
  if (!manifest || !workspace) return;
  const segmentIds = new Set(manifest.segments.map((item) => item.segment_id));
  workspace.querySelectorAll("[data-narration-jump]").forEach((button) => {
    const segmentId = button.dataset.narrationJump;
    button.hidden = !segmentIds.has(segmentId);
  });
  const seconds = manifest.segments.reduce((total, item) => total + item.estimated_duration_seconds, 0);
  const duration = seconds < 60 ? `约 ${seconds} 秒` : `约 ${Math.ceil(seconds / 30) / 2} 分钟`;
  const durationNode = workspace.querySelector("[data-narration-start] small");
  if (durationNode) durationNode.textContent = duration;
  if (state.narrationStatus === "idle") setNarrationStatus("页面先到，声音由你决定。");
  applyVoiceStudyArm();
}

async function ensureNarrationAsset(segment) {
  if (state.narrationAssets[segment.segment_id]) return state.narrationAssets[segment.segment_id];
  if (state.narrationAssetPromises[segment.segment_id]) return state.narrationAssetPromises[segment.segment_id];
  const promise = request(`${API.narration}/cases/${state.caseId}/baseline/segments/${encodeURIComponent(segment.segment_id)}`, {
    method: "POST",
  }).then((body) => {
    state.narrationAssets[segment.segment_id] = { ...body.speech_asset, cache_hit: body.cache_hit };
    return state.narrationAssets[segment.segment_id];
  }).finally(() => {
    delete state.narrationAssetPromises[segment.segment_id];
  });
  state.narrationAssetPromises[segment.segment_id] = promise;
  return promise;
}

async function startNarration(segmentId = "") {
  const manifest = await hydrateNarrationWorkspace();
  if (!manifest?.segments?.length) return;
  if (state.voiceValidationSession?.arm === "text_only") {
    setNarrationStatus("本轮对照只阅读页面；完成后请提交你的理解。");
    return;
  }
  const requestedIndex = segmentId
    ? manifest.segments.findIndex((item) => item.segment_id === segmentId)
    : 0;
  const index = requestedIndex >= 0 ? requestedIndex : 0;
  const segment = manifest.segments[index];
  const plays = state.voiceValidationSegmentPlays[segment.segment_id] || 0;
  state.voiceValidationSegmentPlays[segment.segment_id] = plays + 1;
  void recordVoiceValidationEvent(segmentId ? (plays ? "chapter_replayed" : "chapter_jump") : "narration_requested", {
    segmentId: segment.segment_id,
  });
  stopNarration({ silent: true });
  const generation = ++state.narrationGeneration;
  state.abuPeekPinned = true;
  setAbuSurface("peek", { persist: false });
  await playNarrationSegment(index, generation);
}

async function playNarrationSegment(index, generation = state.narrationGeneration) {
  const manifest = state.narrationManifest;
  const segment = manifest?.segments?.[index];
  if (!segment || generation !== state.narrationGeneration) {
    if (manifest && index >= manifest.segments.length) finishNarration();
    return;
  }
  state.narrationIndex = index;
  state.narrationStatus = "generating";
  applyNarrationSegment(segment);
  updateNarrationControls();
  setNarrationStatus(`声音准备中 · ${segment.title}。页面可以继续看。`);
  showNarrationInAbu(segment, "正在讲这一段");
  state.voiceValidationRequestStartedAt = Date.now();
  try {
    const asset = await ensureNarrationAsset(segment);
    if (generation !== state.narrationGeneration) return;
    const preferredVariant = asset?.media?.playback_variants?.find((item) => item.format === "opus");
    const audioUrl = preferredVariant?.audio_url || asset?.media?.audio_url;
    if (!audioUrl) throw new Error("speech_asset_audio_missing");
    void recordVoiceValidationEvent("audio_ready", {
      segmentId: segment.segment_id,
      requestWaitMs: Math.max(0, Date.now() - state.voiceValidationRequestStartedAt),
      cacheHit: Boolean(asset.cache_hit),
    });
    const audio = new Audio(audioUrl);
    state.narrationAudio = audio;
    audio.preload = "auto";
    audio.addEventListener("play", () => {
      if (generation !== state.narrationGeneration) return;
      state.narrationStatus = "playing";
      void recordVoiceValidationEvent(audio.currentTime > 0 ? "playback_resumed" : "playback_started", {
        segmentId: segment.segment_id,
        playbackPositionMs: Math.round(audio.currentTime * 1000),
      });
      setNarrationStatus(`阿布正在讲 · ${segment.title}`);
      updateNarrationControls();
      const next = manifest.segments[index + 1];
      if (next) void ensureNarrationAsset(next).catch(() => undefined);
    });
    audio.addEventListener("pause", () => {
      if (generation !== state.narrationGeneration || audio.ended) return;
      state.narrationStatus = "paused";
      void recordVoiceValidationEvent("playback_paused", {
        segmentId: segment.segment_id,
        playbackPositionMs: Math.round(audio.currentTime * 1000),
      });
      setNarrationStatus(`已暂停 · ${segment.title}`);
      updateNarrationControls();
    });
    audio.addEventListener("ended", () => {
      if (generation !== state.narrationGeneration) return;
      state.narrationAudio = null;
      void playNarrationSegment(index + 1, generation);
    });
    audio.addEventListener("error", () => {
      if (generation !== state.narrationGeneration) return;
      narrationPlaybackFailed("这一段声音没有接上，页面内容仍然完整。");
    });
    try {
      await audio.play();
    } catch (_) {
      if (generation !== state.narrationGeneration) return;
      state.narrationStatus = "paused";
      setNarrationStatus("声音已经准备好，点“继续”开始播放。");
      updateNarrationControls();
    }
  } catch (_) {
    if (generation !== state.narrationGeneration) return;
    narrationPlaybackFailed("阿布语音暂时没有生成成功，页面内容不受影响。");
  }
}

function toggleNarrationPlayback() {
  const audio = state.narrationAudio;
  if (!audio) return;
  if (audio.paused) {
    void audio.play().catch(() => setNarrationStatus("浏览器没有允许播放，请再点一次继续。"));
  } else {
    audio.pause();
  }
}

function stopNarration({ silent = false } = {}) {
  const hadNarration = state.narrationStatus !== "idle" || Boolean(state.narrationAudio);
  const stoppedSegment = state.narrationManifest?.segments?.[state.narrationIndex];
  const stoppedAt = state.narrationAudio ? Math.round(state.narrationAudio.currentTime * 1000) : null;
  state.narrationGeneration += 1;
  if (state.narrationAudio) {
    state.narrationAudio.pause();
    state.narrationAudio.removeAttribute("src");
    state.narrationAudio.load();
  }
  state.narrationAudio = null;
  state.narrationIndex = -1;
  state.narrationStatus = "idle";
  clearNarrationVisuals();
  updateNarrationControls();
  if (hadNarration) {
    if (!silent) void recordVoiceValidationEvent("playback_stopped", {
      segmentId: stoppedSegment?.segment_id || "",
      playbackPositionMs: stoppedAt,
    });
    state.abuPeekPinned = false;
    el("abuPeekPreview").textContent = "";
    el("abuPeekPreview").hidden = true;
    setAbuState("idle", state.reading ? "在听你说" : "准备听你说");
    if (!silent) setNarrationStatus("讲解已经结束，页面仍可继续阅读。");
    scheduleAbuPeekCollapse();
  }
}

function finishNarration() {
  state.narrationAudio = null;
  state.narrationIndex = -1;
  state.narrationStatus = "complete";
  clearNarrationVisuals();
  updateNarrationControls();
  setNarrationStatus("这一幕讲完了。你可以点任意一段再听。");
  state.abuPeekPinned = false;
  el("abuPeekLabel").textContent = "Abu";
  el("abuPeekText").textContent = "这一幕讲完了";
  el("abuPeekPreview").textContent = "点页面上的任意一段，我可以从那里继续。";
  el("abuPeekPreview").hidden = false;
  setAbuState("completed", "这一幕讲完了");
  void recordVoiceValidationEvent("narration_completed");
  scheduleAbuPeekCollapse();
}

function narrationPlaybackFailed(message) {
  state.narrationAudio = null;
  state.narrationStatus = "error";
  state.abuPeekPinned = false;
  clearNarrationVisuals();
  setNarrationStatus(message);
  updateNarrationControls();
  setAbuState("caution", "声音暂时没有接上");
}

function setNarrationStatus(message) {
  document.querySelectorAll("[data-narration-status]").forEach((node) => { node.textContent = message; });
}

function updateNarrationControls() {
  const workspace = document.querySelector("[data-narrated-workspace]");
  if (!workspace) return;
  const start = workspace.querySelector("[data-narration-start]");
  const toggle = workspace.querySelector("[data-narration-toggle]");
  const stop = workspace.querySelector("[data-narration-stop]");
  const active = ["generating", "playing", "paused"].includes(state.narrationStatus);
  start.hidden = active;
  toggle.hidden = !["playing", "paused"].includes(state.narrationStatus);
  stop.hidden = !active;
  toggle.textContent = state.narrationStatus === "paused" ? "继续" : "暂停";
  workspace.querySelectorAll("[data-narration-jump]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.narrationJump === state.narrationManifest?.segments?.[state.narrationIndex]?.segment_id);
  });
}

function applyNarrationSegment(segment) {
  clearNarrationVisuals();
  segment.visual_anchor_ids.forEach((anchor) => focusNarrationAnchor(anchor, "focus"));
  segment.visual_cues.forEach((cue) => {
    const timer = window.setTimeout(() => focusNarrationAnchor(cue.target, cue.action), cue.at_ms);
    state.narrationCueTimers.push(timer);
  });
}

function focusNarrationAnchor(anchor, action) {
  document.querySelectorAll("[data-narration-anchor]").forEach((node) => {
    if (node.dataset.narrationAnchor !== anchor) return;
    node.classList.add("is-narration-active", `narration-${action}`);
    if (window.innerWidth <= 560 && !reducedMotion.matches) node.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}

function clearNarrationVisuals() {
  state.narrationCueTimers.forEach((timer) => window.clearTimeout(timer));
  state.narrationCueTimers = [];
  document.querySelectorAll("[data-narration-anchor]").forEach((node) => {
    ["is-narration-active", "narration-reveal", "narration-focus", "narration-pulse", "narration-flow", "narration-split", "narration-dim", "narration-sever", "narration-ghost", "narration-restore", "narration-compare"].forEach((name) => node.classList.remove(name));
  });
}

function showNarrationInAbu(segment, label) {
  state.abuPeekPinned = true;
  setAbuState("speaking", label);
  el("abuPeekLabel").textContent = "Abu 正在讲";
  el("abuPeekText").textContent = segment.title;
  el("abuPeekPreview").textContent = segment.text;
  el("abuPeekPreview").hidden = false;
  setAbuSurface("peek", { persist: false });
}

async function initializeVoiceValidation() {
  if (!VOICE_STUDY_ENABLED || !state.account || !state.caseId || !state.narrationManifest) return;
  if (state.voiceValidationSession?.case_id === state.caseId) {
    applyVoiceStudyArm();
    return;
  }
  const requestedArm = state.account.account_role === "admin"
    ? new URLSearchParams(window.location.search).get("voice_arm") || ""
    : "";
  try {
    const body = await request(`${API.voiceValidation}/sessions`, {
      method: "POST",
      body: JSON.stringify({ case_id: state.caseId, requested_arm: requestedArm }),
    });
    state.voiceValidationSession = body.session;
    state.voiceValidationStartedAt = Date.now();
    state.voiceValidationSegmentPlays = {};
    applyVoiceStudyArm();
    await recordVoiceValidationEvent("workspace_viewed");
  } catch (_) {
    const status = document.querySelector("[data-voice-study-status]");
    if (status) status.textContent = "本轮验证没有建立成功；正式页面与语音不受影响。";
  }
}

function applyVoiceStudyArm() {
  if (!VOICE_STUDY_ENABLED) return;
  const workspace = document.querySelector("[data-narrated-workspace]");
  const session = state.voiceValidationSession;
  if (!workspace || !session) return;
  workspace.dataset.voiceStudyArm = session.arm;
  const armCopy = workspace.querySelector("[data-voice-study-arm]");
  if (armCopy) armCopy.textContent = session.arm === "text_only"
    ? "本轮请只阅读页面，不开启语音；读懂后完成下面四项复述。"
    : "本轮可以使用阿布同步讲解；听到哪里、暂停和重播都会只记录为结构化事件。";
  if (session.arm === "text_only" && state.narrationStatus === "idle") {
    setNarrationStatus("本轮对照只阅读页面；完成后请提交你的理解。");
  }
}

async function recordVoiceValidationEvent(eventType, {
  segmentId = "",
  playbackPositionMs = null,
  requestWaitMs = null,
  cacheHit = null,
} = {}) {
  const session = state.voiceValidationSession;
  if (!VOICE_STUDY_ENABLED || !session) return;
  const event = {
    client_event_id: crypto.randomUUID?.() || `voice-event-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    event_type: eventType,
    occurred_at: new Date().toISOString(),
    elapsed_since_session_ms: Math.max(0, Date.now() - state.voiceValidationStartedAt),
    segment_id: segmentId,
    playback_position_ms: playbackPositionMs,
    request_wait_ms: requestWaitMs,
    cache_hit: cacheHit,
  };
  try {
    await request(`${API.voiceValidation}/sessions/${encodeURIComponent(session.session_id)}/events`, {
      method: "POST",
      body: JSON.stringify({ event }),
      keepalive: true,
    });
  } catch (_) {
    // Validation telemetry must never block the reading experience.
  }
}

async function submitVoiceStudyForm(form) {
  const session = state.voiceValidationSession;
  if (!session) return;
  const status = form.querySelector("[data-voice-study-status]");
  const data = new FormData(form);
  const submission = {
    submitted_at: new Date().toISOString(),
    consent_confirmed: data.get("consent_confirmed") === "on",
    whole_chart_summary: String(data.get("whole_chart_summary") || "").trim(),
    work_path_summary: String(data.get("work_path_summary") || "").trim(),
    key_condition_summary: String(data.get("key_condition_summary") || "").trim(),
    uncertainty_summary: String(data.get("uncertainty_summary") || "").trim(),
    natural_followup_question: String(data.get("natural_followup_question") || "").trim(),
    fatigue_score: Number(data.get("fatigue_score")),
    professional_trust_delta: Number(data.get("professional_trust_delta")),
    abu_long_term_listening_score: Number(data.get("abu_long_term_listening_score")),
  };
  status.textContent = "正在保存本轮理解记录…";
  form.querySelector("button[type='submit']").disabled = true;
  try {
    await recordVoiceValidationEvent("comprehension_submitted");
    await request(`${API.voiceValidation}/sessions/${encodeURIComponent(session.session_id)}/comprehension`, {
      method: "POST",
      body: JSON.stringify({ submission }),
    });
    status.textContent = "本轮记录已锁定。谢谢你帮助我们确认阿布是否真的讲清楚。";
    form.querySelectorAll("textarea, select, input, button").forEach((node) => { node.disabled = true; });
  } catch (_) {
    status.textContent = "记录暂时没有保存，请稍后再试。";
    form.querySelector("button[type='submit']").disabled = false;
  }
}

function bindArtifactActions() {
  document.querySelectorAll("[data-narration-start]").forEach((button) => button.addEventListener("click", () => void startNarration()));
  document.querySelectorAll("[data-narration-toggle]").forEach((button) => button.addEventListener("click", toggleNarrationPlayback));
  document.querySelectorAll("[data-narration-stop]").forEach((button) => button.addEventListener("click", () => stopNarration()));
  document.querySelectorAll("[data-narration-jump]").forEach((button) => {
    button.addEventListener("click", () => void startNarration(button.dataset.narrationJump));
    if (button.getAttribute("role") === "button") button.addEventListener("keydown", (event) => {
      if (!["Enter", " "].includes(event.key)) return;
      event.preventDefault();
      void startNarration(button.dataset.narrationJump);
    });
  });
  document.querySelectorAll("[data-voice-study-panel]").forEach((panel) => panel.addEventListener("toggle", () => {
    if (panel.open) void recordVoiceValidationEvent("comprehension_opened");
  }));
  document.querySelectorAll("[data-voice-study-form]").forEach((form) => form.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitVoiceStudyForm(form);
  }));
  document.querySelectorAll("[data-deliberation-stage]").forEach((button) => button.addEventListener("click", () => {
    state.activeDeliberationStage = button.dataset.deliberationStage;
    showArtifact(state.activeArtifact);
  }));
  if (state.readOnlyCase) {
    document.querySelectorAll("[data-open-artifact], [data-select-domain], [data-probe-option], [data-deliberation-option], [data-deliberation-undo], [data-timeline-period], [data-reality-record], [data-monthly-verdict]").forEach((button) => {
      button.disabled = true;
      button.title = "历史案例只读";
    });
    return;
  }
  document.querySelectorAll("[data-open-artifact]").forEach((button) => button.addEventListener("click", () => executeProductAction("OPEN_LENS", { lens: button.dataset.openArtifact })));
  document.querySelectorAll("[data-select-domain]").forEach((button) => button.addEventListener("click", () => executeProductAction("OPEN_DOMAIN", { domain: button.dataset.selectDomain })));
  document.querySelectorAll("[data-probe-option]").forEach((button) => button.addEventListener("click", () => respondToProbe(button.dataset.probeOption)));
  document.querySelectorAll("[data-deliberation-option]").forEach((button) => button.addEventListener("click", () => applyDeliberationChoice(button)));
  document.querySelectorAll("[data-deliberation-undo]").forEach((button) => button.addEventListener("click", undoDeliberationChoice));
  document.querySelectorAll("[data-timeline-period]").forEach((button) => button.addEventListener("click", () => selectTimelinePeriod(button.dataset.timelinePeriod)));
  document.querySelectorAll("[data-reality-record]").forEach((button) => button.addEventListener("click", () => {
    setAbuSurface("open");
    focusComposer("记录：", "reality.record");
  }));
  document.querySelectorAll("[data-monthly-verdict]").forEach((button) => button.addEventListener("click", () => submitMonthlyReview(button.dataset.monthlyVerdict)));
}

async function submitMonthlyReview(verdict) {
  const snapshot = state.reading?.temporal_state?.selected_snapshot;
  if (!state.caseId || !snapshot || state.busy) return;
  setBusy(true, "正在整理月度复盘");
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/monthly-review`, {
      method: "POST",
      body: JSON.stringify({
        period_key: snapshot.period_key,
        temporal_snapshot_id: snapshot.snapshot_id,
        evidence_refs: snapshot.reality_evidence_refs || [],
        verdict,
      }),
    });
    await addTypedMessage("abu", `${body.monthly_review.system_summary}。我已经形成一条案例修正候选，但还没有自动写入。`, "Abu");
    setQuickActions([
      ["确认写入案例版本", () => commitMonthlyRevision(body.candidate.candidate_id)],
      ["先保留候选", () => setQuickActions([])],
    ]);
  } catch (error) {
    await addTypedMessage("abu", friendlyError(error, "这次月度复盘没有完成，原有认知没有改变。"), "Abu");
  } finally {
    setBusy(false);
  }
}

async function commitMonthlyRevision(candidateId) {
  if (!state.caseId || !candidateId || state.busy) return;
  setBusy(true, "正在提交案例修正");
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/case-revisions/commit`, {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId }),
    });
    await restoreCase(state.caseId, true);
    await addTypedMessage("abu", `案例理解已经更新为 ${body.case_version}。旧版本仍保留，出生资料和原局事实没有改变。`, "Abu");
    setAbuState("confidence_up", "案例版本已更新");
  } catch (error) {
    await addTypedMessage("abu", friendlyError(error, "案例修正没有提交，原版本仍然有效。"), "Abu");
  } finally {
    setBusy(false);
  }
}

async function applyDeliberationChoice(button) {
  if (!state.caseId || state.busy || !["practitioner", "research"].includes(state.activeMode)) return;
  const stage = button.closest(".deliberation-stage");
  const rationale = stage?.querySelector("[data-deliberation-rationale]")?.value?.trim() || "";
  const activeDomain = LIFE_DOMAIN_LABELS[state.activeArtifact] && state.activeArtifact !== "whole_chart" ? state.activeArtifact : "whole_chart";
  setBusy(true, "正在检查分支依赖");
  setAbuState("thinking", "正在复核这条分支");
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/deliberation/select`, {
      method: "POST",
      body: JSON.stringify({
        active_mode: state.activeMode,
        stage_id: button.dataset.deliberationStageId,
        option_id: button.dataset.deliberationOption,
        action: button.dataset.deliberationAction,
        active_domain: activeDomain,
        rationale,
      }),
    });
    state.reading = body.reading;
    state.workspaceState = body.reading?.workspace_state || state.workspaceState;
    state.activeDeliberationStage = body.receipt.next_stage_id || button.dataset.deliberationStageId;
    renderReading();
    showRevisionNotice({ summary: body.receipt.revision.summary });
    const nextLabel = deliberationStageLabel(body.receipt.next_stage_id);
    await addTypedMessage("abu", `${body.receipt.revision.summary}${nextLabel ? `\n\n下一步：${nextLabel}。` : ""}`, "Abu");
    setAbuState("wave", "案例研判已更新");
  } catch (error) {
    await addTypedMessage("abu", deliberationErrorMessage(error), "Abu");
    showArtifact(state.activeArtifact);
  } finally {
    setBusy(false);
  }
}

async function undoDeliberationChoice() {
  if (!state.caseId || state.busy || !["practitioner", "research"].includes(state.activeMode)) return;
  const activeDomain = LIFE_DOMAIN_LABELS[state.activeArtifact] && state.activeArtifact !== "whole_chart" ? state.activeArtifact : "whole_chart";
  setBusy(true, "正在撤销最近选择");
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/deliberation/undo`, {
      method: "POST",
      body: JSON.stringify({ active_mode: state.activeMode, active_domain: activeDomain }),
    });
    state.reading = body.reading;
    state.workspaceState = body.reading?.workspace_state || state.workspaceState;
    state.activeDeliberationStage = body.receipt.next_stage_id || "pattern";
    renderReading();
    await addTypedMessage("abu", body.receipt.revision.summary, "Abu");
  } catch (error) {
    await addTypedMessage("abu", deliberationErrorMessage(error), "Abu");
  } finally {
    setBusy(false);
  }
}

function deliberationErrorMessage(error) {
  if (error?.message?.includes("prerequisite")) return "这一步依赖前面的命局判断。先完成当前开放的研判步骤，再继续这里。";
  if (error?.message?.includes("option_stale")) return "这条候选已经过期。我已保留原有判断，请重新打开当前步骤。";
  if (error?.message?.includes("not_allowed") || error?.status === 403) return "当前账户没有执行这项专业研判的权限。";
  if (error?.message?.includes("nothing_to_undo")) return "当前没有可以撤销的专业选择。";
  return "这次专业选择没有写入案例，原有命盘和判断保持不变。";
}

function deliberationStageLabel(stageId) { return ({ pattern: "确认整体命局假设", useful_god: "比较体用与用神", work_path: "审阅主做功", ziwei_focus: "选择紫微交叉重心", domain_assertion: "审阅领域断言" })[stageId] || ""; }

async function respondToProbe(optionId) {
  if (!state.reading?.probe_plan || state.busy) return;
  const plan = state.reading.probe_plan;
  const selected = plan.options.find((item) => item.option_id === optionId);
  if (!selected) return;
  const panel = document.querySelector(".probe-panel");
  const yearValue = panel?.querySelector("[data-probe-year]")?.value;
  const eventNote = panel?.querySelector("[data-probe-note]")?.value?.trim() || "";
  const recurrenceValue = panel?.querySelector("[data-probe-recurrence]")?.value;
  if (panel) {
    const probeSection = panel.closest(".artifact-section");
    if (probeSection && probeSection.querySelectorAll(":scope > *").length === 1) probeSection.remove();
    else panel.remove();
  }
  setBusy(true, "正在更新这张盘的理解");
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/probe-respond`, {
      method: "POST",
      body: JSON.stringify({
        plan_id: plan.plan_id,
        option_id: optionId,
        active_mode: state.activeMode,
        scenario: plan.scenario,
        domain: plan.domain,
        year_value: yearValue ? Number(yearValue) : null,
        event_note: eventNote,
        recurrence_count: recurrenceValue === "" || recurrenceValue == null ? null : Number(recurrenceValue),
      }),
    });
    state.reading = {
      ...body.reading,
      latest_revision: body.revision || body.reading?.latest_revision || null,
    };
    state.workspaceState = body.reading?.workspace_state || state.workspaceState;
    renderReading();
    showRevisionNotice(state.reading.latest_revision);
    setQuickActions([]);
    setAbuState("confidence_up", "已修正当前理解");
  } catch (error) {
    showArtifact(state.activeArtifact);
    await addTypedMessage("abu", friendlyError(error, "这条回答暂时没有记录成功，原有判断不会被改写。"), "Abu");
  } finally {
    setBusy(false);
  }
}

function showRevisionNotice(revision) {
  if (!revision) return;
  document.querySelector(".revision-toast")?.remove();
  const notice = document.createElement("aside");
  notice.className = "revision-toast";
  notice.innerHTML = `<i data-lucide="check"></i><div><strong>命局理解已修正</strong><span>${escapeHtml(revision.summary || "现实线索已进入当前案例。")}</span></div>`;
  document.body.appendChild(notice);
  refreshIcons();
  setTimeout(() => notice.classList.add("leaving"), 5200);
  setTimeout(() => notice.remove(), 5700);
}

async function selectDomain(domain) {
  if (!state.reading) return;
  if (domain === "whole_chart") return showArtifact("overview");
  const label = LIFE_DOMAIN_LABELS[domain] || "这个领域";
  const existing = state.reading.domain_explorations?.[domain];
  setBusy(true, existing ? `正在恢复${label}` : `Abu 正在推演${label}`);
  setAbuState(existing ? "idle" : "thinking", existing ? `正在接上${label}` : `正在看${label}`);
  showDomainLoading(label, existing);
  let hasActiveProbe = false;
  let progressiveStarted = false;
  try {
    const body = await request(`${API.agent}/cases/${state.caseId}/domains/${domain}`, {
      method: "POST",
      body: JSON.stringify({ active_mode: state.activeMode, user_question: "", progressive: true }),
    });
    if (body.status === "domain_job_started") {
      progressiveStarted = true;
      state.jobId = body.job_id;
      localStorage.setItem("deepbazi.cognitive_job_id", body.job_id);
      localStorage.setItem("deepbazi.cognitive_job_sequence", "0");
      await pollCognitiveJob(body.job_id);
      return;
    }
    state.reading = body.reading;
    state.workspaceState = body.reading?.workspace_state || state.workspaceState;
    if (body.status !== "domain_exploration_ready") {
      stopThinkingPreview();
      showDomainReliabilityOutcome(label, body.domain_outcome || {});
      const revision = body.status === "case_revision_candidate";
      await addTypedMessage("abu", revision
        ? `${label}专题发现了一处可能需要修正整盘基线的分歧。我先保留为修正候选，没有悄悄覆盖原判断。`
        : `${label}专题目前仍有竞争解释或没有通过一致性检查，所以没有写入正式案例。`, "Abu");
      setQuickActions([["返回当前命局", () => showArtifact("overview")], ["稍后重试", () => selectDomain(domain)]]);
      return;
    }
    state.pendingPrimaryTypewriter = !existing;
    stopThinkingPreview();
    showArtifact(domain);
    const question = state.reading.domain_explorations?.[domain]?.reading?.core_question;
    const activeProbe = state.reading.probe_plan;
    hasActiveProbe = Boolean(activeProbe);
    await addTypedMessage("abu", question && activeProbe ? `${label}专题已经形成。下面这个问题能帮助我区分两种解释。` : `${label}专题已经形成，当前不需要继续追问。`, "Abu");
    setQuickActions(activeProbe
      ? [["回答区分问题", () => document.querySelector(".probe-panel")?.scrollIntoView({ behavior: "smooth", block: "center" })], ["返回人生地图", () => showArtifact("domains")]]
      : [["返回人生地图", () => showArtifact("domains")]]);
  } catch (error) {
    stopThinkingPreview();
    await addTypedMessage("abu", friendlyError(error, `${label}这一轮暂时没有完成。整盘已有判断仍然保留，你可以稍后继续。`), "Abu");
    showArtifact("domains");
  } finally {
    if (!progressiveStarted) {
      setBusy(false);
      setAbuState(hasActiveProbe ? "probe" : "idle", hasActiveProbe ? "想确认一件关键的事" : "在听你说");
    }
  }
}

function showDomainReliabilityOutcome(label, outcome = {}) {
  el("welcomeScene").hidden = true;
  el("thinkingScene").hidden = true;
  el("failureScene").hidden = true;
  el("readingCanvas").hidden = false;
  el("readingTabs").hidden = true;
  el("readingEyebrow").textContent = `${label} · 暂未提交`;
  el("readingTitle").textContent = outcome.case_revision_candidate ? "专题发现了需要复核的整盘分歧" : "这一专题暂时没有形成可靠判断";
  const issues = outcome.issues || [];
  el("artifactContent").innerHTML = `<section class="artifact-section reliability-state ${outcome.state || "blocked"}">
    <p class="eyebrow">${outcome.state === "competing" ? "存在竞争解释" : "一致性检查未通过"}</p>
    <h3>${outcome.case_revision_candidate ? "原有基线保持不变，新的解释只作为修正候选。" : "Abu 没有用通用文字补成一份专题报告。"}</h3>
    ${outcome.case_revision_candidate?.reason ? `<p>${escapeHtml(cleanUserCopy(outcome.case_revision_candidate.reason))}</p>` : ""}
    ${issues.length ? `<details class="reading-details"><summary>查看为什么没有提交</summary>${issues.slice(0, 5).map((item) => `<p>${escapeHtml(cleanUserCopy(item.message || item.code))}</p>`).join("")}</details>` : ""}
    <button class="secondary-button" type="button" data-open-artifact="overview">返回当前命局</button>
  </section>`;
  decoratePublicArtifact();
  if (window.innerWidth <= 960) showCanvas();
  refreshIcons();
}

const LIFE_DOMAIN_LABELS = {
  whole_chart: "整盘命局",
  self: "自我与性情",
  talent_learning: "天赋与学习",
  career: "事业与职业",
  wealth: "财富与资源",
  relationship: "亲密关系",
  family: "家庭与原生关系",
  children_legacy: "子女与传承",
  health_vitality: "健康与生命力",
  social_network: "社交与合作",
  migration_environment: "迁移与环境",
  life_timing: "人生阶段与时机",
};

function showDomainGuide() {
  addMessage("abu", "我会先理解整张命盘，再按你的真实问题进入人生专题。\n\n可以探索自我、天赋、事业、财富、关系、家庭、传承、生命力、合作、环境与人生阶段。部分专题仍有严格边界，我会明确告诉你哪里能判断、哪里不能。", "Abu");
  setQuickActions([
    ["打开人生地图", () => state.reading ? showArtifact("domains") : focusComposer("告诉 Abu 你的出生信息")],
    ["我想问一个具体问题", () => messageInput.focus()],
  ]);
}

async function restoreAccount() {
  try {
    const body = await request(`${API.product}/auth/me`);
    state.account = body.account;
    state.activeMode = state.account.account_role === "admin"
      ? localStorage.getItem("deepbazi.experience_mode") || "member"
      : defaultModeForRole(state.account.account_role);
    el("accountLabel").textContent = state.account.display_name;
    el("casebookButton").hidden = false;
    el("privacyNote").hidden = true;
  } catch (_) {
    state.account = null;
    state.profiles = [];
    state.activeProfile = null;
    state.activeMode = "guest";
    el("accountLabel").textContent = "登录";
    el("privacyNote").hidden = false;
  }
}

async function submitAuth(event) {
  event.preventDefault();
  const data = new FormData(el("authForm"));
  const payload = { email: data.get("email"), password: data.get("password") };
  if (state.authMode === "register") Object.assign(payload, { display_name: data.get("display_name"), role: data.get("role") });
  el("authError").textContent = "";
  try {
    const body = await request(`${API.product}/auth/${state.authMode}`, { method: "POST", body: JSON.stringify(payload) });
    state.account = body.account;
    state.activeMode = state.account.account_role === "admin" ? "member" : defaultModeForRole(state.account.account_role);
    el("accountLabel").textContent = state.account.display_name;
    el("privacyNote").hidden = true;
    el("casebookButton").hidden = false;
    el("authDialog").close();
    if (state.caseId) {
      const claimed = await request(`${API.agent}/cases/${state.caseId}/claim`, { method: "POST" });
      if (claimed.profile) syncActiveProfile(claimed.profile);
    }
    await refreshProfiles({ selectDefault: !state.activeProfile });
    addMessage("abu", `已经保存好了，${state.account.display_name}。以后回来，我会从这份命理档案继续。`, "Abu");
  } catch (error) {
    el("authError").textContent = friendlyError(error, "登录没有完成，请检查邮箱和密码。");
  }
}

function setAuthMode(mode) {
  state.authMode = mode;
  document.querySelectorAll("[data-auth-mode]").forEach((button) => button.classList.toggle("active", button.dataset.authMode === mode));
  document.querySelectorAll(".register-only").forEach((node) => node.hidden = mode !== "register");
  el("authTitle").textContent = mode === "register" ? "建立你的 DeepBazi 账户" : "登录 DeepBazi";
  el("authSubmit").textContent = mode === "register" ? "注册并保存" : "登录并继续";
}

async function refreshProfiles({ selectDefault = false } = {}) {
  if (!state.account) return [];
  const body = await request(`${API.product}/profiles`);
  state.profiles = body.profiles || [];
  const storedId = localStorage.getItem("deepbazi.active_profile_id");
  const selected = state.profiles.find((item) => item.profile_id === state.activeProfile?.profile_id)
    || state.profiles.find((item) => item.profile_id === storedId)
    || state.profiles.find((item) => (
      item.profile_fingerprint === state.activeProfile?.profile_fingerprint
      && item.display_name === state.activeProfile?.display_name
    ))
    || (selectDefault ? state.profiles.find((item) => item.is_default) || state.profiles[0] : null);
  if (selected) syncActiveProfile(selected);
  return state.profiles;
}

function syncActiveProfile(profile) {
  if (!profile) return;
  state.activeProfile = profile;
  localStorage.setItem("deepbazi.active_profile_id", profile.profile_id);
  setBirthDraft(profileDraft(profile));
  updateCaseHeader();
  messageInput.placeholder = state.reading
    ? "问阿布这份命局里你真正关心的事"
    : "说“开始看盘”，或告诉阿布你想理解的问题";
  if (!state.reading && !state.busy) showWelcome();
}

function syncCaseContext(context) {
  if (context.profile) syncActiveProfile(context.profile);
  else if (context.birth_input) setBirthDraft(draftFromBirthInput(context.birth_input));
}

function profileDraft(profile) {
  return {
    name: profile.display_name || "我的命盘",
    gender: profile.gender || "male",
    calendar_type: profile.calendar_type || "solar",
    birth_date: profile.birth_date || "1990-01-01",
    birth_time: profile.birth_time || "12:00",
    birth_location: profile.birth_location || "首尔",
    timezone: profile.timezone || "Asia/Seoul",
    time_precision: (profile.warnings || []).includes("birth_time_approximate") ? "approximate" : "exact",
    missing_fields: [],
    clarification_question: "",
    ready_for_confirmation: true,
  };
}

function draftFromBirthInput(birthInput) {
  return profileDraft({
    display_name: birthInput.name,
    ...birthInput,
  });
}

function setBirthDraft(draft) {
  state.birthDraft = draft || null;
  if (draft) sessionStorage.setItem("deepbazi.birth_draft", JSON.stringify(draft));
  else sessionStorage.removeItem("deepbazi.birth_draft");
}

async function saveBirthProfile(birthInput, profileId = "") {
  const url = profileId ? `${API.product}/profiles/${profileId}` : `${API.product}/profiles`;
  const body = await request(url, {
    method: profileId ? "PUT" : "POST",
    body: JSON.stringify({ birth_input: birthInput }),
  });
  const profile = body.profile;
  const existingIndex = state.profiles.findIndex((item) => item.profile_id === profile.profile_id);
  if (existingIndex >= 0) state.profiles.splice(existingIndex, 1, profile);
  else state.profiles.unshift(profile);
  syncActiveProfile(profile);
  return profile;
}

async function saveProfileFromDialog(draft) {
  const submit = el("birthFormSubmit");
  submit.disabled = true;
  el("birthFormError").textContent = "";
  try {
    const previousProfileId = state.activeProfile?.profile_id || "";
    const formMode = state.profileFormMode;
    const profile = await saveBirthProfile(
      birthInputFromDraft(draft),
      formMode === "edit" ? state.editingProfileId : "",
    );
    const changedCurrent = Boolean(state.caseId && (formMode === "edit" || previousProfileId !== profile.profile_id));
    el("birthDialog").close();
    state.profileFormMode = "intake";
    state.editingProfileId = "";
    if (changedCurrent) clearCurrentReading();
    addMessage("abu", `${profile.display_name}已经保存并设为当前档案。${changedCurrent ? "出生信息发生了变化，旧测算不会继续套用。" : "不需要再告诉我一次出生信息。"}`, "Abu");
    setQuickActions([["用当前档案开始看盘", () => startCase({ profile_id: profile.profile_id })], ["管理命理档案", openCasebook]]);
    setAbuState("completed", "档案已经保存");
    await openCasebook();
  } catch (error) {
    el("birthFormError").textContent = friendlyError(error, "档案没有保存成功，请检查日期、时间、历法和地点。 ");
  } finally {
    submit.disabled = false;
  }
}

function renderProfileArchiveCard(profile) {
  const isActive = profile.profile_id === state.activeProfile?.profile_id;
  const gender = profile.gender === "female" ? "女" : profile.gender === "male" ? "男" : "未注明";
  const calendar = profile.calendar_type === "lunar" ? "农历" : "公历";
  return `<article class="profile-archive-card${isActive ? " active" : ""}">
    <button class="profile-card-main" type="button" data-profile-use="${escapeAttr(profile.profile_id)}">
      <span class="profile-card-title"><strong>${escapeHtml(profile.display_name)}</strong>${isActive ? "<em>当前</em>" : ""}</span>
      <span>${escapeHtml((profile.pillars || []).filter(Boolean).join(" · "))}</span>
      <small>${calendar} ${escapeHtml(profile.birth_date)} ${escapeHtml(profile.birth_time)} · ${gender} · ${escapeHtml(profile.birth_location || "出生地未记录")}</small>
      <b>${isActive ? "重新看盘" : "选择并看盘"}<i data-lucide="arrow-right"></i></b>
    </button>
    <div class="profile-card-actions">
      <button class="icon-button" type="button" data-profile-edit="${escapeAttr(profile.profile_id)}" title="编辑${escapeAttr(profile.display_name)}"><i data-lucide="pencil"></i></button>
      <button class="icon-button danger" type="button" data-profile-delete="${escapeAttr(profile.profile_id)}" title="删除${escapeAttr(profile.display_name)}"><i data-lucide="trash-2"></i></button>
    </div>
  </article>`;
}

async function useProfileForReading(profileId) {
  const profile = state.profiles.find((item) => item.profile_id === profileId);
  if (!profile) return;
  syncActiveProfile(profile);
  clearCurrentReading();
  el("casebookDialog").close();
  addMessage("abu", `已经切换到${profile.display_name}。出生信息和四柱都已确认，我现在直接开始看盘。`, "Abu");
  await startCase({ profile_id: profile.profile_id });
}

function openProfileCreateDialog() {
  if (el("casebookDialog").open) el("casebookDialog").close();
  configureProfileDialog("create");
}

function openProfileEditDialog(profileId) {
  const profile = state.profiles.find((item) => item.profile_id === profileId);
  if (!profile) return;
  if (el("casebookDialog").open) el("casebookDialog").close();
  configureProfileDialog("edit", profile);
}

function configureProfileDialog(mode, profile = null) {
  state.profileFormMode = mode;
  state.editingProfileId = profile?.profile_id || "";
  el("birthDialogEyebrow").textContent = mode === "edit" ? "修正出生资料" : "建立一份命理档案";
  el("birthDialogTitle").textContent = mode === "edit" ? `编辑${profile.display_name}` : "新建八字档案";
  el("birthFormSubmit").textContent = mode === "edit" ? "保存修改" : "保存档案";
  el("birthFormHint").textContent = "保存后会自动排出四柱，并成为 Abu 当前使用的命理档案。修改出生信息后，需要重新看盘。";
  el("birthFormError").textContent = "";
  fillBirthForm(profile ? profileDraft(profile) : defaultBirthDraft());
  el("birthDialog").showModal();
}

async function deleteProfile(profileId) {
  const profile = state.profiles.find((item) => item.profile_id === profileId);
  if (!profile || !window.confirm(`确定删除“${profile.display_name}”吗？已经保存的历史探索不会同时删除。`)) return;
  await request(`${API.product}/profiles/${profileId}`, { method: "DELETE" });
  state.profiles = state.profiles.filter((item) => item.profile_id !== profileId);
  if (state.activeProfile?.profile_id === profileId) {
    clearCurrentReading();
    state.activeProfile = null;
    localStorage.removeItem("deepbazi.active_profile_id");
    const next = state.profiles.find((item) => item.is_default) || state.profiles[0];
    if (next) syncActiveProfile(next);
    else {
      updateCaseHeader();
      showWelcome();
    }
  }
  addMessage("abu", `${profile.display_name}已经从命理档案中删除。`, "Abu");
  await openCasebook();
}

function clearCurrentReading() {
  stopNarration({ silent: true });
  state.caseId = "";
  state.jobId = "";
  state.reading = null;
  state.narrationManifest = null;
  state.narrationManifestCaseId = "";
  state.narrationAssets = {};
  state.narrationAssetPromises = {};
  state.voiceValidationSession = null;
  state.voiceValidationStartedAt = 0;
  state.voiceValidationSegmentPlays = {};
  state.workspaceState = null;
  state.readOnlyCase = false;
  state.readOnlyReason = "";
  state.progressive = {};
  localStorage.removeItem("deepbazi.case_id");
  localStorage.removeItem("deepbazi.cognitive_job_id");
  localStorage.removeItem("deepbazi.cognitive_job_sequence");
  showWelcome();
  updateCaseHeader();
}

async function openCasebook() {
  if (!state.account) {
    el("authDialog").showModal();
    return;
  }
  if (!el("casebookDialog").open) el("casebookDialog").showModal();
  el("casebookContent").innerHTML = "<p class='empty-state'>正在读取你的命理档案…</p>";
  try {
    const [profiles, cases] = await Promise.all([request(`${API.product}/profiles`), request(`${API.agent}/cases?include_history=true`)]);
    state.profiles = profiles.profiles || [];
    if (state.activeProfile) {
      const current = state.profiles.find((item) => item.profile_id === state.activeProfile.profile_id)
        || state.profiles.find((item) => (
          item.profile_fingerprint === state.activeProfile.profile_fingerprint
          && item.display_name === state.activeProfile.display_name
        ));
      if (current) syncActiveProfile(current);
    }
    const modeSwitch = state.account.account_role === "admin" ? `<section class="casebook-group"><h3>Admin 页面预览</h3><div class="segmented mode-segmented">${[["guest", "游客"], ["member", "个人"], ["practitioner", "命理师"], ["research", "研究"]].map(([mode, label]) => `<button type="button" data-experience-mode="${mode}" class="${state.activeMode === mode ? "active" : ""}">${label}</button>`).join("")}</div><p class="mode-preview-note">只切换页面投影，不改变 Admin 身份或系统判断。</p></section>` : "";
    const emptyContinue = cases.legacy_cases_hidden
      ? "<p class='empty-state'>旧版探索已归档。请从下方命理档案重新开始，Abu 会按新的认知方式看盘。</p>"
      : "<p class='empty-state'>还没有保存的探索。</p>";
    const profileCards = state.profiles.length
      ? state.profiles.map(renderProfileArchiveCard).join("")
      : "<p class='empty-state'>还没有八字档案。新建后，阿布会直接用它开始看盘。</p>";
    const historicalCases = cases.historical_cases || [];
    const historySection = historicalCases.length
      ? `<section class="casebook-group historical-case-group"><div><p class="eyebrow">以前的出生资料</p><h3>历史版本</h3><p>这些案例已被新命盘替代，仅供查看和审计。</p></div>${historicalCases.map((item) => `<button class="casebook-item historical" data-historical-case-id="${escapeAttr(item.case_id)}"><span class="casebook-item-heading"><strong>${escapeHtml(item.display_name)}</strong><em>只读 · ${escapeHtml(item.case_version || "历史")}</em></span><span>${escapeHtml((item.pillars || []).filter(Boolean).join(" · "))}</span></button>`).join("")}</section>`
      : "";
    el("casebookContent").innerHTML = `${modeSwitch}<section class="casebook-group profile-archive"><div class="casebook-section-heading"><div><p class="eyebrow">出生资料</p><h3>八字档案</h3></div><button class="primary-button compact" type="button" id="newProfileButton"><i data-lucide="plus"></i>新建</button></div>${profileCards}</section><section class="casebook-group"><h3>继续探索</h3>${cases.cases.length ? cases.cases.map((item) => `<button class="casebook-item" data-case-id="${escapeAttr(item.case_id)}"><strong>${escapeHtml(item.display_name)}</strong><span>${escapeHtml((item.pillars || []).filter(Boolean).join(" · "))}</span></button>`).join("") : emptyContinue}</section>${historySection}<button class="secondary-button" id="logoutButton">退出登录</button>`;
    document.querySelectorAll("[data-case-id]").forEach((button) => button.addEventListener("click", () => restoreCase(button.dataset.caseId)));
    document.querySelectorAll("[data-historical-case-id]").forEach((button) => button.addEventListener("click", () => restoreCase(button.dataset.historicalCaseId, false, true)));
    document.querySelectorAll("[data-profile-use]").forEach((button) => button.addEventListener("click", () => useProfileForReading(button.dataset.profileUse)));
    document.querySelectorAll("[data-profile-edit]").forEach((button) => button.addEventListener("click", () => openProfileEditDialog(button.dataset.profileEdit)));
    document.querySelectorAll("[data-profile-delete]").forEach((button) => button.addEventListener("click", () => deleteProfile(button.dataset.profileDelete)));
    el("newProfileButton").addEventListener("click", openProfileCreateDialog);
    document.querySelectorAll("[data-experience-mode]").forEach((button) => button.addEventListener("click", async () => {
      state.activeMode = button.dataset.experienceMode;
      state.activeDeliberationStage = "";
      localStorage.setItem("deepbazi.experience_mode", state.activeMode);
      document.querySelectorAll("[data-experience-mode]").forEach((item) => item.classList.toggle("active", item === button));
      if (state.caseId) await restoreCase(state.caseId, true);
    }));
    el("logoutButton").addEventListener("click", logout);
    refreshIcons();
  } catch (_) {
    el("casebookContent").innerHTML = "<p class='empty-state'>档案暂时没有读取成功。</p>";
  }
}

async function restoreCase(caseId, silent = false, historical = false) {
  if (!caseId) return false;
  try {
    const body = await request(`${API.agent}/cases/${caseId}?active_mode=${encodeURIComponent(state.activeMode)}${historical ? "&historical=true" : ""}`);
    if (state.caseId !== caseId) {
      stopNarration({ silent: true });
      state.narrationManifest = null;
      state.narrationManifestCaseId = "";
      state.narrationAssets = {};
      state.narrationAssetPromises = {};
      state.voiceValidationSession = null;
      state.voiceValidationStartedAt = 0;
      state.voiceValidationSegmentPlays = {};
    }
    state.caseId = caseId;
    state.reading = body.reading || null;
    state.workspaceState = body.workspace_state || body.reading?.workspace_state || null;
    state.readOnlyCase = Boolean(body.read_only);
    state.readOnlyReason = body.read_only_reason || "";
    syncCaseContext(body.case_context || {});
    localStorage.setItem("deepbazi.case_id", caseId);
    if (body.outcome?.state === "blocked") {
      state.cognitionBlocked = true;
      showCognitionFailure({
        failure_stage: "epistemic_review",
        message: "这份案例保留了排盘，但整盘认知没有通过可靠性门槛，因此没有正式提交。",
        outcome: body.outcome,
      });
    } else {
      state.cognitionBlocked = false;
      renderReading();
    }
    updateCaseHeader();
    if (!silent) {
      el("casebookDialog").close();
      addMessage("abu", state.readOnlyCase
        ? "这是一份基于旧出生资料的历史案例。我可以陪你查看当时的判断，但不会继续测算或写入新记录。"
        : "这份命理档案已经接上了。你想继续事业、财富，还是挑战我上次的判断？", "Abu");
    }
    return true;
  } catch (error) {
    if (error.status === 404) localStorage.removeItem("deepbazi.case_id");
    if (!silent) addMessage("abu", "这份命理档案暂时没有接上。我会保留入口，稍后可以继续尝试。", "Abu");
    return false;
  }
}

async function logout() {
  await request(`${API.product}/auth/logout`, { method: "POST" });
  state.account = null;
  state.profiles = [];
  state.activeProfile = null;
  state.activeMode = "guest";
  localStorage.removeItem("deepbazi.active_profile_id");
  el("accountLabel").textContent = "登录";
  el("privacyNote").hidden = false;
  el("casebookButton").hidden = false;
  el("casebookDialog").close();
  updateCaseHeader();
  addMessage("abu", "已经退出。当前页面仍然保留，但新的内容不会写入账户。", "Abu");
}

function addMessage(type, text, author) {
  const node = createMessageNode(type, author);
  node.querySelector(".message-body").textContent = text;
  messageList.appendChild(node);
  scrollConversation();
  if (type === "abu") showAbuPeek(compactAbuPeek(text));
  return node;
}

function createMessageNode(type, author) {
  const node = el("messageTemplate").content.firstElementChild.cloneNode(true);
  node.classList.add(type);
  node.querySelector(".message-author").textContent = ["abu", "loading"].includes(type) ? "A" : author || "·";
  return node;
}

async function addTypedMessage(type, text, author) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return addMessage(type, text, author);
  const node = createMessageNode(type, author);
  const body = node.querySelector(".message-body");
  const caret = document.createElement("span");
  caret.className = "typing-caret";
  messageList.appendChild(node);
  body.appendChild(caret);
  scrollConversation();
  const characters = Array.from(String(text || ""));
  const chunkSize = characters.length > 220 ? 4 : characters.length > 100 ? 2 : 1;
  for (let index = 0; index < characters.length; index += chunkSize) {
    caret.before(document.createTextNode(characters.slice(index, index + chunkSize).join("")));
    if (index % Math.max(12, chunkSize * 5) === 0) scrollConversation();
    await delay(characters[index] === "。" || characters[index] === "\n" ? 34 : 11);
  }
  caret.remove();
  scrollConversation();
  if (type === "abu") showAbuPeek(compactAbuPeek(text));
  return node;
}

function addMessageLoading(label) {
  const node = createMessageNode("loading", "Abu");
  const body = node.querySelector(".message-body");
  const textNode = document.createElement("span");
  textNode.textContent = label;
  const dots = document.createElement("span");
  dots.className = "typing-dots";
  dots.setAttribute("aria-label", "处理中");
  dots.innerHTML = "<i></i><i></i><i></i>";
  body.append(textNode, dots);
  messageList.appendChild(node);
  scrollConversation();
  return node;
}

function setQuickActions(actions) {
  quickActions.innerHTML = "";
  actions.forEach(([label, handler]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", handler);
    quickActions.appendChild(button);
  });
}

function sendQuickMessage(message) {
  messageInput.value = message;
  el("composer").requestSubmit();
}

function focusComposer(placeholder, intent = "") {
  state.pendingComposerIntent = intent;
  messageInput.placeholder = placeholder;
  setAbuState("listening", state.reading || state.activeProfile ? "在听你的问题" : "在听出生信息");
  messageInput.focus();
}

function openBirthDialog() {
  state.profileFormMode = "intake";
  state.editingProfileId = "";
  el("birthDialogEyebrow").textContent = "阿布正在整理命盘";
  el("birthDialogTitle").textContent = state.activeProfile ? "核对另一份出生信息" : "确认出生信息";
  el("birthFormSubmit").textContent = "请阿布整理";
  el("birthFormHint").textContent = "如果时间只是大约值，请如实选择。阿布会保留这项不确定性，而不是把它当成精确事实。";
  el("birthFormError").textContent = "";
  fillBirthForm(state.birthDraft || defaultBirthDraft());
  setAbuState("listening", "等你填写出生信息");
  el("birthDialog").showModal();
}

function fillBirthForm(draft) {
  const form = el("birthForm");
  ["name", "gender", "calendar_type", "birth_date", "birth_time", "birth_location", "timezone", "time_precision"].forEach((field) => {
    if (form.elements[field] && draft[field] !== undefined && draft[field] !== null) form.elements[field].value = draft[field];
  });
}

function defaultBirthDraft() {
  return {
    name: "我的命盘",
    gender: "male",
    calendar_type: "solar",
    birth_date: "1990-01-01",
    birth_time: "12:00",
    birth_location: "首尔",
    timezone: "Asia/Seoul",
    time_precision: "exact",
  };
}

function renderInitialAbuContext(restored) {
  if (messageList.children.length) return;
  if (restored && state.cognitionBlocked) {
    addMessage("abu", "这份命盘和排盘事实都在，但上次的整盘判断没有通过检查。我没有把草稿冒充成结论；你可以让我重新看盘。", "Abu");
    setQuickActions([["重新独立看盘", () => state.lastStartPayload ? startCase(state.lastStartPayload) : state.activeProfile ? startCase({ profile_id: state.activeProfile.profile_id }) : openBirthDialog()], ["检查出生信息", openBirthDialog]]);
    setAbuState("sad", "上次判断没有通过检查");
    return;
  }
  if (restored && state.reading) {
    addMessage("abu", `${state.activeProfile?.display_name || "这份命盘"}已经接上了。出生信息和已有判断都在，不需要重新建档。你可以继续探索人生领域，或直接问一个具体问题。`, "Abu");
    setQuickActions([["打开人生地图", () => showArtifact("domains")], ["管理命理档案", openCasebook]]);
    return;
  }
  if (state.activeProfile) {
    addMessage("abu", `欢迎回来。${state.activeProfile.display_name}已经准备好，四柱是${(state.activeProfile.pillars || []).filter(Boolean).join("、")}。不需要再次告诉我出生信息。`, "Abu");
    setQuickActions([["用当前档案开始看盘", () => startCase({ profile_id: state.activeProfile.profile_id })], ["切换命理档案", openCasebook], ["新建一份档案", openProfileCreateDialog]]);
    setAbuState("welcome", "当前档案已经准备好");
    return;
  }
  addMessage("abu", "你好，我是阿布。\n\n你可以直接告诉我出生日期、时间、地点和性别。我会先替你整理，只追问缺少的信息；等你确认命盘后，我再开始独立判断。", "Abu");
  setQuickActions([["直接说出生信息", () => focusComposer("例如：1990年10月19日下午三点，男，出生在广州，公历")], ["按表格填写", openBirthDialog]]);
}

function handleProfileReadyMessage() {
  addMessage("abu", `${state.activeProfile.display_name}已经是当前档案，出生信息不需要再填。你可以直接开始看盘，或先切换另一份档案。`, "Abu");
  setQuickActions([["用当前档案开始看盘", () => startCase({ profile_id: state.activeProfile.profile_id })], ["切换命理档案", openCasebook]]);
  setAbuState("confirming", "当前档案已经确认");
}

function looksLikeBirthStatement(message) {
  return /(?:19|20)\d{2}(?:\s*年|[-/.])/.test(message) || /出生|生日|生辰/.test(message);
}

function setBusy(value, label = "") {
  state.busy = value;
  el("sendButton").disabled = value;
  messageInput.disabled = value;
  el("taskCanvas").setAttribute("aria-busy", String(value));
  if (value) {
    state.abuPeekPinned = true;
    setAbuState(label.includes("出生信息") ? "parsing" : "thinking", label);
    setAbuLoadingPeek(label);
  }
  else if (!["wave", "confirming", "listening", "boundary", "probe", "completed", "confidence_up", "sad"].includes(el("abuStage").dataset.state)) {
    state.abuPeekPinned = false;
    setAbuState("idle", state.reading ? "在听你说" : "准备听你说");
    scheduleAbuPeekCollapse();
  } else {
    state.abuPeekPinned = false;
    scheduleAbuPeekCollapse();
  }
}

function setAbuState(name, label) {
  if (state.abuIdleTimer) clearTimeout(state.abuIdleTimer);
  if (state.abuPlayTimer) clearTimeout(state.abuPlayTimer);
  state.abuIdleTimer = null;
  state.abuPlayTimer = null;
  el("abuStage").dataset.state = name;
  const motion = ABU_STATE_MOTION[name] || "idle_blink";
  const frame = el("abuMotionFrame");
  swapAbuMotion(frame, motion);
  el("abuStateText").textContent = label;
  el("abuPeekText").textContent = label;
  el("abuPeekLabel").textContent = name === "thinking" || name === "parsing"
    ? "Abu 正在理解"
    : name === "speaking" ? "Abu 正在讲"
    : name === "sad" ? "Abu 会陪你重来" : "Abu";
  if (["confirming", "probe", "completed", "boundary", "caution", "confidence_up", "sad"].includes(name)) {
    showAbuPeek(label);
  }
  if (ABU_MOTIONS[motion]?.playback === "one_shot") {
    const duration = ABU_MOTIONS[motion]?.durationMs || 1800;
    setTimeout(() => {
      if (el("abuStage").dataset.state === name) setAbuState("idle", state.reading ? "在听你说" : "准备听你说");
    }, Math.max(300, duration - 40));
  }
  if (name === "idle") scheduleAbuSleep();
}

function scheduleAbuSleep() {
  const idleElapsed = Date.now() - state.abuLastActivityAt;
  const sleepDelay = Math.max(1000, ABU_SLEEP_DELAY_MS - idleElapsed);
  state.abuIdleTimer = setTimeout(() => {
    if (state.busy || document.hidden || document.querySelector("dialog[open]") || messageInput.value.trim()) return;
    if (el("abuStage").dataset.state === "idle") setAbuState("sleep", "安静等你回来");
  }, sleepDelay);

  const moment = chooseAbuAmbientMoment();
  const randomDelay = ABU_PLAY_DELAY_MIN_MS
    + Math.round(Math.random() * (ABU_PLAY_DELAY_MAX_MS - ABU_PLAY_DELAY_MIN_MS));
  const cooldownRemaining = Math.max(0, ABU_PLAY_COOLDOWN_MS - (Date.now() - state.abuLastPlayAt));
  const playDelay = Math.max(randomDelay, cooldownRemaining + 200);
  const motion = moment ? ABU_STATE_MOTION[moment.state] : "";
  const motionDuration = ABU_MOTIONS[motion]?.durationMs || 6000;
  if (moment && playDelay + motionDuration + 1000 < sleepDelay) {
    state.abuPlayTimer = setTimeout(() => {
      if (state.busy || document.hidden || document.querySelector("dialog[open]") || messageInput.value.trim()) return;
      if (el("abuStage").dataset.state !== "idle") return;
      state.abuLastPlayAt = Date.now();
      state.abuLastAmbientState = moment.state;
      setAbuState(moment.state, moment.label);
    }, playDelay);
  }
}

function chooseAbuAmbientMoment() {
  if (!ABU_AMBIENT_MOMENTS.length) return null;
  const alternatives = ABU_AMBIENT_MOMENTS.filter((moment) => moment.state !== state.abuLastAmbientState);
  const pool = alternatives.length ? alternatives : ABU_AMBIENT_MOMENTS;
  const totalWeight = pool.reduce((sum, moment) => sum + Math.max(1, Number(moment.weight) || 1), 0);
  let roll = Math.random() * totalWeight;
  for (const moment of pool) {
    roll -= Math.max(1, Number(moment.weight) || 1);
    if (roll <= 0) return moment;
  }
  return pool[pool.length - 1];
}

function noteAbuActivity() {
  state.abuLastActivityAt = Date.now();
  if (state.abuIdleTimer) clearTimeout(state.abuIdleTimer);
  if (state.abuPlayTimer) clearTimeout(state.abuPlayTimer);
  if (el("abuStage").dataset.state === "sleep") {
    setAbuState("idle", state.reading ? "在听你说" : "准备听你说");
  } else if (el("abuStage").dataset.state === "idle") {
    scheduleAbuSleep();
  }
}

function abuMotionAsset(motion) {
  const asset = ABU_MOTIONS[motion] || ABU_MOTIONS.idle_blink;
  const path = reducedMotion.matches ? asset.poster : asset.animation;
  return path.startsWith("/") ? path : `${ABU_MOTION_ROOT}/${path}`;
}

function applyAbuMotionDisplay(image, motion) {
  const config = ABU_MOTIONS[motion] || ABU_MOTIONS.idle_blink;
  if (!config) return;
  image.style.setProperty("--abu-motion-scale", String(config.displayScale || 1));
  if (image.id === "abuMotionFrame") {
    el("abuStage").dataset.motionProfile = config.stageProfile || "standard";
  }
}

function swapAbuMotion(frame, motion) {
  const asset = abuMotionAsset(motion);
  applyAbuMotionDisplay(frame, motion);
  if (frame.dataset.abuMotion === motion && frame.getAttribute("src") === asset) return;
  const generation = String(Number(frame.dataset.motionSwapGeneration || 0) + 1);
  frame.dataset.motionSwapGeneration = generation;
  frame.classList.add("is-switching");
  window.setTimeout(() => {
    if (frame.dataset.motionSwapGeneration !== generation) return;
    frame.dataset.abuMotion = motion;
    frame.src = asset;
    requestAnimationFrame(() => frame.classList.remove("is-switching"));
  }, reducedMotion.matches ? 0 : 80);
}

function syncAbuMotionAssets() {
  document.querySelectorAll("[data-abu-motion]").forEach((image) => {
    const motion = image.dataset.abuMotion;
    image.src = abuMotionAsset(motion);
    applyAbuMotionDisplay(image, motion);
  });
}

function showThinking() {
  el("welcomeScene").hidden = true;
  el("failureScene").hidden = true;
  el("readingCanvas").hidden = true;
  renderThinkingChartContext();
  el("thinkingScene").hidden = false;
  setAbuLoadingPeek(el("thinkingTitle").textContent || "正在看盘");
  if (window.innerWidth <= 960) showCanvas();
  animateCanvasEntrance(el("thinkingScene"));
}

function renderThinkingChartContext() {
  const container = el("thinkingChartContext");
  if (!container) return;
  const payload = state.lastStartPayload || {};
  const birth = payload.birth_input || {};
  const profileMatches = Boolean(
    state.activeProfile
    && (!payload.profile_id || payload.profile_id === state.activeProfile.profile_id)
    && !payload.birth_input
  );
  const profile = profileMatches ? state.activeProfile : {};
  const chart = state.progressive.chart_ready || {};
  const explicitPillars = [birth.year_pillar, birth.month_pillar, birth.day_pillar, birth.hour_pillar].filter(Boolean);
  const pillars = [chart.pillars, explicitPillars, profile.pillars, state.reading?.pillars]
    .find((items) => Array.isArray(items) && items.filter(Boolean).length) || [];
  const name = birth.name || profile.display_name || profile.name || state.activeProfile?.display_name || "当前命盘";
  const gender = birth.gender || profile.gender || state.activeProfile?.gender || "";
  const calendarType = birth.calendar_type || profile.calendar_type || state.activeProfile?.calendar_type || "";
  const birthDate = birth.birth_date || profile.birth_date || state.activeProfile?.birth_date || "";
  const birthTime = birth.birth_time || profile.birth_time || state.activeProfile?.birth_time || "";
  const birthLocation = birth.birth_location || profile.birth_location || state.activeProfile?.birth_location || "";

  container.hidden = false;
  el("thinkingProfileName").textContent = name;
  el("thinkingProfileGender").textContent = gender === "male" ? "乾造" : gender === "female" ? "坤造" : "命造";
  const birthParts = [
    calendarType ? (calendarType === "lunar" ? "农历" : "公历") : "",
    [birthDate, birthTime].filter(Boolean).join(" "),
    birthLocation,
  ].filter(Boolean);
  el("thinkingBirthMeta").textContent = birthParts.join(" · ") || "出生资料已经确认";
  el("thinkingProfilePillars").innerHTML = pillars.filter(Boolean).length
    ? renderPillarSet(pillars.filter(Boolean))
    : '<p class="thinking-pillars-pending">四柱正在排定，确认后会显示在这里。</p>';
}

function showCognitionFailure(payload = {}) {
  el("welcomeScene").hidden = true;
  el("thinkingScene").hidden = true;
  el("readingCanvas").hidden = true;
  el("failureScene").hidden = false;
  const stageLabels = {
    chart_compilation: "命盘事实没有完整建立",
    pattern_hypothesis: "第一眼判断没有通过事实检查",
    work_path: "主作用路径没有通过一致性检查",
    ziwei_lens: "八字与紫微没有完成本轮参看",
    prior_probe: "现实验证问题没有可靠形成",
    career_domain: "事业专题没有通过检查",
    wealth_domain: "财富专题没有通过检查",
    epistemic_review: "最终事实与证据检查没有通过",
    runtime_recovery: "上一次看盘被服务中断",
  };
  el("failureTitle").textContent = stageLabels[payload.failure_stage] || "这次没有形成可靠判断";
  el("failureDetail").textContent = payload.message || "Abu 没有通过事实与证据检查，所以没有继续生成结论。";
  const facts = el("failureFacts");
  const pillars = payload.outcome?.pillars || [];
  facts.hidden = !pillars.length;
  facts.innerHTML = pillars.length
    ? `<small>已确认的四柱仍然保留</small>${renderPillarSet(pillars)}`
    : "";
  if (window.innerWidth <= 960) showCanvas();
  animateCanvasEntrance(el("failureScene"));
}

function resetThinkingExperience() {
  el("thinkingTitle").textContent = "先找出这张盘真正的重心";
  el("thinkingDetail").textContent = "比较结构、做功路径与相反解释，这会花一点时间。";
  el("thinkingProgressBar").style.width = "8%";
  el("thinkingLog").innerHTML = "";
  el("thinkingDetails").open = false;
  stopThinkingPreview();
  el("thinkingPreview").hidden = true;
  el("thinkingPreviewText").textContent = "";
  el("abuPeekPreview").textContent = "";
  el("abuPeekPreview").hidden = true;
  document.querySelectorAll("[data-thinking-step]").forEach((node, index) => {
    node.classList.toggle("active", index === 0);
    node.classList.remove("complete");
  });
}

function previewTargets() {
  const targets = [];
  const peek = el("abuPeekPreview");
  if (peek && (state.busy || state.abuSurface === "peek")) targets.push(peek);
  return targets;
}

function stopThinkingPreview({ clear = true } = {}) {
  state.thinkingPreviewGeneration += 1;
  if (state.thinkingPreviewTimer) window.clearTimeout(state.thinkingPreviewTimer);
  state.thinkingPreviewTimer = null;
  if (clear) {
    state.thinkingPreviewLines = [];
    state.thinkingPreviewIndex = -1;
    el("abuPeekPreview").textContent = "";
    el("abuPeekPreview").hidden = true;
  }
}

function resumeThinkingPreview() {
  if (!state.thinkingPreviewLines.length) return;
  const index = Math.max(0, state.thinkingPreviewIndex);
  void showThinkingPreviewLine(index, { immediate: true });
}

async function updateThinkingPreview(text) {
  const value = cleanUserCopy(String(text || "")).replace(/\s+/g, " ").trim();
  if (!value) return;
  const compact = value.length > 110 ? `${value.slice(0, 109)}…` : value;
  const existingIndex = state.thinkingPreviewLines.indexOf(compact);
  if (existingIndex >= 0) state.thinkingPreviewLines.splice(existingIndex, 1);
  state.thinkingPreviewLines.push(compact);
  state.thinkingPreviewLines = state.thinkingPreviewLines.slice(-8);
  state.thinkingPreviewIndex = state.thinkingPreviewLines.length - 1;
  await showThinkingPreviewLine(state.thinkingPreviewIndex);
}

async function showThinkingPreviewLine(index, { immediate = false } = {}) {
  if (!state.thinkingPreviewLines.length) return;
  if (state.thinkingPreviewTimer) window.clearTimeout(state.thinkingPreviewTimer);
  state.thinkingPreviewTimer = null;
  const normalizedIndex = ((index % state.thinkingPreviewLines.length) + state.thinkingPreviewLines.length) % state.thinkingPreviewLines.length;
  state.thinkingPreviewIndex = normalizedIndex;
  const characters = Array.from(state.thinkingPreviewLines[normalizedIndex]);
  const generation = ++state.thinkingPreviewGeneration;
  if (!el("thinkingScene").hidden) el("thinkingPreview").hidden = false;
  if (state.busy || state.abuSurface === "peek") el("abuPeekPreview").hidden = false;
  const targets = previewTargets();
  targets.forEach((target) => {
    target.closest(".rolling-preview, .thinking-preview, .abu-peek-copy")?.classList.remove("rolling-out");
    target.textContent = "";
  });
  if (reducedMotion.matches || immediate) {
    targets.forEach((target) => { target.textContent = characters.join(""); });
  } else {
    const carets = targets.map((target) => {
      const caret = document.createElement("span");
      caret.className = "typing-caret";
      target.appendChild(caret);
      return caret;
    });
    const chunkSize = characters.length > 80 ? 2 : 1;
    for (let characterIndex = 0; characterIndex < characters.length; characterIndex += chunkSize) {
      if (generation !== state.thinkingPreviewGeneration) return;
      const chunk = characters.slice(characterIndex, characterIndex + chunkSize).join("");
      carets.forEach((caret) => caret.before(document.createTextNode(chunk)));
      await delay(18);
    }
    carets.forEach((caret) => caret.remove());
  }
  if (generation !== state.thinkingPreviewGeneration) return;
  state.thinkingPreviewTimer = window.setTimeout(() => {
    const currentTargets = previewTargets();
    currentTargets.forEach((target) => target.closest(".rolling-preview, .thinking-preview, .abu-peek-copy")?.classList.add("rolling-out"));
    window.setTimeout(() => {
      if (generation !== state.thinkingPreviewGeneration) return;
      void showThinkingPreviewLine(normalizedIndex + 1);
    }, reducedMotion.matches ? 0 : 220);
  }, state.thinkingPreviewLines.length > 1 ? 2800 : 4200);
}

function updateThinkingExperience(step, progress, title, detail, logText) {
  showThinking();
  el("thinkingTitle").textContent = title;
  el("thinkingDetail").textContent = detail;
  el("thinkingProgressBar").style.width = `${Math.max(8, Math.min(100, progress))}%`;
  setAbuLoadingPeek(title, detail, progress);
  document.querySelectorAll("[data-thinking-step]").forEach((node, index) => {
    node.classList.toggle("active", index === step);
    node.classList.toggle("complete", index < step || progress === 100);
  });
  if (logText && !Array.from(el("thinkingLog").children).some((item) => item.textContent === logText)) {
    const item = document.createElement("li");
    item.textContent = logText;
    el("thinkingLog").appendChild(item);
  }
}

function showDomainLoading(label, existing) {
  stopThinkingPreview();
  setAbuLoadingPeek(existing ? `正在接上${label}` : `正在推演${label}`, existing ? "已有理解会保留。" : "沿着整盘主线进入这个人生问题。");
  const cognition = state.reading || {};
  const currentLines = [
    cognition.life_case?.baseline?.claim,
    cognition.whole_chart_thesis,
    cognition.first_look,
    cognition.work_path?.path_statement,
  ].filter(Boolean);
  currentLines.forEach((line) => {
    const compact = cleanUserCopy(String(line)).replace(/\s+/g, " ").trim();
    if (compact && !state.thinkingPreviewLines.includes(compact)) state.thinkingPreviewLines.push(compact.length > 110 ? `${compact.slice(0, 109)}…` : compact);
  });
  state.thinkingPreviewIndex = 0;
  resumeThinkingPreview();
}

function showWelcome() {
  const profileReady = Boolean(state.activeProfile);
  el("welcomeEyebrow").textContent = profileReady ? `当前命盘 · ${state.activeProfile.display_name}` : "Abu · 柴犬命理师";
  el("welcomeTitle").innerHTML = profileReady ? "命盘已经准备好，<br>从真正的问题开始。" : "先看见命局，<br>再理解人生。";
  el("welcomeDescription").textContent = profileReady
    ? "出生信息和四柱已经确认。告诉阿布你此刻最想看清的人生问题，或直接开始整盘测算。"
    : "直接说出出生日期、时间、地点和性别。阿布会替你整理，请你确认后再开始独立看盘。";
  el("welcomePrinciple").querySelector("span").textContent = profileReady
    ? "不重复索取出生信息；切换档案时，旧测算不会套用。"
    : "不先套经历；不确定的地方，会明确告诉你。";
  el("welcomeScene").hidden = false;
  el("readingCanvas").hidden = true;
  el("thinkingScene").hidden = true;
  el("failureScene").hidden = true;
  animateCanvasEntrance(el("welcomeScene"));
}

function updateCaseHeader() {
  const crumb = el("caseBreadcrumb");
  const hasChartContext = Boolean(state.reading || state.activeProfile);
  crumb.hidden = !hasChartContext;
  if (!hasChartContext) return;
  el("caseName").textContent = state.activeProfile?.display_name || "当前命盘";
  el("casePillars").textContent = (state.activeProfile?.pillars || state.reading?.pillars || []).filter(Boolean).join(" · ");
}

function initializeAbuSurface() {
  const stored = localStorage.getItem("deepbazi.abu_surface");
  const initial = stored === "open" || stored === "collapsed" ? stored : (state.reading ? "collapsed" : "open");
  state.abuSurfaceReady = true;
  setAbuSurface(initial, { persist: false });
}

function setAbuSurface(surface, { persist = true, message = "" } = {}) {
  const next = ["open", "peek", "collapsed"].includes(surface) ? surface : "collapsed";
  if (state.abuPeekTimer) clearTimeout(state.abuPeekTimer);
  state.abuPeekTimer = null;
  state.abuSurface = next;
  appShell.classList.remove("abu-panel-open", "abu-panel-peek", "abu-panel-collapsed", "mobile-canvas");
  appShell.classList.add(`abu-panel-${next}`);
  state.mobileCanvas = next !== "open";
  el("abuStage").setAttribute("aria-expanded", String(next === "open"));
  if (message) el("abuPeekText").textContent = message;
  if (persist && next !== "peek") localStorage.setItem("deepbazi.abu_surface", next);
  if (next === "open") requestAnimationFrame(scrollConversation);
  if (next === "peek" && !state.abuPeekPinned) {
    state.abuPeekTimer = setTimeout(() => {
      if (state.abuSurface === "peek") setAbuSurface("collapsed", { persist: false });
    }, 6500);
  }
}

function showAbuPeek(message) {
  if (!state.abuSurfaceReady || state.abuSurface === "open" || document.hidden) return;
  setAbuSurface("peek", { persist: false, message: message || "我有一条新提示。" });
}

function setAbuLoadingPeek(title, detail = "", progress = null) {
  state.abuPeekPinned = true;
  el("abuPeekLabel").textContent = Number.isFinite(progress) ? `看盘进度 ${Math.round(progress)}%` : "Abu 正在理解";
  el("abuPeekText").textContent = title || "正在沿命盘主线继续理解";
  if (detail && !state.thinkingPreviewLines.length) {
    el("abuPeekPreview").textContent = compactAbuPeek(detail);
    el("abuPeekPreview").hidden = false;
  }
  setAbuSurface("peek", { persist: false });
}

function scheduleAbuPeekCollapse() {
  if (state.abuPeekTimer) clearTimeout(state.abuPeekTimer);
  state.abuPeekTimer = null;
  if (state.abuSurface !== "peek" || state.abuPeekPinned) return;
  state.abuPeekTimer = setTimeout(() => {
    if (state.abuSurface === "peek" && !state.abuPeekPinned) setAbuSurface("collapsed", { persist: false });
  }, 8500);
}

function compactAbuPeek(text) {
  const compact = String(text || "").replace(/\s+/g, " ").trim();
  if (!compact) return "我有一条新提示。";
  const firstSentence = compact.split(/(?<=[。！？!?])/u)[0] || compact;
  return firstSentence.length > 42 ? `${firstSentence.slice(0, 41)}…` : firstSentence;
}

function toggleMobileView() {
  setAbuSurface(state.abuSurface === "open" ? "collapsed" : "open");
}

function showCanvas() {
  state.mobileCanvas = true;
  if (window.innerWidth <= 960) setAbuSurface("collapsed");
}

function showConversation() {
  state.mobileCanvas = false;
  setAbuSurface("open");
}

function autoSizeComposer() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 128)}px`;
  messageInput.style.overflowY = messageInput.scrollHeight > 128 ? "auto" : "hidden";
}

function scrollConversation() { requestAnimationFrame(() => { el("conversationScroll").scrollTop = el("conversationScroll").scrollHeight; }); }
function delay(milliseconds) { return new Promise((resolve) => setTimeout(resolve, milliseconds)); }

async function request(url, options = {}) {
  const response = await fetch(url, { credentials: "same-origin", headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  let body = {};
  try { body = await response.json(); } catch (_) { /* no-op */ }
  if (!response.ok) {
    const error = new Error(typeof body.detail === "string" ? body.detail : `request_failed_${response.status}`);
    error.status = response.status;
    throw error;
  }
  return body;
}

function readStoredJson(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key) || "null");
  } catch (_) {
    sessionStorage.removeItem(key);
    return null;
  }
}

function friendlyError(error, fallback) {
  if (!error?.message) return fallback;
  if (error.message.includes("authentication_required")) return "请先登录，再继续读取这份档案。";
  if (error.message.includes("calendar") || error.message.includes("pillars")) return "这份出生信息暂时无法准确排盘，请检查日期、时间、历法和地点。";
  if (error.message.includes("cognition_failed") || error.message.includes("model")) return fallback;
  return fallback;
}

function confidenceLabel(value) { return ({ high: "较高把握", medium: "中等把握", low: "初步判断" })[value] || "仍需验证"; }
function defaultModeForRole(role) { return ({ admin: "member", practitioner: "practitioner", research_master: "research", member: "member" })[role] || "guest"; }
function modeLabel(mode) { return ({ guest: "初识 · Abu 第一眼", member: "个人探索 · 当前命局", practitioner: "专业研判 · 案例工作台", research: "研究审计 · 假设空间" })[mode] || "命局"; }
function probeHeading(mode) { return ({ guest: "Abu 想确认一件事", member: "Abu 想确认一件事", practitioner: "案例鉴别", research: "反例检查" })[mode] || "继续确认"; }
function beliefDeltaLabel(delta) { return ({ strengthen: "增强", weaken: "减弱", unchanged: "不变" })[delta] || "不变"; }
function humanizeHypothesisName(value) { return String(value || "").replace(/[，,]\s*[A-Za-z][A-Za-z0-9_]*(?:\s*成立)?/g, "").replace(/[（(][A-Za-z][A-Za-z0-9_\s-]*[）)]/g, "").trim(); }
function cleanUserCopy(value) {
  return String(value || "")
    .replace(/[（(]\s*(?:F|PA|PP|Z|K|O|R|E|C)\d+(?:\s*[,，、/]\s*(?:F|PA|PP|Z|K|O|R|E|C)?\d+)*\s*[）)]/gi, "")
    .replace(/\[(?:F|PA|PP|Z|K|O|R|E|C)\d+(?:\s*[,，、/]\s*(?:F|PA|PP|Z|K|O|R|E|C)?\d+)*\]/gi, "")
    .replace(/命主/g, "你")
    .replace(/[（(][^）)]*(?:甲木|乙木|丙火|丁火|戊土|己土|庚金|辛金|壬水|癸水|子水|丑土|寅木|卯木|辰土|巳火|午火|未土|申金|酉金|戌土|亥水|七杀|官杀|印星|食伤|伤官|财星|比劫|日主|命宫|身宫|福德宫|迁移宫|疾厄宫|兄弟宫|大限|流年|化权|化忌|擎羊|破军|枭神|H\d+)[^）)]*[）)]/gi, "")
    .replace(/[（(][^）)]*(?:支持|增强|削弱|激活)\s*H\d+(?:\s*[\/、]\s*H\d+)*[^）)]*[）)]/gi, "")
    .replace(/[（(]支持[^）)]*[）)]/g, "")
    .replace(/[（(]激活[^）)]*[）)]/g, "")
    .replace(/\bH\d+(?:\s*[\/、]\s*H\d+)*\b/gi, "")
    .replace(/枭神夺食/g, "思虑压住行动")
    .replace(/食神/g, "稳定输出")
    .replace(/正财|偏财/g, "现实资源")
    .replace(/劫财/g, "竞争与资源分流")
    .replace(/正印|偏印/g, "学习与支持")
    .replace(/正官|偏官/g, "规则与责任")
    .replace(/必须通过/g, "主要需要通过")
    .replace(/个体/g, "你")
    .replace(/核心根基/g, "身体与生活根基")
    .replace(/基础能源/g, "恢复力")
    .replace(/剧烈冲克/g, "剧烈冲击")
    .replace(/身强印旺/g, "内在积累很多、也容易想得过重")
    .replace(/身强喜泄秀/g, "需要把内在积累转化为表达和行动")
    .replace(/泄秀/g, "把积累转化为表达")
    .replace(/七杀|官杀/g, "外部规则与压力")
    .replace(/印星/g, "学习与支持")
    .replace(/食伤/g, "表达与输出")
    .replace(/伤官/g, "表达与突破")
    .replace(/财星/g, "现实资源")
    .replace(/比劫/g, "自主性与同伴关系")
    .replace(/日主/g, "自身")
    .replace(/大限/g, "长期阶段")
    .replace(/流年/g, "年份")
    .replace(/命宫/g, "人生主轴")
    .replace(/身宫/g, "行动方式")
    .replace(/福德宫/g, "内在感受")
    .replace(/迁移宫/g, "环境与变动主题")
    .replace(/疾厄宫/g, "精力与健康主题")
    .replace(/兄弟宫/g, "合作与同伴主题")
    .replace(/冲克/g, "持续冲击")
    .replace(/合绊/g, "相互牵制")
    .replace(/岁运/g, "阶段变化")
    .replace(/生财/g, "转化为现实资源")
    .replace(/反侮/g, "反向压制")
    .replace(/燥库/g, "偏燥的土库")
    .replace(/脆金/g, "使金受损")
    .replace(/开闭状态/g, "能否发挥作用")
    .replace(/根气/g, "现实支撑")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([，。；：])/g, "$1")
    .trim();
}
function refreshIcons() { if (window.lucide) window.lucide.createIcons(); else setTimeout(() => window.lucide && window.lucide.createIcons(), 400); }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]); }
function escapeAttr(value) { return escapeHtml(value).replace(/`/g, "&#96;"); }
