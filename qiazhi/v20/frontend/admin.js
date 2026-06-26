const setText = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value ?? "";
};

const logoutButton = document.querySelector("#logoutButton");
const locale = localStorage.getItem("v20_locale") || "zh";

const ADMIN_TEXT = {
  zh: { status: "状态", refresh: "刷新", save: "保存", models: "模型", clear_cache: "清理缓存", no_data: "暂无数据。", await_db: "等待 V20_DATABASE_URL。", logout: "登出", entry: "入口", profiles: "档案", measure: "测算" },
  en: { status: "Status", refresh: "Refresh", save: "Save", models: "Models", clear_cache: "Clear Cache", no_data: "No data.", await_db: "Waiting for V20_DATABASE_URL.", logout: "Log Out", entry: "Entry", profiles: "Profiles", measure: "Reading" },
  ko: { status: "상태", refresh: "새로고침", save: "저장", models: "모델", clear_cache: "캐시 정리", no_data: "데이터 없음.", await_db: "V20_DATABASE_URL 대기 중.", logout: "로그아웃", entry: "입구", profiles: "프로필", measure: "분석" },
};
const adminText = () => ADMIN_TEXT[locale] || ADMIN_TEXT.zh;

const setAdminTab = (tab) => {
  const clean = tab === "training" ? "training" : "config";
  document.body.dataset.adminTab = clean;
  document.querySelectorAll("[data-admin-tab-target]").forEach((button) => {
    button.classList.toggle("active", button.dataset.adminTabTarget === clean);
  });
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

const loadCurrentSession = async () => {
  try {
    const result = await requestJson("/api/v20/auth/me");
    const session = result.session || {};
    if (logoutButton) logoutButton.hidden = !result.authenticated;
    if (session.role !== "admin") {
      setText("#adminStatus", "需要管理员登录");
    }
    return session;
  } catch (error) {
    if (logoutButton) logoutButton.hidden = true;
    setText("#adminStatus", "需要管理员登录");
    return {};
  }
};

const logout = async () => {
  await requestJson("/api/v20/auth/logout", {
    method: "POST",
    body: JSON.stringify({}),
  });
  window.location.href = "/v20/ui/";
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

const renderDb = async () => {
  const db = await requestJson("/api/v20/admin/db");
  await renderAdminConfig();
  setText("#adminStatus", `数据库：${zhStatus(db.status)}`);
  const summary = document.querySelector("#dbSummary");
  clear(summary);
  [
    [adminText().status, db.status],
    ["Profile", db.active_profile],
    ["Host", `${db.postgres?.host || "-"}:${db.postgres?.port || "-"}`],
    ["Database", db.postgres?.database || "-"],
    ["URL", db.database_url_present ? "present" : "missing"],
    ["Authority", db.authority_table || "v20_corpus_snapshots"],
  ].forEach(([label, value]) => summary.append(metric(label, value)));

  const tableRoot = document.querySelector("#dbTables");
  clear(tableRoot);
  Object.entries(db.counts || {}).forEach(([name, count]) => {
    const row = el("div", "kv-row");
    row.append(el("span", "", name));
    row.append(el("strong", "", count === null ? "missing" : String(count)));
    tableRoot.append(row);
  });
  if (!Object.keys(db.counts || {}).length) {
    tableRoot.append(el("div", "empty-note", adminText().await_db));
  }

  renderTags("#dbIndexes", db.corpus_indexes || []);
};

const renderLlm = async (probeModels = false) => {
  const [llm, architecture] = await Promise.all([
    requestJson(`/api/v20/admin/llm${probeModels ? "?probe_models=true" : ""}`),
    requestJson("/api/v20/admin/central-brain-architecture"),
  ]);
  await renderAdminConfig();
  setText("#adminStatus", `LLM：${zhStatus(llm.status)}`);
  const ready = llm.readiness || {};
  const summary = document.querySelector("#llmSummary");
  clear(summary);
  [
    [adminText().status, llm.status],
    ["服务", ready.provider || "-"],
    ["模型", ready.model || "-"],
    ["执行", ready.execute_llm ? "开启" : "关闭"],
    ["可连接", ready.ready_for_connection ? "是" : "否"],
    ["Base URL", ready.resolved_base_url || "-"],
  ].forEach(([label, value]) => summary.append(metric(label, value)));

  const models = (llm.models || []).map((row) => row.id).filter(Boolean);
  renderModelOptions(models, ready.model || "");
  renderTags("#llmModels", models);
  renderTags("#llmGuardrails", [
    ...(ready.guardrails || llm.guardrails || []),
    ...((architecture.llm_prompt_context_design || {}).ui_labels || []),
  ]);
  renderLlmConfigDesignSummary(summary, architecture.llm_prompt_context_design || {});
};

const renderLlmConfigDesignSummary = (root, design = {}) => {
  if (!root || !design.version) return;
  [
    ["Prompt 设计", `${design.completion_percent ?? 0}%`],
    ["Prompt 方式", "短提示词 + 结构化上下文"],
    ["上下文层", `${(design.context_layers || []).length} 层`],
    ["遗留上下文", (design.retired_context_paths || []).length ? "已清理" : "无遗留"],
  ].forEach(([label, value]) => root.append(metric(label, value)));
};

const renderAdminConfig = async () => {
  const config = await requestJson("/api/v20/admin/config");
  fillForm("#dbConfigForm", config.database || {});
  fillForm("#llmConfigForm", config.llm || {});
};

const renderRedis = async () => {
  const redis = await requestJson("/api/v20/redis/cache-status");
  setText("#adminStatus", `缓存：${zhStatus(redis.status)}`);
  const summary = document.querySelector("#redisSummary");
  clear(summary);
  [
    [adminText().status, redis.status],
    ["Keyspace", redis.keyspace || "-"],
    ["Keys", String(redis.key_count ?? 0)],
    ["TTL", `${redis.ttl_seconds || 0}s`],
    ["DB", String(redis.db ?? "-")],
    ["Ping", redis.ping ? "ok" : "-"],
  ].forEach(([label, value]) => summary.append(metric(label, value)));
  renderTags("#redisGuardrails", redis.guardrails || []);
};

let trainingTaskPollTimer = null;
let activeTrainingTaskId = "";
let latestTrainingTask = {};
let startingTrainingTaskKey = "";
let trainingLabelByKey = new Map();

const zhStatus = (status) => ({
  ready: "正常",
  complete: "完成",
  completed: "完成",
  completed_with_findings: "完成，有发现",
  needs_work: "待补齐",
  queued: "已排队",
  running: "运行中",
  succeeded: "已完成",
  failed: "失败",
  paused: "已暂停",
  idle: "空闲",
  not_run: "未运行",
  not_found: "暂无结果",
  unavailable: "暂不可用",
  blocked: "已阻断",
  blocked_by_machine_gate: "机器验证未通过",
  bundle_active: "训练包已生效",
  latest_candidate_active: "候选已生效",
  candidate_active: "候选已生效",
  blocked_no_latest_candidate: "没有候选",
  needs_runtime_consumers: "还没完全接入系统",
  consumed: "已接入系统",
  needs_consumer: "待接入系统",
  missing_or_partial: "部分就绪",
  covered: "已覆盖",
  needs_expansion: "需扩展",
  pass: "通过",
  active: "启用中",
  active_ready: "已就绪",
  central_brain_controlled: "中枢控制",
  fallback: "使用基础版本",
  model_probe_ready: "模型已刷新",
  model_probe_failed: "模型刷新失败",
  pending: "等待中",
  observe_only: "只验证",
  machine_ready: "可自动优化",
  optimizer_missing: "缺少自动调参器",
  awaiting_acceptance: "等待生效",
  ready_for_candidate_apply: "候选可推进",
  needs_more_replay: "需要更多回放",
  promote_candidate: "推进候选",
  run_recommended_replay: "先跑回放",
}[status] || status || "-");

const zhRisk = (risk) => ({ low: "低", normal: "中", high: "高" }[risk] || risk || "-");
const zhHeavy = (level) => ({ light: "轻量", medium: "中等", heavy: "较重" }[level] || level || "-");
const zhDuration = (value) => ({
  seconds: "几秒",
  seconds_to_minutes: "几秒到几分钟",
  minutes: "几分钟",
  minutes_or_more: "几分钟以上",
}[value] || value || "-");
const zhStrategy = (value) => ({
  fast_iteration_with_gated_auto_apply: "快速迭代，机器验证后自动调参",
  deterministic_replay_plus_distribution_eval: "确定性回放和分布验证",
}[value] || value || "-");
const zhRole = (role) => ({
  guest: "游客",
  user: "用户",
  practitioner: "命理师",
  analyst: "命理师",
  admin: "管理员",
  lab: "实验室",
}[role] || role || "-");
const zhParamTarget = (target) => ({
  portrait_axis_weight: "画像轴权重",
  confidence_threshold: "置信阈值",
  role_depth: "角色展示深度",
  topic_projection_weight: "主题投射权重",
  rule_weight: "规则权重",
  subcondition_threshold: "子条件阈值",
  counterexample_penalty: "反例惩罚",
  registry_priority: "判断优先级",
  knowledge_rule_mapping_weight: "知识规则映射权重",
  answer_guidance_weight: "回答引导权重",
  source_trust: "来源可信度",
  counterexample_coverage: "反例覆盖",
  source_weight: "问题来源权重",
  rank_weight: "排序权重",
  dag_transition_weight: "追问链路权重",
  mainline_focus_weight: "主线聚焦权重",
  role_ordering: "角色排序",
  visibility_level: "可见深度",
  question_count: "问题数量",
  seed_fit_policy: "种子问题匹配",
  role_context_density_weight: "角色上下文密度",
  bazi_context_profile_weight: "八字上下文权重",
  answer_contract_structure_weight: "回答结构约束",
  prompt_context_budget_weight: "上下文长度预算",
  feature_threshold: "特征阈值",
  coverage_prior: "覆盖先验",
  similar_case_weight: "相似案例权重",
  corpus_shard_quality: "语料分片质量",
}[target] || target || "-");
const zhScript = (scriptPath) => {
  const name = String(scriptPath || "").split("/").pop() || "";
  return ({
    "run_training_iteration.py": "训练迭代脚本",
    "run_synthetic_case_suite.py": "合成八字验证脚本",
    "run_structure_dynamics_synthetic.py": "结构动态做功链验证脚本",
    "run_structure_dynamics_corpus_distribution.py": "结构动态语料回放脚本",
    "run_rule_synthetic_training.py": "规则合成训练脚本",
    "run_question_source_training.py": "问题来源训练脚本",
    "run_question_ranking_training.py": "问题排序训练脚本",
    "run_question_dag_training.py": "追问链路训练脚本",
    "run_next_question_synthetic_validation.py": "下一问合成验证脚本",
    "run_practitioner_calibration_training.py": "命理师校准训练脚本",
    "run_role_interaction_training.py": "角色体验训练脚本",
    "run_rule_subcondition_split.py": "规则条件拆分脚本",
    "run_rule_replay_eval.py": "规则回放评估脚本",
    "run_decision_registry_iteration.py": "判断库迭代脚本",
    "run_rule_portrait_batch.py": "规则画像批量训练脚本",
    "run_knowledge_rule_orchestrator.py": "知识规则联合训练脚本",
    "run_knowledge_rule_review_overlay.py": "知识规则对齐脚本",
    "extract_rules_llm.py": "LLM 规则草稿脚本",
    "run_nightly_learning_executor.py": "夜间小分片训练脚本",
    "run_full_precompute.py": "语料预计算脚本",
  }[name] || name || "-");
};
const trainingDisplayLabel = (task = {}) => trainingLabelByKey.get(task.task_key || "") || task.label || task.task_key || "-";
const trainingDisplayFromKey = (taskKey, fallback = "") => trainingLabelByKey.get(taskKey || "") || fallback || taskKey || "-";
const zhWriter = (status) => ({
  ready: "自动调参已就绪",
  missing_or_partial: "自动调参部分就绪",
  missing: "缺少自动调参",
}[status] || zhStatus(status));
const zhConsumer = (consumer) => ({
  "api.runtime": "测算主流程",
  "orchestrator.mainline": "中枢主线判断",
  "orchestrator.question_focus": "问题聚焦",
  "role_view.projection": "角色页面展示",
  "interaction.question_ranker": "问题排序",
  "corpus.artifacts.find_similar_cases": "相似案例检索",
  "rules.engine": "规则引擎",
  "decision.defeasible_model": "反证判断模型",
  "interaction.portrait_projection": "画像投射",
  "decision.knowledge_bridge": "知识规则桥",
  "knowledge.rule_library": "知识规则库",
}[consumer] || consumer || "-");
const zhPointerTarget = (target) => ({
  knowledge_runtime_policy_pointer: "知识策略指针",
  rule_runtime_policy_pointer: "规则策略指针",
  portrait_runtime_policy_pointer: "画像策略指针",
  question_runtime_policy_pointer: "问题策略指针",
  role_view_runtime_policy_pointer: "角色视图指针",
  orchestrator_runtime_policy_pointer: "中枢策略指针",
  corpus_runtime_policy_pointer: "语料策略指针",
  synthetic_training_artifact: "合成训练产物",
}[target] || target || "-");

const renderTrainingTasks = async () => {
  let registry = {};
  let list = {};
  let activations = {};
  let runtimeAudit = {};
  let centralBrain = {};
  let mainlineStatus = {};
  try {
    [registry, list, activations, runtimeAudit, centralBrain, mainlineStatus] = await Promise.all([
      requestJson("/api/v20/admin/training/tasks/registry"),
      requestJson("/api/v20/admin/training/tasks"),
      requestJson("/api/v20/admin/training/activations"),
      requestJson("/api/v20/admin/runtime-consumption-audit"),
      requestJson("/api/v20/admin/central-brain-architecture"),
      requestJson("/api/v20/admin/mainline-status"),
    ]);
  } catch (error) {
    renderTrainingTaskLoadError(error);
    return;
  }
  setText("#adminStatus", `训练任务：${zhStatus(registry.status)}`);
  const summary = document.querySelector("#trainingTaskSummary");
  clear(summary);
  [
    ["状态", zhStatus(registry.status || "-")],
    ["完成度", `${registry.mainline_completion?.percent ?? 0}%`],
    ["待补齐", String(registry.mainline_completion?.remaining_count ?? 0)],
    ["参数优化", zhStatus(registry.parameter_impact?.status || "-")],
    ["自动调参", registry.parameter_impact?.auto_parameter_optimization ? "开启" : "未开启"],
    ["计划", zhStrategy(registry.training_plan?.strategy || "-")],
    ["冷却中", String(registry.training_plan?.dedupe_summary?.cooldown_blocked_count ?? 0)],
    ["合成缺口", String(registry.training_plan?.synthetic_rule_plan?.gap_count ?? 0)],
    ["可运行任务", String(registry.task_count ?? 0)],
    ["运行记录", String(list.task_count ?? 0)],
    ["调参记录", String(activations.record_count ?? 0)],
    ["最近状态", zhStatus(list.latest?.status || "-")],
    ["下一步", trainingDisplayFromKey(registry.recommended_next?.task_key, registry.recommended_next?.label || "-")],
  ].forEach(([label, value]) => summary.append(metric(label, value)));

  const root = document.querySelector("#trainingTaskRegistry");
  clear(root);
  trainingLabelByKey = new Map((registry.tasks || []).map((task) => [task.task_key, task.label]));
  latestTrainingTask = list.latest || {};
  const activeTask = registry.active_task || {};
  const latestByKey = new Map();
  (list.tasks || []).forEach((task) => {
    if (task.task_key && !latestByKey.has(task.task_key)) latestByKey.set(task.task_key, task);
  });
  renderCentralBrainArchitecture(root, centralBrain || {});
  renderMainlineStatus(root, mainlineStatus || {});
  renderBrainGraphTaskMap(root, registry.central_brain || {});
  renderTrainingRecommendation(root, registry.recommended_next || {}, activeTask);
  renderRuntimeConsumptionAudit(root, runtimeAudit || {});
  renderTrainingPlan(root, registry.training_plan || {});
  renderTrainingTaskSections(root, registry.tasks || [], registry.sections || [], latestByKey, activeTask);
  if (!(registry.tasks || []).length) {
    root.append(el("div", "empty-note", adminText().no_data));
  }
  renderTrainingTaskStatus(latestTrainingTask);
  renderTrainingHistory(list.tasks || []);
  renderTrainingActivationHistory(activations.preflights || []);
  if (list.latest?.task_id && ["queued", "running"].includes(list.latest.status)) {
    activeTrainingTaskId = list.latest.task_id;
    scheduleTrainingTaskPoll();
  }
};

const renderCentralBrainArchitecture = (root, architecture = {}) => {
  if (!architecture.version) return;
  const card = el("section", "training-plan-card central-brain-card");
  const head = el("div", "training-task-section-head");
  const title = el("div", "");
  title.append(el("span", "section-kicker", "中枢大脑"));
  title.append(el("h3", "", "中枢训练控制台"));
  head.append(title);
  head.append(el("span", "small-pill", zhStatus(architecture.status || "-")));
  card.append(head);
  const principles = architecture.principles || {};
  const metrics = el("div", "admin-summary compact");
  [
    ["完成度", `${architecture.completion_percent ?? 0}%`],
    ["BrainGraph", `${architecture.brain_graph?.nodes?.length ?? 0} 个节点`],
    ["受控模块", `${architecture.modules?.length ?? 0} 个`],
    ["训练专题", `${architecture.training_topics?.length ?? 0} 个`],
    ["直接生效", principles.training_outputs_apply_directly ? "开启" : "未开启"],
    ["生效方式", principles.no_human_review_gate ? "直接生效" : "待接入直生效"],
  ].forEach(([label, value]) => metrics.append(metric(label, value)));
  card.append(metrics);

  const graph = el("div", "brain-graph-strip");
  (architecture.brain_graph?.nodes || []).slice(0, 12).forEach((node, index) => {
    const item = el("div", "brain-graph-node");
    item.append(el("span", "", String(index + 1).padStart(2, "0")));
    item.append(el("strong", "", zhBrainNode(node.node_key || "")));
    item.append(el("em", "", node.owner || ""));
    graph.append(item);
  });
  card.append(graph);

  const modules = el("div", "training-topic-grid");
  (architecture.modules || []).forEach((mod) => {
    const item = el("div", "training-topic-card");
    const row = el("div", "training-topic-head");
    row.append(el("strong", "", mod.label || mod.module_key || "-"));
    row.append(el("span", "small-pill", zhStatus(mod.control_status || "-")));
    item.append(row);
    item.append(el("span", "", `生效目标：${zhPointerTarget(mod.runtime_pointer_target || "")}`));
    const tasks = el("div", "training-arg-list");
    (mod.atomic_trainings || []).forEach((task) => tasks.append(el("code", "", trainingDisplayFromKey(task, task))));
    item.append(tasks);
    modules.append(item);
  });
  card.append(modules);

  const promptDesign = architecture.llm_prompt_context_design || {};
  if (promptDesign.version) {
    card.append(renderLlmPromptContextDesign(promptDesign));
  }

  const topics = el("div", "training-plan-rows");
  (architecture.training_topics || []).forEach((topic) => {
    const item = el("div", "training-plan-row central-topic-row");
    item.append(el("strong", "", topic.label || topic.topic_key || "-"));
    item.append(el("span", "", "训练成功后自动写入对应 runtime pointer，不需要人工审核。"));
    const params = el("div", "training-arg-list");
    (topic.parameter_targets || []).slice(0, 5).forEach((target) => params.append(el("code", "", zhParamTarget(target))));
    item.append(params);
    const pointers = el("div", "training-arg-list");
    (topic.runtime_pointer_targets || []).forEach((target) => pointers.append(el("code", "", zhPointerTarget(target))));
    item.append(pointers);
    topics.append(item);
  });
  card.append(topics);

  const ui = architecture.ui_alignment || {};
  const uiBox = el("div", "training-plan-gaps central-ui-contract");
  (ui.required_panels || []).slice(0, 8).forEach((panel) => uiBox.append(el("span", "small-pill", zhUiPanel(panel))));
  card.append(uiBox);
  root.append(card);
};

const renderMainlineStatus = (root, status = {}) => {
  if (!status.version) return;
  const card = el("section", "training-plan-card mainline-status-card");
  const head = el("div", "training-task-section-head");
  const title = el("div", "");
  title.append(el("span", "section-kicker", "主线状态"));
  title.append(el("h3", "", "主线完成度与最新设计"));
  head.append(title);
  head.append(el("span", "small-pill", status.completion_label || `${status.completion_percent ?? 0}%`));
  card.append(head);
  const metrics = el("div", "admin-summary compact");
  const llm = status.llm_prompt_context_design || {};
  const answer = status.answer_governance_training || {};
  [
    ["系统主线", zhStatus(status.status || "-")],
    ["完成度", status.completion_label || `${status.completion_percent ?? 0}%`],
    ["训练原则", status.principle?.no_human_review_gate_for_training ? "训练直接生效" : "待接入直生效"],
    ["LLM 新流程", `${llm.completion_percent ?? 0}%`],
    ["上下文层", `${llm.context_layer_count ?? 0} 层`],
    ["流式质量样本", `${answer.stream_answer_quality_sample_count ?? 0} 条`],
    ["上下文预算权重", Number(answer.prompt_context_budget_weight || 0).toFixed(3)],
    ["遗留上下文", Number(llm.retired_context_count || 0) > 0 ? "已清理" : "无遗留"],
  ].forEach(([label, value]) => metrics.append(metric(label, value)));
  card.append(metrics);
  const tags = el("div", "training-arg-list");
  tags.append(el("code", "", "短提示词"));
  tags.append(el("code", "", "结构化上下文"));
  tags.append(el("code", "", "role_context"));
  tags.append(el("code", "", "bazi_context_profile"));
  tags.append(el("code", "", "answer_contract"));
  tags.append(el("code", "", "answer_plan_rewrite.context.v2"));
  card.append(tags);
  if ((status.blockers || []).length) {
    const gaps = el("div", "training-plan-gaps");
    status.blockers.forEach((row) => gaps.append(el("span", "small-pill", `${row.area}:${row.reason}`)));
    card.append(gaps);
  } else {
    card.append(el("p", "", "当前主线已完成；后续训练产物按 runtime pointer 直接生效，不走人工审核。"));
  }
  root.append(card);
};

const renderLlmPromptContextDesign = (design = {}) => {
  const box = el("div", "training-plan-row llm-prompt-design");
  const top = el("div", "training-topic-head");
  top.append(el("strong", "", "LLM 提示词与上下文"));
  top.append(el("span", "small-pill", `${design.completion_percent ?? 0}%`));
  box.append(top);
  box.append(el("span", "", "新流程：短提示词负责任务和边界；角色、八字结构、规则、画像、特征和中枢判断进入结构化上下文，并用上下文预算防止提示词膨胀。"));
  const tags = el("div", "training-arg-list");
  (design.ui_labels || []).forEach((label) => tags.append(el("code", "", label)));
  box.append(tags);
  const layers = el("div", "training-arg-list");
  (design.context_layers || []).slice(0, 8).forEach((layer) => layers.append(el("code", "", zhContextLayer(layer))));
  box.append(layers);
  const budget = design.prompt_budget || {};
  if (Object.keys(budget).length) {
    const budgetTags = el("div", "training-arg-list");
    budgetTags.append(el("code", "", `回答目标 ${budget.practitioner_answer_target_chars || "-"} 字符`));
    budgetTags.append(el("code", "", `回答上限 ${budget.practitioner_answer_max_chars || "-"} 字符`));
    budgetTags.append(el("code", "", `流式输入 ${budget.practitioner_stream_payload_max_chars || "-"} 字符`));
    box.append(budgetTags);
  }
  const consumers = el("div", "training-arg-list");
  (design.runtime_consumers || []).forEach((consumer) => consumers.append(el("code", "", zhLlmConsumer(consumer))));
  box.append(consumers);
  if ((design.retired_context_paths || []).length) {
    box.append(el("p", "training-when", `已清理遗留上下文：${design.retired_context_paths.join("、")}`));
  }
  return box;
};

const zhContextLayer = (layer) => ({
  "context.system_understanding": "系统理解",
  "context.system_understanding.role_context": "角色上下文",
  "context.system_understanding.bazi_context_profile": "八字结构上下文",
  "context.context_budget": "上下文预算",
  answer_contract: "回答合同",
  "questions[].question_narrative": "问题叙事",
  "answer_plan_rewrite.context.v2": "改写上下文 v2",
}[layer] || layer || "-");

const zhLlmConsumer = (consumer) => ({
  "llm.prompts.practitioner_answer_prompt": "命理师回答 prompt",
  "llm.prompts.answer_rewrite_prompt": "回答改写 prompt",
  "llm.context.build_llm_context_pack": "LLM 上下文包",
}[consumer] || consumer || "-");

const renderBrainGraphTaskMap = (root, centralBrain = {}) => {
  const sections = centralBrain.brain_graph_task_sections || [];
  if (!sections.length) return;
  const card = el("section", "training-plan-card central-brain-card");
  const head = el("div", "training-task-section-head");
  const title = el("div", "");
  title.append(el("span", "section-kicker", "中枢编排"));
  title.append(el("h3", "", "中枢任务编排"));
  head.append(title);
  head.append(el("span", "small-pill", zhStatus(centralBrain.status || "-")));
  card.append(head);
  card.append(el("p", "", "按中枢大脑链路组织训练：知识、规则、画像、问题、角色、合成、518K 和参数生效。训练产物有调参器时直接写入 runtime pointer，不走人工审核。"));

  const rows = el("div", "training-plan-rows brain-task-map");
  sections.forEach((section) => {
    const row = el("div", "training-plan-row central-topic-row");
    const top = el("div", "training-topic-head");
    top.append(el("strong", "", section.label || zhBrainNode(section.node_key || "")));
    top.append(el("span", "small-pill", `${section.task_count || 0} 个任务`));
    row.append(top);
    row.append(el("span", "", section.purpose || ""));
    const tasks = el("div", "training-arg-list");
    (section.task_keys || []).forEach((taskKey) => tasks.append(el("code", "", trainingDisplayFromKey(taskKey, taskKey))));
    row.append(tasks);
    const pointers = el("div", "training-arg-list");
    (section.runtime_pointer_targets || []).slice(0, 6).forEach((target) => pointers.append(el("code", "", zhPointerTarget(target))));
    if ((section.runtime_pointer_targets || []).length) row.append(pointers);
    rows.append(row);
  });
  card.append(rows);
  root.append(card);
};

const zhBrainNode = (nodeKey) => ({
  knowledge_gap_pick: "知识缺口",
  knowledge_atom_contract: "知识合同",
  rule_candidate_generation: "规则生成",
  portrait_mapping_generation: "画像映射",
  question_policy_generation: "问题策略",
  role_policy_generation: "角色策略",
  llm_context_policy_generation: "LLM 上下文",
  synthetic_case_binding: "合成绑定",
  synthetic_validation: "合成验证",
  corpus_replay_518k: "518K 回放",
  parameter_optimizer: "参数优化",
  runtime_pointer_publish: "指针生效",
  ui_observability: "UI 观测",
}[nodeKey] || nodeKey || "-");

const zhUiPanel = (panel) => ({
  mainline_status: "主线状态",
  central_brain_graph: "中枢图",
  training_topics: "训练专题",
  atomic_training_tasks: "原子训练",
  current_background_task: "后台任务",
  parameter_targets: "参数目标",
  runtime_pointer_effects: "生效结果",
  rollback_entry: "回滚入口",
}[panel] || panel || "-");

const renderRuntimeConsumptionAudit = (root, audit = {}) => {
  if (!audit.version) return;
  const card = el("section", "training-plan-card");
  const head = el("div", "training-task-section-head");
  const title = el("div", "");
  title.append(el("span", "section-kicker", "参数是否真的生效"));
  title.append(el("h3", "", "训练结果接入系统检查"));
  head.append(title);
  head.append(el("span", "small-pill", zhStatus(audit.status || "-")));
  card.append(head);
  const metrics = el("div", "admin-summary compact");
  [
    ["已接入", `${audit.consumed_family_count ?? 0}/${audit.family_count ?? 0}`],
    ["接入率", `${audit.consumption_percent ?? 0}%`],
    ["已启用", `${audit.active_family_count ?? 0}/${audit.family_count ?? 0}`],
    ["启用率", `${audit.active_percent ?? 0}%`],
  ].forEach(([label, value]) => metrics.append(metric(label, value)));
  card.append(metrics);
  const effect = audit.pointer_effect_summary || {};
  if (effect.version) {
    const effectRow = el("div", "training-plan-row");
    const effectHead = el("div", "training-topic-head");
    effectHead.append(el("strong", "", "调参影响总览"));
    effectHead.append(el("span", "small-pill", zhStatus(effect.status || "-")));
    effectRow.append(effectHead);
    effectRow.append(el("span", "", effect.summary || ""));
    const scopes = el("div", "training-arg-list");
    (effect.active_scopes || []).slice(0, 8).forEach((scope) => scopes.append(el("code", "", scope)));
    effectRow.append(scopes);
    card.append(effectRow);
  }
  const grid = el("div", "training-topic-grid");
  (audit.families || []).forEach((family) => {
    const item = el("div", "training-topic-card");
    const row = el("div", "training-topic-head");
    row.append(el("strong", "", family.label || family.family || "-"));
    row.append(el("span", "small-pill", zhStatus(family.runtime_consumer_status || "-")));
    item.append(row);
    item.append(el("span", "", `当前状态：${zhStatus(family.pointer_status || "-")}`));
    const versions = el("div", "training-arg-list");
    versions.append(el("code", "", family.active_policy_version || "baseline"));
    if (family.candidate_policy_version) versions.append(el("code", "", family.candidate_policy_version));
    item.append(versions);
    const effect = family.before_after_effect || {};
    if (effect.version) {
      item.append(el("span", "", `调参影响：${pointerEffectLabel(effect.effect_status)} · 当前 ${effect.active_policy_version || "baseline"}`));
    }
    const scopes = el("div", "training-arg-list");
    (family.effect_scope || []).slice(0, 4).forEach((scope) => scopes.append(el("code", "", scope)));
    if ((family.effect_scope || []).length) item.append(scopes);
    const consumers = el("div", "training-arg-list");
    (family.expected_consumers || []).forEach((consumer) => consumers.append(el("code", "", zhConsumer(consumer))));
    item.append(consumers);
    const counts = el("div", "training-arg-list");
    Object.entries(family.payload_counts || {}).slice(0, 5).forEach(([key, value]) => {
      counts.append(el("code", "", `${key}:${value}`));
    });
    item.append(counts);
    if (family.blocking_gate) item.append(el("p", "", `暂未生效原因：${family.blocking_gate}`));
    grid.append(item);
  });
  card.append(grid);
  if ((audit.next_actions || []).length) {
    const gaps = el("div", "training-plan-gaps");
    audit.next_actions.slice(0, 6).forEach((row) => {
      gaps.append(el("span", "small-pill", `${row.family}: 还需接入系统`));
    });
    card.append(gaps);
  }
  root.append(card);
};

const pointerEffectLabel = (status) => ({
  active_candidate_consumed: "候选已消费",
  baseline_or_blocked: "基线或阻断",
}[status] || status || "-");

const renderTrainingPlan = (root, plan = {}) => {
  if (!plan.version) return;
  const card = el("section", "training-plan-card");
  const head = el("div", "training-task-section-head");
  const title = el("div", "");
  title.append(el("span", "section-kicker", "训练安排"));
  title.append(el("h3", "", "训练计划与去重"));
  head.append(title);
  head.append(el("span", "small-pill", zhStrategy(plan.strategy || "-")));
  card.append(head);
  const metrics = el("div", "admin-summary compact");
  [
    ["训练档位", String((plan.profiles || []).length)],
    ["专题", String((plan.optimization_topics || []).length)],
    ["冷却中", String(plan.dedupe_summary?.cooldown_blocked_count ?? 0)],
    ["合成缺口", String(plan.synthetic_rule_plan?.gap_count ?? 0)],
    ["覆盖状态", zhStatus(plan.synthetic_rule_plan?.coverage_status || "-")],
    ["候选质量", zhStatus(plan.candidate_quality_signal?.status || "-")],
  ].forEach(([label, value]) => metrics.append(metric(label, value)));
  card.append(metrics);
  const quality = plan.candidate_quality_signal || {};
  if (quality.version) {
    const qualityBox = el("div", "training-plan-row training-quality-signal");
    const top = el("div", "training-topic-head");
    top.append(el("strong", "", "候选质量信号"));
    top.append(el("span", "small-pill", zhStatus(quality.status || "-")));
    qualityBox.append(top);
    qualityBox.append(el("span", "", quality.candidate_gate_note || ""));
    const qualityTags = el("div", "training-arg-list");
    qualityTags.append(el("code", "", `合成缺口 ${quality.synthetic_gap_count ?? 0}`));
    qualityTags.append(el("code", "", `推进分 ${Math.round(Number(quality.candidate_promotion_score || 0) * 100)}%`));
    qualityTags.append(el("code", "", zhStatus(quality.promotion_decision || "-")));
    qualityTags.append(el("code", "", `518K ${zhStatus(quality.corpus_training_status || quality.corpus_artifact_status || "-")}`));
    (quality.gate_blockers || []).forEach((gate) => qualityTags.append(el("code", "", zhGateBlocker(gate))));
    (quality.recommended_tasks || []).slice(0, 4).forEach((task) => qualityTags.append(el("code", "", trainingDisplayFromKey(task, task))));
    qualityBox.append(qualityTags);
    const scoreTags = el("div", "training-arg-list");
    Object.entries(quality.quality_scores || {}).forEach(([key, value]) => {
      scoreTags.append(el("code", "", `${zhQualityScore(key)} ${Math.round(Number(value || 0) * 100)}%`));
    });
    qualityBox.append(scoreTags);
    card.append(qualityBox);
  }
  const structureDistribution = plan.structure_dynamics_path_distribution || {};
  if (structureDistribution.version) {
    const structureBox = el("div", "training-plan-row structure-dynamics-coverage");
    const top = el("div", "training-topic-head");
    top.append(el("strong", "", "结构动态覆盖"));
    top.append(el("span", "small-pill", zhStatus(structureDistribution.status || "-")));
    structureBox.append(top);
    structureBox.append(el("span", "", "做功链样本、反例边界和岁运阻断已进入同一套结构动态验证。"));
    const tags = el("div", "training-arg-list");
    tags.append(el("code", "", `样本 ${structureDistribution.case_count || 0}`));
    tags.append(el("code", "", `通过 ${Math.round(Number(structureDistribution.pass_rate || 0) * 100)}%`));
    tags.append(el("code", "", `反例 ${zhStatus(structureDistribution.counterexample_coverage?.status || "-")}`));
    tags.append(el("code", "", `岁运阻断 ${zhStatus(structureDistribution.time_blocker_coverage?.status || "-")}`));
    (structureDistribution.counterexample_coverage?.covered_labels || []).forEach((label) => tags.append(el("code", "", label)));
    (structureDistribution.time_blocker_coverage?.covered_types || []).forEach((type) => tags.append(el("code", "", zhRelationType(type))));
    structureBox.append(tags);
    const labelTags = el("div", "training-arg-list");
    (structureDistribution.label_distribution || []).slice(0, 6).forEach((row) => {
      labelTags.append(el("code", "", `${row.key} ${row.count}`));
    });
    structureBox.append(labelTags);
    card.append(structureBox);
  }
  const structureKnowledge = plan.structure_dynamics_knowledge_coverage || {};
  if (structureKnowledge.version) {
    const knowledgeBox = el("div", "training-plan-row structure-knowledge-coverage");
    const top = el("div", "training-topic-head");
    top.append(el("strong", "", "结构知识覆盖"));
    top.append(el("span", "small-pill", structureKnowledgeCoverageLabel(structureKnowledge.status || "-")));
    knowledgeBox.append(top);
    knowledgeBox.append(el("span", "", "当前做功链名称必须能回到知识机制、完整知识单元、八字目录和规则目录，避免算法套固定套路。"));
    const tags = el("div", "training-arg-list");
    tags.append(el("code", "", `观察标签 ${structureKnowledge.observed_label_count || 0}`));
    tags.append(el("code", "", `机制单元 ${structureKnowledge.mechanism_unit_count || 0}`));
    tags.append(el("code", "", `知识单元 ${structureKnowledge.full_knowledge_unit_count || 0}`));
    tags.append(el("code", "", `已覆盖 ${structureKnowledge.covered_count || 0}`));
    tags.append(el("code", "", `缺口 ${structureKnowledge.unsupported_count || 0}`));
    (structureKnowledge.unsupported_labels || []).forEach((label) => tags.append(el("code", "", `待补 ${label}`)));
    knowledgeBox.append(tags);
    const rowTags = el("div", "training-arg-list");
    (structureKnowledge.coverage_rows || []).slice(0, 8).forEach((row) => {
      const sourceCount = (row.support_sources || []).length;
      rowTags.append(el("code", "", `${row.label} ${sourceCount}源`));
    });
    knowledgeBox.append(rowTags);
    card.append(knowledgeBox);
  }
  const structureCorpus = plan.structure_dynamics_corpus_distribution || {};
  if (structureCorpus.version) {
    const corpusBox = el("div", "training-plan-row structure-corpus-distribution");
    const top = el("div", "training-topic-head");
    top.append(el("strong", "", "结构语料回放"));
    top.append(el("span", "small-pill", zhStatus(structureCorpus.status || "-")));
    corpusBox.append(top);
    corpusBox.append(el("span", "", "把 518K 八字空间按分片回放，观察真实做功链分布和知识缺口，不把语料当单盘结论。"));
    const tags = el("div", "training-arg-list");
    tags.append(el("code", "", `样本 ${structureCorpus.limit || structureCorpus.case_count || 0}`));
    tags.append(el("code", "", `覆盖 ${Math.round(Number(structureCorpus.coverage_ratio || 0) * 10000) / 100}%`));
    tags.append(el("code", "", `知识缺口 ${structureCorpus.unsupported_label_count || 0}`));
    tags.append(el("code", "", `失败 ${structureCorpus.failure_count || 0}`));
    (structureCorpus.unsupported_labels || []).forEach((label) => tags.append(el("code", "", `待补 ${label}`)));
    corpusBox.append(tags);
    const labelTags = el("div", "training-arg-list");
    (structureCorpus.label_distribution || []).slice(0, 8).forEach((row) => {
      labelTags.append(el("code", "", `${row.key} ${row.count}`));
    });
    corpusBox.append(labelTags);
    card.append(corpusBox);
  }
  const legacySwitch = plan.structure_dynamics_legacy_v2_switch || {};
  if (legacySwitch.version) {
    const switchBox = el("div", "training-plan-row structure-dynamics-switch");
    const top = el("div", "training-topic-head");
    top.append(el("strong", "", "结构动态切换报告"));
    top.append(el("span", "small-pill", structureSwitchStatusLabel(legacySwitch.status || "-")));
    switchBox.append(top);
    switchBox.append(el("span", "", "结构动态主读已切到最新做功链；旧链只保留为排查用，不参与中枢和页面判断。"));
    const tags = el("div", "training-arg-list");
    tags.append(el("code", "", `样本 ${legacySwitch.case_count || 0}`));
    tags.append(el("code", "", `可解释 ${legacySwitch.explainable_count || 0}`));
    tags.append(el("code", "", `未解释 ${legacySwitch.unexplained_conflict_count || 0}`));
    tags.append(el("code", "", `主读 ${runtimeFieldLabel(legacySwitch.switch_policy?.recommended_runtime_field || "-")}`));
    switchBox.append(tags);
    card.append(switchBox);
  }
  const tuning = plan.central_brain_tuning_package || {};
  if (tuning.version) {
    const tuningBox = el("div", "training-plan-row central-tuning-package");
    const top = el("div", "training-topic-head");
    top.append(el("strong", "", "中枢调参决策包"));
    top.append(el("span", "small-pill", centralTuningDecisionLabel(tuning.decision || tuning.status)));
    tuningBox.append(top);
    tuningBox.append(el("span", "", `合成验证、518K 回放和八字上下文偏离已合并为同一个中枢调参决策。`));
    const tuningTags = el("div", "training-arg-list");
    tuningTags.append(el("code", "", `推进分 ${Math.round(Number(tuning.candidate_promotion_score || 0) * 100)}%`));
    tuningTags.append(el("code", "", `八字偏离 ${Math.round(Number(tuning.context_drift_score || 0) * 100)}%`));
    tuningTags.append(el("code", "", `参数组 ${tuning.parameter_update_count || 0}`));
    (tuning.runtime_pointer_targets || []).slice(0, 6).forEach((target) => tuningTags.append(el("code", "", zhPointerTarget(target))));
    tuningBox.append(tuningTags);
    const apply = tuning.apply_report || {};
    if (apply.version) {
      const applyLine = el("div", "training-arg-list");
      applyLine.append(el("code", "", `可生效 ${apply.ready_pointer_count || 0}/${apply.pointer_update_count || 0}`));
      applyLine.append(el("code", "", `阻断 ${apply.blocked_pointer_count || 0}`));
      (apply.pointer_updates || []).slice(0, 7).forEach((row) => {
        applyLine.append(el("code", "", `${zhPointerTarget(row.runtime_pointer_target)} ${centralApplyStatusLabel(row.status)}`));
      });
      tuningBox.append(applyLine);
    }
    const updates = el("div", "training-topic-grid");
    (tuning.parameter_updates || []).slice(0, 4).forEach((row) => {
      const item = el("div", "training-topic-card compact");
      const updateHead = el("div", "training-topic-head");
      updateHead.append(el("strong", "", row.label || row.topic_key || "-"));
      updateHead.append(el("span", "small-pill", centralTuningStatusLabel(row.status)));
      item.append(updateHead);
      item.append(el("span", "", `适配 ${Math.round(Number(row.topic_fit_score || 0) * 100)}% · ${centralTuningHintLabel(row.activation_hint)}`));
      const targets = el("div", "training-arg-list");
      (row.parameter_targets || []).slice(0, 4).forEach((target) => targets.append(el("code", "", target)));
      item.append(targets);
      updates.append(item);
    });
    tuningBox.append(updates);
    card.append(tuningBox);
  }
  const cadence = el("div", "training-plan-rows");
  (plan.recommended_cadence || []).forEach((row) => {
    const item = el("div", "training-plan-row");
    item.append(el("strong", "", row.label || row.cadence_key || "-"));
    item.append(el("span", "", row.trigger || ""));
    const tasks = el("div", "training-arg-list");
    (row.tasks || []).forEach((task) => tasks.append(el("code", "", task)));
    item.append(tasks);
    cadence.append(item);
  });
  card.append(cadence);
  const topics = el("div", "training-topic-grid");
  (plan.optimization_topics || []).forEach((topic) => {
    const item = el("div", "training-topic-card");
    const row = el("div", "training-topic-head");
    row.append(el("strong", "", topic.label || topic.topic_key || "-"));
    row.append(el("span", "small-pill", zhWriter(topic.optimizer_writer_status || "-")));
    item.append(row);
    const roles = el("div", "training-plan-gaps");
    (topic.roles || []).forEach((role) => roles.append(el("span", "small-pill", zhRole(role))));
    item.append(roles);
    item.append(el("span", "", `训练方式：${zhStrategy(topic.model_pattern || "")}`));
    const atoms = el("div", "training-arg-list");
    (topic.atomic_trainings || []).forEach((task) => atoms.append(el("code", "", task)));
    item.append(atoms);
    const params = el("div", "training-arg-list");
    (topic.parameter_targets || []).slice(0, 5).forEach((target) => params.append(el("code", "", zhParamTarget(target))));
    item.append(params);
    (topic.training_groups || []).slice(0, 2).forEach((group) => {
      const groupRow = el("div", "training-plan-row compact");
      groupRow.append(el("strong", "", group.label || group.group_key || "-"));
      groupRow.append(el("span", "", `原子训练：${(group.atomic_trainings || []).map((task) => trainingDisplayFromKey(task, task)).join("、")}`));
      const groupTargets = el("div", "training-arg-list");
      (group.runtime_pointer_targets || []).forEach((target) => groupTargets.append(el("code", "", zhPointerTarget(target))));
      groupRow.append(groupTargets);
      item.append(groupRow);
    });
    item.append(el("p", "", topic.current_gap || ""));
    topics.append(item);
  });
  if ((plan.optimization_topics || []).length) {
    card.append(topics);
  }
  const nextCases = plan.synthetic_rule_plan?.next_cases || [];
  if (nextCases.length) {
    const gaps = el("div", "training-plan-gaps");
    nextCases.slice(0, 6).forEach((row) => {
      gaps.append(el("span", "small-pill", `${row.gap_type}:${row.key}`));
    });
    card.append(gaps);
  }
  root.append(card);
};

const zhGateBlocker = (gate) => ({
  synthetic_coverage_needs_expansion: "合成覆盖不足",
  corpus_518k_replay_artifacts_not_ready: "518K 回放不足",
  bazi_context_alignment_drift: "八字上下文偏离",
}[gate] || gate || "-");

const zhQualityScore = (key) => ({
  synthetic_pass_rate: "合成通过",
  structure_dynamic_path_consistency: "结构链一致",
  structure_semantic_candidate_precision: "结构命中",
  rule_false_positive_rate: "规则误触",
  portrait_drift_score: "画像漂移",
  question_focus_score: "问题聚焦",
  corpus_distribution_shift: "分布偏移",
  similar_case_stability: "相似稳定",
  bazi_context_drift_score: "八字偏离",
}[key] || key || "-");

const zhRelationType = (type) => ({
  clash: "冲",
  break: "破",
  punishment: "刑",
  harm: "害",
  harmony: "合",
  three_harmony: "三合",
  three_meeting: "三会",
}[type] || type || "-");

const structureSwitchStatusLabel = (status) => ({
  switch_ready_primary: "v2 已主读",
  switch_ready_shadow: "待切主读",
  needs_legacy_compat: "保留兼容",
  unavailable: "暂不可用",
}[status] || status || "-");

const structureKnowledgeCoverageLabel = (status) => ({
  covered_current_scope: "当前范围已覆盖",
  needs_knowledge_expansion: "知识库待补",
  unavailable: "暂不可用",
}[status] || zhStatus(status) || "-");

const centralTuningDecisionLabel = (decision) => ({
  direct_apply_candidates: "可直接生效",
  continue_training: "继续训练",
  ready_to_apply: "可直接生效",
  needs_more_training: "继续训练",
}[decision] || decision || "-");

const centralTuningStatusLabel = (status) => ({
  candidate_ready: "候选可用",
  collect_more_signal: "补信号",
}[status] || status || "-");

const centralTuningHintLabel = (hint) => ({
  auto_apply_pointer: "训练后写入指针",
  run_recommended_replay: "先跑推荐回放",
}[hint] || hint || "-");

const centralApplyStatusLabel = (status) => ({
  ready_to_apply: "可生效",
  blocked: "阻断",
  applied: "已生效",
  partial_applied: "部分生效",
}[status] || status || "-");

const renderTrainingRecommendation = (root, recommendation, activeTask = {}) => {
  if (!recommendation.task_key && !activeTask.task_id) return;
  const card = el("section", "training-next-card");
  const title = recommendation.blocked_by_active_task ? "当前任务" : "推荐下一步";
  card.append(el("span", "section-kicker", title));
  card.append(el("strong", "", trainingDisplayLabel(recommendation.task_key ? recommendation : activeTask)));
  card.append(el("p", "", recommendation.reason || recommendation.when_to_run || "按当前训练状态推荐。"));
  const meta = el("div", "training-task-foot");
  meta.append(el("span", "small-pill", recommendation.risk_level ? `风险 ${zhRisk(recommendation.risk_level)}` : "运行中"));
  meta.append(el("span", "small-pill", recommendation.last_status ? `上次 ${zhStatus(recommendation.last_status)}` : "无历史"));
  if (recommendation.section) meta.append(el("span", "small-pill", recommendation.section));
  card.append(meta);
  root.append(card);
};

const renderTrainingTaskSections = (root, tasks, sections, latestByKey, activeTask = {}) => {
  const sectionRows = (sections || []).length
    ? sections
    : Array.from(
        new Map(
          tasks.map((task) => [
            task.section_key || task.category || "other",
            {
              section_key: task.section_key || task.category || "other",
              label: task.section_label || task.category || "其他",
              order: Number(task.section_order || 100),
            },
          ]),
        ).values(),
      ).sort((a, b) => Number(a.order || 0) - Number(b.order || 0));
  sectionRows.forEach((section) => {
    const sectionTasks = tasks.filter((task) => (task.section_key || task.category || "other") === section.section_key);
    if (!sectionTasks.length) return;
    const block = el("section", "training-task-section");
    const head = el("div", "training-task-section-head");
    head.append(el("h3", "", section.label || section.section_key || "训练任务"));
    head.append(el("span", "small-pill", `${sectionTasks.length} 项`));
    block.append(head);
    const grid = el("div", "training-task-section-grid");
    sectionTasks.forEach((task) => grid.append(trainingTaskCard(task, latestByKey.get(task.task_key) || {}, activeTask)));
    block.append(grid);
    root.append(block);
  });
};

const renderTrainingTaskLoadError = (error) => {
  setText("#adminStatus", `训练任务加载失败：${error.message || "接口暂不可用"}`);
  const summary = document.querySelector("#trainingTaskSummary");
  const root = document.querySelector("#trainingTaskRegistry");
  const history = document.querySelector("#trainingTaskHistory");
  if (summary) {
    clear(summary);
    [
      ["状态", "暂不可用"],
      ["原因", trainingTaskErrorHint(error)],
    ].forEach(([label, value]) => summary.append(metric(label, value)));
  }
  if (root) {
    clear(root);
    const note = el("div", "empty-note training-load-error", trainingTaskErrorHint(error));
    root.append(note);
  }
  if (history) {
    clear(history);
    history.append(el("div", "empty-note", adminText().no_data));
  }
  const activations = document.querySelector("#trainingActivationHistory");
  if (activations) {
    clear(activations);
    activations.append(el("div", "empty-note", adminText().no_data));
  }
  renderTrainingTaskStatus({});
};

const trainingTaskErrorHint = (error) => {
  const message = String(error?.message || "");
  if (message.startsWith("404")) return "后台尚未加载训练任务 API；需要部署并重启 V20 后端服务。";
  if (message.startsWith("401") || message.startsWith("403")) return "需要先用 admin 账号登录后才能查看和启动训练任务。";
  if (message.includes("duplicate_success_cooldown")) return "这个任务刚成功跑过，系统暂时阻止重复训练。";
  if (message.includes("active_task_running")) return "已有后台训练在运行，请先等待完成或暂停。";
  return message || "训练任务接口暂不可用。";
};

const trainingTaskCard = (task, latest = {}, activeTask = {}) => {
  const card = el("div", task.is_recommended_next ? "training-task-card recommended" : "training-task-card");
  const head = el("div", "training-task-head");
  const title = el("div", "");
  title.append(el("strong", "", trainingDisplayLabel(task)));
  title.append(el("span", "", `${task.section_label || task.category || "-"} · ${zhHeavy(task.heavy_level)} · ${zhDuration(task.estimated_duration)}`));
  const controls = el("div", "training-task-actions");
  const isStarting = startingTrainingTaskKey === task.task_key;
  const startButton = el("button", "mini-action secondary", isStarting ? "提交中" : "开始");
  startButton.type = "button";
  const duplicateBlocked = task.dedupe_policy?.duplicate_blocked === true;
  startButton.disabled = isStarting || Boolean(activeTask.task_id) || duplicateBlocked || task.start_allowed === false;
  startButton.title = activeTask.task_id
    ? "已有后台训练在运行；先等待完成或暂停。"
    : duplicateBlocked
      ? task.dedupe_policy?.reason || "冷却期内避免重复训练。"
      : "";
  startButton.dataset.taskKey = task.task_key || "";
  startButton.addEventListener("click", () => startTrainingTask(task.task_key).catch((error) => setText("#adminStatus", `启动失败：${error.message}`)));
  const pauseButton = el("button", "mini-action secondary", "暂停");
  pauseButton.type = "button";
  pauseButton.disabled = !latest.task_id || !["queued", "running"].includes(latest.status);
  pauseButton.addEventListener("click", () => pauseTrainingTask(latest.task_id).catch((error) => setText("#adminStatus", error.message)));
  controls.append(startButton);
  controls.append(pauseButton);
  head.append(title);
  head.append(controls);
  card.append(head);
  card.append(el("p", "", task.description || ""));
  if (task.when_to_run) {
    const when = el("p", "training-when", `什么时候跑：${task.when_to_run}`);
    card.append(when);
  }
  const script = el("div", "training-script-path");
  script.append(el("span", "", "后台脚本"));
  script.append(el("code", "", zhScript(task.script_path)));
  card.append(script);
  const args = el("div", "training-args");
  args.append(el("span", "", "参数"));
  const argList = el("div", "training-arg-list");
  (task.default_args || []).forEach((arg) => argList.append(el("code", "", arg)));
  if (!(task.default_args || []).length) argList.append(el("em", "", "无默认参数"));
  args.append(argList);
  card.append(args);
  const progress = Math.max(0, Math.min(100, Number(latest.progress_percent || 0)));
  const miniProgress = el("div", "training-progress mini");
  const miniBar = el("div", "training-progress-bar");
  miniBar.style.width = `${progress}%`;
  miniProgress.append(miniBar);
  card.append(miniProgress);
  const foot = el("div", "training-task-foot");
  foot.append(el("span", "small-pill", trainingEffectLabel(task)));
  foot.append(el("span", "small-pill", "后台独立运行"));
  foot.append(el("span", "small-pill", `风险 ${zhRisk(task.risk_level || "normal")}`));
  foot.append(el("span", "small-pill", `冷却 ${task.dedupe_policy?.cooldown_hours ?? "-"} 小时`));
  foot.append(el("span", "small-pill", latest.status ? `${zhStatus(latest.status)} ${progress}%` : "未运行"));
  if (duplicateBlocked) foot.append(el("span", "small-pill", "避免重复"));
  if (task.is_recommended_next) foot.append(el("span", "small-pill", "推荐"));
  card.append(foot);
  if (task.primary_brain_node || (task.brain_nodes || []).length || (task.runtime_pointer_targets || []).length) {
    const brain = el("div", "training-arg-list training-brain-targets");
    if (task.primary_brain_node) brain.append(el("code", "", `主节点：${zhBrainNode(task.primary_brain_node)}`));
    (task.brain_nodes || []).slice(0, 3).forEach((node) => brain.append(el("code", "", zhBrainNode(node))));
    (task.runtime_pointer_targets || []).slice(0, 3).forEach((target) => brain.append(el("code", "", zhPointerTarget(target))));
    card.append(brain);
  }
  if (activeTask.task_id || duplicateBlocked || task.start_allowed === false) {
    const reason = activeTask.task_id
      ? "已有后台训练正在运行。"
      : duplicateBlocked
        ? "这个任务刚成功跑过，冷却期内先不重复跑。"
        : "当前条件不允许启动。";
    card.append(el("p", "training-when", reason));
  }
  return card;
};

const startTrainingTask = async (taskKey) => {
  if (!taskKey) return;
  startingTrainingTaskKey = taskKey;
  setText("#adminStatus", "已提交后台训练，正在创建独立脚本进程...");
  await renderTrainingTasks();
  try {
    const result = await requestJson("/api/v20/admin/training/tasks/start", {
      method: "POST",
      body: JSON.stringify({ task_key: taskKey }),
    });
    activeTrainingTaskId = result.task_id || "";
    latestTrainingTask = result;
    setText("#adminStatus", `后台训练已启动：${trainingDisplayLabel(result)}`);
    renderTrainingTaskStatus(result);
    await renderTrainingTasks();
    scheduleTrainingTaskPoll();
  } finally {
    startingTrainingTaskKey = "";
  }
};

const trainingEffectLabel = (task = {}) => {
  const key = task.task_key || "";
  const category = task.category || "";
  if (["synthetic_case_suite", "extract_rules_llm_draft"].includes(key)) return "生成训练信号";
  if (["fast", "training", "question", "role", "rule", "portrait", "knowledge", "corpus"].includes(category)) {
    return "训练后自动调参";
  }
  if (task.writes_artifact) return "生成训练结果";
  return "辅助训练信号";
};

const pauseTrainingTask = async (taskId = activeTrainingTaskId) => {
  if (!taskId) return;
  setText("#adminStatus", "正在暂停后台训练...");
  const result = await requestJson(`/api/v20/admin/training/tasks/${encodeURIComponent(taskId)}/pause`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  latestTrainingTask = result;
  setText("#adminStatus", `后台训练已${zhStatus(result.status)}`);
  renderTrainingTaskStatus(result);
  if (trainingTaskPollTimer) {
    window.clearInterval(trainingTaskPollTimer);
    trainingTaskPollTimer = null;
  }
  await renderTrainingTasks();
};

const scheduleTrainingTaskPoll = () => {
  if (trainingTaskPollTimer) window.clearInterval(trainingTaskPollTimer);
  trainingTaskPollTimer = window.setInterval(refreshActiveTrainingTask, 2200);
};

const refreshActiveTrainingTask = async () => {
  if (!activeTrainingTaskId) return;
  const result = await requestJson(`/api/v20/admin/training/tasks/${encodeURIComponent(activeTrainingTaskId)}`);
  latestTrainingTask = result;
  renderTrainingTaskStatus(result);
  if (!["queued", "running"].includes(result.status)) {
    window.clearInterval(trainingTaskPollTimer);
    trainingTaskPollTimer = null;
    await renderTrainingTasks();
  }
};

const renderTrainingTaskStatus = (task) => {
  const status = task.status || "idle";
  const percent = Math.max(0, Math.min(100, Number(task.progress_percent || 0)));
  setText("#trainingTaskTitle", task.task_id ? trainingDisplayLabel(task) : "等待任务。");
  setText("#trainingTaskStatus", zhStatus(status));
  const pauseButton = document.querySelector("#pauseTrainingTask");
  if (pauseButton) {
    pauseButton.disabled = !task.task_id || !["queued", "running"].includes(status);
  }
  const bar = document.querySelector("#trainingProgressBar");
  if (bar) bar.style.width = `${percent}%`;
  const meta = document.querySelector("#trainingTaskMeta");
  clear(meta);
  [
    ["任务", task.task_key || "-"],
    ["阶段", zhStatus(task.current_stage || "-")],
    ["进度", `${percent}%`],
    ["后台脚本", task.command ? zhScript((task.command || [])[1]) : "-"],
    ["参数", task.command ? (task.command || []).slice(2).join(" ") || "无" : "-"],
    ["进程 PID", String(task.pid || "-")],
    ["更新时间", task.updated_at ? String(task.updated_at).slice(0, 19) : "-"],
    ["完成时间", task.finished_at ? String(task.finished_at).slice(0, 19) : "-"],
  ].forEach(([label, value]) => {
    const item = el("div", "kv-row");
    item.append(el("span", "", label));
    item.append(el("strong", "", value));
    meta.append(item);
  });
  renderTrainingResultSummary(task);
  setText("#trainingTaskLog", (task.log_tail || []).join("\n") || task.error || "暂无后台训练日志。");
};

const renderTrainingResultSummary = (task = {}) => {
  const root = document.querySelector("#trainingResultSummary");
  if (!root) return;
  clear(root);
  const summary = task.result_summary || {};
  const status = summary.status || "not_found";
  if (status === "not_found" || status === "idle") {
    root.append(el("div", "empty-note", "暂无训练结果。"));
    return;
  }
  const head = el("div", "training-result-head");
  head.append(el("strong", "", summary.outcome || status));
  head.append(el("span", "small-pill", `风险 ${summary.risk_level || "-"}`));
  root.append(head);
  const rows = [
    ["建议", summary.recommended_action || "-"],
    ["结果状态", zhStatus(summary.contract_status || "-")],
    ["执行脚本", zhScript(summary.contract_script || "-")],
    ["耗时", summary.elapsed_seconds ? `${summary.elapsed_seconds}s` : "-"],
    ["退出码", summary.exit_code === "" || summary.exit_code === undefined ? "-" : String(summary.exit_code)],
  ];
  rows.forEach(([label, value]) => {
    const row = el("div", "kv-row");
    row.append(el("span", "", label));
    row.append(el("strong", "", value));
    root.append(row);
  });
  const gate = summary.machine_gate || {};
  if (gate.status) {
    const gateRow = el("div", "training-optimization-gate");
    gateRow.append(el("strong", "", `机器调参：${optimizationGateLabel(gate.status)}`));
    gateRow.append(el("span", "", gate.reason || "-"));
    root.append(gateRow);
  }
  const contextQuality = summary.context_quality_signal || {};
  if (contextQuality.version) {
    const contextRow = el("div", "training-publish-preview");
    contextRow.append(el("strong", "", `八字上下文：${trainingContextQualityLabel(contextQuality.status)}`));
    contextRow.append(el("span", "", `偏离 ${Math.round(Number(contextQuality.bazi_context_drift_score || 0) * 100)}%`));
    if (contextQuality.context_id) contextRow.append(el("span", "", `上下文 ${contextQuality.context_id}`));
    if (contextQuality.module_count) contextRow.append(el("span", "", `模块 ${contextQuality.aligned_count || 0}/${contextQuality.module_count}`));
    root.append(contextRow);
  }
  const preview = summary.publish_preview || {};
  if (preview.status) {
    const previewRow = el("div", "training-publish-preview");
    previewRow.append(el("strong", "", `自动调参：${publishPreviewLabel(preview.status)}`));
    previewRow.append(el("span", "", preview.reason || "-"));
    if (preview.activation_family) {
      previewRow.append(el("span", "", `优化方向：${activationFamilyLabel(preview.activation_family)}`));
    }
    if (preview.auto_optimization?.enabled) {
      previewRow.append(el("span", "", `自动调参：${preview.auto_optimization.auto_apply_candidate ? "训练完成后直接写入" : "还缺调参器"}`));
      if (preview.auto_optimization.optimizer_writer) {
        previewRow.append(el("span", "", `调参器：${preview.auto_optimization.optimizer_writer}`));
      }
    }
    (preview.impacted_targets || []).slice(0, 3).forEach((target) => {
      previewRow.append(el("span", "", `${target.key || target.target_type}: ${target.value || "-"}`));
    });
    previewRow.append(trainingActivationActions(task.task_id || "", preview));
    root.append(previewRow);
  }
  renderTrainingWriterResults(root, task.auto_parameter_apply || {});
  Object.entries(summary.key_counts || {}).slice(0, 6).forEach(([key, value]) => {
    const row = el("div", "kv-row");
    row.append(el("span", "", key));
    row.append(el("strong", "", String(value)));
    root.append(row);
  });
  if (summary.error) {
    root.append(el("p", "training-result-error", summary.error));
  }
};

const trainingContextQualityLabel = (status) => ({
  aligned: "已贴合当前命盘",
  drifted: "已偏离当前命盘",
  not_declared: "训练未声明",
  observe_only: "只读任务",
}[status] || status || "-");

const renderTrainingWriterResults = (root, autoApply = {}) => {
  const domainResult = autoApply.activation_plan?.domain_activation?.domain_result || {};
  const writers = domainResult.writer_results || [];
  if (!writers.length) return;
  const box = el("div", "training-writer-results");
  const head = el("div", "training-writer-head");
  head.append(el("strong", "", "自动调参写入结果"));
  head.append(el("span", "small-pill", `${domainResult.activated_writer_count || 0}/${domainResult.writer_count || writers.length} 已生效`));
  box.append(head);
  writers.forEach((writer) => {
    const row = el("div", "training-writer-row");
    const left = el("div", "");
    left.append(el("strong", "", writerLabel(writer.writer_key || "")));
    left.append(el("span", "", writer.runtime_mutation ? "已写入 active pointer" : `未生效：${writer.blocking_gate || writer.status || "-"}`));
    row.append(left);
    row.append(el("span", writer.runtime_mutation ? "small-pill ok" : "small-pill warn", zhStatus(writer.status || "-")));
    box.append(row);
  });
  root.append(box);
};

const writerLabel = (key) => ({
  orchestrator_policy: "中枢策略",
  question_policy: "智能问答",
  role_view_policy: "角色体验",
  rule_policy: "规则参数",
  portrait_policy: "画像参数",
  knowledge_policy: "知识映射",
  corpus_policy: "语料特征",
}[key] || key || "-");

const trainingActivationActions = (taskId, preview = {}) => {
  const row = el("div", "training-activation-actions");
  const applyButton = el("button", "mini-action", "重新尝试生效");
  applyButton.type = "button";
  applyButton.disabled = !taskId || !canApplyTrainingParameters(preview);
  applyButton.title = canApplyTrainingParameters(preview)
    ? "训练成功后会自动走机器验证；这里可手动重新尝试生效。"
    : "只有已有自动调参器且机器验证通过后才可直接生效。";
  applyButton.addEventListener("click", () => recordTrainingParameterApply(taskId).catch((error) => setText("#adminStatus", error.message)));
  row.append(applyButton);
  return row;
};

const canApplyTrainingParameters = (preview = {}) => (
  preview.eligible_for_publish === true && preview.auto_optimization?.parameter_apply_supported === true
);

const recordTrainingParameterApply = async (taskId) => {
  const result = await requestJson(`/api/v20/admin/training/tasks/${encodeURIComponent(taskId)}/activate`, {
    method: "POST",
    body: JSON.stringify({
      dry_run: false,
      confirm_token: "ACTIVATE_TRAINING_RESULT",
      reason: "admin parameter apply from training result center",
    }),
  });
  const activation = result.activation_plan?.domain_activation || {};
  setText("#adminStatus", `调参结果：${zhStatus(activation.status || result.status)}`);
  await refreshActiveTrainingTask();
};

const optimizationGateLabel = (status) => ({
  machine_ready: "可优化",
  reviewable: "可优化",
  observe_only: "仅验证",
  blocked: "阻断",
  paused: "已暂停",
  pending: "等待完成",
}[status] || zhStatus(status) || "-");

const publishPreviewLabel = (status) => ({
  ready: "可直接优化",
  optimizer_missing: "缺优化器",
  awaiting_acceptance: "等待优化",
  blocked: "阻断",
  pending: "等待完成",
}[status] || zhStatus(status) || "-");

const activationFamilyLabel = (family) => ({
  question_policy: "问题策略",
  portrait_policy: "画像策略",
  rule_iteration: "规则迭代",
  knowledge_review: "知识策略",
  corpus_precompute: "语料预计算",
  training_bundle: "训练总包",
  manual_review: "未接优化器",
}[family] || family || "-");

const runtimeFieldLabel = (field) => ({
  primary_dynamic_chain: "新结构主链",
  dominant_chain_v2: "图算法做功链",
  legacy_dynamic_chain: "旧链排查字段",
  primary_dynamic_chain_with_legacy_debug: "新主链+旧链排查",
}[field] || field || "-");

const renderTrainingHistory = (tasks) => {
  const root = document.querySelector("#trainingTaskHistory");
  clear(root);
  tasks.slice(0, 12).forEach((task) => {
    const item = el("button", "kv-row training-history-row");
    item.type = "button";
    item.append(el("span", "", `${trainingDisplayLabel(task)} · ${zhStatus(task.status || "-")}`));
    item.append(el("strong", "", `${task.progress_percent ?? 0}%`));
    item.addEventListener("click", () => {
      activeTrainingTaskId = task.task_id || "";
      renderTrainingTaskStatus(task);
      if (["queued", "running"].includes(task.status)) scheduleTrainingTaskPoll();
    });
    root.append(item);
  });
  if (!tasks.length) {
    root.append(el("div", "empty-note", adminText().no_data));
  }
};

const renderTrainingActivationHistory = (rows) => {
  const root = document.querySelector("#trainingActivationHistory");
  if (!root) return;
  clear(root);
  rows.slice(0, 10).forEach((row) => {
    const item = el("div", "kv-row training-history-row");
    const family = activationFamilyLabel(row.activation_family || "");
    const status = row.domain_activation?.status || row.blocking_gate || "ready";
    item.append(el("span", "", `${trainingDisplayLabel(row)} · ${family} · ${zhStatus(status)}`));
    item.append(el("strong", "", row.created_at ? String(row.created_at).slice(0, 19) : "-"));
    root.append(item);
  });
  if (!rows.length) {
    root.append(el("div", "empty-note", adminText().no_data));
  }
};

const clearRedisCache = async () => {
  const result = await requestJson("/api/v20/redis/cache-clear", {
    method: "POST",
    body: JSON.stringify({}),
  });
  setText("#adminStatus", `缓存已清理 ${result.deleted_count || 0} 条`);
  await renderRedis();
};

const saveDbConfig = async () => {
  const payload = readForm("#dbConfigForm");
  const result = await requestJson("/api/v20/admin/db/config", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  scrubSecrets("#dbConfigForm");
  setText("#adminStatus", `数据库配置：${zhStatus(result.status)}`);
  await renderDb();
};

const saveLlmConfig = async () => {
  const payload = readForm("#llmConfigForm");
  const result = await requestJson("/api/v20/admin/llm/config", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  scrubSecrets("#llmConfigForm");
  setText("#adminStatus", `LLM 配置：${zhStatus(result.status)}`);
  await renderLlm(false);
};

const testLlm = async () => {
  const prompt = document.querySelector("#llmTestPrompt")?.value || "";
  setText("#llmTestResult", "测试中...");
  const result = await requestJson("/api/v20/admin/llm/test", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
  setText("#adminStatus", `LLM 测试：${zhStatus(result.status)}`);
  setText(
    "#llmTestResult",
    [
      `status: ${result.status}`,
      `model: ${result.model || "-"}`,
      `duration: ${result.duration_ms ?? "-"}ms`,
      result.sample ? `sample: ${result.sample}` : `failure: ${result.failure || "-"}`,
    ].join("\n"),
  );
};

const metric = (label, value) => {
  const node = el("div", "metric-tile");
  node.append(el("span", "", label));
  node.append(el("strong", "", value));
  return node;
};

const renderTags = (selector, tags) => {
  const root = document.querySelector(selector);
  clear(root);
  if (!tags.length) {
    root.append(el("div", "empty-note", adminText().no_data));
    return;
  }
  tags.slice(0, 24).forEach((tag) => root.append(el("span", "tag", tag)));
};

const renderModelOptions = (models, currentModel) => {
  const select = document.querySelector("#llmModelSelect");
  if (!select) return;
  clear(select);
  select.append(new Option(models.length ? "选择模型" : "暂无模型", ""));
  models.slice(0, 80).forEach((model) => {
    const option = new Option(model, model);
    option.selected = model === currentModel;
    select.append(option);
  });
};

const fillForm = (selector, values) => {
  const form = document.querySelector(selector);
  if (!form) return;
  Array.from(form.elements).forEach((field) => {
    if (!field.name || field.type === "password") return;
    const value = values[field.name];
    if (field.type === "checkbox") {
      field.checked = value === true || value === "1" || value === "true";
      return;
    }
    if (value !== undefined && value !== null) field.value = String(value);
  });
};

const readForm = (selector) => {
  const form = document.querySelector(selector);
  const payload = {};
  if (!form) return payload;
  Array.from(form.elements).forEach((field) => {
    if (!field.name) return;
    if (field.type === "checkbox") {
      payload[field.name] = field.checked;
      return;
    }
    const value = String(field.value || "").trim();
    if (!value && field.type === "password") return;
    if (!value) return;
    payload[field.name] = field.type === "number" ? Number(value) : value;
  });
  return payload;
};

const scrubSecrets = (selector) => {
  const form = document.querySelector(selector);
  if (!form) return;
  form.querySelectorAll('input[type="password"]').forEach((field) => {
    field.value = "";
  });
};

const refreshAll = async () => {
  const jobs = await Promise.allSettled([
    renderDb(),
    renderLlm(false),
    renderRedis(),
    renderTrainingTasks(),
  ]);
  const failed = jobs.find((row) => row.status === "rejected");
  try {
    if (failed) throw failed.reason;
    setText("#adminStatus", "正常");
  } catch (error) {
    setText("#adminStatus", `部分加载失败：${error.message || "错误"}`);
  }
};

const applyAdminLocale = () => {
  const t = adminText();
  document.documentElement.lang = locale === "zh" ? "zh-CN" : locale;
  document.querySelectorAll("[data-admin-ui]").forEach((node) => {
    const value = t[node.dataset.adminUi];
    if (value) node.textContent = value;
  });
};
applyAdminLocale();
setAdminTab("config");

document.querySelectorAll("[data-admin-tab-target]").forEach((button) => {
  button.addEventListener("click", () => setAdminTab(button.dataset.adminTabTarget || "config"));
});

document.querySelector("#refreshDb").addEventListener("click", renderDb);
document.querySelector("#refreshLlm").addEventListener("click", () => renderLlm(false));
document.querySelector("#saveDbConfig").addEventListener("click", () => saveDbConfig().catch((error) => setText("#adminStatus", error.message)));
document.querySelector("#saveLlmConfig").addEventListener("click", () => saveLlmConfig().catch((error) => setText("#adminStatus", error.message)));
document.querySelector("#probeModels").addEventListener("click", () => renderLlm(true));
document.querySelector("#testLlm").addEventListener("click", () => testLlm().catch((error) => setText("#llmTestResult", error.message)));
document.querySelector("#llmModelSelect").addEventListener("change", (event) => {
  const modelInput = document.querySelector('#llmConfigForm [name="model"]');
  if (modelInput && event.target.value) modelInput.value = event.target.value;
});
document.querySelector("#refreshRedis").addEventListener("click", renderRedis);
document.querySelector("#clearRedisCache").addEventListener("click", () => clearRedisCache().catch((error) => setText("#adminStatus", error.message)));
document.querySelector("#refreshTrainingTasks").addEventListener("click", renderTrainingTasks);
document.querySelector("#pauseTrainingTask").addEventListener("click", () => pauseTrainingTask().catch((error) => setText("#adminStatus", error.message)));
logoutButton?.addEventListener("click", () => logout().catch((error) => setText("#adminStatus", error.message)));

loadCurrentSession()
  .then((session) => {
    if (session.role === "admin") return refreshAll();
    return null;
  })
  .catch((error) => setText("#adminStatus", error.message));
