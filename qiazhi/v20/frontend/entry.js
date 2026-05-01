const ENTRY_TEXT = {
  zh: {
    title: "进入掐指一算",
    subtitle: "选择游客、命理师或 Admin 入口，进入 V20 命理测算系统。",
    language: "语言",
    guest_title: "游客即时测算",
    guest_desc: "不需要账号，直接进入测算台。适合快速体验和临时问盘。",
    guest_button: "游客进入",
    login_title: "本地账号登录",
    login_desc: "用于保留多用户、命理师工作流和后续用户档案。",
    username: "用户名",
    password: "密码",
    role: "角色",
    role_guest: "游客",
    role_practitioner: "命理师",
    login_button: "登录",
    register_button: "注册",
    admin_desc: "Admin 页面只保留数据库与 LLM 运行状态，复杂知识和规则治理不放在入口页。",
    workbench_link: "直接进入测算台",
  },
  en: {
    title: "Enter Qiazhi",
    subtitle: "Choose Guest, Practitioner, or Admin to enter the V20 Bazi system.",
    language: "Language",
    guest_title: "Guest Reading",
    guest_desc: "No account required. Open the workbench for a quick reading.",
    guest_button: "Continue as Guest",
    login_title: "Local Account",
    login_desc: "Keeps multi-user, practitioner workflow, and future profile continuity.",
    username: "Username",
    password: "Password",
    role: "Role",
    role_guest: "Guest",
    role_practitioner: "Practitioner",
    login_button: "Log In",
    register_button: "Register",
    admin_desc: "Admin only shows database and LLM status; deeper rule governance stays out of the entry page.",
    workbench_link: "Open Workbench",
  },
  ko: {
    title: "Qiazhi 시작",
    subtitle: "게스트, 명리사, Admin 입구를 선택해 V20 사주 시스템으로 들어갑니다.",
    language: "언어",
    guest_title: "게스트 즉시 분석",
    guest_desc: "계정 없이 바로 분석 작업대로 들어갑니다.",
    guest_button: "게스트로 시작",
    login_title: "로컬 계정",
    login_desc: "다중 사용자, 명리사 작업 흐름, 향후 프로필 연속성을 보존합니다.",
    username: "사용자명",
    password: "비밀번호",
    role: "역할",
    role_guest: "게스트",
    role_practitioner: "명리사",
    login_button: "로그인",
    register_button: "등록",
    admin_desc: "Admin은 DB와 LLM 상태만 표시합니다. 복잡한 규칙 관리는 입구에 두지 않습니다.",
    workbench_link: "작업대 열기",
  },
};

const localeSelect = document.querySelector("#entryLocale");
const statusLine = document.querySelector("#entryStatus");

const requestJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.detail?.message || payload.message || `HTTP ${response.status}`);
  }
  return payload;
};

const applyLocale = (locale) => {
  const clean = ENTRY_TEXT[locale] ? locale : "zh";
  const text = ENTRY_TEXT[clean];
  document.documentElement.lang = clean === "zh" ? "zh-CN" : clean;
  document.querySelectorAll("[data-entry]").forEach((node) => {
    const value = text[node.dataset.entry];
    if (value) node.textContent = value;
  });
  document.querySelectorAll("[data-entry-option]").forEach((node) => {
    const value = text[node.dataset.entryOption];
    if (value) node.textContent = value;
  });
  localStorage.setItem("v20_locale", clean);
};

const goWorkbench = (session) => {
  const role = session?.role || document.querySelector("#loginRole").value || "user";
  const locale = localeSelect.value || "zh";
  const params = new URLSearchParams({ role, locale });
  window.location.href = `/v20/ui/workbench.html?${params.toString()}`;
};

const guestStart = async () => {
  statusLine.textContent = "...";
  const result = await requestJson("/api/v20/auth/guest", {
    method: "POST",
    body: JSON.stringify({ locale: localeSelect.value }),
  });
  goWorkbench(result.session);
};

const login = async () => {
  statusLine.textContent = "...";
  const result = await requestJson("/api/v20/auth/login", {
    method: "POST",
    body: JSON.stringify({
      username: document.querySelector("#loginName").value,
      password: document.querySelector("#loginPassword").value,
      locale: localeSelect.value,
    }),
  });
  goWorkbench(result.session);
};

const register = async () => {
  statusLine.textContent = "...";
  const result = await requestJson("/api/v20/auth/register", {
    method: "POST",
    body: JSON.stringify({
      username: document.querySelector("#loginName").value,
      password: document.querySelector("#loginPassword").value,
      role: document.querySelector("#loginRole").value,
      locale: localeSelect.value,
    }),
  });
  goWorkbench(result.session);
};

const loadMe = async () => {
  const result = await requestJson("/api/v20/auth/me");
  const session = result.session || {};
  statusLine.textContent = result.authenticated ? `${session.username} · ${session.role}` : "not authenticated";
};

localeSelect.value = localStorage.getItem("v20_locale") || "zh";
applyLocale(localeSelect.value);
localeSelect.addEventListener("change", () => applyLocale(localeSelect.value));
document.querySelector("#guestStart").addEventListener("click", () => guestStart().catch((error) => statusLine.textContent = error.message));
document.querySelector("#loginButton").addEventListener("click", () => login().catch((error) => statusLine.textContent = error.message));
document.querySelector("#registerButton").addEventListener("click", () => register().catch((error) => statusLine.textContent = error.message));
loadMe().catch(() => statusLine.textContent = "not authenticated");
