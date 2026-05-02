const state = {
  latest: null,
  activeProfile: null,
  measureTimer: null,
  isMeasuring: false,
  pendingMeasure: false,
  lastMeasureKey: "",
  chatTurns: [],
  chatSeq: 0,
  activeLlmMode: "deterministic",
  practitionerSelections: [],
  latentManifest: null,
  latentAnswers: [],
};
const params = new URLSearchParams(window.location.search);

const form = document.querySelector("#measureForm");
const questionSelect = document.querySelector("#questionSelect");
const roleSelect = document.querySelector("#roleSelect");
const localeSelect = document.querySelector("#localeSelect");
const chatText = document.querySelector("#chatText");
const chatButton = document.querySelector("#chatButton");
const chatTranscript = document.querySelector("#chatTranscript");

const UI_TEXT = {
  zh: {
    app_title: "命理测算台",
    nav_profiles: "档案",
    nav_measure: "测算",
    chart_title: "命盘结构",
    features_title: "八字特征状态",
    portrait_title: "主题投射画像",
    questions_title: "智能问题",
    answer_title: "八字专业回复",
    evidence_title: "证据锚点",
    feedback_title: "反馈校准",
    run: "开始测算",
    running: "测算中",
    roles: { user: "游客", analyst: "命理师" },
  },
  en: {
    app_title: "Bazi Workbench",
    nav_profiles: "Profiles",
    nav_measure: "Reading",
    chart_title: "Chart Structure",
    features_title: "Bazi Feature States",
    portrait_title: "Topic Projection",
    questions_title: "Smart Questions",
    answer_title: "Professional Bazi Reply",
    evidence_title: "Evidence Anchors",
    feedback_title: "Feedback Calibration",
    run: "Run Reading",
    running: "Reading",
    roles: { user: "Guest", analyst: "Practitioner" },
  },
  ko: {
    app_title: "사주 분석 작업대",
    nav_profiles: "프로필",
    nav_measure: "분석",
    chart_title: "명식 구조",
    features_title: "사주 특징 상태",
    portrait_title: "주제 투사",
    questions_title: "지능형 질문",
    answer_title: "전문 사주 답변",
    evidence_title: "근거 앵커",
    feedback_title: "피드백 보정",
    run: "분석 시작",
    running: "분석 중",
    roles: { user: "게스트", analyst: "명리사" },
  },
};

const setText = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value ?? "";
};

const requestJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${detail}`);
  }
  return response.json();
};

const clear = (node) => {
  while (node.firstChild) node.removeChild(node.firstChild);
};

const el = (tag, className = "", text = "") => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
};

const measure = async ({ force = false, interactionText = "", interactionSource = "", llmMode = "deterministic" } = {}) => {
  const text = currentText();
  const payload = payloadFromForm();
  payload.llm_mode = llmMode;
  payload.practitioner_selections = state.practitionerSelections;
  payload.latent_event_answers = state.latentAnswers;
  const key = JSON.stringify(payload);
  if (!force && key === state.lastMeasureKey) return;
  if (!hasCompletePillars(payload)) return;
  if (state.isMeasuring) {
    state.pendingMeasure = true;
    setText("#llmStatus", "排队中");
    return;
  }
  state.isMeasuring = true;
  state.lastMeasureKey = key;
  state.activeLlmMode = llmMode;
  const turnId = interactionText ? appendChatTurn(interactionText, interactionSource || "提问") : "";
  setMeasureBusy(true, text, llmMode);
  setText("#answerText", "正在根据当前问题重新测算。");
  try {
    const role = measurementRole(payload.role_key);
    delete payload.role_key;
    const endpoint = `/api/v20/measure/view/${role}`;
    const result = await requestJson(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.latest = result;
    renderRuntime(result);
    if (turnId) completeChatTurn(turnId, result.answer_text || "", result);
  } catch (error) {
    setText("#answerText", `测算失败：${error.message}`);
    if (turnId) failChatTurn(turnId, error.message);
    state.lastMeasureKey = "";
  } finally {
    state.isMeasuring = false;
    setMeasureBusy(false, currentText(), state.activeLlmMode);
    if (state.pendingMeasure) {
      state.pendingMeasure = false;
      scheduleMeasure({ force: true });
    }
  }
};

const scheduleMeasure = ({ force = false } = {}) => {
  clearTimeout(state.measureTimer);
  state.measureTimer = setTimeout(() => measure({ force }), 280);
};

const renderRuntime = (result) => {
  const selected = result.selected_question || {};
  const chart = result.chart_facts || {};
  const featureLayer = result.feature_layer || {};
  const decisionReport = result.decision_report || {};
  const featureStateModel = result.feature_state_model || {};
  const questionIntentModel = result.question_intent_model || {};
  const interactionSession = result.interaction_session || {};
  const portraitProjection = decisionReport.portrait_projection || {};
  const role = result.role?.role_key || measurementRole(roleSelect.value);

  document.body.dataset.role = role;
  setText("#selectedQuestion", selected.title || selected.question_key || "已完成测算");
  setText("#selectedBoundary", selected.boundary || result.prediction_policy?.core_focus || "");
  setText("#featureCount", featureStateModel.feature_state_count ?? decisionReport.decision_count ?? featureLayer.feature_count ?? 0);
  setText("#questionCount", questionIntentModel.intent_count ?? (result.questions || []).length);
  setText("#knowledgeCount", result.knowledge_report?.count ?? 0);
  setText("#coreCapacity", featureStateModel.algorithm || result.core_inference?.day_master_capacity || "fusion");
  setText("#intentSummary", intentSummary(questionIntentModel));
  setText("#interactionSummary", `${interactionSession.signal_count ?? 0} signals`);
  setText("#dayMasterBadge", `日主 ${chart.day_master || "-"}`);
  setText("#llmStatus", llmStatusLabel(result));
  setText("#answerText", result.answer_text || "");

  renderPillars(chart, result.time_context || {});
  renderTenGods(chart);
  renderFeatures(
    featureStateModel.priority_features ||
      featureStateModel.states ||
      decisionReport.mainlines ||
      decisionReport.decisions ||
      featureLayer.macro_features ||
      featureLayer.features ||
      []
  );
  renderPortrait(portraitProjection.axes || []);
  renderPractitionerCalibration(decisionReport.practitioner_controls || [], result.input_id || "", role);
  renderLatentCalibration(result.input_id || "", role);
  renderQuestions(result.questions || [], selected.question_key || "", questionIntentModel);
  renderQuestionSelect(result.questions || [], selected.question_key || "");
  renderInteractionSignals(interactionSession);
  renderEvidence(
    result.knowledge_refs || [],
    result.decision_validation || {},
    {
      featureStateModel,
      questionIntentModel,
      interactionSession,
      decisionModel: decisionReport.defeasible_decision_model || {},
    }
  );
};

const setMeasureBusy = (busy, text = currentText(), llmMode = "deterministic") => {
  const button = form.querySelector("button[type='submit']");
  button.disabled = busy;
  button.textContent = busy ? text.running : text.run;
  chatButton.disabled = busy;
  chatButton.textContent = busy ? (llmMode === "practitioner" ? "生成中" : "测算中") : "发送";
  document.querySelectorAll(".question-row").forEach((node) => {
    node.disabled = busy;
  });
  if (busy) setText("#llmStatus", llmMode === "practitioner" ? "llm practitioner" : "测算中");
};

const renderPillars = (chart, timeContext = {}) => {
  const root = document.querySelector("#pillarPanel");
  clear(root);
  const pillars = chart.pillars || {};
  const timePillars = Object.fromEntries((timeContext.layers || []).map((layer) => [layer.layer_key, layer.pillar || {}]));
  [
    ["year", "年柱", "原局"],
    ["month", "月柱", "原局"],
    ["day", "日柱", "日主"],
    ["hour", "时柱", "原局"],
    ["luck", "大运", "运势背景"],
    ["flow_year", "流年", "当前触发"],
  ].forEach(([key, label, hint]) => {
    const pillar = pillars[key] || timePillars[key] || fallbackPillar(key);
    const card = el("div", `pillar-card ${key === "day" ? "active" : ""}`);
    card.append(el("span", "", label));
    card.append(el("strong", "", `${pillar.stem || "-"}${pillar.branch || ""}`));
    card.append(el("em", "", hint));
    root.append(card);
  });
};

const renderTenGods = (chart) => {
  const visible = (chart.visible_ten_gods || []).map((row) => row.label).filter(Boolean);
  const hidden = (chart.hidden_ten_gods || []).map((row) => row.label).filter(Boolean);
  setText("#tenGodLine", `透出 ${unique(visible).join(" / ") || "-"} · 藏干 ${unique(hidden).slice(0, 6).join(" / ") || "-"}`);
};

const renderFeatures = (features) => {
  const root = document.querySelector("#featureChips");
  clear(root);
  if (!features.length) {
    root.append(el("div", "empty-note", "当前尚未发现可展示的命理特征。"));
    return;
  }
  features.slice(0, 10).forEach((feature) => {
    const card = el("div", "feature-card");
    card.dataset.domain = feature.domain || "general";
    card.dataset.state = feature.state || feature.status || "available";
    card.append(el("strong", "", feature.label || feature.title || feature.feature_id || feature.macro_id || "feature"));
    const score = feature.priority ?? feature.score ?? feature.discovery_score ?? feature.peak_confidence ?? feature.confidence ?? "-";
    const label = feature.domain_label || feature.domain || "domain";
    const stateLabel = featureStateLabel(feature.state || feature.status || feature.readiness);
    card.append(el("span", "", `${label} · ${stateLabel} · score ${score}`));
    const links = [
      ...(feature.decision_keys || []),
      ...(feature.mainline_keys || []),
      ...(feature.portrait_axis_ids || []),
    ].filter(Boolean);
    if (links.length) card.append(el("p", "", links.slice(0, 3).join(" / ")));
    else if (feature.support) card.append(el("p", "", feature.support.slice(0, 3).join(" / ")));
    else if (feature.reason) card.append(el("p", "", feature.reason));
    else if (feature.summary) card.append(el("p", "", feature.summary));
    const hook = (feature.question_hooks || [feature.question_seed]).filter(Boolean)[0];
    if (hook) card.append(el("p", "feature-question-seed", hook));
    root.append(card);
  });
};

const featureStateLabel = (state) => ({
  active: "已入主链",
  available: "可用",
  evidence_gap: "补证",
  requires_review: "复核",
  blocked_or_countered: "被反证",
  confirmed: "成立",
  candidate: "候选",
  weak_candidate: "弱候选",
  volatile: "岁运引动",
  mixed: "成而不纯",
}[state] || state || "状态");

const renderPortrait = (axes) => {
  const root = document.querySelector("#portraitAxes");
  clear(root);
  if (!axes.length) {
    root.append(el("div", "empty-note", "当前视图隐藏画像投影。"));
    return;
  }
  axes.slice(0, 8).forEach((axis) => {
    const row = el("div", "axis-row");
    row.dataset.domain = axis.domain || "general";
    const score = axis.score ?? axis.intelligence_score ?? axis.peak_confidence ?? axis.alignment_score ?? 0;
    const temperature = portraitTemperature(score);
    row.dataset.temperature = temperature.key;
    const title = el("div", "axis-title-line");
    title.append(el("strong", "", axis.label || axis.axis_id || "动态画像"));
    title.append(el("span", "axis-tag", portraitDomainLabel(axis.domain)));
    title.append(el("span", `axis-temp ${temperature.key}`, temperature.label));
    row.append(title);
    row.append(el("span", "", axis.summary || axis.calibration_state || `${axis.domain || "命理"} · score ${score}`));
    const seeds = (axis.question_seeds || []).filter(Boolean).slice(0, 2);
    const boundaries = (axis.evidence_boundaries || []).filter(Boolean).slice(0, 2);
    if (boundaries.length) row.append(el("p", "", boundaries.join(" / ")));
    else if (seeds.length) row.append(el("p", "", seeds.join(" / ")));
    const meter = el("i");
    meter.style.width = `${Math.round(Number(score || 0) * 100)}%`;
    const bar = el("div", "meter");
    bar.append(meter);
    row.append(bar);
    root.append(row);
  });
};

const portraitDomainLabel = (domain) => ({
  strength: "强弱",
  career: "事业",
  wealth: "财运",
  ten_god: "十神",
  useful_god: "用神",
  time: "时间",
  branch: "地支",
  element: "五行",
  pattern: "格局",
  relationship: "关系",
  health: "健康",
}[domain] || "命理");

const portraitTemperature = (score) => {
  const value = Number(score || 0);
  if (value >= 0.78) return { key: "hot", label: "高关注" };
  if (value >= 0.58) return { key: "warm", label: "成形" };
  if (value >= 0.38) return { key: "mild", label: "待复核" };
  return { key: "cool", label: "线索" };
};

const renderPractitionerCalibration = (controls, inputId, role) => {
  const root = document.querySelector("#practitionerCalibration");
  const list = document.querySelector("#calibrationControls");
  const status = document.querySelector("#calibrationStatus");
  if (!root || !list || !status) return;
  clear(list);
  if (role !== "analyst" || !controls.length) {
    root.hidden = true;
    return;
  }
  root.hidden = false;
  status.textContent = practitionerSessionStatus();
  controls.slice(0, 4).forEach((control) => {
    const row = el("div", "calibration-control");
    row.append(el("strong", "", control.label || control.control_key || "命理师校准"));
    const options = el("div", "calibration-options");
    const selected = state.practitionerSelections.find((item) => item.control_key === control.control_key);
    (control.options || []).forEach((option) => {
      const button = el("button", "", option);
      button.type = "button";
      button.dataset.controlKey = control.control_key || "";
      button.dataset.option = option;
      if (option === control.default) button.classList.add("default");
      if (selected?.option === option) button.classList.add("selected");
      button.addEventListener("click", () => recordPractitionerCalibration(control, option, inputId, button));
      options.append(button);
    });
    row.append(options);
    list.append(row);
  });
};

const recordPractitionerCalibration = async (control, option, inputId, activeButton) => {
  const status = document.querySelector("#calibrationStatus");
  const sourceDecisionKeys = control.source_decision_keys || [];
  if (status) status.textContent = "记录中";
  try {
    const result = await requestJson("/api/v20/practitioner/calibration/record", {
      method: "POST",
      body: JSON.stringify({
        input_id: inputId || state.latest?.input_id || "",
        source_role: "analyst",
        locale: localeSelect.value,
        selections: [{
          control_key: control.control_key,
          option,
          source_decision_keys: sourceDecisionKeys,
        }],
      }),
    });
    document.querySelectorAll(`.calibration-options button[data-control-key="${control.control_key}"]`).forEach((button) => {
      button.classList.toggle("selected", button === activeButton);
    });
    upsertPractitionerSelection(control, option);
    questionSelect.value = "";
    if (status) status.textContent = result.storage?.status === "stored" ? "已记录 · 刷新问题" : "已接收 · 刷新问题";
    measure({ force: true, llmMode: "deterministic" });
  } catch (error) {
    if (status) status.textContent = "记录失败";
  }
};

const upsertPractitionerSelection = (control, option) => {
  const selection = {
    control_key: control.control_key,
    option,
    source_decision_keys: control.source_decision_keys || [],
  };
  state.practitionerSelections = [
    ...state.practitionerSelections.filter((item) => item.control_key !== control.control_key),
    selection,
  ];
};

const renderLatentCalibration = (inputId, role) => {
  const root = document.querySelector("#latentCalibration");
  const list = document.querySelector("#latentCalibrationControls");
  const status = document.querySelector("#latentCalibrationStatus");
  if (!root || !list || !status) return;
  clear(list);
  const scenarios = state.latentManifest?.scenarios || [];
  if (!document.body.classList.contains("profile-reading") || !scenarios.length) {
    root.hidden = true;
    return;
  }
  root.hidden = false;
  status.textContent = state.latentAnswers.length ? `已校准 ${state.latentAnswers.length} 项` : "choice only";
  scenarios.slice(0, 4).forEach((scenario) => {
    const saved = state.latentAnswers.find((answer) => answer.scenario_id === scenario.scenario_id) || {};
    const row = el("div", "latent-calibration-row");
    const title = el("div", "latent-calibration-title");
    title.append(el("strong", "", latentScenarioTitle(scenario)));
    title.append(el("span", "", scenario.prompt || ""));
    row.append(title);
    const fields = el("div", "latent-calibration-fields");
    fields.append(latentSelect(scenario, "year_option", saved.year_option || "unknown", scenario.year_options || [], latentYearLabel));
    fields.append(latentSelect(scenario, "result_option", saved.result_option || (scenario.result_options || ["no_clear_change"])[0], scenario.result_options || [], latentResultLabel));
    fields.append(latentSelect(scenario, "intensity", saved.intensity || "clear", scenario.intensity_options || [], latentIntensityLabel));
    fields.append(latentSelect(scenario, "confidence", saved.confidence || "medium", scenario.confidence_options || [], latentConfidenceLabel));
    const button = el("button", "mini-action", saved.scenario_id ? "已记录" : "记录");
    button.type = "button";
    button.addEventListener("click", () => recordLatentCalibration(scenario, inputId || state.latest?.input_id || "", role, row));
    fields.append(button);
    row.append(fields);
    list.append(row);
  });
};

const latentSelect = (scenario, key, selected, options, labeler) => {
  const label = el("label", "latent-field");
  label.append(el("span", "", latentFieldLabel(key)));
  const select = document.createElement("select");
  select.dataset.scenarioId = scenario.scenario_id || "";
  select.dataset.field = key;
  options.forEach((option) => {
    const node = document.createElement("option");
    node.value = option;
    node.textContent = labeler(option);
    select.append(node);
  });
  select.value = selected;
  label.append(select);
  return label;
};

const recordLatentCalibration = async (scenario, inputId, role, row) => {
  const status = document.querySelector("#latentCalibrationStatus");
  const answer = {
    scenario_id: scenario.scenario_id,
    year_option: row.querySelector('[data-field="year_option"]').value,
    result_option: row.querySelector('[data-field="result_option"]').value,
    intensity: row.querySelector('[data-field="intensity"]').value,
    confidence: row.querySelector('[data-field="confidence"]').value,
  };
  if (status) status.textContent = "记录中";
  try {
    const result = await requestJson("/api/v20/latent-event/calibration/record", {
      method: "POST",
      body: JSON.stringify({
        input_id: inputId,
        source_role: role === "analyst" ? "analyst" : "user",
        locale: localeSelect.value,
        answers: [answer],
      }),
    });
    upsertLatentAnswer(answer);
    questionSelect.value = "";
    if (status) status.textContent = result.storage?.status === "stored" ? "已记录 · 刷新问题" : "已接收 · 刷新问题";
    measure({ force: true, llmMode: "deterministic" });
  } catch (error) {
    if (status) status.textContent = "记录失败";
  }
};

const upsertLatentAnswer = (answer) => {
  state.latentAnswers = [
    ...state.latentAnswers.filter((item) => item.scenario_id !== answer.scenario_id),
    answer,
  ];
};

const renderQuestions = (questions, selectedKey, questionIntentModel = {}) => {
  const root = document.querySelector("#questionList");
  clear(root);
  if (!questions.length) {
    root.append(el("div", "empty-note", "确认四柱后会生成建议问题。"));
    return;
  }
  const bindingByKey = questionBindingByKey(questionIntentModel);
  questions.slice(0, 5).forEach((question) => {
    root.append(questionButton(question, selectedKey, "question-row", bindingByKey[question.question_key] || {}));
  });
};

const questionButton = (question, selectedKey, className, binding = {}) => {
  const button = el("button", `${className}${question.question_key === selectedKey ? " active" : ""}`);
  button.type = "button";
  button.append(el("strong", "", question.title || question.question_key));
  if (className === "question-row") {
    const intent = intentTypeLabel(binding.primary_intent_type);
    const priority = binding.intent_priority ? ` · ${Number(binding.intent_priority).toFixed(2)}` : "";
    button.append(el("span", "", `${question.measurement_topic || question.domain || "命理测算"} · ${intent}${priority}`));
  }
  button.addEventListener("click", () => runQuestion(question));
  return button;
};

const questionBindingByKey = (questionIntentModel = {}) => {
  const rows = questionIntentModel.question_bindings || [];
  return Object.fromEntries(rows.map((row) => [row.question_key, row]));
};

const intentSummary = (questionIntentModel = {}) => {
  const counts = questionIntentModel.intent_type_counts || {};
  const top = Object.entries(counts).sort((a, b) => Number(b[1]) - Number(a[1]))[0];
  return top ? `${intentTypeLabel(top[0])} ${top[1]}` : "intent";
};

const intentTypeLabel = (intentType) => ({
  confirm_structure: "确认结构",
  explore_candidate: "展开候选",
  collect_evidence: "补齐证据",
  resolve_mixed_state: "裁决混合",
  inspect_timing_trigger: "岁运引动",
  ask_practitioner_review: "命理师复核",
  explain_boundary: "边界说明",
  explore_structure: "结构追问",
  suppress_output: "不输出",
}[intentType] || intentType || "智能意图");

const runQuestion = (question) => {
  const title = question.title || question.question_key || "";
  questionSelect.value = question.question_key;
  setInquiryText(title, { syncOnly: true });
  measure({
    force: true,
    interactionText: title,
    interactionSource: "推荐问题",
    llmMode: "practitioner",
  });
};

const renderQuestionSelect = (questions, selectedKey) => {
  const current = questionSelect.value || selectedKey;
  questionSelect.innerHTML = '<option value="">自动路由</option>';
  questions.forEach((question) => {
    const option = document.createElement("option");
    option.value = question.question_key;
    option.textContent = question.title || question.question_key;
    questionSelect.append(option);
  });
  questionSelect.value = current;
};

const renderInteractionSignals = (session = {}) => {
  const root = document.querySelector("#interactionSignals");
  if (!root) return;
  clear(root);
  const signals = session.signals || [];
  const actions = session.next_actions || [];
  if (!signals.length && !actions.length) {
    root.append(el("div", "empty-note", "当前只有选中问题作为会话焦点。"));
    return;
  }
  signals.slice(0, 4).forEach((signal) => {
    const row = el("div", "signal-row");
    row.dataset.type = signal.signal_type || "";
    row.append(el("strong", "", signalTypeLabel(signal.signal_type)));
    row.append(el("span", "", `${portraitDomainLabel(signal.domain)} · ${signal.effect || signal.primary_intent_type || "focus"} · ${signal.strength ?? "-"}`));
    root.append(row);
  });
  actions.slice(0, 3).forEach((action) => {
    const row = el("div", "signal-row action");
    row.append(el("strong", "", actionTypeLabel(action.action_type)));
    row.append(el("span", "", `${portraitDomainLabel(action.domain)} · ${action.reason || "next"}`));
    root.append(row);
  });
};

const signalTypeLabel = (type) => ({
  selected_question: "当前问题",
  practitioner_control: "命理师校准",
  latent_event_answer: "命主反馈",
}[type] || type || "会话信号");

const actionTypeLabel = (type) => ({
  answer_selected_question: "生成回答",
  rerank_followup_questions: "重排追问",
  refresh_evidence_pack: "刷新证据",
}[type] || type || "下一步");

const renderEvidence = (refs, decisionValidation = {}, runtimeModels = {}) => {
  const root = document.querySelector("#evidenceList");
  clear(root);
  refs.slice(0, 5).forEach((ref) => {
    const row = el("div", "evidence-row");
    row.append(el("strong", "", ref.title || ref.knowledge_id || "knowledge"));
    row.append(el("span", "", `${ref.domain || "domain"} · ${ref.reviewed ? "reviewed" : "draft"}`));
    root.append(row);
  });
  if (decisionValidation.status) {
    const row = el("div", "evidence-row validation");
    row.append(el("strong", "", "动态裁决验证"));
    row.append(el("span", "", `${decisionValidation.status} · ${decisionValidation.decision_count ?? 0} decisions`));
    root.append(row);
  }
  const featureStateModel = runtimeModels.featureStateModel || {};
  const questionIntentModel = runtimeModels.questionIntentModel || {};
  const interactionSession = runtimeModels.interactionSession || {};
  const decisionModel = runtimeModels.decisionModel || {};
  [
    ["特征状态模型", featureStateModel.status, `${featureStateModel.feature_state_count ?? 0} states`],
    ["问题意图模型", questionIntentModel.status, `${questionIntentModel.intent_count ?? 0} intents`],
    ["交互会话模型", interactionSession.status, `${interactionSession.signal_count ?? 0} signals`],
    ["可反证裁决模型", decisionModel.status, `${decisionModel.argument_count ?? 0} arguments`],
  ].forEach(([title, status, detail]) => {
    if (!status) return;
    const row = el("div", "evidence-row model");
    row.append(el("strong", "", title));
    row.append(el("span", "", `${status} · ${detail}`));
    root.append(row);
  });
  if (!refs.length && !decisionValidation.status && !featureStateModel.status) root.append(el("div", "empty-note", "暂无可展示证据。"));
};

const appendChatTurn = (questionText, source) => {
  const id = `turn-${++state.chatSeq}`;
  state.chatTurns.push({
    id,
    source,
    questionText,
    answerText: "正在生成回复...",
    status: "pending",
    llmStatus: "llm generating",
  });
  renderChatTranscript();
  return id;
};

const completeChatTurn = (id, answerText, result) => {
  const turn = state.chatTurns.find((item) => item.id === id);
  if (!turn) return;
  turn.answerText = answerText || "本轮没有生成可展示回复。";
  turn.status = "ready";
  turn.llmStatus = llmStatusLabel(result);
  renderChatTranscript();
};

const failChatTurn = (id, message) => {
  const turn = state.chatTurns.find((item) => item.id === id);
  if (!turn) return;
  turn.answerText = `测算失败：${message}`;
  turn.status = "error";
  turn.llmStatus = "error";
  renderChatTranscript();
};

const renderChatTranscript = () => {
  if (!chatTranscript) return;
  clear(chatTranscript);
  if (!state.chatTurns.length) {
    chatTranscript.hidden = true;
    return;
  }
  chatTranscript.hidden = false;
  state.chatTurns.slice(-4).forEach((turn) => {
    const row = el("article", `chat-turn ${turn.status}`);
    const question = el("div", "chat-bubble user");
    question.append(el("span", "", turn.source || "提问"));
    question.append(el("strong", "", turn.questionText));
    const answer = el("div", "chat-bubble assistant");
    answer.append(el("span", "", turn.llmStatus || turn.status));
    answer.append(el("p", "", turn.answerText));
    row.append(question);
    row.append(answer);
    chatTranscript.append(row);
  });
};

const llmStatusLabel = (result) => {
  const assist = result?.llm_assist || {};
  const practitioner = assist.practitioner_answer || {};
  if (practitioner.status && practitioner.status !== "not_requested") return `llm practitioner ${practitioner.status}`;
  const rewrite = assist.answer_rewrite || {};
  if (rewrite.status && rewrite.status !== "not_requested") return `llm ${rewrite.status}`;
  return `llm ${assist.status || "idle"}`;
};

const latentScenarioTitle = (scenario) => ({
  wealth: "财务变化",
  career: "事业节点",
  relationship: "关系重心",
  relocation: "环境迁移",
  stress: "压力恢复",
  global: "行动节奏",
}[scenario.domain] || "命主校准");

const latentFieldLabel = (key) => ({
  year_option: "时间",
  result_option: "结果",
  intensity: "强度",
  confidence: "把握",
}[key] || key);

const latentYearLabel = (value) => ({
  unknown: "不确定",
  birth_to_12: "0-12岁",
  "13_to_18": "13-18岁",
  "19_to_24": "19-24岁",
  "25_to_30": "25-30岁",
  "31_to_36": "31-36岁",
  "37_to_42": "37-42岁",
  "43_to_48": "43-48岁",
  "49_to_54": "49-54岁",
  "55_plus": "55岁以后",
}[value] || value);

const latentResultLabel = (value) => ({
  no_clear_change: "没有明显变化",
  income_up: "收入/资源上升",
  income_down: "收入下降",
  resource_gain: "获得资源支持",
  resource_pressure: "资源或财务压力",
  role_up: "角色上升",
  role_down: "角色下降",
  platform_change: "平台变化",
  responsibility_change: "责任变化",
  relationship_stabilized: "关系稳定",
  relationship_changed: "关系变化",
  relationship_pressure: "关系压力",
  family_focus_shift: "家庭重心变化",
  city_change: "城市变化",
  work_environment_change: "工作环境变化",
  home_environment_change: "居住环境变化",
  travel_or_mobility_up: "流动增加",
  stable: "基本稳定",
  recovered_fast: "恢复较快",
  recovered_slow: "恢复较慢",
  repeated_pressure: "压力反复",
  support_helped: "外部支持有效",
  not_observed: "尚未观察",
  result_fast: "见效快",
  result_slow: "见效慢",
  needs_repeated_attempts: "需要反复尝试",
  external_help_decisive: "外部帮助关键",
  mixed: "混合",
}[value] || value);

const latentIntensityLabel = (value) => ({
  none: "无",
  mild: "轻微",
  clear: "明显",
  strong: "强烈",
}[value] || value);

const latentConfidenceLabel = (value) => ({
  low: "低",
  medium: "中",
  high: "高",
}[value] || value);

const loadLatentCalibrationManifest = async () => {
  try {
    state.latentManifest = await requestJson("/api/v20/learning/latent-event-calibration");
    renderLatentCalibration(state.latest?.input_id || "", measurementRole(roleSelect.value));
  } catch (error) {
    const status = document.querySelector("#latentCalibrationStatus");
    if (status) status.textContent = "manifest error";
  }
};

const loadStatus = async () => {
  try {
    const [health, status, deps] = await Promise.all([
      requestJson("/health"),
      requestJson("/api/v20/system/status"),
      requestJson("/api/v20/runtime/dependencies"),
    ]);
    setText("#runtimeStatus", `${health.status} · ${health.active_profile}`);
    setText("#profileBadge", health.active_profile);
    setText("#corpusState", `corpus ${status.corpus_artifact_status} · ${status.corpus_cluster_count || 0} clusters`);
    setText("#ruleState", `rules ${status.knowledge_rule_library_full_definition_count || status.knowledge_rule_library_definition_count || 0} · ${status.knowledge_rule_validation_status}`);
    setText("#dbState", `db ${deps.postgres.ready_for_connection ? "ready" : "config"}`);
  } catch (error) {
    setText("#runtimeStatus", "status error");
    setText("#dbState", error.message);
  }
};

const practitionerSessionStatus = () => {
  const session = state.latest?.practitioner_session || {};
  if (!state.practitionerSelections.length) return "待裁决";
  if (session.questions_refreshed) return `已刷新 ${session.selection_count || state.practitionerSelections.length} 项`;
  return "已接收";
};

const applyLocale = (locale) => {
  const text = UI_TEXT[locale] || UI_TEXT.zh;
  document.documentElement.lang = locale === "ko" ? "ko" : locale === "en" ? "en" : "zh-CN";
  document.querySelectorAll("[data-ui]").forEach((node) => {
    const key = node.dataset.ui;
    if (text[key]) node.textContent = text[key];
  });
  roleSelect.querySelectorAll("option").forEach((option) => {
    option.textContent = text.roles[option.value] || option.textContent;
  });
  const submit = form.querySelector("button[type='submit']");
  submit.textContent = text.run;
};

const renderInitialPanels = () => {
  renderPillars({});
  renderFeatures([]);
  renderPortrait([]);
  renderPractitionerCalibration([], "", measurementRole(roleSelect.value));
  renderLatentCalibration("", measurementRole(roleSelect.value));
  renderQuestions([], "", {});
  renderInteractionSignals({});
  renderEvidence([], {}, {});
};

const loadActiveProfile = async () => {
  const profileId = params.get("profile_id") || "";
  if (!profileId) return;
  document.querySelector("#selectedProfileCard").hidden = false;
  document.querySelector("#inputId").value = `profile:${profileId}`;
  setText("#selectedProfileName", params.get("profile_name") || profileId);
  const backParams = new URLSearchParams({ role: measurementRole(roleSelect.value), locale: localeSelect.value });
  document.querySelector("#backToProfiles").href = `/v20/ui/profiles.html?${backParams.toString()}`;
  try {
    const result = await requestJson(`/api/v20/profiles/${encodeURIComponent(profileId)}`);
    const profile = result.profile || {};
    state.activeProfile = profile;
    applyProfileDefaults(profile);
    setText("#selectedProfileName", profile.display_name || profile.profile_id || profileId);
    setText("#selectedProfileMeta", profileMeta(profile));
  } catch (error) {
    setText("#selectedProfileMeta", "profile unavailable");
  }
};

const payloadFromForm = () => {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
};

const hasCompletePillars = (payload) => ["year", "month", "day", "hour"].every((key) => String(payload[key] || "").trim().length === 2);

const fallbackPillar = (key) => {
  const fieldByKey = {
    luck: "luck_pillar",
    flow_year: "flow_year_pillar",
  };
  const value = String(form.elements[fieldByKey[key]]?.value || "").trim();
  if (value.length < 2) return {};
  return { stem: value.slice(0, 1), branch: value.slice(1, 2) };
};

const setInquiryText = (value, { syncOnly = false } = {}) => {
  const text = String(value || "");
  form.elements.user_text.value = text;
  if (chatText && chatText.value !== text) chatText.value = text;
  if (!syncOnly) scheduleMeasure({ force: true });
};

const hydrateFormFromParams = () => {
  [
    "year",
    "month",
    "day",
    "hour",
    "flow_year_pillar",
    "luck_pillar",
    "flow_month_pillar",
    "user_text",
    "question_key",
  ].forEach((key) => {
    const value = params.get(key);
    if (value !== null && form.elements[key]) form.elements[key].value = value;
  });
  if (chatText) chatText.value = form.elements.user_text.value || "";
};

const applyProfileDefaults = (profile) => {
  const defaults = profile.chart_defaults || {};
  const pillars = defaults.pillars || {};
  const timePillars = defaults.time_pillars || {};
  [
    ["year", pillars.year],
    ["month", pillars.month],
    ["day", pillars.day],
    ["hour", pillars.hour],
    ["flow_year_pillar", timePillars.flow_year],
    ["luck_pillar", timePillars.luck],
  ].forEach(([key, value]) => {
    if (value && form.elements[key]) form.elements[key].value = value;
  });
  if (defaults.status === "ready") {
    setText("#profileBadge", "profile chart");
  }
};

const unique = (items) => Array.from(new Set(items));
const currentText = () => UI_TEXT[localeSelect.value] || UI_TEXT.zh;
const measurementRole = (role) => (role === "user" ? "user" : "analyst");
const profileMeta = (profile) => {
  const birth = profile.birth_input || {};
  const date = [birth.year, String(birth.month || "").padStart(2, "0"), String(birth.day || "").padStart(2, "0")]
    .filter((value) => value && value !== "00")
    .join("-");
  const time = birth.hour !== undefined ? `${String(birth.hour).padStart(2, "0")}:${String(birth.minute || 0).padStart(2, "0")}` : "";
  return [date, time, profile.owner_id || "", profile.status || ""].filter(Boolean).join(" · ");
};

form.addEventListener("submit", (event) => {
  event.preventDefault();
  measure({
    force: true,
    interactionText: form.elements.user_text.value.trim(),
    interactionSource: "手动测算",
    llmMode: "practitioner",
  });
});
localeSelect.addEventListener("change", () => {
  applyLocale(localeSelect.value);
  scheduleMeasure({ force: true });
});
form.querySelectorAll("input, textarea, select").forEach((node) => {
  node.addEventListener("change", () => scheduleMeasure({ force: true }));
  if (node.tagName === "INPUT" || node.tagName === "TEXTAREA") {
    node.addEventListener("input", () => scheduleMeasure());
  }
  if (node.name === "user_text") {
    node.addEventListener("input", () => {
      if (chatText && chatText.value !== node.value) chatText.value = node.value;
    });
  }
});
chatButton.addEventListener("click", () => {
  const value = chatText.value.trim();
  if (!value) {
    setText("#answerText", "请输入想继续看的方向。");
    return;
  }
  questionSelect.value = "";
  setInquiryText(value, { syncOnly: true });
  measure({
    force: true,
    interactionText: value,
    interactionSource: "继续追问",
    llmMode: "practitioner",
  });
});
chatText.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    const value = chatText.value.trim();
    if (!value) {
      setText("#answerText", "请输入想继续看的方向。");
      return;
    }
    questionSelect.value = "";
    setInquiryText(value, { syncOnly: true });
    measure({
      force: true,
      interactionText: value,
      interactionSource: "继续追问",
      llmMode: "practitioner",
    });
  }
});

if (params.get("locale")) localeSelect.value = params.get("locale");
roleSelect.value = measurementRole(params.get("role") || roleSelect.value);
document.body.classList.toggle("profile-reading", Boolean(params.get("profile_id")));
hydrateFormFromParams();
applyLocale(localeSelect.value);
renderInitialPanels();
loadStatus();
loadLatentCalibrationManifest();
loadActiveProfile().finally(() => scheduleMeasure({ force: true }));
setInterval(loadStatus, 10000);
