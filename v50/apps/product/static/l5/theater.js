const API = "/api/v50/theater";

const state = {
  account: null,
  cases: [],
  sessionId: localStorage.getItem("deepbazi.theater.session") || "",
  participantRunId: localStorage.getItem("deepbazi.theater.run") || "",
  accessToken: localStorage.getItem("deepbazi.theater.token") || "",
  snapshot: null,
  socket: null,
  reconnectAttempts: 0,
  pollTimer: null,
  lastCueId: "",
  activePerformanceCueId: "",
  performancePackage: null,
  performancePhase: "idle",
  textFallback: false,
  experimentPayload: null,
  experimentLoading: false,
  experimentError: "",
};

const el = Object.fromEntries([
  "theaterShell", "lobby", "performance", "lobbyTitle", "lobbyIntro", "programSelect", "caseSelect", "caseHint", "enterSolo", "createLive",
  "sessionCode", "joinLive", "programMode", "studioToggle", "directorDock", "topicEyebrow",
  "leaveSession",
  "topicTitle", "connectionState", "participantCount", "sceneLabel", "abuDialogue", "subtitle",
  "actRail", "abuActor", "actorState", "mingliStage", "reportGhost", "pillarStage", "reasoningStage",
  "unresolvedStage", "mingliExperiment", "groupTrace", "performanceTransport", "playPauseButton", "performanceStatus",
  "elapsedTime", "durationTime", "performanceProgress", "muteButton", "transportReplayButton",
  "textFallbackButton", "timelineDetails", "timelineList", "liveCaption", "interactionSheet", "interactionKicker", "interactionPrompt",
  "interactionPrivacy", "interactionControls", "continueButton", "replayButton", "toast"
].map((id) => [id, document.getElementById(id)]));

class AbuActorRenderer {
  loadAssets(_assets) {}
  setAction(_event) {}
  setVoiceActivity(_event) {}
  reset() {}
}

class WebPActorRenderer extends AbuActorRenderer {
  constructor(image, label) {
    super();
    this.image = image;
    this.label = label;
    this.assets = {};
    this.lastAction = "";
  }

  loadAssets(assets) { this.assets = assets || {}; }

  setAction(event) {
    if (!event || event.action === this.lastAction) return;
    this.lastAction = event.action;
    const assetByAction = {
      enter: "abu-welcome",
      speak: "abu-taoist",
      push_report: "abu-welcome",
      point_chart: "abu-divination",
      point_path: "abu-taoist",
      serious: "abu-divination",
      listen: "abu-head-tilt",
    };
    const labels = {
      enter: "走进命盘",
      speak: "正在讲述",
      push_report: "先放下结论",
      point_chart: "看向四柱",
      point_path: "指出主线",
      serious: "保留未决条件",
      listen: "在听你的选择",
    };
    const asset = this.assets[assetByAction[event.action]];
    if (asset?.uri) this.image.src = asset.uri;
    this.image.closest(".abu-actor")?.setAttribute("data-action", event.action);
    this.label.textContent = labels[event.action] || "在听";
  }

  setVoiceActivity(event) {
    const actor = this.image.closest(".abu-actor");
    if (actor) {
      const openness = Number(event?.openness || 0);
      actor.style.setProperty("--voice-level", String(openness));
      actor.style.setProperty("--voice-glow", String(0.36 + openness * 0.34));
      actor.style.setProperty("--voice-scale", String(1 + openness * 0.035));
    }
  }

  reset() {
    this.lastAction = "";
    this.label.textContent = "在听";
    this.image.closest(".abu-actor")?.style.setProperty("--voice-level", "0");
    this.image.closest(".abu-actor")?.style.setProperty("--voice-glow", ".36");
    this.image.closest(".abu-actor")?.style.setProperty("--voice-scale", "1");
  }
}

class MingliStageRenderer {
  constructor(root) {
    this.root = root;
    this.package = null;
    this.applied = new Set();
  }

  load(performancePackage) {
    this.package = performancePackage;
    this.applied.clear();
    el.pillarStage.replaceChildren();
    el.reasoningStage.replaceChildren();
    el.unresolvedStage.replaceChildren();
    const snapshot = performancePackage.stage_snapshot || {};
    (snapshot.chart_facts || []).forEach((fact) => el.pillarStage.append(this.pillarNode(fact)));
    (snapshot.reasoning_steps || []).forEach((step, index) => el.reasoningStage.append(this.reasoningNode(step, index)));
    if (snapshot.approved_claim) el.reasoningStage.append(this.claimNode(snapshot.approved_claim));
    if (snapshot.unresolved_text) {
      const kicker = document.createElement("span");
      kicker.textContent = "仍未确认";
      const text = document.createElement("p");
      text.textContent = snapshot.unresolved_text;
      el.unresolvedStage.append(kicker, text);
    }
    this.root.classList.remove("hidden");
    this.reset();
  }

  pillarNode(fact) {
    const node = document.createElement("div");
    node.className = "pillar-node stage-object";
    node.dataset.ref = fact.fact_ref;
    node.dataset.anchor = fact.visual_anchor || "";
    const match = String(fact.display_value || "").match(/^(年柱|月柱|日柱|时柱)\s*([^\s])([^\s])/);
    const label = document.createElement("span");
    label.textContent = match?.[1] || fact.fact_type || "命盘";
    const stem = document.createElement("strong");
    stem.className = `pillar-glyph ${fiveElementClass(match?.[2] || "")}`;
    stem.textContent = match?.[2] || fact.display_value;
    const branch = document.createElement("strong");
    branch.className = `pillar-glyph ${fiveElementClass(match?.[3] || "")}`;
    branch.textContent = match?.[3] || "";
    node.append(label, stem, branch);
    return node;
  }

  reasoningNode(step, index) {
    const node = document.createElement("div");
    node.className = "reasoning-node stage-object";
    node.dataset.ref = step.step_ref;
    node.dataset.anchor = step.visual_anchor;
    const count = document.createElement("span");
    count.textContent = String(index + 1).padStart(2, "0");
    const copy = document.createElement("p");
    copy.textContent = `${step.premise}，因此 ${step.conclusion}`;
    node.append(count, copy);
    return node;
  }

  claimNode(claim) {
    const node = document.createElement("div");
    node.className = "approved-path stage-object";
    node.dataset.ref = claim.claim_ref;
    node.dataset.anchor = "approved-path";
    const label = document.createElement("span");
    label.textContent = "当前已确认的主线";
    const copy = document.createElement("p");
    copy.textContent = claim.subtitle_summary || claim.spoken_summary || claim.approved_meaning;
    node.append(label, copy);
    return node;
  }

