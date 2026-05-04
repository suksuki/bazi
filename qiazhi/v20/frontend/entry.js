const ENTRY_TEXT = {
  zh: {
    title: "进入掐指一算",
    subtitle: "选择游客或本地账号进入 V20 命理测算系统。",
    language: "语言",
    guest_title: "游客即时测算",
    guest_desc: "不需要账号，直接进入测算台。适合快速体验和临时问盘。",
    guest_button: "游客进入",
    login_title: "本地账号登录",
    login_desc: "用于保留多用户、命理师工作流和后续用户档案。",
    register_title: "注册本地账号",
    register_desc: "普通用户用于保存个人档案，命理师用于后续校准与工作流。",
    username: "用户名",
    password: "密码",
    register_role: "注册角色",
    role_user: "普通用户",
    role_practitioner: "命理师",
    login_button: "登录",
    register_button: "注册",
    logout_button: "登出",
    logged_out: "已登出",
    not_authenticated: "未登录",
    or: "或者",
  },
  en: {
    title: "Enter Qiazhi",
    subtitle: "Choose Guest or a local account to enter the V20 Bazi system.",
    language: "Language",
    guest_title: "Guest Reading",
    guest_desc: "No account required. Open the workbench for a quick reading.",
    guest_button: "Continue as Guest",
    login_title: "Local Account",
    login_desc: "Keeps multi-user, practitioner workflow, and future profile continuity.",
    register_title: "Register Local Account",
    register_desc: "Regular users keep personal profiles; practitioners unlock calibration workflow.",
    username: "Username",
    password: "Password",
    register_role: "Registration Role",
    role_user: "Regular User",
    role_practitioner: "Practitioner",
    login_button: "Log In",
    register_button: "Register",
    logout_button: "Log Out",
    logged_out: "Logged out",
    not_authenticated: "Not authenticated",
    or: "OR",
  },
  ko: {
    title: "Qiazhi 시작",
    subtitle: "게스트 또는 로컬 계정으로 V20 사주 시스템에 들어갑니다.",
    language: "언어",
    guest_title: "게스트 즉시 분석",
    guest_desc: "계정 없이 바로 분석 작업대로 들어갑니다.",
    guest_button: "게스트로 시작",
    login_title: "로컬 계정",
    login_desc: "다중 사용자, 명리사 작업 흐름, 향후 프로필 연속성을 보존합니다.",
    register_title: "로컬 계정 등록",
    register_desc: "일반 사용자는 개인 프로필을 저장하고, 명리사는 보정 작업 흐름을 사용합니다.",
    username: "사용자명",
    password: "비밀번호",
    register_role: "등록 역할",
    role_user: "일반 사용자",
    role_practitioner: "명리사",
    login_button: "로그인",
    register_button: "등록",
    logout_button: "로그아웃",
    logged_out: "로그아웃됨",
    not_authenticated: "인증되지 않음",
    or: "또는",
  },
};

const localeSelect = document.querySelector("#entryLocale");
const statusLine = document.querySelector("#entryStatus");
// Removed redundant logout button from entry page for cleaner 3-in-1 look
const currentEntryText = () => ENTRY_TEXT[localeSelect.value] || ENTRY_TEXT.zh;

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
  document.title = text.title + " · Qiazhi V20";
};

const goWorkbench = (session) => {
  const role = session?.role || "user";
  const locale = localeSelect.value || "zh";
  const params = new URLSearchParams({ role, locale });
  window.location.href = `/v20/ui/workbench.html?${params.toString()}`;
};

const goProfiles = (session) => {
  const role = session?.role || "user";
  const locale = localeSelect.value || "zh";
  const params = new URLSearchParams({ role, locale });
  // Redirect back to the correct Profiles page
  window.location.href = `/v20/ui/profiles.html?${params.toString()}`;
};

