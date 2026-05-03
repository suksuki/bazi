const params = new URLSearchParams(window.location.search);
const localeSelect = document.querySelector("#profileLocale");
const profileList = document.querySelector("#profileList");
const newProfileButton = document.querySelector("#newProfileButton");
const logoutButton = document.querySelector("#logoutButton");
const editor = document.querySelector("#profileEditor");
const editorTitle = document.querySelector("#profileEditorTitle");
const cancelProfileEdit = document.querySelector("#cancelProfileEdit");
const saveProfileButton = document.querySelector("#saveProfileButton");
const state = { profiles: [], editingProfileId: "" };

const PROFILE_TEXT = {
  zh: {
    app_title: "八字档案管理",
    nav_profiles: "档案",
    nav_measure: "测算",
    list_title: "档案列表",
    new_profile: "新增档案",
    enter_profile: "进入测算",
    edit_profile: "修改",
    delete_profile: "删除",
    owner: "归属",
    empty: "暂无档案",
    logout_button: "登出",
    editor_new: "新增档案",
    editor_edit: "修改档案",
    cancel: "取消",
    display_name: "姓名/标题",
    calendar: "历法",
    birth_year: "出生年",
    birth_month: "出生月",
    birth_day: "出生日",
    birth_hour: "出生时",
    birth_minute: "出生分",
    profile_status_label: "状态",
    save_profile: "保存档案",
    saved: "已保存",
    deleted: "已删除",
    delete_confirm: "确定删除这个档案？",
  },
  en: {
    app_title: "Bazi Profiles",
    nav_profiles: "Profiles",
    nav_measure: "Reading",
    list_title: "Profile List",
    new_profile: "New Profile",
    enter_profile: "Open Reading",
    edit_profile: "Edit",
    delete_profile: "Delete",
    owner: "Owner",
    empty: "No profiles",
    logout_button: "Log Out",
    editor_new: "New Profile",
    editor_edit: "Edit Profile",
    cancel: "Cancel",
    display_name: "Name / Title",
    calendar: "Calendar",
    birth_year: "Birth Year",
    birth_month: "Birth Month",
    birth_day: "Birth Day",
    birth_hour: "Birth Hour",
    birth_minute: "Birth Minute",
    profile_status_label: "Status",
    save_profile: "Save Profile",
    saved: "Saved",
    deleted: "Deleted",
    delete_confirm: "Delete this profile?",
  },
  ko: {
    app_title: "사주 프로필",
    nav_profiles: "프로필",
    nav_measure: "분석",
    list_title: "프로필 목록",
    new_profile: "프로필 추가",
    enter_profile: "분석 열기",
    edit_profile: "수정",
    delete_profile: "삭제",
    owner: "소유자",
    empty: "프로필 없음",
    logout_button: "로그아웃",
    editor_new: "프로필 추가",
    editor_edit: "프로필 수정",
    cancel: "취소",
    display_name: "이름 / 제목",
    calendar: "달력",
    birth_year: "출생 연도",
    birth_month: "출생 월",
    birth_day: "출생 일",
    birth_hour: "출생 시",
    birth_minute: "출생 분",
    profile_status_label: "상태",
    save_profile: "저장",
    saved: "저장됨",
    deleted: "삭제됨",
    delete_confirm: "이 프로필을 삭제할까요?",
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
};

const loadMe = async () => {
  const result = await requestJson("/api/v20/auth/me");
  const session = result.session || {};
  document.body.dataset.role = session.role || params.get("role") || "user";
  document.body.dataset.ownerId = session.user_id || "";
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
  const result = await requestJson("/api/v20/profiles?limit=120");
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
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "mini-action secondary";
    edit.textContent = text.edit_profile;
    edit.addEventListener("click", () => openProfileEditor(profile));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "mini-action danger";
    remove.textContent = text.delete_profile;
    remove.addEventListener("click", () => deleteProfile(profile));
    actions.append(link, edit, remove);
    card.append(actions);

    profileList.append(card);
  });
};