  reset() {
    this.applied.clear();
    this.root.dataset.camera = "wide";
    this.root.querySelectorAll(".stage-object").forEach((item) => item.classList.remove("visible", "active"));
    el.unresolvedStage.classList.add("hidden");
    el.reportGhost.classList.remove("dismissed");
  }

  renderAt(milliseconds) {
    if (!this.package) return;
    (this.package.stage_track || []).forEach((event, index) => {
      const key = `${index}:${event.action}`;
      if (event.at_ms <= milliseconds && !this.applied.has(key)) {
        this.applied.add(key);
        this.apply(event);
      }
    });
    const camera = latestAt(this.package.camera_track || [], milliseconds);
    if (camera) this.root.dataset.camera = camera.framing;
  }

  apply(event) {
    if (event.action === "reset") return;
    if (event.action === "reveal_chart_fact") {
      this.root.querySelector(`[data-ref="${cssEscape(event.target_ref)}"]`)?.classList.add("visible");
      el.reportGhost.classList.add("dismissed");
    }
    if (event.action === "reveal_reasoning_step") {
      this.root.querySelector(`[data-ref="${cssEscape(event.target_ref)}"]`)?.classList.add("visible");
    }
    if (event.action === "highlight_approved_path") {
      this.root.querySelector(`[data-ref="${cssEscape(event.target_ref)}"]`)?.classList.add("visible", "active");
    }
    if (event.action === "show_unresolved_condition") el.unresolvedStage.classList.remove("hidden");
  }

  complete() {
    if (!this.package) return;
    this.root.querySelectorAll(".stage-object").forEach((item) => item.classList.add("visible"));
    this.root.querySelector(".approved-path")?.classList.add("active");
    el.unresolvedStage.classList.toggle("hidden", !this.package.stage_snapshot?.unresolved_text);
    el.reportGhost.classList.add("dismissed");
    this.root.dataset.camera = "choice";
  }
}

class MingliExperimentRenderer {
  constructor(root, { onSelect }) {
    this.root = root;
    this.onSelect = onSelect;
    this.payload = null;
  }

  load(payload) {
    this.payload = payload;
    this.render();
    this.root.classList.remove("hidden");
  }

  showError(message) {
    this.root.replaceChildren();
    const note = document.createElement("div");
    note.className = "experiment-error";
    note.textContent = message;
    this.root.append(note);
    this.root.classList.remove("hidden");
  }

  hide() {
    this.root.classList.add("hidden");
  }

  reset() {
    this.payload = null;
    this.root.replaceChildren();
    this.hide();
  }

  render() {
    if (!this.payload) return;
    const { snapshot, visual_spec: visualSpec, sandbox_state: sandbox, sandbox_result: result } = this.payload;
    const nodes = new Map((visualSpec.nodes || []).map((item) => [item.node_id, item]));
    const predicted = sandbox.predicted_key_node_id || "";
    const ablated = result?.deterministic_changes?.removed_node_id || "";
    const locked = Boolean(result);
    this.root.replaceChildren();

    const boundaries = document.createElement("div");
    boundaries.className = "experiment-boundaries";
    (this.payload.boundaries || snapshot.boundaries || []).slice(0, 3).forEach((text) => {
      const item = document.createElement("span");
      item.textContent = text;
      boundaries.append(item);
    });

    const titleRow = document.createElement("div");
    titleRow.className = "experiment-title-row";
    const title = document.createElement("strong");
    title.textContent = "原局结构 · 实验分支";
    const status = document.createElement("p");
    status.textContent = result ? "正在比较 Baseline 与 Modified" : predicted ? "已锁定你的猜测，等待消融" : "先猜哪一个节点不可替代";
    titleRow.append(title, status);

    const pillars = document.createElement("div");
    pillars.className = "experiment-pillars";
    (snapshot.pillars || []).forEach((pillar) => {
      const card = document.createElement("div");
      card.className = "experiment-pillar";
      const label = document.createElement("span");
      label.textContent = pillar.label;
      const stem = this.nodeButton(nodes.get(pillar.stem_node_id), { predicted, ablated, locked });
      const branch = this.nodeButton(nodes.get(pillar.branch_node_id), { predicted, ablated, locked });
      const hidden = document.createElement("small");
      hidden.textContent = pillar.hidden_stems?.length ? `藏干 ${pillar.hidden_stems.join(" · ")}` : "藏干未列";
      card.append(label, stem, branch, hidden);
      pillars.append(card);
    });

    const paths = document.createElement("div");
    paths.className = "experiment-paths";
    (visualSpec.paths || []).forEach((path) => paths.append(this.pathLane(path, nodes, { predicted, ablated, result, locked })));

    this.root.append(boundaries, titleRow, pillars, paths);
    if (result) this.root.append(this.diffPanel(result, nodes));
  }

  nodeButton(node, { predicted, ablated, locked }) {
    const button = document.createElement("button");
    button.type = "button";
    if (!node) {
      button.textContent = "?";
      button.disabled = true;
      return button;
    }
    button.textContent = node.label;
    button.className = fiveElementClass(node.label);
    button.dataset.nodeId = node.node_id;
    button.title = `${node.position || "结构节点"}${node.ten_god ? ` · ${node.ten_god}` : ""}`;
    button.classList.toggle("is-predicted", node.node_id === predicted);
    button.classList.toggle("is-ablated", node.node_id === ablated);
    button.disabled = locked || !node.selectable;
    button.addEventListener("click", () => this.onSelect(node.node_id));
    return button;
  }

  pathLane(path, nodes, { predicted, ablated, result, locked }) {
    const affected = new Set(result?.deterministic_changes?.affected_paths || []);
    const unaffected = new Set(result?.deterministic_changes?.unaffected_paths || []);
    const invalidatedEdges = new Set(result?.deterministic_changes?.invalidated_edges || []);
    const lane = document.createElement("div");
    lane.className = "experiment-path";
    lane.dataset.kind = path.path_kind;
    lane.classList.toggle("is-affected", affected.has(path.path_ref));
    lane.classList.toggle("is-unaffected", unaffected.has(path.path_ref));
    const heading = document.createElement("div");
    heading.className = "path-heading";
    const label = document.createElement("strong");
    label.textContent = path.path_kind === "approved" ? "已批准主路径" : "竞争路径";
    const meaning = document.createElement("span");
    meaning.textContent = path.display_label;
    heading.append(label, meaning);
    const track = document.createElement("div");
    track.className = "path-track";
    path.node_ids.forEach((nodeId, index) => {
      const button = this.nodeButton(nodes.get(nodeId), { predicted, ablated, locked });
      button.classList.add("experiment-node");
      track.append(button);
      if (index < path.edge_ids.length) {
        const link = document.createElement("span");
        link.className = "path-link";
        link.textContent = relationName(path.relation_types[index]);
        link.classList.toggle("is-severed", invalidatedEdges.has(path.edge_ids[index]));
        track.append(link);
      }
    });
    lane.append(heading, track);
    return lane;
  }

