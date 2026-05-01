const state = {
  latest: null,
  activeProfile: null,
  measureTimer: null,
  isMeasuring: false,
  pendingMeasure: false,
  lastMeasureKey: "",
};
const params = new URLSearchParams(window.location.search);

const form = document.querySelector("#measureForm");
const questionSelect = document.querySelector("#questionSelect");
const roleSelect = document.querySelector("#roleSelect");
const localeSelect = document.querySelector("#localeSelect");
const feedbackButton = document.querySelector("#feedbackButton");
const chatText = document.querySelector("#chatText");
const chatButton = document.querySelector("#chatButton");

const UI_TEXT = {
  zh: {
    app_title: "命理测算台",
    nav_profiles: "档案",
    nav_measure: "测算",
    chart_title: "命盘结构",
    features_title: "命理特征主线",
    portrait_title: "画像投影",
    questions_title: "推荐问题",
    answer_title: "八字专业回复",
    evidence_title: "证据与系统状态",
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
    features_title: "Bazi Feature Spine",
    portrait_title: "Portrait Projection",
    questions_title: "Recommended Questions",
    answer_title: "Professional Bazi Reply",
    evidence_title: "Evidence and System",
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
    features_title: "명리 특징 축",
    portrait_title: "프로필 투영",
    questions_title: "추천 질문",
    answer_title: "전문 사주 답변",
    evidence_title: "근거와 시스템",
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

const measure = async ({ force = false } = {}) => {
  const text = currentText();
  const payload = payloadFromForm();
  const key = JSON.stringify(payload);
  if (!force && key === state.lastMeasureKey) return;
  if (!hasCompletePillars(payload)) return;
  if (state.isMeasuring) {
    state.pendingMeasure = true;
    return;
  }
  const button = form.querySelector("button[type='submit']");
  state.isMeasuring = true;
  state.lastMeasureKey = key;
  button.disabled = true;
  button.textContent = text.running;
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
  } catch (error) {
    setText("#answerText", `测算失败：${error.message}`);
    state.lastMeasureKey = "";
  } finally {
    state.isMeasuring = false;
    button.disabled = false;
    button.textContent = currentText().run;
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
  const role = result.role?.role_key || measurementRole(roleSelect.value);

  document.body.dataset.role = role;
  setText("#selectedQuestion", selected.title || selected.question_key || "已完成测算");
  setText("#selectedBoundary", selected.boundary || result.prediction_policy?.core_focus || "");
  setText("#featureCount", featureLayer.feature_count ?? 0);
  setText("#questionCount", (result.questions || []).length);
  setText("#knowledgeCount", result.knowledge_report?.count ?? 0);
  setText("#coreCapacity", result.core_inference?.day_master_capacity || "core");
  setText("#dayMasterBadge", `日主 ${chart.day_master || "-"}`);
  setText("#llmStatus", `llm ${result.llm_assist?.status || "idle"}`);
  setText("#answerText", result.answer_text || "");

  renderPillars(chart, result.time_context || {});
  renderTenGods(chart);
  renderFeatures(featureLayer.macro_features || featureLayer.features || []);
  renderPortrait(result.portrait_projection?.axes || []);
  renderQuestions(result.questions || [], selected.question_key || "");
  renderQuestionSelect(result.questions || [], selected.question_key || "");
  renderEvidence(result.knowledge_refs || []);
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
    root.append(el("div", "empty-note", "当前视图隐藏内部特征。"));
    return;
  }
  features.slice(0, 10).forEach((feature) => {
    const card = el("div", "feature-card");
    card.dataset.domain = feature.domain || "general";
    card.append(el("strong", "", feature.title || feature.feature_id || feature.macro_id || "feature"));
    card.append(el("span", "", `${feature.domain || "domain"} · confidence ${feature.peak_confidence ?? feature.confidence ?? "-"}`));
    if (feature.summary) card.append(el("p", "", feature.summary));
    root.append(card);
  });
};

const renderPortrait = (axes) => {
  const root = document.querySelector("#portraitAxes");
  clear(root);
  if (!axes.length) {
    root.append(el("div", "empty-note", "当前视图隐藏画像投影。"));
    return;
  }
  axes.slice(0, 8).forEach((axis) => {
    const row = el("div", "axis-row");
    row.append(el("strong", "", axis.label || axis.axis_id));
    row.append(el("span", "", `${axis.domain} · ${axis.feature_count} features · ${axis.knowledge_ref_count ?? 0} refs`));
    const meter = el("i");
    meter.style.width = `${Math.round(Number(axis.peak_confidence || 0) * 100)}%`;
    const bar = el("div", "meter");
    bar.append(meter);
    row.append(bar);
    root.append(row);
  });
};

const renderQuestions = (questions, selectedKey) => {
  const root = document.querySelector("#questionList");
  clear(root);
  if (!questions.length) {
    root.append(el("div", "empty-note", "确认四柱后会生成建议问题。"));
    return;
  }
  questions.slice(0, 5).forEach((question) => {
    const button = el("button", `question-row${question.question_key === selectedKey ? " active" : ""}`);
    button.type = "button";
    button.append(el("strong", "", question.title || question.question_key));
    button.append(el("span", "", question.measurement_topic || question.domain || "命理测算"));
    button.addEventListener("click", () => {
      questionSelect.value = question.question_key;
      setInquiryText(question.title || question.question_key || "", { syncOnly: true });
      measure({ force: true });
    });
    root.append(button);
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

const renderEvidence = (refs) => {
  const root = document.querySelector("#evidenceList");
  clear(root);
  refs.slice(0, 5).forEach((ref) => {
    const row = el("div", "evidence-row");
    row.append(el("strong", "", ref.title || ref.knowledge_id || "knowledge"));
    row.append(el("span", "", `${ref.domain || "domain"} · ${ref.reviewed ? "reviewed" : "draft"}`));
    root.append(row);
  });
  if (!refs.length) root.append(el("div", "empty-note", "暂无可展示证据。"));
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
    setText("#ruleState", `rules ${status.knowledge_rule_extraction_validation_status}/${status.knowledge_llm_rule_extraction_validation_status}`);
    setText("#dbState", `db ${deps.postgres.ready_for_connection ? "ready" : "config"}`);
  } catch (error) {
    setText("#runtimeStatus", "status error");
    setText("#dbState", error.message);
  }
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
  renderQuestions([], "");
  renderEvidence([]);
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

const submitFeedback = async () => {
  const text = document.querySelector("#feedbackText").value.trim();
  if (!text) {
    setText("#feedbackOutput", "请输入反馈。");
    return;
  }
  const latest = state.latest || {};
  const featureIds = (latest.feature_layer?.features || []).slice(0, 4).map((feature) => feature.feature_id);
  feedbackButton.disabled = true;
  feedbackButton.textContent = "分析中";
  try {
    const result = await requestJson("/api/v20/feedback/record", {
      method: "POST",
      body: JSON.stringify({
        input_id: latest.input_id || "ui.feedback",
        source_role: measurementRole(roleSelect.value),
        feedback_text: text,
        feature_ids: featureIds,
      }),
    });
    const analysis = result.analysis || {};
    setText("#feedbackState", result.storage?.record_id || "recorded");
    setText("#feedbackOutput", `${analysis.redacted_summary || ""}\nproposal ${analysis.learning_proposal?.proposal_type || "-"}\nledger ${result.storage?.relative_path || "-"}`);
  } catch (error) {
    setText("#feedbackOutput", `反馈分析失败：${error.message}`);
  } finally {
    feedbackButton.disabled = false;
    feedbackButton.textContent = "分析反馈";
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
  measure({ force: true });
});
feedbackButton.addEventListener("click", submitFeedback);
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
chatButton.addEventListener("click", () => setInquiryText(chatText.value));
chatText.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    setInquiryText(chatText.value);
  }
});

if (params.get("locale")) localeSelect.value = params.get("locale");
roleSelect.value = measurementRole(params.get("role") || roleSelect.value);
document.body.classList.toggle("profile-reading", Boolean(params.get("profile_id")));
hydrateFormFromParams();
applyLocale(localeSelect.value);
renderInitialPanels();
loadStatus();
loadActiveProfile().finally(() => scheduleMeasure({ force: true }));
setInterval(loadStatus, 10000);