const openProfileEditor = (profile = {}) => {
  state.editingProfileId = profile.profile_id || "";
  const birth = profile.birth_input || {};
  editor.hidden = false;
  editorTitle.textContent = state.editingProfileId ? currentText().editor_edit : currentText().editor_new;
  setValue("#profileDisplayName", profile.display_name || "");
  setValue("#profileCalendar", birth.calendar_type || birth.calendar || "solar");
  setValue("#profileBirthYear", birth.year || "");
  setValue("#profileBirthMonth", birth.month || "");
  setValue("#profileBirthDay", birth.day || "");
  setValue("#profileBirthHour", birth.hour ?? "");
  setValue("#profileBirthMinute", birth.minute ?? "0");
  setValue("#profileRecordStatus", profile.status || "active");
  editor.scrollIntoView({ behavior: "smooth", block: "start" });
};

const closeProfileEditor = () => {
  state.editingProfileId = "";
  editor.hidden = true;
};

const saveProfile = async () => {
  const payload = profilePayloadFromEditor();
  const profileId = state.editingProfileId;
  const result = await requestJson(profileId ? `/api/v20/profiles/${encodeURIComponent(profileId)}` : "/api/v20/profiles", {
    method: profileId ? "PATCH" : "POST",
    body: JSON.stringify(payload),
  });
  setText("#profileStatus", `${currentText().saved} · ${result.status}`);
  closeProfileEditor();
  await loadProfiles();
};

const deleteProfile = async (profile) => {
  if (!window.confirm(currentText().delete_confirm)) return;
  const result = await requestJson(`/api/v20/profiles/${encodeURIComponent(profile.profile_id || "")}`, { method: "DELETE" });
  setText("#profileStatus", `${currentText().deleted} · ${result.status}`);
  await loadProfiles();
};

const profilePayloadFromEditor = () => ({
  display_name: value("#profileDisplayName") || "未命名档案",
  status: value("#profileRecordStatus") || "active",
  birth_input: {
    calendar_type: value("#profileCalendar") || "solar",
    year: numberOrString("#profileBirthYear"),
    month: numberOrString("#profileBirthMonth"),
    day: numberOrString("#profileBirthDay"),
    hour: numberOrString("#profileBirthHour"),
    minute: numberOrString("#profileBirthMinute") || 0,
  },
  metadata: { source_system: "v20_native" },
});

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

const profileMeta = (profile) => {
  const birth = profile.birth_input || {};
  const date = [birth.year, String(birth.month || "").padStart(2, "0"), String(birth.day || "").padStart(2, "0")]
    .filter((next) => next && next !== "00")
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

const value = (selector) => String(document.querySelector(selector)?.value || "").trim();
const setValue = (selector, next) => {
  const node = document.querySelector(selector);
  if (node) node.value = next;
};
const numberOrString = (selector) => {
  const raw = value(selector);
  if (raw === "") return "";
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : raw;
};

const currentText = () => PROFILE_TEXT[localeSelect.value] || PROFILE_TEXT.zh;
const measurementRole = (role) => (role === "user" ? "user" : role === "admin" ? "admin" : "analyst");

localeSelect.value = params.get("locale") || localStorage.getItem("v20_locale") || "zh";
applyLocale(localeSelect.value);
newProfileButton.addEventListener("click", () => openProfileEditor());
cancelProfileEdit.addEventListener("click", closeProfileEditor);
saveProfileButton.addEventListener("click", () => saveProfile().catch((error) => setText("#profileStatus", error.message)));
logoutButton?.addEventListener("click", () => logout().catch((error) => setText("#profileStatus", error.message)));
loadMe().catch((error) => setText("#profileRuntimeStatus", error.message));
loadProfiles().catch((error) => setText("#profileStatus", error.message));
