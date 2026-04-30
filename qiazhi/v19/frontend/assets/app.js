const $ = (id) => document.getElementById(id);
let sessionId = "";
let lastData = null;

$("run").addEventListener("click", () => runAgent());
$("newSession").addEventListener("click", resetSession);
$("flowYearRange").addEventListener("input", () => {
  $("flowYear").value = $("flowYearRange").value;
});
$("flowYear").addEventListener("input", () => {
  const value = Number($("flowYear").value || 2025);
  if (Number.isFinite(value)) $("flowYearRange").value = String(Math.max(1984, Math.min(2050, value)));
});
$("calendar").addEventListener("change", () => {
  const isLunar = $("calendar").value === "lunar";
  $("lunarLeapMonth").disabled = !isLunar;
  if (!isLunar) $("lunarLeapMonth").checked = false;
});
$("calendar").dispatchEvent(new Event("change"));
$("message").addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    runAgent();
  }
});

async function runAgent() {
  $("run").disabled = true;
  $("run").textContent = sessionId ? "Running..." : "Generating...";
  $("runtimeInfo").textContent = "calling /api/agent/turn ...";
  $("headerLlm").textContent = "LLM: checking";
  try {
    const payload = buildPayload();
    const response = await fetch("/api/agent/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    render(await response.json(), payload);
  } catch (error) {
    showError("CLIENT_ERROR", error && error.message ? error.message : String(error));
  } finally {
    $("run").disabled = false;
    $("run").textContent = "Run Analysis";
  }
}

function buildPayload() {
  const calendar = $("calendar").value;
  return {
    birth_input: {
      year: Number($("year").value),
      month: Number($("month").value),
      day: Number($("day").value),
      hour: Number($("hour").value),
      gender: $("gender").value,
      calendar,
      calendar_type: calendar,
      lunar_is_leap_month: calendar === "lunar" && $("lunarLeapMonth").checked,
    },
    selected_year: Number($("flowYear").value),
    message: $("message").value.trim() || "请基于当前结构上下文继续。",
    session_id: sessionId,
  };
}

function resetSession() {
  sessionId = "";
  lastData = null;
  $("sessionInfo").textContent = "session: not started";
  $("runtimeInfo").textContent = "LLM / DB 状态会在第一次调用后显示。";
  $("headerSession").textContent = "session: idle";
  $("headerLlm").textContent = "LLM: pending";
  $("empty").classList.remove("hidden");
  $("result").classList.add("hidden");
}

function render(result, payload) {
  if (!result.ok) {
    showError(result.code || "AGENT_ERROR", result.message || "Unknown error");
    return;
  }

  const data = result.data;
  lastData = data;
  $("empty").classList.add("hidden");
  $("result").classList.remove("hidden");

  updateSession(data);
  renderRunHeader(data, payload);
  renderChart(data);
  renderIncomeStability(data);
  renderFlowYear(data);
  renderLuckCycles(data);
  renderSignalEvidence(data);
  renderKnowledge(data);
  renderRuleGraphRoutePack(data);
  renderPersonalizedQuestions(data);
  renderGuidedAnswerEvidencePack(data);
  renderConversation(data);
  renderAlgorithmStatus(data);
  renderTrace(data);
}

function updateSession(data) {
  if (data.session && data.session.session_id) {
    sessionId = data.session.session_id;
    const sessionText = `session: ${sessionId} · turns: ${data.session.turn_count} · storage: ${storageText(data.session.storage)}`;
    $("sessionInfo").textContent = sessionText;
    $("headerSession").textContent = `turns: ${data.session.turn_count}`;
  }
  const llm = data.llm_status || {};
  const llmText = llm.enabled
    ? `LLM: enabled · used: ${Boolean(llm.used)}${llm.model ? ` · model: ${llm.model}` : ""}${llm.reason ? ` · reason: ${llm.reason}` : ""}${llm.error ? ` · error: ${llm.error}` : ""}`
    : "LLM: disabled";
  $("runtimeInfo").textContent = llmText;
  $("headerLlm").textContent = llm.enabled ? `LLM: ${llm.used ? "used" : "not used"}` : "LLM: disabled";
}

function renderRunHeader(data, payload) {
  const chart = data.chart || {};
  const flow = data.time_context && data.time_context.flow_year;
  $("runTitle").textContent = `${payload.birth_input.year}-${pad(payload.birth_input.month)}-${pad(payload.birth_input.day)} · Flow ${payload.selected_year}`;
  $("runBadges").innerHTML = [
    badge(chart.status || "chart_ok"),
    badge(`calendar:${payload.birth_input.calendar}`),
    badge(flow ? `flow:${flow.pillar.display}` : "flow:none"),
    badge(data.agent_reply ? data.agent_reply.role : "agent"),
  ].join("");
}

function renderChart(data) {
  const chart = data.chart || {};
  const pillars = (chart && chart.pillars) || {};
  $("chartMeta").textContent = chart.day_master ? `day master: ${chart.day_master}` : "structure only";
  const rows = ["year", "month", "day", "hour"].map((name) => {
    const pillar = pillars[name] || {};
    return `<article class="structure-tag">
      <span>${escapeHtml(labelOfPillar(name))}</span>
      <strong>${escapeHtml(pillar.display || "-")}</strong>
      <em>${escapeHtml(pillar.stem_element || "?")} / ${escapeHtml(pillar.branch_element || "?")}</em>
    </article>`;
  });
  if (chart.day_master) {
    rows.unshift(`<article class="structure-tag key-tag"><span>Day Master</span><strong>${escapeHtml(chart.day_master)}</strong><em>anchor</em></article>`);
  }
  $("pillars").innerHTML = rows.join("");
}

function renderIncomeStability(data) {
  const bundle = ((data.inference_context || {}).income_stability) || {};
  const signals = Array.isArray(bundle.signals) ? bundle.signals : [];
  const signalMap = Object.fromEntries(signals.map((row) => [row.key, row.value]));
  if (bundle.status !== "ok") {
    $("incomeStability").innerHTML = `<div class="knowledge-empty">income_stability inference not available.</div>`;
    return;
  }
  const orderedKeys = [
    "self_capacity",
    "wealth_presence",
    "wealth_accessibility",
    "volatility",
    "structure_binding",
    "income_stability",
  ];
  const rows = orderedKeys
    .filter((key) => Object.prototype.hasOwnProperty.call(signalMap, key))
    .map((key) => `<div class="metric-row ${key === "income_stability" ? "primary-metric" : ""}">
      <span>${escapeHtml(key)}</span>
      <strong>${escapeHtml(String(signalMap[key]).toUpperCase())}</strong>
    </div>`)
    .join("");
  $("incomeStability").innerHTML = `<div class="income-instrument">
    <div class="income-readout">
      <span>Income Stability</span>
      <strong>${escapeHtml(String(signalMap.income_stability || "unknown").toUpperCase())}</strong>
      <em>scope: ${escapeHtml(bundle.scope || "")} · prediction: ${bundle.is_prediction ? "yes" : "no"}</em>
    </div>
    <div class="metric-table">${rows}</div>
  </div>`;
}

function renderSignalEvidence(data) {
  const bundle = ((data.inference_context || {}).income_stability) || {};
  const signals = Array.isArray(bundle.signals) ? bundle.signals : [];
  const evidenceRows = signals.filter((row) => row.rule_id || row.rule_version || row.sources);
  $("signalEvidence").innerHTML = evidenceRows.length
    ? evidenceRows.map((row) => `<article class="knowledge-item compact-evidence">
        <div class="knowledge-top"><span>${escapeHtml(row.key || "signal")}</span><strong>${escapeHtml(String(row.value || ""))}</strong></div>
        <h3>${escapeHtml(row.rule_id || "rule attribution pending")}</h3>
        <p>${escapeHtml(signalAttributionText(row) || "No source path recorded.")}</p>
      </article>`).join("")
    : `<div class="knowledge-empty">No signal evidence recorded.</div>`;
}

function renderFlowYear(data) {
  const context = data.time_context || {};
  const flow = context.flow_year || {};
  const rel = flow.relations_with_natal || {};
  $("flowYearResult").innerHTML = `<div class="time-readout">
    <span>Flow Year</span>
    <strong>${escapeHtml(flow.year || "-")} ${escapeHtml((flow.pillar && flow.pillar.display) || "")}</strong>
    <em>Relations with natal</em>
  </div>
  <div class="relation-list">
    ${relationList(rel)}
  </div>`;
}

function renderLuckCycles(data) {
  const luck = data.luck_cycles || {};
  const context = data.time_context || {};
  const active = context.luck_cycle || null;
  $("luckMeta").textContent = `direction: ${luck.direction || "unknown"} · ${luck.start_age_note || "start age pending"}`;
  $("activeLuck").innerHTML = active
    ? `<div class="focus-title">Active Luck Cycle</div><div class="focus-main">age ${active.start_age}-${active.end_age} · ${escapeHtml(active.pillar.display || "")}</div><div class="focus-sub">${escapeHtml(relationText(active.relations_with_natal || {}))}</div>`
    : `<div class="focus-title">Active Luck Cycle</div><div class="focus-sub">当前流年未命中大运，或大运仍为 stub。</div>`;
  const cycles = Array.isArray(luck.cycles) ? luck.cycles : [];
  const activeStart = active && active.start_age;
  $("luckCycles").innerHTML = cycles
    .slice(0, 8)
    .map((cycle) =>
      card(
        `age ${cycle.start_age}-${cycle.end_age}`,
        `${(cycle.pillar && cycle.pillar.display) || "-"}`,
        relationText(cycle.relations_with_natal || {}),
        cycle.start_age === activeStart,
      ),
    )
    .join("");
}

function renderKnowledge(data) {
  const context = data.knowledge_context || {};
  const items = Array.isArray(context.items) ? context.items : [];
  $("knowledgeMeta").textContent = `${items.length} unit(s) · ${context.runtime_scope || "agent_context"}`;
  $("knowledgeContext").innerHTML = items.length
    ? items.map((item) => knowledgeItem(item)).join("")
    : `<div class="knowledge-empty">No knowledge unit retrieved.</div>`;
}

function renderRuleGraphRoutePack(data) {
  const runtime = data.rule_graph_runtime_context || {};
  const route = runtime.knowledge_route || {};
  const routes = Array.isArray(runtime.routes) ? runtime.routes : [];
  const selected = Array.isArray(runtime.selected_paths) ? runtime.selected_paths : [];
  const lanes = Object.entries(route.by_topic_lane || {}).slice(0, 8);
  $("ruleGraphRouteMeta").textContent = runtime.status
    ? `${runtime.status} · ${selected.length} path(s) · ${runtime.route_count || 0} route(s)`
    : "not available";
  const routeCards = routes.slice(0, 3).map((row) => `<article class="knowledge-item compact-evidence">
    <div class="knowledge-top"><span>${escapeHtml(row.route_id || "route")}</span><strong>${escapeHtml(row.intent || "")}</strong></div>
    <h3>${escapeHtml((row.selected_knowledge_ids || []).slice(0, 3).join(" · ") || "No selected knowledge")}</h3>
    <p>${escapeHtml(`selected ${row.selected_count || 0} / candidates ${row.candidate_count || 0} · audit ${row.answer_audit_status || "-"}`)}</p>
  </article>`);
  const laneCard = `<article class="knowledge-item compact-evidence">
    <div class="knowledge-top"><span>topic lanes</span><strong>${escapeHtml((runtime.answer_audit || {}).status || "-")}</strong></div>
    <h3>${escapeHtml(lanes.map(([key, value]) => `${key}:${value}`).join(" · ") || "No lane counts")}</h3>
    <p>${escapeHtml(`scope ${runtime.runtime_scope || ""} · mutation ${((runtime.summary || {}).runtime_mutation === true) ? "yes" : "no"}`)}</p>
  </article>`;
  $("ruleGraphRoutePack").innerHTML = runtime.status
    ? [laneCard, ...routeCards].join("")
    : `<div class="knowledge-empty">No rule graph runtime context recorded.</div>`;
}

function renderPersonalizedQuestions(data) {
  const context = data.guided_question_context || {};
  const personalization = context.question_personalization_context || {};
  const questions = Array.isArray(context.questions) ? context.questions : [];
  $("personalizedQuestionsMeta").textContent = questions.length
    ? `${questions.length} question(s) · ${personalization.status || "ready"}`
    : "no question context";
  $("personalizedQuestionsPanel").innerHTML = questions.length
    ? questions.slice(0, 8).map((row) => {
        const meta = row.personalization || {};
        const reasons = Array.isArray(meta.reasons) ? meta.reasons.join(" · ") : "";
        return `<article class="knowledge-item compact-evidence">
          <div class="knowledge-top"><span>${escapeHtml(row.key || "question")}</span><strong>${escapeHtml(`score ${row.personalized_score ?? row.score ?? "-"}`)}</strong></div>
          <h3>${escapeHtml(localizedText(row.label) || row.key || "")}</h3>
          <p>${escapeHtml(`bucket ${meta.bucket || "-"} · route boost ${meta.route_boost || 0}${reasons ? ` · ${reasons}` : ""}`)}</p>
        </article>`;
      }).join("")
    : `<div class="knowledge-empty">No personalized guided questions recorded.</div>`;
}

function renderGuidedAnswerEvidencePack(data) {
  const answer = data.guided_question_answer || {};
  const pack = answer.evidence_pack || {};
  const summary = pack.summary || {};
  const facts = (pack.fact_evidence || {}).present_fact_scopes || [];
  const knowledgeIds = (pack.knowledge_evidence || {}).applied_ids || [];
  const runtimeIds = (pack.rule_graph_evidence || {}).runtime_selected_knowledge_ids || [];
  const bindings = Array.isArray(pack.evidence_bindings) ? pack.evidence_bindings : [];
  $("evidencePackMeta").textContent = pack.status
    ? `${pack.status} · ${bindings.length} binding(s) · audit ${(pack.audit || {}).status || "-"}`
    : "not available";
  if (!pack.status) {
    $("guidedAnswerEvidencePack").innerHTML = `<div class="knowledge-empty">No guided answer evidence pack recorded.</div>`;
    return;
  }
  const cards = [
    ["Fact scopes", facts.join(" · ") || "-", `count ${summary.fact_scope_count || facts.length}`],
    ["Applied knowledge", knowledgeIds.slice(0, 8).join(" · ") || "-", `bindings ${summary.knowledge_binding_count || 0}`],
    ["Runtime route knowledge", runtimeIds.slice(0, 8).join(" · ") || "-", `rule graph bindings ${summary.rule_graph_binding_count || 0}`],
    ["Mutation guard", `answer ${summary.answer_mutation_count || 0} · runtime ${summary.runtime_mutation === true ? "yes" : "no"}`, pack.runtime_scope || ""],
  ];
  $("guidedAnswerEvidencePack").innerHTML = cards.map(([title, value, sub]) => `<article class="knowledge-item compact-evidence">
    <div class="knowledge-top"><span>${escapeHtml(title)}</span><strong>evidence_pack</strong></div>
    <h3>${escapeHtml(value)}</h3>
    ${sub ? `<p>${escapeHtml(sub)}</p>` : ""}
  </article>`).join("");
}

function renderConversation(data) {
  const history = Array.isArray(data.history) ? data.history : [];
  $("agentMeta").textContent = history.length ? `${history.length} message(s)` : "secondary layer";
  $("conversation").innerHTML = history.length
    ? history.map((turn, index) => conversationTurn(turn, index)).join("")
    : `<div class="agent-bubble assistant">${escapeHtml((data.agent_reply && data.agent_reply.content || []).join("\n"))}</div>`;
}

function renderAlgorithmStatus(data) {
  const status = data.algorithm_status || {};
  const rows = [
    ["System", status.system_name || "V19 Standalone Agent Lab", status.public_product_ready === false ? "not public prediction product" : ""],
    ["Chart", ((status.chart_structure || {}).status || "unknown"), (((status.chart_structure || {}).limitations || []).slice(0, 2).join(" · "))],
    ["Time", ((status.time_structure || {}).status || "unknown"), (((status.time_structure || {}).limitations || []).slice(0, 2).join(" · "))],
    ["Knowledge", ((status.knowledge || {}).status || "unknown"), (status.knowledge || {}).not_rule_db ? "Evidence Store, not Rule DB" : ""],
    ["Income Stability", ((status.income_stability || {}).status || "unknown"), (status.income_stability || {}).is_prediction === false ? "not prediction" : ""],
    ["LLM", ((status.llm || {}).status || "unknown"), (status.llm || {}).primary_for_income_stability === false ? "not primary for income_stability" : ""],
  ];
  $("algorithmStatus").innerHTML = rows.map(([title, value, sub]) => `<article class="knowledge-item compact-evidence">
    <div class="knowledge-top"><span>${escapeHtml(title)}</span><strong>status</strong></div>
    <h3>${escapeHtml(value)}</h3>
    ${sub ? `<p>${escapeHtml(sub)}</p>` : ""}
  </article>`).join("");
}

function renderTrace(data) {
  $("traceJson").textContent = JSON.stringify(data, null, 2);
}

function showError(code, message) {
  $("empty").innerHTML = `<div><div class="empty-title">${escapeHtml(code)}</div><p>${escapeHtml(message)}</p></div>`;
  $("empty").classList.remove("hidden");
  $("result").classList.add("hidden");
  $("runtimeInfo").textContent = `${code}: ${message}`;
  $("headerLlm").textContent = "error";
}

function knowledgeItem(item) {
  const facts = Array.isArray(item.structured_facts) ? item.structured_facts.slice(0, 5).join(" · ") : "";
  const routeScore = Number(item.route_match_score || 0);
  const routeReasons = Array.isArray(item.route_match_reasons) ? item.route_match_reasons.join(" · ") : "";
  return `<article class="knowledge-item">
    <div class="knowledge-top">
      <span>${escapeHtml(item.knowledge_id || "")}</span>
      <strong>${escapeHtml(item.domain || "")}</strong>
    </div>
    <h3>${escapeHtml(item.title || "")}</h3>
    <p>${escapeHtml(item.statement || "")}</p>
    ${facts ? `<div class="knowledge-facts">${escapeHtml(facts)}</div>` : ""}
    <div class="knowledge-guard">Evidence only · no direct prediction · score ${escapeHtml(item.match_score ?? "-")}${routeScore ? ` · route +${escapeHtml(routeScore)}` : ""}</div>
    ${routeReasons ? `<div class="knowledge-guard">route reasons · ${escapeHtml(routeReasons)}</div>` : ""}
  </article>`;
}

function conversationTurn(turn, index) {
  return `<div class="turn">
    <div class="turn-index">#${index + 1}</div>
    <div class="agent-bubble user">${escapeHtml(turn.user || "")}</div>
    <div class="agent-bubble assistant">${escapeHtml(turn.assistant || "")}</div>
  </div>`;
}

function card(label, value, sub, active = false) {
  return `<div class="card ${active ? "active" : ""}">
    <div class="label">${escapeHtml(label)}</div>
    <div class="value">${escapeHtml(value)}</div>
    ${sub ? `<div class="sub">${escapeHtml(sub)}</div>` : ""}
  </div>`;
}

function badge(value) {
  return `<span class="badge">${escapeHtml(value)}</span>`;
}

function relationText(relations) {
  const rows = [
    ...((relations.clashes || []).map((item) => `clash:${item}`)),
    ...((relations.combinations || []).map((item) => `combination:${item}`)),
  ];
  return rows.length ? rows.join(" · ") : "none";
}

function relationList(relations) {
  const rows = [
    ...((relations.clashes || []).map((item) => ["clash", item])),
    ...((relations.combinations || []).map((item) => ["combination", item])),
  ];
  if (!rows.length) return `<div class="relation-row"><span>none</span><strong>-</strong></div>`;
  return rows.map(([type, value]) => `<div class="relation-row"><span>${escapeHtml(type)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");
}

function signalAttributionText(row) {
  const rule = row.rule_id ? `${row.rule_id}@v${row.rule_version || "?"}` : "";
  const sources = Array.isArray(row.sources)
    ? row.sources.map((item) => typeof item === "object" ? `${item.path}=${item.value}` : String(item)).join(" · ")
    : "";
  return [rule, sources].filter(Boolean).join(" · ");
}

function labelOfPillar(name) {
  return { year: "年柱", month: "月柱", day: "日柱", hour: "时柱" }[name] || name;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

function localizedText(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value.zh || value.en || value.ko || "";
  }
  return String(value || "");
}

function storageText(storage) {
  if (!storage) return "unknown";
  const fallback = storage.fallback_reason ? ` (${storage.fallback_reason})` : "";
  return `${storage.backend || "unknown"}${fallback}`;
}

function pad(value) {
  return String(value).padStart(2, "0");
}
