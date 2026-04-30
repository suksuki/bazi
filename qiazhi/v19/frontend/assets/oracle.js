const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(window.location.search);
const profileId = params.get("profile_id") || "";
const QUESTION_LIBRARY = [
  { key: "q_structure_overview", theme: "structure_basis", required: ["chart"], depth: "beginner", phase: "before_result", related_questions: ["q_day_master_month_anchor", "q_hidden_stem_role", "q_income_stability", "q_time_context"], forbidden_prediction: true },
  { key: "q_strength_assessment", theme: "strength_structure", required: ["chart"], depth: "beginner", phase: "any", related_questions: ["q_day_master_month_anchor", "q_month_command_anchor", "q_useful_god_candidates"], forbidden_prediction: true, label: { zh: "这个八字的日主强弱，应该先看哪些证据？", en: "Which evidence should be checked first for day-master strength?", ko: "이 사주의 일간 강약은 어떤 근거를 먼저 봐야 하나요?" } },
  { key: "q_useful_god_candidates", theme: "useful_god_boundary", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_strength_assessment", "q_favorable_elements_boundary", "q_unfavorable_god_boundary"], forbidden_prediction: true, label: { zh: "这张命盘的用神，当前只能先形成哪些候选路径？", en: "What useful-god candidate paths can be formed at this stage?", ko: "이 명식의 용신은 현재 어떤 후보 경로로만 볼 수 있나요?" } },
  { key: "q_unfavorable_god_boundary", theme: "useful_god_boundary", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_useful_god_candidates", "q_strength_assessment", "q_read_result_not_fortune"], forbidden_prediction: true, label: { zh: "忌神问题现在应该如何只按结构边界回答？", en: "How should unfavorable-god questions be answered only as structural boundaries?", ko: "기신 질문은 현재 구조 경계로만 어떻게 답해야 하나요?" } },
  { key: "q_favorable_elements_boundary", theme: "useful_god_boundary", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_useful_god_candidates", "q_unfavorable_god_boundary", "q_element_flow_metadata"], forbidden_prediction: true, label: { zh: "喜什么五行这类问题，当前能回答到什么边界？", en: "For favorable-element questions, what boundary can be answered now?", ko: "희신 오행 질문은 현재 어느 경계까지 답할 수 있나요?" } },
  { key: "q_pattern_structure", theme: "pattern_structure", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_strength_assessment", "q_ten_god_focus", "q_read_result_not_fortune"], forbidden_prediction: true, label: { zh: "这个八字的格局，应该先按哪些结构入口判断？", en: "Which structural entries should be checked first for chart pattern?", ko: "이 사주의 격국은 어떤 구조 입구부터 봐야 하나요?" } },
  { key: "q_ten_god_focus", theme: "structure_basis", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_ten_god_metadata", "q_pattern_structure", "q_income_factors"], forbidden_prediction: true, label: { zh: "财、官、印、食伤里，当前哪些十神关系更值得先看？", en: "Among wealth, officer, resource, and output, which Ten God relations deserve first attention?", ko: "재성·관성·인성·식상 중 어떤 십성 관계를 먼저 봐야 하나요?" } },
  { key: "q_income_stability", theme: "income_stability", required: ["chart"], depth: "beginner", phase: "any", related_questions: ["q_income_factors", "q_signal_combination", "q_day_master_month_anchor", "follow_rule_basis"], forbidden_prediction: true },
  { key: "q_income_factors", theme: "income_stability", required: ["chart"], depth: "beginner", phase: "any", related_questions: ["q_signal_combination", "q_income_continuity", "q_wealth_accessibility", "q_volatility_factors"], forbidden_prediction: true },
  { key: "q_read_result_not_fortune", theme: "structure_basis", required: ["result"], depth: "beginner", phase: "after_result", related_questions: ["q_no_good_bad", "q_result_card_boundary", "follow_rule_basis", "q_time_context_boundary"], forbidden_prediction: true },
  { key: "q_signal_combination", theme: "income_stability", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["q_primary_auxiliary_signals", "follow_rule_basis", "q_wealth_accessibility", "q_read_result_not_fortune"], forbidden_prediction: true },
  { key: "q_income_continuity", theme: "income_stability", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["q_signal_combination", "q_volatility_factors", "follow_rule_basis"], forbidden_prediction: true },
  { key: "q_wealth_accessibility", theme: "income_stability", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["q_accessibility_signals", "q_signal_combination", "follow_rule_basis"], forbidden_prediction: true },
  { key: "q_accessibility_signals", theme: "income_stability", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["q_wealth_accessibility", "q_primary_auxiliary_signals", "follow_rule_basis"], forbidden_prediction: true },
  { key: "q_cautious_reading", theme: "structure_basis", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["q_result_card_boundary", "q_no_good_bad", "follow_feedback"], forbidden_prediction: true },
  { key: "q_primary_auxiliary_signals", theme: "income_stability", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["q_signal_combination", "follow_rule_basis"], forbidden_prediction: true },
  { key: "q_volatility_factors", theme: "income_stability", required: ["result"], signal: "volatility_not_low", depth: "intermediate", phase: "after_result", related_questions: ["q_income_factors", "q_signal_combination", "follow_rule_basis"], forbidden_prediction: true },
  { key: "q_time_context", theme: "time_context", required: ["time_relation"], depth: "beginner", phase: "any", related_questions: ["q_branch_relation_detail", "q_time_vs_natal_relation", "q_time_context_boundary", "q_luck_flow_layers"], forbidden_prediction: true },
  { key: "q_time_context_boundary", theme: "time_context", required: ["time_relation"], depth: "beginner", phase: "any", related_questions: ["q_time_context", "q_time_vs_natal_relation", "q_time_not_inference", "q_read_result_not_fortune"], forbidden_prediction: true },
  { key: "q_luck_flow_layers", theme: "time_context", required: ["time_relation"], depth: "intermediate", phase: "any", related_questions: ["q_time_context_boundary", "q_time_vs_natal_relation", "q_time_not_inference"], forbidden_prediction: true },
  { key: "q_time_not_inference", theme: "time_context", required: ["time_relation"], depth: "intermediate", phase: "any", related_questions: ["q_time_context_boundary", "q_result_card_boundary"], forbidden_prediction: true },
  { key: "q_day_master_month_anchor", theme: "structure_basis", required: ["chart"], depth: "beginner", phase: "any", related_questions: ["q_structure_overview", "q_hidden_stem_role", "q_income_factors"], forbidden_prediction: true },
  { key: "q_month_command_anchor", theme: "structure_basis", required: ["chart"], depth: "beginner", phase: "any", related_questions: ["q_day_master_month_anchor", "q_structure_overview", "q_hidden_stem_role"], forbidden_prediction: true },
  { key: "q_hidden_stem_role", theme: "structure_basis", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_day_master_month_anchor", "q_structure_overview", "q_income_factors"], forbidden_prediction: true },
  { key: "q_ten_god_metadata", theme: "structure_basis", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_hidden_stem_role", "q_income_factors", "q_read_result_not_fortune"], forbidden_prediction: true },
  { key: "q_element_flow_metadata", theme: "structure_basis", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_day_master_month_anchor", "q_ten_god_metadata", "q_income_factors"], forbidden_prediction: true },
  { key: "q_branch_relation_detail", theme: "structure_basis", required: ["branch_relation"], depth: "beginner", phase: "any", related_questions: ["q_combination_context", "q_time_context", "q_time_vs_natal_relation", "q_cautious_reading"], forbidden_prediction: true },
  { key: "q_time_vs_natal_relation", theme: "time_context", required: ["time_relation"], depth: "intermediate", phase: "any", related_questions: ["q_time_context", "q_luck_flow_layers", "q_time_not_inference"], forbidden_prediction: true },
  { key: "q_combination_context", theme: "structure_basis", required: ["branch_relation"], signal: "combination_relation", depth: "intermediate", phase: "any", related_questions: ["q_branch_relation_detail", "q_structure_overview", "q_time_context_boundary"], forbidden_prediction: true },
  { key: "q_three_harmony_context", theme: "structure_basis", required: ["branch_relation"], signal: "three_harmony", depth: "intermediate", phase: "any", related_questions: ["q_branch_relation_detail", "q_structure_overview", "q_time_context_boundary"], forbidden_prediction: true },
  { key: "q_vault_structure", theme: "structure_basis", required: ["chart"], depth: "intermediate", phase: "any", related_questions: ["q_hidden_stem_role", "q_structure_overview", "q_time_context_boundary"], forbidden_prediction: true },
  { key: "q_income_path_structure", theme: "income_stability", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["q_income_factors", "q_wealth_accessibility", "q_signal_combination"], forbidden_prediction: true },
  { key: "q_no_good_bad", theme: "boundary", required: ["result"], depth: "beginner", phase: "after_result", related_questions: ["q_result_card_boundary", "q_read_result_not_fortune"], forbidden_prediction: true },
  { key: "q_result_card_boundary", theme: "boundary", required: ["result"], depth: "beginner", phase: "after_result", related_questions: ["q_read_result_not_fortune", "follow_rule_basis", "follow_feedback"], forbidden_prediction: true },
  { key: "q_analyst_review_needed", theme: "feedback", required: ["result"], depth: "intermediate", phase: "after_result", related_questions: ["follow_feedback", "follow_rule_basis"], forbidden_prediction: true },
  { key: "follow_rule_basis", theme: "structure_basis", required: ["result"], depth: "beginner", phase: "after_result", related_questions: ["q_signal_combination", "q_primary_auxiliary_signals", "q_read_result_not_fortune", "follow_feedback"], forbidden_prediction: true },
  { key: "follow_feedback", theme: "feedback", required: ["result"], depth: "beginner", phase: "after_result", related_questions: ["q_read_result_not_fortune"], forbidden_prediction: true },
];
const FORBIDDEN_QUESTION_PATTERN = /(未来财运|今年.*好|什么时候发财|发财|命运如何|fortune|future wealth|good luck|bad luck|운세|재물운.*좋|언제.*부자)/i;
const HIDDEN_STEMS = {"子":["癸"],"丑":["己","癸","辛"],"寅":["甲","丙","戊"],"卯":["乙"],"辰":["戊","乙","癸"],"巳":["丙","庚","戊"],"午":["丁","己"],"未":["己","丁","乙"],"申":["庚","壬","戊"],"酉":["辛"],"戌":["戊","辛","丁"],"亥":["壬","甲"]};
const FALLBACK_LABELS = {
  zh: {
    guided_answer: "结构回答",
    question_answer_only: "回答当前问题",
    selected_question: "当前问题",
    answer_empty: "这个问题暂时没有匹配到可解释的命盘结构，我不会硬编答案。你可以换一个上方推荐问题，或把问题改得更具体一点。",
  },
  en: {
    guided_answer: "Structured answer",
    question_answer_only: "Answers current question",
    selected_question: "Current question",
    answer_empty: "This question does not match an explainable chart structure yet, so the system will not invent an answer. Try a recommended question above or make the question more specific.",
  },
  ko: {
    guided_answer: "구조 답변",
    question_answer_only: "현재 질문 답변",
    selected_question: "현재 질문",
    answer_empty: "이 질문은 아직 설명 가능한 명식 구조와 연결되지 않아 답변을 지어내지 않습니다. 위 추천 질문을 선택하거나 질문을 더 구체적으로 바꿔 주세요.",
  },
};
let locale = localStorage.getItem("v19_oracle_locale") || params.get("locale") || "zh";
let labels = {};
let profile = null;
let structureData = null;
let lastData = null;
let dynamicQuestions = [];
let sessionId = "";
let selectedYear = Number(params.get("year") || new Date().getFullYear());
let selectedQuestionKey = "q_income_stability";
let lastQuestionKey = "";
const visitedQuestionKeys = new Set();
let localQuestionFeedback = loadLocalQuestionFeedback();

boot();

async function boot() {
  await loadLabels(locale);
  bindEvents();
  renderStaticLabels();
  if (!profileId) {
    $("profileMissing").classList.remove("hidden");
    return;
  }
  await loadProfile();
}

function bindEvents() {
  $("locale").addEventListener("change", async () => {
    locale = $("locale").value;
    localStorage.setItem("v19_oracle_locale", locale);
    await loadLabels(locale);
    renderStaticLabels();
    if (structureData) {
      renderPillarPanel(structureData);
      renderPortraitPanel(structureData);
    }
    renderQuestions();
    if (structureData) renderQuestionContext(structureData);
    if (lastData) renderResult(lastData);
  });
  $("run").addEventListener("click", runAgent);
  $("message").addEventListener("input", syncSelectedQuestionFromMessage);
}

async function loadLabels(nextLocale) {
  const clean = ["zh", "en", "ko"].includes(nextLocale) ? nextLocale : "zh";
  const result = await fetch(`/api/labels?locale=${encodeURIComponent(clean)}`).then((response) => response.json());
  locale = result.locale || clean;
  labels = { ...fallbackTerms(locale), ...(result.terms || {}) };
}

function renderStaticLabels() {
  document.documentElement.lang = locale === "zh" ? "zh-CN" : locale;
  document.title = t("app_title");
  document.querySelectorAll("[data-i18n]").forEach((node) => node.textContent = t(node.dataset.i18n || ""));
  $("locale").innerHTML = ["zh", "en", "ko"].map((item) => `<option value="${item}" ${item === locale ? "selected" : ""}>${escapeHtml(t(`locale_${item}`))}</option>`).join("");
}

async function loadProfile() {
  const response = await fetch(`/api/profiles/${encodeURIComponent(profileId)}`);
  if (response.status === 401 || response.status === 404) {
    $("profileMissing").classList.remove("hidden");
    return;
  }
  const result = await response.json();
  profile = result.data;
  $("profileTitle").textContent = profile.name || t("profile_list");
  $("agentMain").classList.remove("hidden");
  await loadStructure();
  renderQuestions();
  setQuestion(selectedQuestionKey);
}

async function loadStructure() {
  const result = await postJson("/api/agent/structure", { birth_input: profile.birth_input, selected_year: selectedYear });
  if (!result.ok) {
    $("oracleStatus").textContent = result.message || result.code || "error";
    return;
  }
  structureData = result.data;
  dynamicQuestions = dynamicQuestionsFrom(structureData);
  renderPillarPanel(structureData);
  renderPortraitPanel(structureData);
  renderQuestionContext(structureData);
}

function renderQuestions() {
  const keys = guidanceQuestionKeys(structureData, lastData);
  $("questionChips").innerHTML = keys.map((key) => questionChip(key, key === selectedQuestionKey, "data-question-key")).join("");
  document.querySelectorAll("[data-question-key]").forEach((button) => button.addEventListener("click", () => setQuestion(button.dataset.questionKey || "q_income_stability")));
}

function setQuestion(key) {
  selectedQuestionKey = key;
  lastQuestionKey = key;
  visitedQuestionKeys.add(key);
  $("message").value = questionLabel(key);
  document.querySelectorAll("[data-question-key]").forEach((button) => button.classList.toggle("active", button.dataset.questionKey === key));
}

function syncSelectedQuestionFromMessage() {
  if (messageMatchesSelectedQuestion($("message").value.trim())) return;
  selectedQuestionKey = "";
  document.querySelectorAll("[data-question-key]").forEach((button) => button.classList.remove("active"));
}

function messageMatchesSelectedQuestion(message) {
  if (!selectedQuestionKey) return false;
  return String(message || "").trim() === questionLabel(selectedQuestionKey).trim();
}

async function runAgent() {
  $("run").disabled = true;
  $("run").textContent = t("running");
  try {
    const message = $("message").value.trim() || t("q_income_stability");
    const result = await postJson("/api/agent/turn", { birth_input: profile.birth_input, selected_year: selectedYear, message, selected_question_key: messageMatchesSelectedQuestion(message) ? selectedQuestionKey : "", session_id: sessionId, locale });
    if (!result.ok) { $("oracleStatus").textContent = result.message || result.code || "error"; return; }
    lastData = result.data;
    dynamicQuestions = dynamicQuestionsFrom(lastData);
    sessionId = (lastData.session || {}).session_id || sessionId;
    renderResult(lastData);
    $("result").classList.remove("hidden");
    $("oracleStatus").textContent = "";
  } finally {
    $("run").disabled = false;
    $("run").textContent = t("run_analysis");
  }
}

function renderResult(data) { renderGuidedAnswer(data); renderAnswerFeedback(data); renderNextQuestions(); }

function renderGuidedAnswer(data) {
  const answer = data.guided_question_answer || {};
  if (!answer.available) {
    $("questionAnswer").innerHTML = `<div class="answer-prose"><p>${escapeHtml(t("answer_empty"))}</p></div>`;
    renderAnswerEvidenceSummary({});
    return;
  }
  const text = answerText(answer);
  $("questionAnswer").innerHTML = `<div class="answer-prose">${text.split(/\n{2,}/).filter(Boolean).map((paragraph) => `<p>${escapeHtml(paragraph.trim())}</p>`).join("")}</div>`;
  renderAnswerEvidenceSummary(answer);
}

function renderPillarPanel(data) {
  const pillars = data.chart?.pillars || {};
  const activeLuck = data.time_context?.luck_cycle || null;
  const flow = data.time_context?.flow_year || {};
  $("pillarPanel").innerHTML = `<section class="pillar-section"><div class="pillar-panel-head"><span>${escapeHtml(t("pillar_panel"))}</span></div><div class="pillar-subhead">${escapeHtml(t("natal_chart"))}</div><div class="pillar-grid natal-pillars">${["year","month","day","hour"].map((key)=>pillarCell(t(key), pillars[key], key==="day")).join("")}</div><div class="pillar-context-grid"><article class="context-pillar luck-context" tabindex="0"><span>${escapeHtml(t("current_luck_cycle"))}</span><strong>${escapeHtml(activeLuck?.pillar?.display || "-")}</strong><em>${activeLuck ? `${activeLuck.start_age}-${activeLuck.end_age}` : t("context_only")}</em>${activeLuck?.pillar ? `<div class="pillar-tooltip">${escapeHtml(pillarTooltip(activeLuck.pillar, false))}</div>` : ""}</article><article class="context-pillar flow-context" tabindex="0"><span>${escapeHtml(t("flow_year"))}</span><strong>${escapeHtml(flow.pillar?.display || "-")}</strong><em>${escapeHtml(String(flow.year || ""))} · ${escapeHtml(t("context_only"))}</em>${flow.pillar ? `<div class="pillar-tooltip">${escapeHtml(pillarTooltip(flow.pillar, false))}</div>` : ""}</article></div></section>`;
}

function renderPortraitPanel(data) {
  if (!$("portraitPanel")) return;
  const portrait = data.structure_portrait || data.guided_question_context?.structure_portrait || {};
  const allLabels = Array.isArray(portrait.labels) ? portrait.labels : [];
  const labels = portraitVisibleLabels(portrait, 5);
  const judgements = Array.isArray(portrait.candidate_judgements) ? portrait.candidate_judgements.slice(0, 3) : [];
  if (!portrait.status || !allLabels.length || !labels.length) {
    $("portraitPanel").classList.add("hidden");
    $("portraitPanel").innerHTML = "";
    return;
  }
  $("portraitPanel").classList.remove("hidden");
  const chips = labels.map((row) => `<span class="portrait-chip"><b>${escapeHtml(portraitFamilyLabel(row.family))}</b>${escapeHtml(portraitValueLabel(row.value))}</span>`).join("");
  const judgementRows = judgements.map((row) => `<li>${escapeHtml(row.text || row.candidate_statement || row.statement || row.judgement_id || "")}</li>`).join("");
  $("portraitPanel").innerHTML = `<section class="portrait-section"><div class="pillar-panel-head"><span>${escapeHtml(portraitTitleLabel())}</span><em>${escapeHtml(portraitEvidenceLabel(portrait, labels.length, allLabels.length))}</em></div><div class="portrait-chip-row">${chips}</div>${judgementRows ? `<ul class="portrait-judgements">${judgementRows}</ul>` : ""}</section>`;
}

function pillarCell(label, pillar, isDay) { return `<article class="pillar-cell ${isDay ? "day-master-cell" : ""}" tabindex="0"><span>${escapeHtml(label)}</span><strong>${escapeHtml(pillar?.display || "-")}</strong><em>${isDay ? escapeHtml(t("day_master")) : escapeHtml(pillar?.stem_element || "")}</em><div class="pillar-tooltip">${escapeHtml(pillarTooltip(pillar || {}, isDay))}</div></article>`; }
function pillarTooltip(pillar, isDay) { if (!pillar.stem || !pillar.branch) return t("structure_only_note"); const hidden = HIDDEN_STEMS[pillar.branch] || []; return [`${t("stem")}: ${pillar.stem} (${elementLabel(pillar.stem_element)}, ${t(pillar.stem_yin_yang || "unknown")})`,`${t("branch")}: ${pillar.branch} (${elementLabel(pillar.branch_element)}, ${t(pillar.branch_yin_yang || "unknown")})`,`${t("hidden_stems")}: ${hidden.join(" / ") || "-"}`,isDay ? t("day_master_note") : t("structure_only_note")].join("\n"); }
function elementLabel(value) { return value ? t(`element_${value}`) : t("unknown"); }
function renderQuestionContext(data) { const day = data.chart?.pillars?.day?.display || ""; const month = data.chart?.pillars?.month?.display || ""; $("questionContext").textContent = `${t("question_context_prefix")}: ${t("day_master")} ${day || "-"} · ${t("month_structure")} ${month || "-"}`; }
function renderNextQuestions() {
  const keys = rankedQuestionKeys(structureData, lastData, { afterResult: true, pathFirst: true }).slice(0, 5);
  $("nextQuestionBlock").classList.toggle("hidden", !keys.length);
  $("nextQuestions").innerHTML = keys.map((key) => questionChip(key, false, "data-next-key")).join("");
  document.querySelectorAll("[data-next-key]").forEach((button)=>button.addEventListener("click",()=>{setQuestion(button.dataset.nextKey||"q_income_stability"); $("message").focus();}));
  renderQuestions();
}

function renderAnswerFeedback(data) {
  if (!$("answerFeedback")) return;
  const answer = data?.guided_question_answer || {};
  const item = findQuestion(selectedQuestionKey);
  const hasAnswer = Boolean(answer.available && item);
  $("answerFeedback").classList.toggle("hidden", !hasAnswer);
  if (!hasAnswer) return;
  $("answerFeedback").innerHTML = `<span>${escapeHtml(t("answer_helpful_prompt"))}</span><button type="button" data-answer-helpful="1">${escapeHtml(t("helpful_yes"))}</button><button type="button" data-answer-helpful="-1">${escapeHtml(t("helpful_no"))}</button>`;
  document.querySelectorAll("[data-answer-helpful]").forEach((button) => button.addEventListener("click", () => submitQuestionFeedback(Number(button.dataset.answerHelpful || 0), answer)));
}

async function submitQuestionFeedback(rating, answer = {}) {
  const item = findQuestion(selectedQuestionKey) || {};
  const payload = {
    subject_type: "guided_question",
    subject_id: selectedQuestionKey,
    rating,
    comment: `guided_answer_helpfulness:${selectedQuestionKey}`,
    tags: ["guided_question", "guided_answer", item.theme || "unknown", item.depth || "unknown"],
    suggested_action: "analyst_review_queue",
    payload: {
      answer_kind: answer.answer_kind || "",
      question_contract: answer.question_contract || {},
      intent: answer.intent || {},
      source_signal_id: answer.source_signal_id || "",
      source_signal_category: answer.source_signal_category || "",
      retrieved_facts: answer.retrieved_facts || {},
      evidence_pack: answer.evidence_pack || {},
      observed_facts: answer.observed_facts || {},
      answer_text: answerText(answer).slice(0, 2000),
    },
    metadata: {
      question_key: selectedQuestionKey,
      profile_id: profileId,
      session_id: sessionId,
      selected_year: selectedYear,
      theme: item.theme || "",
      depth: item.depth || "",
      answer_kind: answer.answer_kind || "",
      question_contract: answer.question_contract || {},
      intent: answer.intent || {},
      source_signal_id: answer.source_signal_id || "",
      source_signal_category: answer.source_signal_category || "",
      retrieved_facts: answer.retrieved_facts || {},
      evidence_pack: answer.evidence_pack || {},
      observed_facts: answer.observed_facts || {},
      forbidden_prediction: true,
    },
  };
  const result = await postJson("/api/agent/feedback", payload);
  if (result.ok !== false) {
    rememberQuestionFeedback(selectedQuestionKey, rating);
    renderQuestions();
    if (lastData) renderNextQuestions();
  }
  $("oracleStatus").textContent = result.ok === false ? (result.message || result.code || "feedback failed") : t("answer_feedback_saved");
}
function guidanceQuestionKeys(structure, result) {
  const backendOrdered = backendPersonalizedQuestionKeys();
  if (backendOrdered.length) return backendOrdered.slice(0, 5);
  return rankedQuestionKeys(structure, result, { afterResult: Boolean(result) }).slice(0, 5);
}
function rankedQuestionKeys(structure, result, options = {}) {
  const signals = signalMapFromResult(result);
  const rel = structure?.time_context?.flow_year?.relations_with_natal || {};
  const luckRel = structure?.time_context?.luck_cycle?.relations_with_natal || {};
  const natalRelations = structure?.chart?.relations?.items || [];
  const timeRelationCount = relationPayloadCount(rel) + relationPayloadCount(luckRel);
  const related = relatedQuestionSet(lastQuestionKey);
  const context = {
    chart: Boolean(structure?.chart),
    result: Boolean(result),
    time_relation: Boolean(timeRelationCount),
    branch_relation: Boolean(timeRelationCount || natalRelations.length),
    combination_relation: hasCombinationRelation(natalRelations, rel, luckRel),
    three_harmony: hasThreeHarmonyRelation(natalRelations, rel, luckRel),
    volatility_not_low: Boolean(signals.volatility && signals.volatility !== "low"),
  };
  const library = mergedQuestionLibrary();
  return library
    .filter((item) => item.forbidden_prediction)
    .filter((item) => !FORBIDDEN_QUESTION_PATTERN.test(questionLabel(item.key)))
    .filter((item) => depthAvailable(item, context))
    .filter((item) => (item.required || []).every((key) => Boolean(context[key])))
    .filter((item) => !item.signal || Boolean(context[item.signal]))
    .map((item) => ({ ...item, score: questionScore(item, context, options, related) }))
    .sort((a, b) => b.score - a.score || a.key.localeCompare(b.key))
    .map((item) => item.key);
}
function questionScore(item, context, options, related) {
  let score = item.depth === "beginner" ? 20 : 10;
  if (!context.result && item.phase === "before_result") score += 60;
  if (context.result && item.phase === "after_result") score += 60;
  if (item.theme === "income_stability") score += context.result ? 25 : 15;
  if (item.theme === "strength_structure") score += context.result ? 18 : 36;
  if (item.theme === "useful_god_boundary") score += context.result ? 14 : 28;
  if (item.theme === "pattern_structure") score += context.result ? 14 : 24;
  if (item.dynamic) score += Number(item.personalized_score ?? item.score ?? 0);
  if (item.theme === "structure_basis") score += context.result ? 18 : 30;
  if (item.theme === "time_context" && context.time_relation) score += 35;
  if (item.theme === "boundary" && context.result) score += 22;
  if (item.theme === "feedback" && context.result) score += 8;
  if (item.signal === "volatility_not_low" && context.volatility_not_low) score += 30;
  if (item.signal === "combination_relation" && context.combination_relation) score += 32;
  if (item.signal === "three_harmony" && context.three_harmony) score += 34;
  if (options.afterResult && item.key === "follow_rule_basis") score += 20;
  if (related.has(item.key)) score += options.pathFirst ? 75 : 45;
  if (visitedQuestionKeys.has(item.key)) score -= 12;
  if (options.afterResult && item.key === lastQuestionKey) score -= 70;
  const feedback = questionFeedbackRating(item.key);
  if (feedback > 0) score += 14;
  if (feedback < 0) score -= 45;
  return score;
}
function questionChip(key, active = false, dataAttribute = "data-question-key") {
  const item = findQuestion(key) || {};
  const personal = item.personalization || {};
  const boost = Number(personal.route_boost || 0);
  const score = item.personalized_score ?? item.score;
  const meta = boost > 0 ? `${structureMatchLabel()} +${boost}${score ? ` · ${score}` : ""}` : "";
  return `<button type="button" class="oracle-chip personalized-question-chip ${active ? "active" : ""}" ${dataAttribute}="${escapeHtml(key)}"><span>${escapeHtml(questionLabel(key))}</span>${meta ? `<small class="question-personalization">${escapeHtml(meta)}</small>` : ""}</button>`;
}
function backendPersonalizedQuestionKeys() {
  if (!dynamicQuestions.length) return [];
  return uniqueKeys(dynamicQuestions
    .filter((item) => item && item.key)
    .filter((item) => !FORBIDDEN_QUESTION_PATTERN.test(questionLabel(item.key)))
    .map((item) => item.key));
}
function renderAnswerEvidenceSummary(answer) {
  if (!$("answerEvidenceSummary")) return;
  const pack = answer.evidence_pack || (answer.retrieved_facts || {}).evidence_pack || {};
  const facts = (pack.fact_evidence || {}).present_fact_scopes || [];
  const knowledgeIds = (pack.knowledge_evidence || {}).applied_ids || pack.knowledge_ids || [];
  const runtimeIds = (pack.rule_graph_evidence || {}).runtime_selected_knowledge_ids || pack.runtime_selected_knowledge_ids || [];
  const portraitLabels = (pack.portrait_evidence || {}).label_ids || (answer.structure_portrait || {}).labels || [];
  const portraitCount = Array.isArray(portraitLabels) ? portraitLabels.length : 0;
  const audit = (pack.audit || {}).status || pack.audit_status || "";
  const status = pack.status || "";
  if (!status && !facts.length && !knowledgeIds.length && !runtimeIds.length && !portraitCount) {
    $("answerEvidenceSummary").classList.add("hidden");
    $("answerEvidenceSummary").innerHTML = "";
    return;
  }
  $("answerEvidenceSummary").classList.remove("hidden");
  $("answerEvidenceSummary").innerHTML = `<span>${escapeHtml(evidenceSummaryLabel())}</span><strong>${escapeHtml(`${facts.length} facts · ${knowledgeIds.length} knowledge · ${runtimeIds.length} route · ${portraitCount} portrait · ${audit || status || "-"}`)}</strong>`;
}
function relatedQuestionSet(key) {
  const item = findQuestion(key);
  return new Set(item?.related_questions || []);
}
function depthAvailable(item, context) {
  if (item.depth === "beginner") return true;
  if (item.depth === "intermediate") {
    if (context.result) return true;
    return mergedQuestionLibrary().some((row) => row.depth === "beginner" && visitedQuestionKeys.has(row.key) && (row.related_questions || []).includes(item.key));
  }
  return false;
}
function signalMapFromResult(result) {
  const signals = Array.isArray(result?.inference_context?.income_stability?.signals) ? result.inference_context.income_stability.signals : [];
  return Object.fromEntries(signals.map((row) => [row.key, row.value]));
}
function uniqueKeys(keys) { return [...new Set(keys.filter(Boolean))]; }
function tValue(value) { const key = String(value || "unknown").toLowerCase(); return labels[key] ? labels[key].label : String(value || t("unknown")); }
function t(key) { if (labels[key] && labels[key].label) return labels[key].label; console.warn(`Missing V19 label: ${key}`); return key; }
function dynamicQuestionsFrom(data) { return Array.isArray(data?.guided_question_context?.questions) ? data.guided_question_context.questions : []; }
function mergedQuestionLibrary() {
  const byKey = new Map();
  const source = dynamicQuestions.length ? dynamicQuestions : QUESTION_LIBRARY;
  source.forEach((item) => byKey.set(item.key, { ...item, dynamic: Boolean(dynamicQuestions.length) }));
  return Array.from(byKey.values());
}
function findQuestion(key) { return mergedQuestionLibrary().find((row) => row.key === key); }
function questionLabel(key) {
  const item = findQuestion(key);
  if (item?.label && typeof item.label === "object") return item.label[locale] || item.label.zh || item.label.en || key;
  return t(key);
}
function localText(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) return value[locale] || value.zh || value.en || value.ko || "";
  return String(value || "");
}
function answerText(answer) {
  if (answer.text && typeof answer.text === "object") {
    const text = answer.text[locale] || answer.text.zh || answer.text.en || answer.text.ko || "";
    if (String(text).trim()) return String(text).trim();
  }
  if (answer.content && typeof answer.content === "object") {
    const lines = answer.content[locale] || answer.content.zh || answer.content.en || answer.content.ko || [];
    if (Array.isArray(lines) && lines.join("").trim()) return lines.join("\n").trim();
  }
  return [localText(answer.summary), localText(answer.result_relation)].filter(Boolean).join("\n\n");
}
function structureMatchLabel() {
  return ({ zh: "结构匹配", en: "Structure match", ko: "구조 매칭" }[locale] || "Structure match");
}
function portraitTitleLabel() {
  return ({ zh: "结构画像", en: "Structure portrait", ko: "구조 프로필" }[locale] || "Structure portrait");
}
function portraitEvidenceLabel(portrait, visibleCount, totalCount) {
  const total = Number(totalCount || portrait.label_count || (portrait.labels || []).length || 0);
  const visible = Number(visibleCount || 0);
  if (visible && total && visible < total) {
    return ({ zh: `重点 ${visible} / 全部 ${total}`, en: `Top ${visible} / ${total}`, ko: `중점 ${visible} / 전체 ${total}` }[locale] || `Top ${visible} / ${total}`);
  }
  return ({ zh: `${total} 个重点标签`, en: `${total} key labels`, ko: `중점 라벨 ${total}개` }[locale] || `${total} key labels`);
}
function portraitVisibleLabels(portrait, limit = 5) {
  const labels = Array.isArray(portrait.labels) ? portrait.labels.filter((row) => row && typeof row === "object") : [];
  if (!labels.length) return [];
  const judgementFamilies = new Set((portrait.candidate_judgements || []).map((row) => String(row?.family || "")).filter(Boolean));
  const lowSignalValues = new Set(["limited", "weak_or_hidden", "background_only", "insufficient_evidence", "insufficient_index"]);
  const familyWeights = { strength: 0.14, useful_god: 0.16, pattern: 0.12, branch: 0.12, time: 0.08, wealth: 0.1, ten_god: 0.04 };
  const ranked = labels
    .map((row, index) => {
      const score = Number(row.score || 0);
      const confidence = Number(row.confidence || 0);
      const family = String(row.family || "");
      const judged = judgementFamilies.has(family);
      const lowSignal = lowSignalValues.has(String(row.value || ""));
      return {
        ...row,
        _portraitRank: score + confidence * 0.12 + (familyWeights[family] || 0) + (judged ? 0.16 : 0) - (lowSignal && !judged ? 0.18 : 0) - index * 0.001,
        _lowSignal: lowSignal,
        _judged: judged,
      };
    })
    .filter((row) => !row._lowSignal || row._judged || Number(row.score || 0) >= 0.5)
    .sort((a, b) => b._portraitRank - a._portraitRank);
  const out = [];
  const seenFamilies = new Set();
  for (const row of ranked) {
    const family = String(row.family || "");
    if (seenFamilies.has(family)) continue;
    out.push(row);
    seenFamilies.add(family);
    if (out.length >= limit) break;
  }
  if (out.length >= 3) return out;
  for (const row of labels) {
    const family = String(row.family || "");
    if (seenFamilies.has(family)) continue;
    out.push(row);
    seenFamilies.add(family);
    if (out.length >= Math.min(limit, 3)) break;
  }
  return out;
}
function portraitFamilyLabel(value) {
  const table = {
    zh: { strength: "强弱", useful_god: "用神", ten_god: "十神", wealth: "财富", branch: "地支", time: "时间", pattern: "格局" },
    en: { strength: "Strength", useful_god: "Useful god", ten_god: "Ten God", wealth: "Wealth", branch: "Branches", time: "Time", pattern: "Pattern" },
    ko: { strength: "강약", useful_god: "용신", ten_god: "십성", wealth: "재성", branch: "지지", time: "시간", pattern: "격국" },
  };
  return (table[locale] || table.zh)[value] || value || t("unknown");
}
function portraitValueLabel(value) {
  const table = {
    zh: {
      balanced_or_uncertain_candidate: "均衡候选",
      weaker_capacity_candidate: "偏弱候选",
      stronger_capacity_candidate: "偏强候选",
      weak_candidate: "偏弱候选",
      strong_candidate: "偏强候选",
      candidate_only: "候选路径",
      insufficient_evidence: "证据不足",
      active: "活跃",
      limited: "有限",
      visible: "可见",
      weak_or_hidden: "弱或隐藏",
      stable_candidate: "稳定候选",
      stability_needs_review: "需复核",
      quiet: "较静",
      trigger_context: "触发背景",
      background_only: "仅背景",
      pattern_index_available: "可建索引",
      pattern_index_weak: "索引较弱",
      index_candidate: "索引候选",
      insufficient_index: "索引不足",
    },
    en: {
      balanced_or_uncertain_candidate: "balanced candidate",
      weaker_capacity_candidate: "weaker candidate",
      stronger_capacity_candidate: "stronger candidate",
      weak_candidate: "weak candidate",
      strong_candidate: "strong candidate",
      candidate_only: "candidate path",
      insufficient_evidence: "insufficient",
      active: "active",
      limited: "limited",
      visible: "visible",
      weak_or_hidden: "weak/hidden",
      stable_candidate: "stable candidate",
      stability_needs_review: "review needed",
      quiet: "quiet",
      trigger_context: "trigger context",
      background_only: "background only",
      pattern_index_available: "index available",
      pattern_index_weak: "weak index",
      index_candidate: "index candidate",
      insufficient_index: "insufficient index",
    },
    ko: {
      balanced_or_uncertain_candidate: "균형 후보",
      weaker_capacity_candidate: "약한 후보",
      stronger_capacity_candidate: "강한 후보",
      weak_candidate: "약한 후보",
      strong_candidate: "강한 후보",
      candidate_only: "후보 경로",
      insufficient_evidence: "근거 부족",
      active: "활성",
      limited: "제한",
      visible: "가시",
      weak_or_hidden: "약함/숨김",
      stable_candidate: "안정 후보",
      stability_needs_review: "검토 필요",
      quiet: "조용함",
      trigger_context: "촉발 배경",
      background_only: "배경만",
      pattern_index_available: "색인 가능",
      pattern_index_weak: "색인 약함",
      index_candidate: "색인 후보",
      insufficient_index: "색인 부족",
    },
  };
  return (table[locale] || table.zh)[value] || String(value || t("unknown"));
}
function evidenceSummaryLabel() {
  return ({ zh: "回答依据", en: "Answer evidence", ko: "답변 근거" }[locale] || "Answer evidence");
}
function relationPayloadCount(...payloads) {
  return payloads.reduce((total, payload) => total + Object.values(payload || {}).reduce((sum, value) => sum + (Array.isArray(value) ? value.length : 0), 0), 0);
}
function hasThreeHarmonyRelation(natalRelations, ...payloads) {
  if ((natalRelations || []).some((row) => /three_harmony|三合/i.test(String(row?.type || row?.relation_type || "")))) return true;
  return payloads.some((payload) => Object.keys(payload || {}).some((key) => /three_harmony|三合/i.test(key)));
}
function hasCombinationRelation(natalRelations, ...payloads) {
  if ((natalRelations || []).some((row) => /combination|六合|合/i.test(String(row?.type || row?.relation_type || "")))) return true;
  return payloads.some((payload) => Object.keys(payload || {}).some((key) => /combination|六合|合/i.test(key)));
}
function loadLocalQuestionFeedback() {
  try {
    return JSON.parse(localStorage.getItem(questionFeedbackStorageKey()) || "{}");
  } catch (_) {
    return {};
  }
}
function questionFeedbackStorageKey() { return `v19_oracle_question_feedback:${profileId || "anonymous"}`; }
function rememberQuestionFeedback(key, rating) {
  if (!key) return;
  localQuestionFeedback = { ...localQuestionFeedback, [key]: Number(rating || 0) };
  localStorage.setItem(questionFeedbackStorageKey(), JSON.stringify(localQuestionFeedback));
}
function questionFeedbackRating(key) { return Number(localQuestionFeedback[key] || 0); }
function fallbackTerms(nextLocale) {
  const table = FALLBACK_LABELS[nextLocale] || FALLBACK_LABELS.zh;
  return Object.fromEntries(Object.entries(table).map(([key, label]) => [key, { label }]));
}
async function postJson(url, payload) { const response = await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}); return response.json(); }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"})[char]); }
