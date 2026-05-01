const setText = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value ?? "";
};

const requestJson = async (url) => {
  const response = await fetch(url);
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

const renderDb = async () => {
  const db = await requestJson("/api/v20/admin/db");
  setText("#adminStatus", `db ${db.status}`);
  const summary = document.querySelector("#dbSummary");
  clear(summary);
  [
    ["状态", db.status],
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
    tableRoot.append(el("div", "empty-note", "等待 V20_DATABASE_URL。"));
  }

  renderTags("#dbIndexes", db.corpus_indexes || []);
};

const renderLlm = async (probeModels = false) => {
  const llm = await requestJson(`/api/v20/admin/llm${probeModels ? "?probe_models=true" : ""}`);
  setText("#adminStatus", `llm ${llm.status}`);
  const ready = llm.readiness || {};
  const summary = document.querySelector("#llmSummary");
  clear(summary);
  [
    ["状态", llm.status],
    ["Provider", ready.provider || "-"],
    ["Model", ready.model || "-"],
    ["Execute", ready.execute_llm ? "enabled" : "disabled"],
    ["Ready", ready.ready_for_connection ? "yes" : "no"],
    ["Base URL", ready.resolved_base_url || "-"],
  ].forEach(([label, value]) => summary.append(metric(label, value)));

  renderTags("#llmModels", (llm.models || []).map((row) => row.id).filter(Boolean));
  renderTags("#llmGuardrails", ready.guardrails || llm.guardrails || []);
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
    root.append(el("div", "empty-note", "暂无数据。"));
    return;
  }
  tags.slice(0, 24).forEach((tag) => root.append(el("span", "tag", tag)));
};

const refreshAll = async () => {
  try {
    await Promise.all([renderDb(), renderLlm(false)]);
    setText("#adminStatus", "ready");
  } catch (error) {
    setText("#adminStatus", "error");
    setText("#dbSummary", error.message);
  }
};

document.querySelector("#refreshDb").addEventListener("click", renderDb);
document.querySelector("#refreshLlm").addEventListener("click", () => renderLlm(false));
document.querySelector("#probeModels").addEventListener("click", () => renderLlm(true));

refreshAll();