  diffPanel(result, nodes) {
    const changes = result.deterministic_changes;
    const panel = document.createElement("div");
    panel.className = "experiment-diff";
    const heading = document.createElement("div");
    heading.className = "diff-heading";
    const title = document.createElement("strong");
    title.textContent = "结构差异已经算清";
    const authority = document.createElement("span");
    authority.textContent = "DETERMINISTIC STRUCTURE";
    heading.append(title, authority);
    const metrics = document.createElement("div");
    metrics.className = "diff-metrics";
    [
      [changes.invalidated_edges.length, "关系消失"],
      [changes.affected_paths.length, "路径受影响"],
      [changes.unaffected_paths.length, "路径仍保留"],
    ].forEach(([value, label]) => {
      const metric = document.createElement("div");
      metric.className = "diff-metric";
      const number = document.createElement("strong");
      number.textContent = String(value);
      const copy = document.createElement("span");
      copy.textContent = label;
      metric.append(number, copy);
      metrics.append(metric);
    });
    const removed = nodes.get(changes.removed_node_id);
    const note = document.createElement("p");
    note.className = "experiment-abu-note";
    const pathResult = changes.affected_paths.length
      ? `${changes.affected_paths.length}条路径在这里断开`
      : "当前获批路径没有因此断开";
    const retained = changes.unaffected_paths.length
      ? `，另有${changes.unaffected_paths.length}条路径仍然存在`
      : "";
    note.textContent = `你刚才拿开的是${removed?.label || "这个节点"}。${changes.invalidated_edges.length}条关系消失，${pathResult}${retained}。现实中会怎样表现，还需要专业推理。`;
    panel.append(heading, metrics, note);
    return panel;
  }
}

class PerformanceTimelinePlayer {
  constructor({ actorRenderer, stageRenderer, onEnded }) {
    this.actorRenderer = actorRenderer;
    this.stageRenderer = stageRenderer;
    this.onEnded = onEnded;
    this.audio = null;
    this.package = null;
    this.frame = 0;
  }

  load(performancePackage, audioUrl, assets) {
    this.destroyAudio();
    this.package = performancePackage;
    this.audio = new Audio(audioUrl);
    this.audio.preload = "auto";
    this.actorRenderer.loadAssets(assets);
    this.actorRenderer.reset();
    this.stageRenderer.load(performancePackage);
    this.audio.addEventListener("play", () => {
      state.performancePhase = "playing";
      el.playPauseButton.textContent = "Ⅱ";
      el.playPauseButton.setAttribute("aria-label", "暂停");
      el.performanceStatus.textContent = "阿布正在讲这份命盘";
      el.liveCaption.textContent = "阿布开始讲了。声音、字幕与命盘舞台正在同步前进。";
      this.tick();
    });
    this.audio.addEventListener("pause", () => {
      if (state.performancePhase === "playing") state.performancePhase = "paused";
      el.playPauseButton.textContent = "▶";
      el.playPauseButton.setAttribute("aria-label", "播放");
      cancelAnimationFrame(this.frame);
    });
    this.audio.addEventListener("ended", () => {
      cancelAnimationFrame(this.frame);
      this.stageRenderer.complete();
      this.actorRenderer.setAction({ action: "listen" });
      el.performanceStatus.textContent = "这一幕已经说完";
      el.liveCaption.textContent = "这一幕说完了。选择你想继续看的方向。";
      this.onEnded();
    });
    el.durationTime.textContent = formatTime(performancePackage.audio.duration_ms);
    el.elapsedTime.textContent = "0:00";
    el.performanceProgress.value = "0";
    el.liveCaption.textContent = "声音准备好后，阿布会从这里开始讲。";
    renderTimeline(performancePackage);
  }

  async toggle() {
    if (!this.audio) return;
    if (this.audio.paused) await this.audio.play();
    else this.audio.pause();
  }

  replay() {
    if (!this.audio) return;
    this.audio.pause();
    this.audio.currentTime = 0;
    this.actorRenderer.reset();
    this.stageRenderer.reset();
    state.performancePhase = "ready";
    state.textFallback = false;
    el.liveCaption.textContent = "阿布会从头重新讲这一幕。";
    renderInteraction(currentView());
    this.audio.play().catch((error) => showToast(`无法播放：${error.message}`));
  }

  seek(ratio) {
    if (!this.audio || !Number.isFinite(this.audio.duration)) return;
    this.audio.currentTime = Math.max(0, Math.min(1, ratio)) * this.audio.duration;
    this.stageRenderer.reset();
    this.render(this.audio.currentTime * 1000);
  }

  setMuted(muted) { if (this.audio) this.audio.muted = muted; }

  tick() {
    if (!this.audio || this.audio.paused) return;
    this.render(this.audio.currentTime * 1000);
    this.frame = requestAnimationFrame(() => this.tick());
  }

  render(milliseconds) {
    const duration = this.package?.audio?.duration_ms || 1;
    el.elapsedTime.textContent = formatTime(milliseconds);
    el.performanceProgress.value = String(Math.round(milliseconds / duration * 1000));
    const subtitle = activeBetween(this.package?.subtitle_track || [], milliseconds);
    if (subtitle) {
      el.abuDialogue.textContent = subtitle.text;
      el.abuDialogue.classList.remove("hidden");
      el.subtitle.textContent = "阿布正在按冻结的原台词讲述";
      el.liveCaption.textContent = subtitle.text;
    }
    this.actorRenderer.setAction(latestAt(this.package?.actor_track || [], milliseconds));
    this.actorRenderer.setVoiceActivity(latestAt(this.package?.viseme_track || [], milliseconds));
    this.stageRenderer.renderAt(milliseconds);
  }

  pause() { this.audio?.pause(); }

  destroyAudio() {
    cancelAnimationFrame(this.frame);
    if (this.audio) {
      this.audio.pause();
      this.audio.removeAttribute("src");
      this.audio.load();
    }
    this.audio = null;
  }
}

const actorRenderer = new WebPActorRenderer(el.abuActor, el.actorState);
const stageRenderer = new MingliStageRenderer(el.mingliStage);
const experimentRenderer = new MingliExperimentRenderer(el.mingliExperiment, {
  onSelect: predictExperimentNode,
});
const performancePlayer = new PerformanceTimelinePlayer({
  actorRenderer,
  stageRenderer,
  onEnded: () => {
    state.performancePhase = "completed";
    renderInteraction(currentView());
  },
});

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  let payload = {};
  try { payload = await response.json(); } catch (_) { /* empty */ }
  if (!response.ok) throw new Error(payload.detail || `请求失败 ${response.status}`);
  return payload;
}

