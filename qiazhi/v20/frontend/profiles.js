const params = new URLSearchParams(window.location.search);
const localeSelect = document.querySelector("#profileLocale");
const profileList = document.querySelector("#profileList");
const importButton = document.querySelector("#importProfilesButton");
const instantMeasureLink = document.querySelector("#instantMeasureLink");
const logoutButton = document.querySelector("#logoutButton");
const state = { profiles: [] };

const PROFILE_TEXT = {
  zh: {
    app_title: "八字档案管理",
    nav_profiles: "档案",
    nav_measure: "测算",
    list_title: "档案列表",
    instant_measure: "临时测算",
    import_profiles: "迁移 V19 档案",
    language: "语言",
    enter_profile: "进入测算",
    owner: "归属",
    empty: "暂无档案",
    importing: "迁移中",
    logout_button: "登出",
  },
  en: {
    app_title: "Bazi Profiles",
    nav_profiles: "Profiles",
    nav_measure: "Reading",
    list_title: "Profile List",
    instant_measure: "Instant Reading",
    import_profiles: "Import V19 Profiles",
    language: "Language",
    enter_profile: "Open Reading",
    owner: "Owner",
    empty: "No profiles",
    importing: "Importing",
    logout_button: "Log Out",
  },
  ko: {
    app_title: "사주 프로필",
    nav_profiles: "프로필",
    nav_measure: "분석",
    list_title: "프로필 목록",
    instant_measure: "즉시 분석",
    import_profiles: "V19 프로필 가져오기",
    language: "언어",
    enter_profile: "분석 열기",
    owner: "소유자",
    empty: "프로필 없음",
    importing: "가져오는 중",
    logout_button: "로그아웃",
  },
};

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

const setText = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value ?? "";
};

const applyLocale = (locale) => {
  const clean = PROFILE_TEXT[locale] ? locale : "zh";
  const text = PROFILE_TEXT[clean];
  document.documentElement.lang = clean === "zh" ? "zh-CN" : clean;
  document.querySelectorAll("[data-profile-ui]").forEach((node) => {
    const value = text[node.dataset.profileUi];
    if (value) node.textContent = value;
  });
  localStorage.setItem("v20_locale", clean);
  updateLinks();
};

const loadMe = async () => {
  const result = await requestJson("/api/v20/auth/me");
  const session = result.session || {};
  document.body.dataset.role = session.role || params.get("role") || "user";
  document.querySelectorAll(".admin-nav-link").forEach((node) => {
    node.hidden = session.role !== "admin";
  });
  if (logoutButton) logoutButton.hidden = !result.authenticated;
  setText("#profileRuntimeStatus", result.authenticated ? `${session.username || "local"} · ${session.role || "user"}` : "not authenticated");
};

const logout = async () => {
  await requestJson("/api/v20/auth/logout", {
    method: "POST",
    body: JSON.stringify({}),
  });
  window.location.href = `/v20/ui/?locale=${encodeURIComponent(localeSelect.value || "zh")}`;
};

const loadProfiles = async () => {
  const result = await requestJson("/api/v20/profiles?owner_id=admin&limit=120");
  state.profiles = result.profiles || [];
  renderProfiles(state.profiles);
  setText("#profileCount", String(result.profile_count || 0));
  setText("#profileStatus", result.status || "ready");
};

const renderProfiles = (profiles) => {
  profileList.innerHTML = "";
  const text = currentText();
  if (!profiles.length) {
    const empty = document.createElement("article");
    empty.className = "profile-card empty-note";
    empty.textContent = text.empty;
    profileList.append(empty);
    return;
  }
  profiles.forEach((profile) => {
    const card = document.createElement("article");
    card.className = "profile-card";

    const title = document.createElement("h2");
    title.textContent = profile.display_name || profile.profile_id || "V20 Profile";
    card.append(title);

    const meta = document.createElement("p");
    meta.textContent = profileMeta(profile);
    card.append(meta);

    const tags = document.createElement("div");
    tags.className = "profile-tag-row";
    tags.append(tag(`${text.owner} ${profile.owner_id || "-"}`));
    tags.append(tag(profile.status || "profile"));
    if (profile.metadata?.source_system) tags.append(tag(profile.metadata.source_system));
    card.append(tags);

    const actions = document.createElement("div");
    actions.className = "profile-card-actions";
    const link = document.createElement("a");
    link.className = "mini-action";
    link.href = measureUrl(profile);
    link.textContent = text.enter_profile;
    actions.append(link);
    card.append(actions);

    profileList.append(card);
  });
};

const importProfiles = async () => {
  importButton.disabled = true;
  importButton.textContent = currentText().importing;
  try {
    const result = await requestJson("/api/v20/profiles/import-v19?apply=true&owner_id=admin", { method: "POST" });
    setText("#profileStatus", `${result.status} ${result.imported_or_updated || 0}`);
    await loadProfiles();
  } catch (error) {
    setText("#profileStatus", error.message);
  } finally {
    importButton.disabled = false;
    importButton.textContent = currentText().import_profiles;
  }
};

const measureUrl = (profile) => {
  const query = new URLSearchParams({
    role: measurementRole(params.get("role") || document.body.dataset.role),
    locale: localeSelect.value,
    profile_id: profile.profile_id || "",
    profile_name: profile.display_name || "",
  });
  appendProfileDefaults(query, profile);
  return `/v20/ui/workbench.html?${query.toString()}`;
};

const appendProfileDefaults = (query, profile) => {
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
    if (value) query.set(key, value);
  });
};

const updateLinks = () => {
  const query = new URLSearchParams({
    role: measurementRole(params.get("role") || document.body.dataset.role),
    locale: localeSelect.value,
  });
  instantMeasureLink.href = `/v20/ui/workbench.html?${query.toString()}`;
};

const profileMeta = (profile) => {
  const birth = profile.birth_input || {};
  const date = [birth.year, String(birth.month || "").padStart(2, "0"), String(birth.day || "").padStart(2, "0")]
    .filter((value) => value && value !== "00")
    .join("-");
  const time = birth.hour !== undefined ? `${String(birth.hour).padStart(2, "0")}:${String(birth.minute || 0).padStart(2, "0")}` : "";
  const calendar = birth.calendar_type || birth.calendar || "";
  return [date, time, calendar].filter(Boolean).join(" · ");
};

const tag = (text) => {
  const node = document.createElement("span");
  node.className = "tag";
  node.textContent = text;
  return node;
};

const currentText = () => PROFILE_TEXT[localeSelect.value] || PROFILE_TEXT.zh;
const measurementRole = (role) => (role === "user" ? "user" : role === "admin" ? "admin" : "analyst");

localeSelect.value = params.get("locale") || localStorage.getItem("v20_locale") || "zh";
applyLocale(localeSelect.value);
localeSelect.addEventListener("change", () => {
  applyLocale(localeSelect.value);
  renderProfiles(state.profiles);
  loadProfiles().catch((error) => setText("#profileStatus", error.message));
});
importButton.addEventListener("click", importProfiles);
logoutButton?.addEventListener("click", () => logout().catch((error) => setText("#profileStatus", error.message)));
loadMe().then(updateLinks).catch(() => updateLinks());
loadProfiles().catch((error) => setText("#profileStatus", error.message));
