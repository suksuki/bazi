const setText = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value ?? "";
};

const logoutButton = document.querySelector("#logoutButton");
const locale = localStorage.getItem("v20_locale") || "zh";

const ADMIN_TEXT = {
  zh: { status: "状态", refresh: "刷新", models: "模型", no_data: "暂无数据。", await_db: "等待 V20_DATABASE_URL。", logout: "登出", entry: "入口", profiles: "档案", measure: "测算" },
  en: { status: "Status", refresh: "Refresh", models: "Models", no_data: "No data.", await_db: "Waiting for V20_DATABASE_URL.", logout: "Log Out", entry: "Entry", profiles: "Profiles", measure: "Reading" },
  ko: { status: "상태", refresh: "새로고침", models: "모델", no_data: "데이터 없음.", await_db: "V20_DATABASE_URL 대기 중.", logout: "로그아웃", entry: "입구", profiles: "프로필", measure: "분석" },
};
const adminText = () => ADMIN_TEXT[locale] || ADMIN_TEXT.zh;

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
      setText("#adminStatus", "admin required");
    }
    return session;
  } catch (error) {
    if (logoutButton) logoutButton.hidden = true;
    setText("#adminStatus", "admin required");
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
  setText("#adminStatus", `db ${db.status}`);
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
  const llm = await requestJson(`/api/v20/admin/llm${probeModels ? "?probe_models=true" : ""}`);
  setText("#adminStatus", `llm ${llm.status}`);
  const ready = llm.readiness || {};
  const summary = document.querySelector("#llmSummary");
  clear(summary);
  [
    [adminText().status, llm.status],
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
    root.append(el("div", "empty-note", adminText().no_data));
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

const applyAdminLocale = () => {
  const t = adminText();
  document.documentElement.lang = locale === "zh" ? "zh-CN" : locale;
  document.querySelectorAll("[data-admin-ui]").forEach((node) => {
    const value = t[node.dataset.adminUi];
    if (value) node.textContent = value;
  });
};
applyAdminLocale();

document.querySelector("#refreshDb").addEventListener("click", renderDb);
document.querySelector("#refreshLlm").addEventListener("click", () => renderLlm(false));
document.querySelector("#probeModels").addEventListener("click", () => renderLlm(true));
logoutButton?.addEventListener("click", () => logout().catch((error) => setText("#adminStatus", error.message)));

loadCurrentSession()
  .then((session) => {
    if (session.role === "admin") return refreshAll();
    return null;
  })
  .catch((error) => setText("#adminStatus", error.message));
