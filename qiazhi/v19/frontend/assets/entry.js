const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(window.location.search);
let locale = localStorage.getItem("v19_oracle_locale") || params.get("locale") || "zh";
let labels = {};

boot();

async function boot() {
  await loadLabels(locale);
  renderLabels();
  bindEvents();
  await loadMe();
}

async function loadLabels(nextLocale) {
  const clean = ["zh", "en", "ko"].includes(nextLocale) ? nextLocale : "zh";
  const result = await fetch(`/api/labels?locale=${encodeURIComponent(clean)}`).then((response) => response.json());
  locale = result.locale || clean;
  labels = result.terms || {};
}

function renderLabels() {
  document.documentElement.lang = locale === "zh" ? "zh-CN" : locale;
  document.title = t("entry_title");
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n || "");
  });
  $("locale").innerHTML = ["zh", "en", "ko"].map((item) => `<option value="${item}" ${item === locale ? "selected" : ""}>${escapeHtml(t(`locale_${item}`))}</option>`).join("");
}

function bindEvents() {
  $("locale").addEventListener("change", async () => {
    locale = $("locale").value;
    localStorage.setItem("v19_oracle_locale", locale);
    await loadLabels(locale);
    renderLabels();
  });
  $("guestStart").addEventListener("click", async () => {
    await authPost("/api/auth/guest", {}, "/profiles");
  });
  $("login").addEventListener("click", async () => {
    const result = await authPost("/api/auth/login", readLogin());
    routeAfterAuth(result);
  });
  $("register").addEventListener("click", async () => {
    const result = await authPost("/api/auth/user/register", readLogin());
    routeAfterAuth(result);
  });
}

function readLogin() {
  return { username: $("loginName").value, password: $("loginPassword").value };
}

function routeAfterAuth(result) {
  if (!result) return;
  window.location.href = `/profiles?locale=${encodeURIComponent(locale)}`;
}

async function authPost(url, payload, redirectTo = "") {
  $("entryStatus").textContent = "...";
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok || !result.ok) {
    $("entryStatus").textContent = (result.detail && result.detail.message) || result.message || t("auth_failed");
    return null;
  }
  $("entryStatus").textContent = `${result.data?.role || "guest"} authenticated`;
  if (redirectTo) window.location.href = `${redirectTo}?locale=${encodeURIComponent(locale)}`;
  return result;
}

async function loadMe() {
  const result = await fetch("/api/auth/me").then((response) => response.json()).catch(() => null);
  if (!result || !result.ok) return;
  const data = result.data || {};
  const warning = data.admin_default_password_used ? " · admin local default password active" : "";
  $("entryStatus").textContent = `${data.authenticated ? "authenticated" : "not authenticated"} · role: ${data.role || "guest"}${warning}`;
}

function t(key) {
  if (labels[key] && labels[key].label) return labels[key].label;
  console.warn(`Missing V19 label: ${key}`);
  return key;
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