async function bootstrap() {
  try {
    const auth = await api("/api/v50/product/auth/me");
    state.account = auth.account;
    if (state.account.account_role === "admin") {
      el.studioToggle.classList.remove("hidden");
    }
    const response = await api("/api/v50/agent/cases");
    state.cases = response.cases || [];
    renderCases();
  } catch (_) {
    el.caseHint.textContent = "你可以先完整旁听；登录并建立正式案例后，阿布会打开私人命盘镜头。";
  }
  bindActions();
  renderProgramChoice();
  const urlSession = new URLSearchParams(location.search).get("session");
  if (urlSession) state.sessionId = urlSession;
  if (state.sessionId && state.participantRunId && state.accessToken) {
    try {
      state.snapshot = await loadSnapshot();
      showPerformance();
      renderSnapshot(state.snapshot);
      connectStream();
      return;
    } catch (_) {
      clearLocalRun();
    }
  }
  el.lobby.classList.remove("hidden");
}

function renderCases() {
  if (!state.cases.length) {
    el.caseHint.textContent = "当前账户还没有可用的正式案例，本场将以旁听模式进入。";
    return;
  }
  state.cases.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.case_id;
    const pillars = item.pillars?.join(" · ") || "命盘已建立";
    option.textContent = `${item.profile_name || "我的命盘"} · ${pillars}`;
    el.caseSelect.append(option);
  });
  el.caseSelect.value = state.cases[0].case_id;
  el.caseHint.textContent = "私人镜头只读取这份案例中已经正式提交的认知。";
}

function bindActions() {
  el.programSelect.addEventListener("change", renderProgramChoice);
  el.enterSolo.addEventListener("click", () => createAndJoin("solo"));
  el.createLive.addEventListener("click", () => createAndJoin("live"));
  el.joinLive.addEventListener("click", () => joinExisting(el.sessionCode.value.trim()));
  el.studioToggle.addEventListener("click", () => el.directorDock.classList.toggle("hidden"));
  el.directorDock.addEventListener("click", async (event) => {
    const action = event.target.dataset.director;
    if (!action) return;
    try {
      const path = action === "advance" ? "advance" : action;
      await api(`${API}/sessions/${state.sessionId}/director/${path}`, {
        method: "POST",
        body: action === "advance" ? JSON.stringify({ event: "next" }) : undefined,
      });
      state.snapshot = await loadSnapshot();
      renderSnapshot(state.snapshot);
    } catch (error) { showToast(error.message); }
  });
  el.replayButton.addEventListener("click", playReplay);
  el.playPauseButton.addEventListener("click", () => performancePlayer.toggle().catch((error) => showToast(error.message)));
  el.transportReplayButton.addEventListener("click", () => performancePlayer.replay());
  el.muteButton.addEventListener("click", () => {
    const muted = el.muteButton.dataset.muted !== "true";
    el.muteButton.dataset.muted = String(muted);
    el.muteButton.textContent = muted ? "静" : "音";
    el.muteButton.setAttribute("aria-label", muted ? "取消静音" : "静音");
    performancePlayer.setMuted(muted);
  });
  el.performanceProgress.addEventListener("input", () => performancePlayer.seek(Number(el.performanceProgress.value) / 1000));
  el.textFallbackButton.addEventListener("click", showTextFallback);
  el.leaveSession.addEventListener("click", leaveSession);
}

async function createAndJoin(mode) {
  const program = selectedProgram();
  const topicId = program.value;
  if (program.dataset.requiresCase === "true" && !el.caseSelect.value) {
    showToast("结构实验需要一份已经提交正式认知的命理案例。");
    return;
  }
  setBusy(true, mode === "live" ? "正在建立现场…" : "正在打开个人场…");
  try {
    const created = await api(`${API}/sessions`, {
      method: "POST",
      body: JSON.stringify({ topic_id: topicId, topic_version: "1.0.0", mode }),
    });
    await joinSession(created.session.session_id);
    history.replaceState({}, "", `/theater?session=${encodeURIComponent(state.sessionId)}`);
  } catch (error) {
    showToast(error.message);
  } finally { setBusy(false); }
}

function renderProgramChoice() {
  const program = selectedProgram();
  const experiment = program.dataset.experience === "mingli_experiment";
  el.lobbyTitle.textContent = program.dataset.title || "进入阿布的命理剧场。";
  el.lobbyIntro.textContent = program.dataset.intro || "选择一份命盘，开始本场探索。";
  el.enterSolo.firstChild.textContent = experiment ? "进入结构实验 " : "进入个人场 ";
  el.createLive.classList.toggle("hidden", experiment || state.account?.account_role !== "admin");
}

function selectedProgram() {
  return el.programSelect.selectedOptions[0] || el.programSelect.options[0];
}

function topicCapabilities(snapshot) {
  return new Set(snapshot?.topic?.required_experience_capabilities || []);
}

async function joinExisting(sessionId) {
  if (!sessionId) return showToast("请输入现场编号");
  setBusy(true, "正在进入现场…");
  try { await joinSession(sessionId); }
  catch (error) { showToast(error.message); }
  finally { setBusy(false); }
}

async function joinSession(sessionId) {
  const caseId = el.caseSelect.value || null;
  const joined = await api(`${API}/sessions/${sessionId}/join`, {
    method: "POST",
    body: JSON.stringify({
      case_id: caseId,
      disclosure_level: caseId ? "approved_insights" : "observer",
    }),
  });
  state.sessionId = sessionId;
  state.participantRunId = joined.participant_run.participant_run_id;
  state.accessToken = joined.access_token;
  state.snapshot = joined.snapshot;
  localStorage.setItem("deepbazi.theater.session", state.sessionId);
  localStorage.setItem("deepbazi.theater.run", state.participantRunId);
  localStorage.setItem("deepbazi.theater.token", state.accessToken);
  showPerformance();
  renderSnapshot(state.snapshot);
  connectStream();
}

function showPerformance() {
  window.scrollTo({ top: 0, behavior: "instant" });
  el.lobby.classList.add("hidden");
  el.performance.classList.remove("hidden");
  el.leaveSession.classList.remove("hidden");
}