const guestStart = async () => {
  statusLine.textContent = "...";
  const result = await requestJson("/api/v20/auth/guest", {
    method: "POST",
    body: JSON.stringify({ locale: localeSelect.value }),
  });
  
  // CRITICAL: Save guest session so measurement API can be called!
  if (result.session) {
    localStorage.setItem("v20_session", result.session);
  }
  
  const calendarVal = document.querySelector("#guestCalendar").value;
  const leapChecked = document.querySelector("#guestLeapMonth")?.checked || false;
  const params = new URLSearchParams({
    role: "guest",
    locale: localeSelect.value,
    calendar: calendarVal,
    gender: document.querySelector("#guestGender").value,
    year: document.querySelector("#guestYear").value.substring(0, 4),
    month: document.querySelector("#guestMonth").value,
    day: document.querySelector("#guestDay").value,
    hour: document.querySelector("#guestHour").value,
    minute: document.querySelector("#guestMinute").value,
    flow_year: document.querySelector("#guestFlowYear").value,
    auto_measure: "true"
  });
  if (calendarVal === "lunar") params.set("lunar_is_leap", leapChecked ? "true" : "false");
  window.location.href = `/v20/ui/workbench.html?${params.toString()}`;
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
  goProfiles(result.session);
};

const register = async () => {
  statusLine.textContent = "...";
  const result = await requestJson("/api/v20/auth/register", {
    method: "POST",
    body: JSON.stringify({
      username: document.querySelector("#registerName").value,
      password: document.querySelector("#registerPassword").value,
      role: document.querySelector("#registerRole").value,
      locale: localeSelect.value,
    }),
  });
  goProfiles(result.session);
};

const logout = async () => {
  statusLine.textContent = "...";
  await requestJson("/api/v20/auth/logout", {
    method: "POST",
    body: JSON.stringify({}),
  });
  if (logoutButton) logoutButton.hidden = true;
  statusLine.textContent = currentEntryText().logged_out;
};

const loadMe = async () => {
  const result = await requestJson("/api/v20/auth/me");
  const session = result.session || {};
  statusLine.textContent = result.authenticated ? `${session.username} · ${session.role}` : "";
};

const initTabs = () => {
  const tabs = document.querySelectorAll(".tab-btn");
  const panes = document.querySelectorAll(".auth-pane");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      panes.forEach((p) => p.classList.toggle("active", p.id === `${target}Pane`));
      statusLine.textContent = "";
    });
  });
};

const setupGuestForm = () => {
  const now = new Date();
  document.querySelector("#guestYear").value = 1990; // Sensible default
  document.querySelector("#guestMonth").value = now.getMonth() + 1;
  document.querySelector("#guestDay").value = now.getDate();
  document.querySelector("#guestHour").value = 12;
  document.querySelector("#guestMinute").value = 0;

  const flowYearSelect = document.querySelector("#guestFlowYear");
  const currentYear = now.getFullYear();
  for (let y = currentYear - 1; y <= currentYear + 10; y++) {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = `${y}年`;
    if (y === currentYear) opt.selected = true;
    flowYearSelect.appendChild(opt);
  }

  // Toggle leap month row when calendar changes
  const calSelect = document.querySelector("#guestCalendar");
  const leapRow = document.querySelector("#guestLeapRow");
  calSelect.addEventListener("change", () => {
    leapRow.style.display = calSelect.value === "lunar" ? "" : "none";
  });
};

hydrateLocale();
initTabs();
setupGuestForm();
document.querySelector("#guestStart").addEventListener("click", () => guestStart().catch((error) => statusLine.textContent = error.message));
document.querySelector("#loginButton").addEventListener("click", () => login().catch((error) => statusLine.textContent = error.message));
document.querySelector("#registerButton").addEventListener("click", () => register().catch((error) => statusLine.textContent = error.message));
loadMe().catch(() => {});

function hydrateLocale() {
  localeSelect.value = localStorage.getItem("v20_locale") || "zh";
  applyLocale(localeSelect.value);
  localeSelect.addEventListener("change", () => applyLocale(localeSelect.value));
}
