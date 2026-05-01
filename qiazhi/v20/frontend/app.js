const state = {
  latest: null,
};

const form = document.querySelector("#measureForm");
const questionSelect = document.querySelector("#questionSelect");
const roleSelect = document.querySelector("#roleSelect");
const feedbackButton = document.querySelector("#feedbackButton");

const setText = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value;
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

const measure = async () => {
  const data = new FormData(form);
  const payload = Object.fromEntries(data.entries());
  const button = form.querySelector("button");
  button.disabled = true;
  button.textContent = "测算中";
  try {
    const role = payload.role_key || "full";
    delete payload.role_key;
    const endpoint = role === "full" ? "/api/v20/measure" : `/api/v20/measure/view/${role}`;
    const result = await requestJson("/api/v20/measure", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const view = role === "full" ? result : await requestJson(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (role !== "full") {
      view.full_runtime = result;
    }
    state.latest = view;
    renderRuntime(view);
  } catch (error) {
    setText("#answerText", `测算失败：${error.message}`);
  } finally {
    button.disabled = false;
    button.textContent = "开始测算";
  }
};

const renderRuntime = (result) => {
  const selected = result.selected_question || {};
  const fullRuntime = result.full_runtime || result;
  setText("#selectedQuestion", selected.title || selected.question_key || "已完成测算");
  setText("#featureCount", result.feature_layer?.feature_count ?? fullRuntime.feature_layer?.feature_count ?? 0);
  setText("#topicCount", result.measurement_report?.topic_count ?? 0);
  setText("#knowledgeCount", result.knowledge_report?.count ?? fullRuntime.knowledge_report?.count ?? 0);
  setText("#coreCapacity", result.core_inference?.day_master_capacity || fullRuntime.core_inference?.day_master_capacity || result.role?.role_key || "core");
  setText("#appliedDomains", (result.measurement_report?.applied_domain_keys || []).join(" / "));
  setText("#llmStatus", `llm ${result.llm_assist?.status || fullRuntime.llm_assist?.status || "hidden"}`);
  setText("#answerText", result.answer_text || "");
  renderQuestionSelect(fullRuntime.questions || result.questions || [], selected.question_key || "");
  renderFeatures(result.feature_layer?.features || fullRuntime.feature_layer?.features || []);
  renderTopics(result.measurement_report?.topics || []);
  renderQuestions(result.questions || [], selected.question_key || "");
  renderPortrait(result.portrait_projection?.axes || fullRuntime.portrait_projection?.axes || []);
};

const renderQuestionSelect = (questions, selectedKey) => {
  const current = questionSelect.value || selectedKey;
  questionSelect.innerHTML = '<option value="">自动路由</option>';
  questions.forEach((question) => {
    const option = document.createElement("option");
    option.value = question.question_key;
    option.textContent = question.title;
    questionSelect.appendChild(option);
  });
  questionSelect.value = current;
};

const renderFeatures = (features) => {
  const root = document.querySelector("#featureChips");
  root.innerHTML = "";
  features.slice(0, 8).forEach((feature) => {
    const row = document.createElement("div");
    row.className = "chip";
    row.dataset.domain = feature.domain;
    row.innerHTML = `<strong>${feature.title}</strong><span>${feature.domain} · confidence ${feature.confidence}</span>`;
    root.appendChild(row);
  });
};

const renderTopics = (topics) => {
  const root = document.querySelector("#measurementTopics");
  root.innerHTML = "";
  topics.forEach((topic) => {
    const row = document.createElement("div");
    row.className = "topic-row";
    row.innerHTML = `<strong>${topic.label}</strong><span>${topic.stage} · ${topic.status}</span><div class="meter"><i style="width:${Math.round(topic.confidence * 100)}%"></i></div>`;
    root.appendChild(row);
  });
};

const renderQuestions = (questions, selectedKey) => {
  const root = document.querySelector("#questionList");
  root.innerHTML = "";
  questions.forEach((question) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `question-row${question.question_key === selectedKey ? " active" : ""}`;
    button.innerHTML = `<strong>${question.title}</strong><span>${question.measurement_topic} · score ${question.score}</span>`;
    button.addEventListener("click", () => {
      questionSelect.value = question.question_key;
      measure();
    });
    root.appendChild(button);
  });
};

const renderPortrait = (axes) => {
  const root = document.querySelector("#portraitAxes");
  root.innerHTML = "";
  axes.forEach((axis) => {
    const row = document.createElement("div");
    row.className = "axis-row";
    row.innerHTML = `<strong>${axis.label}</strong><span>${axis.measurement_stage} · ${axis.feature_count} features</span><div class="meter"><i style="width:${Math.round(axis.peak_confidence * 100)}%"></i></div>`;
    root.appendChild(row);
  });
};

const loadOps = async () => {
  try {
    const [health, corpus, validation, learning, dependencies, policyReview, matrix] = await Promise.all([
      requestJson("/health"),
      requestJson("/api/v20/corpus/coverage"),
      requestJson("/api/v20/validation/synthetic-suite"),
      requestJson("/api/v20/learning/evolution-plan"),
      requestJson("/api/v20/runtime/dependencies"),
      requestJson("/api/v20/learning/policy-review"),
      requestJson("/api/v20/testing/matrix"),
    ]);
    document.querySelector("#runtimeStatus").innerHTML = `<span>${health.active_profile}</span><strong>${health.status}</strong>`;
    setText("#profileBadge", health.active_profile);
    setText("#corpusState", `${corpus.plan.target_case_count} cases · ${corpus.plan.shard_count} shards`);
    setText("#validationState", `${validation.ok ? "pass" : "blocked"} · ${validation.case_count} cases`);
    setText("#learningState", `${learning.status} · ${learning.allowed_algorithm_tracks.length} tracks`);
    setText("#dependencyState", `pg ${dependencies.postgres.ready_for_connection ? "ready" : "config"} · redis ${dependencies.redis.ready_for_connection ? "ready" : "config"}`);
    setText("#policyState", `${policyReview.supported_policy_types.length} policy types · dry-run`);
    setText("#testMatrixState", `${matrix.area_count} areas · ${matrix.default_tier}`);
  } catch (error) {
    document.querySelector("#runtimeStatus").innerHTML = `<span>health</span><strong>error</strong>`;
    setText("#validationState", error.message);
  }
};

const submitFeedback = async () => {
  const text = document.querySelector("#feedbackText").value.trim();
  if (!text) {
    setText("#feedbackOutput", "请输入反馈。");
    return;
  }
  const latest = state.latest?.full_runtime || state.latest || {};
  const featureIds = (latest.feature_layer?.features || []).slice(0, 4).map((feature) => feature.feature_id);
  feedbackButton.disabled = true;
  feedbackButton.textContent = "分析中";
  try {
    const result = await requestJson("/api/v20/feedback/analyze", {
      method: "POST",
      body: JSON.stringify({
        input_id: latest.input_id || "ui.feedback",
        source_role: roleSelect.value === "full" ? "analyst" : roleSelect.value,
        feedback_text: text,
        feature_ids: featureIds,
      }),
    });
    setText("#feedbackState", result.learning_proposal?.status || "recorded");
    setText("#feedbackOutput", `hash ${result.source_hash}\n${result.redacted_summary}\nproposal ${result.learning_proposal?.proposal_type}`);
  } catch (error) {
    setText("#feedbackOutput", `反馈分析失败：${error.message}`);
  } finally {
    feedbackButton.disabled = false;
    feedbackButton.textContent = "分析反馈";
  }
};

form.addEventListener("submit", (event) => {
  event.preventDefault();
  measure();
});
feedbackButton.addEventListener("click", submitFeedback);

loadOps();
measure();