function leaveSession() {
  if (state.socket) state.socket.close();
  if (state.pollTimer) clearInterval(state.pollTimer);
  clearLocalRun();
  state.snapshot = null;
  state.lastCueId = "";
  state.activePerformanceCueId = "";
  state.performancePackage = null;
  state.performancePhase = "idle";
  state.textFallback = false;
  state.experimentPayload = null;
  state.experimentLoading = false;
  state.experimentError = "";
  performancePlayer.destroyAudio();
  stageRenderer.reset();
  experimentRenderer.reset();
  el.performanceTransport.classList.add("hidden");
  el.mingliStage.classList.add("hidden");
  el.theaterShell.dataset.act = "act-1-seen";
  history.replaceState({}, "", "/theater");
  el.performance.classList.add("hidden");
  el.directorDock.classList.add("hidden");
  el.leaveSession.classList.add("hidden");
  el.lobby.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadSnapshot(after = 0) {
  const query = new URLSearchParams({
    participant_run_id: state.participantRunId,
    access_token: state.accessToken,
    after: String(after),
  });
  return api(`${API}/sessions/${state.sessionId}?${query}`);
}

function connectStream() {
  if (state.socket) state.socket.close();
  if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = null; }
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const query = new URLSearchParams({
    participant_run_id: state.participantRunId,
    access_token: state.accessToken,
    after: String(state.snapshot?.session?.sequence || 0),
  });
  const socket = new WebSocket(`${protocol}//${location.host}${API}/sessions/${state.sessionId}/stream?${query}`);
  state.socket = socket;
  socket.addEventListener("open", () => {
    state.reconnectAttempts = 0;
    el.connectionState.textContent = "现场已连接";
  });
  socket.addEventListener("message", (event) => {
    const update = JSON.parse(event.data);
    if (mergeSnapshot(update)) renderSnapshot(state.snapshot);
  });
  socket.addEventListener("close", () => {
    el.connectionState.textContent = "正在恢复连接";
    state.reconnectAttempts += 1;
    if (!state.sessionId) return;
    if (state.reconnectAttempts <= 3) setTimeout(connectStream, 1200 * state.reconnectAttempts);
    else startHttpPolling();
  });
}

function startHttpPolling() {
  el.connectionState.textContent = "现场已同步";
  state.pollTimer = setInterval(async () => {
    try {
      const cursor = state.snapshot?.session?.sequence || 0;
      const update = await loadSnapshot(cursor);
      if (update.events?.length && mergeSnapshot(update)) renderSnapshot(state.snapshot);
    } catch (_) {
      el.connectionState.textContent = "等待网络恢复";
    }
  }, 1200);
}

function mergeSnapshot(update) {
  if (!state.snapshot || !update.recovered) {
    state.snapshot = update;
    return true;
  }
  const currentSequence = Number(state.snapshot.session?.sequence || 0);
  const updateSequence = Number(update.session?.sequence || 0);
  if (updateSequence <= currentSequence) return false;
  const cues = new Map((state.snapshot.cues || []).map((item) => [item.cue_instance_id, item]));
  (update.cues || []).forEach((item) => cues.set(item.cue_instance_id, item));
  const events = new Map((state.snapshot.events || []).map((item) => [item.event_id, item]));
  (update.events || []).forEach((item) => events.set(item.event_id, item));
  state.snapshot = {
    ...state.snapshot,
    ...update,
    events: [...events.values()].sort((left, right) => left.sequence - right.sequence),
    cues: [...cues.values()],
    assets: { ...(state.snapshot.assets || {}), ...(update.assets || {}) },
  };
  return true;
}

function renderSnapshot(snapshot) {
  if (!snapshot) return;
  const { session, participant, scene, topic } = snapshot;
  const capabilities = topicCapabilities(snapshot);
  const isProof = capabilities.has("performance_package");
  const isExperiment = capabilities.has("single_node_ablation");
  el.programMode.textContent = isExperiment ? "阿布说命 · 结构实验" : isProof ? "阿布命盘剧场" : session.mode === "live" ? "阿布生命剧场 · LIVE" : session.mode === "time_shift" ? "阿布生命剧场 · 时空场" : "阿布生命剧场 · 个人场";
  el.topicEyebrow.textContent = isExperiment ? "EXECUTABLE MINGLI" : isProof ? "PRIVATE MINGLI PERFORMANCE" : `ABU LIVING THEATER · ${session.mode.toUpperCase()}`;
  el.topicTitle.textContent = topic?.title || "阿布生命剧场";
  el.actRail.classList.toggle("hidden", isProof || isExperiment);
  el.participantCount.textContent = session.participant_count;
  el.connectionState.textContent = session.status === "paused" ? "现场暂停" : session.status === "completed" ? "本场完成" : "现场进行中";
  el.theaterShell.dataset.act = scene.act;
  document.querySelectorAll(".act-rail li").forEach((item) => item.classList.toggle("active", item.dataset.act === scene.act));
  el.sceneLabel.textContent = isExperiment ? "一次结构消融实验" : isProof ? "只属于你的命盘镜头" : scene.act === "act-1-seen" ? "第一幕 · 被看见" : scene.act === "act-2-not-casual" ? "第二幕 · 判断的来处" : "第三幕 · 留给未来";
  if (!isExperiment || scene.interaction.kind !== "mingli_experiment") experimentRenderer.hide();

  const visibleEvents = snapshot.events || [];
  const cueEvent = [...visibleEvents].reverse().find((item) => item.event_type === "cue_frozen");
  if (cueEvent && cueEvent.cue_instance_id !== state.lastCueId) {
    state.lastCueId = cueEvent.cue_instance_id;
    animateCue(cueEvent, snapshot.assets || {});
  }
  const trace = [...visibleEvents].reverse().find((item) => ["group_trace_revealed", "group_trace_suppressed"].includes(item.event_type));
  renderGroupTrace(trace);
  renderInteraction({ session, participant, scene });
  el.replayButton.classList.toggle("hidden", session.status !== "completed");
}

function animateCue(event, assets) {
  const body = event.payload || {};
  const cue = (state.snapshot?.cues || []).find((item) => item.cue_instance_id === event.cue_instance_id);
  const isPerformanceCue = cue?.template_id?.startsWith("proof-");
  el.abuDialogue.classList.add("hidden");
  el.subtitle.classList.add("hidden");
  if (isPerformanceCue) {
    state.activePerformanceCueId = cue.cue_instance_id;
    state.performancePhase = "preparing";
    state.textFallback = false;
    el.performanceTransport.classList.remove("hidden");
    el.playPauseButton.disabled = true;
    el.performanceStatus.textContent = "阿布正在准备这一次声音";
    el.liveCaption.textContent = "阿布正在整理声音、动作和命盘。";
    el.abuActor.src = assets["abu-divination"]?.uri || el.abuActor.src;
    el.actorState.textContent = "正在准备";
    preparePerformance(cue, assets);
  }
  window.setTimeout(() => {
    if (!isPerformanceCue || state.performancePhase === "preparing") {
      el.abuDialogue.textContent = isPerformanceCue ? "阿布正在把声音、动作和命盘放到同一条时间线上。" : body.dialogue || "阿布正在听。";
      el.subtitle.textContent = isPerformanceCue ? "第一次会生成并冻结声音；之后的回放不会重新生成。" : body.subtitle || "";
    }
    const actor = body.actor_commands?.[0];
    const asset = actor?.motion_asset ? assets[actor.motion_asset] : null;
    if (asset?.uri) el.abuActor.src = asset.uri;
    const background = (body.stage_commands || []).find((item) => item.command === "set_background" && item.asset_ref);
    if (background && assets[background.asset_ref]?.uri) {
      document.querySelector(".stage-background").style.backgroundImage = `url("${assets[background.asset_ref].uri}")`;
    }
    el.abuDialogue.classList.remove("hidden");
    el.subtitle.classList.remove("hidden");
  }, 170);
}

