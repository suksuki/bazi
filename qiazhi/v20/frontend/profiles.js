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
    nav_entry: "入口",
    nav_profiles: "档案",
    nav_measure: "测算",
    list_title: "档案列表",
    new_profile: "新增档案",
    enter_profile: "进入测算",
    edit_profile: "修改",
    delete_profile: "删除",
    empty: "暂无档案",
    logout_button: "登出",
    editor_new: "新增档案",
    editor_edit: "修改档案",
    cancel: "取消",
    display_name: "姓名/标题",
    gender: "性别",
    calendar: "历法",
    lunar_leap_month: "农历闰月",
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
    unnamed_profile: "未命名档案",
    not_authenticated: "未登录",
    local_user: "本地用户",
    ready: "就绪",
    gender_male: "男",
    gender_female: "女",
    calendar_solar: "公历",
    calendar_lunar: "农历",
    status_active: "启用",
    status_archived: "归档",
  },
  en: {
    app_title: "Bazi Profiles",
    nav_entry: "Entry",
    nav_profiles: "Profiles",
    nav_measure: "Reading",
    list_title: "Profile List",
    new_profile: "New Profile",
    enter_profile: "Open Reading",
    edit_profile: "Edit",
    delete_profile: "Delete",
    empty: "No profiles",
    logout_button: "Log Out",
    editor_new: "New Profile",
    editor_edit: "Edit Profile",
    cancel: "Cancel",
    display_name: "Name / Title",
    gender: "Gender",
    calendar: "Calendar",
    lunar_leap_month: "Lunar Leap Month",
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
    unnamed_profile: "Untitled Profile",
    not_authenticated: "Not authenticated",
    local_user: "Local User",
    ready: "Ready",
    gender_male: "Male",
    gender_female: "Female",
    calendar_solar: "Solar",
    calendar_lunar: "Lunar",
    status_active: "Active",
    status_archived: "Archived",
  },
  ko: {
    app_title: "사주 프로필",
    nav_entry: "입구",
    nav_profiles: "프로필",
    nav_measure: "분석",
    list_title: "프로필 목록",
    new_profile: "프로필 추가",
    enter_profile: "분석 열기",
    edit_profile: "수정",
    delete_profile: "삭제",
    empty: "프로필 없음",
    logout_button: "로그아웃",
    editor_new: "프로필 추가",
    editor_edit: "프로필 수정",
    cancel: "취소",
    display_name: "이름 / 제목",
    gender: "성별",
    calendar: "달력",
    lunar_leap_month: "음력 윤달",
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
    unnamed_profile: "이름 없는 프로필",
    not_authenticated: "로그인되지 않음",
    local_user: "로컬 사용자",
    ready: "준비됨",
    gender_male: "남성",
    gender_female: "여성",
    calendar_solar: "양력",
    calendar_lunar: "음력",
    status_active: "사용",
    status_archived: "보관",
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
  document.querySelectorAll("[data-profile-option]").forEach((node) => {
    const value = text[node.dataset.profileOption];
    if (value) node.textContent = value;
  });
  localStorage.setItem("v20_locale", clean);
};

const populateBirthSelects = (preset = {}) => {
  const year = preset.year ?? value("#profileBirthYear");
  const month = preset.month ?? value("#profileBirthMonth");
  const day = preset.day ?? value("#profileBirthDay");
  const hour = preset.hour ?? value("#profileBirthHour");
  const minute = preset.minute ?? value("#profileBirthMinute") ?? "0";
  const currentYear = Math.max(1900, new Date().getFullYear());
  fillNumberSelect("#profileBirthYear", 1900, currentYear, year);
  fillNumberSelect("#profileBirthMonth", 1, 12, month, { pad: true });
  updateBirthDayOptions(day);
  fillNumberSelect("#profileBirthHour", 0, 23, hour, { pad: true, includeEmpty: false });
  fillNumberSelect("#profileBirthMinute", 0, 59, minute, { pad: true, includeEmpty: false });
};

const fillNumberSelect = (selector, start, end, selected, options = {}) => {
  const node = document.querySelector(selector);
  if (!node) return;
  const selectedText = selected === undefined || selected === null ? "" : String(selected);
  const selectedNumber = Number(selectedText);
  const fragment = document.createDocumentFragment();
  if (options.includeEmpty !== false) {
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "--";
    fragment.append(empty);
  }
  for (let next = start; next <= end; next += 1) {
    const option = document.createElement("option");
    option.value = String(next);
    option.textContent = options.pad ? String(next).padStart(2, "0") : String(next);
    fragment.append(option);
  }
  node.replaceChildren(fragment);
  if (Number.isFinite(selectedNumber) && selectedNumber >= start && selectedNumber <= end) {
    node.value = String(selectedNumber);
  } else if (options.includeEmpty === false) {
    node.value = String(start);
  } else {
    node.value = "";
  }
};

const updateBirthDayOptions = (selectedDay = value("#profileBirthDay")) => {
  const calendar = value("#profileCalendar") || "solar";
  const year = Number(value("#profileBirthYear"));
  const month = Number(value("#profileBirthMonth"));
  const solarDayCount = Number.isFinite(year) && Number.isFinite(month) && month >= 1 ? new Date(year, month, 0).getDate() : 31;
  const maxDay = calendar === "lunar" ? 30 : solarDayCount;
  fillNumberSelect("#profileBirthDay", 1, maxDay, selectedDay, { pad: true });
};