async function preparePerformance(cue, assets) {
  try {
    const response = await api(`${API}/sessions/${state.sessionId}/cues/${cue.cue_instance_id}/performance`, {
      method: "POST",
      body: JSON.stringify({ participant_run_id: state.participantRunId, access_token: state.accessToken }),
    });
    if (state.activePerformanceCueId !== cue.cue_instance_id) return;
    state.performancePackage = response.package;
    state.performancePhase = "ready";
    const query = new URLSearchParams({ participant_run_id: state.participantRunId, access_token: state.accessToken });
    const audioUrl = `${API}/sessions/${state.sessionId}/performance/${response.package.package_id}/audio?${query}`;
    performancePlayer.load(response.package, audioUrl, assets);
    el.playPauseButton.disabled = false;
    el.performanceStatus.textContent = "声音已经准备好，点击播放";
    el.liveCaption.textContent = "声音准备好了。点击播放，让阿布亲自讲给你听。";
    el.abuDialogue.textContent = "这一幕已经冻结。准备好后，让阿布亲自讲给你听。";
    el.subtitle.textContent = "声音、字幕、阿布动作与命盘舞台会沿同一条时间线前进。";
    renderInteraction(currentView());
  } catch (error) {
    if (state.activePerformanceCueId !== cue.cue_instance_id) return;
    state.performancePhase = "fallback";
    el.performanceStatus.textContent = "声音暂时没有准备好";
    el.playPauseButton.disabled = true;
    showTextFallback();
    showToast("声音暂时不可用，已经完整切换为文字，不会阻断本场。", 4200);
  }
}

function renderGroupTrace(event) {
  if (!event) return el.groupTrace.classList.add("hidden");
  el.groupTrace.classList.remove("hidden");
  if (event.event_type === "group_trace_suppressed") {
    el.groupTrace.textContent = "人数尚不足以形成匿名群体痕迹，这一幕安静保留。";
    return;
  }
  el.groupTrace.textContent = Object.entries(event.payload.choice_counts || {}).map(([key, value]) => `${key} ${value}`).join(" · ");
}

function renderInteraction({ session, participant, scene }) {
  el.interactionControls.replaceChildren();
  if (session.status === "completed") {
    el.interactionKicker.textContent = "本场完成";
    el.interactionPrompt.textContent = "这不是结论的终点，而是下次继续的起点。";
    el.interactionPrivacy.textContent = "回放会使用今晚冻结的原台词和动作，不会重新生成。";
    return;
  }
  if (participant?.status === "private_scene" && scene.visibility === "participant_private") {
    if (scene.interaction.kind === "mingli_experiment") {
      renderExperimentInteraction();
      return;
    }
    const performancePending = state.activePerformanceCueId
      && !state.textFallback
      && !["completed", "fallback"].includes(state.performancePhase);
    if (performancePending) {
      el.interactionKicker.textContent = "这一幕正在进行";
      el.interactionPrompt.textContent = state.performancePhase === "preparing"
        ? "阿布正在把声音和命盘舞台编成同一场表演"
        : "先听阿布说完，再选择你想继续的方向";
      el.interactionPrivacy.textContent = "本场只使用已经冻结的案例认知；播放和重播都不会重新测算。";
      const note = document.createElement("span");
      note.className = "waiting-note";
      note.textContent = state.performancePhase === "preparing" ? "正在准备声音" : "你也可以切换为完整文字";
      el.interactionControls.append(note);
      return;
    }
    el.interactionKicker.textContent = "你的私人镜头";
    el.interactionPrompt.textContent = scene.interaction.prompt || "准备好时继续";
    el.interactionPrivacy.textContent = "这条回答只进入你的 Participant Run，不进入公共流，也不会自动改写 LifeCase。";
    if (scene.interaction.kind === "choice") {
      scene.interaction.options.forEach((option) => {
        const button = document.createElement("button");
        button.className = "choice-button";
        button.textContent = option;
        button.addEventListener("click", () => completePrivate(option));
        el.interactionControls.append(button);
      });
    } else if (scene.interaction.kind === "capsule") {
      const input = document.createElement("input");
      input.className = "capsule-input";
      input.maxLength = 800;
      input.placeholder = "三个月后，我希望自己记得……";
      const button = actionButton("封存这句话", () => completePrivate(input.value));
      el.interactionControls.append(input, button);
    } else {
      el.interactionControls.append(actionButton("我看见了，继续", () => completePrivate("")));
    }
    return;
  }
  if (participant?.status === "at_barrier") {
    el.interactionKicker.textContent = "等待汇合";
    el.interactionPrompt.textContent = "你的私人镜头已经完成。";
    el.interactionPrivacy.textContent = session.mode === "live" ? "其他人完成后，阿布会带大家回到同一个公共场景。" : "阿布正在带你回到主线。";
    const note = document.createElement("span"); note.className = "waiting-note"; note.textContent = "私人内容已安全保存";
    el.interactionControls.append(note);
    return;
  }
  el.interactionKicker.textContent = session.mode === "live" ? "共享时钟" : "继续这场探索";
  el.interactionPrompt.textContent = scene.interaction.prompt || "准备好时进入下一幕";
  el.interactionPrivacy.textContent = session.mode === "live" ? "现场节奏由阿布导演台统一推进。" : "你的个人场会沿同一份 CompiledTopic 前进。";
  if (session.mode === "live") {
    const note = document.createElement("span"); note.className = "waiting-note"; note.textContent = "等待阿布推进现场";
    el.interactionControls.append(note);
  } else {
    el.interactionControls.append(actionButton("继续", advanceSolo));
  }
}