const toggleLunarLeapMonth = () => {
  const row = document.querySelector("#profileLunarLeapMonthRow");
  const checkbox = document.querySelector("#profileLunarLeapMonth");
  const isLunar = value("#profileCalendar") === "lunar";
  if (row) row.hidden = !isLunar;
  if (checkbox) {
    checkbox.disabled = !isLunar;
    if (!isLunar) checkbox.checked = false;
  }
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
  setText("#profileRuntimeStatus", result.authenticated ? `${session.username || currentText().local_user} · ${roleLabel(session.role || "user")}` : currentText().not_authenticated);
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
  setText("#profileStatus", result.status || currentText().ready);
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
    title.textContent = profile.display_name || profile.profile_id || currentText().unnamed_profile;
    card.append(title);

    const meta = document.createElement("p");
    meta.textContent = profileMeta(profile);
    card.append(meta);

    const tags = document.createElement("div");
    tags.className = "profile-tag-row";
    tags.append(tag(profile.status === "archived" ? text.status_archived : text.status_active));
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
  setValue("#profileGender", birth.gender === "female" ? "female" : "male");
  setValue("#profileCalendar", birth.calendar_type || birth.calendar || "solar");
  populateBirthSelects({
    year: birth.year || 1990,
    month: birth.month || 1,
    day: birth.day || 1,
    hour: birth.hour ?? 0,
    minute: birth.minute ?? 0,
  });
  setChecked("#profileLunarLeapMonth", Boolean(birth.lunar_is_leap_month || birth.is_lunar_leap_month));
  toggleLunarLeapMonth();
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
  display_name: value("#profileDisplayName") || currentText().unnamed_profile,
  status: value("#profileRecordStatus") || "active",
  birth_input: {
    calendar: value("#profileCalendar") || "solar",
    calendar_type: value("#profileCalendar") || "solar",
    gender: value("#profileGender") === "female" ? "female" : "male",
    year: numberOrString("#profileBirthYear"),
    month: numberOrString("#profileBirthMonth"),
    day: numberOrString("#profileBirthDay"),
    hour: numberOrString("#profileBirthHour"),
    minute: numberOrString("#profileBirthMinute") || 0,
    lunar_is_leap_month: value("#profileCalendar") === "lunar" && checked("#profileLunarLeapMonth"),
  },
  metadata: { source_system: "v20_native" },
});

const measureUrl = (profile) => {
  const query = new URLSearchParams({
    role: measurementRole(params.get("role") || document.body.dataset.role),
    locale: localeSelect.value,
    calendar: profile.birth_input?.calendar || profile.birth_input?.calendar_type || "solar",
    lunar_is_leap: profile.birth_input?.lunar_is_leap_month || profile.birth_input?.is_lunar_leap_month || profile.birth_input?.lunar_is_leap || false,
    gender: profile.birth_input?.gender || "male",
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
  const text = currentText();
  const calendarLabel = calendar === "lunar" ? `${text.calendar_lunar}${birth.lunar_is_leap_month ? ` · ${text.lunar_leap_month}` : ""}` : calendar === "solar" ? text.calendar_solar : calendar;
  const gender = birth.gender === "female" ? text.gender_female : birth.gender === "male" ? text.gender_male : "";
  return [date, time, calendarLabel, gender].filter(Boolean).join(" · ");
};

const tag = (text) => {
  const node = document.createElement("span");
  node.className = "tag";
  node.textContent = text;
  return node;
};

const value = (selector) => String(document.querySelector(selector)?.value || "").trim();
const checked = (selector) => Boolean(document.querySelector(selector)?.checked);
const setValue = (selector, next) => {
  const node = document.querySelector(selector);
  if (node) node.value = next;
};
const setChecked = (selector, next) => {
  const node = document.querySelector(selector);
  if (node) node.checked = Boolean(next);
};
const numberOrString = (selector) => {
  const raw = value(selector);
  if (raw === "") return "";
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : raw;
};

const currentText = () => PROFILE_TEXT[localeSelect.value] || PROFILE_TEXT.zh;
const measurementRole = (role) => (role === "user" ? "user" : role === "admin" ? "admin" : "analyst");
const roleLabel = (role) => {
  const labels = {
    zh: { user: "普通用户", analyst: "命理师", admin: "管理员" },
    en: { user: "Regular User", analyst: "Practitioner", admin: "Admin" },
    ko: { user: "일반 사용자", analyst: "명리사", admin: "관리자" },
  };
  const lang = PROFILE_TEXT[localeSelect.value] ? localeSelect.value : "zh";
  return labels[lang][role] || role;
};

localeSelect.value = params.get("locale") || localStorage.getItem("v20_locale") || "zh";
applyLocale(localeSelect.value);
populateBirthSelects();
toggleLunarLeapMonth();
document.querySelector("#profileCalendar")?.addEventListener("change", () => {
  updateBirthDayOptions();
  toggleLunarLeapMonth();
});
document.querySelector("#profileBirthYear")?.addEventListener("change", () => updateBirthDayOptions());
document.querySelector("#profileBirthMonth")?.addEventListener("change", () => updateBirthDayOptions());
newProfileButton.addEventListener("click", () => openProfileEditor());
cancelProfileEdit.addEventListener("click", closeProfileEditor);
saveProfileButton.addEventListener("click", () => saveProfile().catch((error) => setText("#profileStatus", error.message)));
logoutButton?.addEventListener("click", () => logout().catch((error) => setText("#profileStatus", error.message)));
loadMe().catch((error) => setText("#profileRuntimeStatus", error.message));
loadProfiles().catch((error) => setText("#profileStatus", error.message));