function renderExperimentInteraction() {
  if (!state.experimentPayload && !state.experimentLoading && !state.experimentError) {
    loadExperiment();
  }
  el.interactionKicker.textContent = "实验分支";
  if (state.experimentLoading) {
    el.interactionPrompt.textContent = "阿布正在打开已批准的命局结构";
    el.interactionPrivacy.textContent = "只读取正式认知，并重建确定性 Graph；不会调用 LLM，也不会修改 LifeCase。";
    const note = document.createElement("span");
    note.className = "waiting-note";
    note.textContent = "正在核对四柱、路径与版本";
    el.interactionControls.append(note);
    return;
  }
  if (state.experimentError) {
    el.interactionPrompt.textContent = "这份案例目前还不能安全进入结构实验";
    el.interactionPrivacy.textContent = state.experimentError;
    experimentRenderer.showError(`阿布没有替你猜一条路径：${state.experimentError}`);
    el.interactionControls.append(actionButton("结束本场", () => completePrivate("experiment_unavailable")));
    return;
  }
  const payload = state.experimentPayload;
  if (!payload) return;
  experimentRenderer.load(payload);
  const sandbox = payload.sandbox_state;
  const result = payload.sandbox_result;
  const nodeMap = new Map((payload.snapshot.nodes || []).map((item) => [item.node_id, item]));
  const predicted = nodeMap.get(sandbox.predicted_key_node_id);
  const removed = nodeMap.get(result?.deterministic_changes?.removed_node_id);
  if (!sandbox.predicted_key_node_id) {
    el.interactionPrompt.textContent = "先猜一个你认为不可替代的节点";
    el.interactionPrivacy.textContent = "点击四柱或路径中的一个字。此时只是记录你的猜测，不会重新计算。";
    const note = document.createElement("span");
    note.className = "waiting-note";
    note.textContent = "从上方命盘中选择";
    el.interactionControls.append(note);
    return;
  }
  if (!result) {
    el.interactionPrompt.textContent = `你猜的是“${predicted?.label || "这个节点"}”`;
    el.interactionPrivacy.textContent = "下一步会进入确定性结构消融：相关边和路径完整性会重新计算，现实含义不会在这里生成。";
    el.interactionControls.append(actionButton(`暂时拿开 ${predicted?.label || "这个节点"}`, () => ablateExperimentNode(sandbox.predicted_key_node_id)));
    return;
  }
  if (sandbox.status === "modified") {
    const changes = result.deterministic_changes;
    el.interactionPrompt.textContent = `拿开“${removed?.label || "节点"}”后，${changes.affected_paths.length}条路径受到影响`;
    el.interactionPrivacy.textContent = "结构差异已经确定；任何现实人生含义仍标记为 reasoning_required。请先恢复原局。";
    el.interactionControls.append(actionButton("恢复原局", restoreExperiment));
    return;
  }
  if (sandbox.status === "restored") {
    el.interactionPrompt.textContent = "原局已经恢复。留下你看见的变化。";
    el.interactionPrivacy.textContent = "这段观察只保存为本次 TopicExploration，不会自动写入正式认知。";
    const form = document.createElement("div");
    form.className = "experiment-form";
    const observation = document.createElement("input");
    observation.maxLength = 1200;
    observation.placeholder = "我观察到……（可留空）";
    const question = document.createElement("input");
    question.maxLength = 1200;
    question.placeholder = "我还想问……（可留空）";
    const save = actionButton("保存这次探索", () => saveExperiment(observation.value, question.value));
    form.append(observation, question, save);
    el.interactionControls.append(form);
    return;
  }
  el.interactionPrompt.textContent = "这次结构实验已经保存";
  el.interactionPrivacy.textContent = "原命盘和正式 LifeCase 均未改变。";
  el.interactionControls.append(actionButton("完成本场", () => completePrivate("experiment_saved")));
}

async function loadExperiment() {
  state.experimentLoading = true;
  state.experimentError = "";
  renderInteraction(currentView());
  try {
    const query = new URLSearchParams({
      participant_run_id: state.participantRunId,
      access_token: state.accessToken,
    });
    state.experimentPayload = await api(`${API}/sessions/${state.sessionId}/participant/experiment?${query}`);
    experimentRenderer.load(state.experimentPayload);
    el.abuDialogue.textContent = "一张命盘里，出现次数最多的字，不一定最关键。先猜一个，再亲手把它暂时拿开。";
    el.subtitle.textContent = "实验分支 · 原命盘不会改变";
  } catch (error) {
    state.experimentError = friendlyExperimentError(error.message);
  } finally {
    state.experimentLoading = false;
    renderInteraction(currentView());
  }
}

async function predictExperimentNode(nodeId) {
  if (!state.experimentPayload || state.experimentPayload.sandbox_result) return;
  try {
    state.experimentPayload = await experimentPost("predict", { node_id: nodeId });
    const node = state.experimentPayload.snapshot.nodes.find((item) => item.node_id === nodeId);
    el.abuDialogue.textContent = `你先选了“${node?.label || "这个节点"}”。现在，我们只看把它拿开后，结构会发生什么。`;
    el.subtitle.textContent = "你的猜测已经锁定；下一步才会执行确定性重算。";
    renderExperimentInteraction();
  } catch (error) { showToast(error.message); }
}

async function ablateExperimentNode(nodeId) {
  try {
    state.experimentPayload = await experimentPost("ablate", { node_id: nodeId });
    const result = state.experimentPayload.sandbox_result;
    const node = state.experimentPayload.snapshot.nodes.find((item) => item.node_id === nodeId);
    const changes = result.deterministic_changes;
    el.abuDialogue.textContent = `拿开“${node?.label || "这个节点"}”后，${changes.invalidated_edges.length}条关系消失，${changes.affected_paths.length}条路径受到影响。`;
    el.subtitle.textContent = changes.unaffected_paths.length
      ? `还有${changes.unaffected_paths.length}条路径保留；现实含义仍需专业推理。`
      : "当前展示路径均受影响；现实含义仍需专业推理。";
    experimentRenderer.load(state.experimentPayload);
    renderExperimentInteraction();
  } catch (error) { showToast(error.message); }
}

async function restoreExperiment() {
  try {
    state.experimentPayload = await experimentPost("restore");
    el.abuDialogue.textContent = "原来的节点、关系和路径已经全部回到原位。刚才发生的，只是一条实验分支。";
    el.subtitle.textContent = "原命盘没有改变 · 正式认知没有改变";
    experimentRenderer.load(state.experimentPayload);
    renderExperimentInteraction();
  } catch (error) { showToast(error.message); }
}

async function saveExperiment(observation, openQuestion) {
  try {
    state.experimentPayload = await experimentPost("save", {
      observation,
      open_question: openQuestion,
    });
    el.abuDialogue.textContent = "我把这次观察保存在专题探索里了。它会留给你继续思考，但不会悄悄改写正式命局。";
    el.subtitle.textContent = "TopicExploration 已保存 · LifeCase 未修改";
    renderExperimentInteraction();
  } catch (error) { showToast(error.message); }
}

async function experimentPost(action, fields = {}) {
  return api(`${API}/sessions/${state.sessionId}/participant/experiment/${action}`, {
    method: "POST",
    body: JSON.stringify({
      participant_run_id: state.participantRunId,
      access_token: state.accessToken,
      ...fields,
    }),
  });
}

function friendlyExperimentError(message) {
  const labels = {
    approved_personal_cognition_required: "需要一份已经正式提交、且属于你的整盘认知。",
    experiment_case_reference_missing: "当前场次没有关联到可追踪的命理案例。",
    approved_cognitive_record_required: "这份命盘还没有形成可用于实验的正式认知。",
    approved_path_not_uniquely_reconstructable: "正式认知中的路径暂时无法与当前 Graph 唯一对应。",
    baseline_record_mismatch: "正式基线与当前认知版本不一致，需要先完成案例收敛。",
    topic_does_not_permit_structural_ablation: "当前节目没有结构实验权限。",
  };
  return labels[message] || message;
}

function actionButton(label, handler) {
  const button = document.createElement("button");
  button.className = "primary-action";
  button.innerHTML = `${label} <span>→</span>`;
  button.addEventListener("click", handler);
  return button;
}

async function advanceSolo() {
  try {
    await api(`${API}/sessions/${state.sessionId}/participant/advance`, {
      method: "POST",
      body: JSON.stringify({ participant_run_id: state.participantRunId, access_token: state.accessToken, event: "next" }),
    });
    state.snapshot = await loadSnapshot();
    renderSnapshot(state.snapshot);
  } catch (error) { showToast(error.message); }
}

async function completePrivate(response) {
  try {
    await api(`${API}/sessions/${state.sessionId}/participant/complete`, {
      method: "POST",
      body: JSON.stringify({ participant_run_id: state.participantRunId, access_token: state.accessToken, response }),
    });
    state.snapshot = await loadSnapshot();
    renderSnapshot(state.snapshot);
  } catch (error) { showToast(error.message); }
}

async function playReplay() {
  try {
    if (state.performancePackage) {
      performancePlayer.replay();
      return;
    }
    const query = new URLSearchParams({ participant_run_id: state.participantRunId, access_token: state.accessToken });
    const replay = await api(`${API}/sessions/${state.sessionId}/replay?${query}`);
    const cueEvents = replay.events.filter((item) => item.event_type === "cue_frozen");
    let index = 0;
    const play = () => {
      if (index >= cueEvents.length) return showToast("回放完成：没有重新调用 LLM、Reasoner 或 TTS。", 3800);
      animateCue(cueEvents[index], state.snapshot.assets || {});
      index += 1;
      setTimeout(play, 2300);
    };
    play();
  } catch (error) { showToast(error.message); }
}

function showTextFallback() {
  const cue = (state.snapshot?.cues || []).find((item) => item.cue_instance_id === state.activePerformanceCueId);
  if (!cue) return;
  performancePlayer.pause();
  state.textFallback = true;
  state.performancePhase = "fallback";
  el.abuDialogue.textContent = cue.final_dialogue;
  el.abuDialogue.classList.remove("hidden");
  el.subtitle.textContent = "完整原文已经展开；没有新增或改写任何命理判断。";
  el.subtitle.classList.remove("hidden");
  if (state.performancePackage) stageRenderer.complete();
  el.performanceStatus.textContent = "当前使用完整文字版本";
  el.liveCaption.textContent = "已切换为完整文字。命理内容没有新增或改写。";
  el.actorState.textContent = "等你继续";
  renderInteraction(currentView());
}

function currentView() {
  return {
    session: state.snapshot?.session || {},
    participant: state.snapshot?.participant || null,
    scene: state.snapshot?.scene || {},
  };
}

function renderTimeline(performancePackage) {
  const labels = {
    reset: "舞台渐亮",
    reveal_chart_fact: "四柱进入",
    reveal_reasoning_step: "判断路径出现",
    highlight_approved_path: "已确认主线点亮",
    show_unresolved_condition: "未决条件保留",
  };
  el.timelineList.replaceChildren();
  (performancePackage.stage_track || []).forEach((event) => {
    const item = document.createElement("li");
    const time = document.createElement("time");
    time.textContent = formatTime(event.at_ms);
    const text = document.createElement("span");
    text.textContent = labels[event.action] || event.action;
    item.append(time, text);
    el.timelineList.append(item);
  });
}

function activeBetween(rows, milliseconds) {
  return rows.find((item) => item.start_ms <= milliseconds && item.end_ms > milliseconds)
    || (milliseconds >= (rows.at(-1)?.end_ms || Infinity) ? rows.at(-1) : null);
}

function latestAt(rows, milliseconds) {
  let selected = null;
  for (const item of rows) {
    if (item.at_ms > milliseconds) break;
    selected = item;
  }
  return selected;
}

function formatTime(milliseconds) {
  const seconds = Math.max(0, Math.round(Number(milliseconds || 0) / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

function relationName(value) {
  const names = {
    generates: "生",
    controls: "克",
    same_element_support: "同气",
    stores: "藏",
    roots: "通根",
    forms_half_combination: "半合",
    forms_triple_combination: "三合",
    clashes: "冲",
    harmonizes: "合",
    activates: "引动",
    bridges: "承接",
    position_link: "同柱",
  };
  return names[value] || value || "关系";
}

function fiveElementClass(value) {
  if ("甲乙寅卯".includes(value)) return "element-wood";
  if ("丙丁巳午".includes(value)) return "element-fire";
  if ("戊己辰戌丑未".includes(value)) return "element-earth";
  if ("庚辛申酉".includes(value)) return "element-metal";
  if ("壬癸亥子".includes(value)) return "element-water";
  return "";
}

function cssEscape(value) {
  return window.CSS?.escape ? window.CSS.escape(String(value || "")) : String(value || "").replace(/[^a-zA-Z0-9_-]/g, "");
}

function setBusy(busy, message = "") {
  el.enterSolo.disabled = busy;
  el.createLive.disabled = busy;
  if (message) showToast(message, 1400);
}

function showToast(message, duration = 2600) {
  el.toast.textContent = message;
  el.toast.classList.remove("hidden");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => el.toast.classList.add("hidden"), duration);
}

function clearLocalRun() {
  state.sessionId = state.participantRunId = state.accessToken = "";
  ["deepbazi.theater.session", "deepbazi.theater.run", "deepbazi.theater.token"].forEach((key) => localStorage.removeItem(key));
}

bootstrap();
