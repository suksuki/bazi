const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(window.location.search);
let locale = localStorage.getItem("v19_oracle_locale") || params.get("locale") || "zh";
let labels = {};
let draftBirth = null;
let draftStructure = null;
let activeProfile = null;
let editingProfile = null;

boot();

async function boot() {
  await loadLabels(locale);
  renderLabels();
  initInputs();
  bindEvents();
  await loadProfiles();
}

async function loadLabels(nextLocale) {
  const clean = ["zh", "en", "ko"].includes(nextLocale) ? nextLocale : "zh";
  const result = await fetch(`/api/labels?locale=${encodeURIComponent(clean)}`).then((response) => response.json());
  locale = result.locale || clean;
  labels = result.terms || {};
}

function renderLabels() {
  document.documentElement.lang = locale === "zh" ? "zh-CN" : locale;
  document.title = t("profile_list");
  document.querySelectorAll("[data-i18n]").forEach((node) => node.textContent = t(node.dataset.i18n || ""));
  $("locale").innerHTML = ["zh", "en", "ko"].map((item) => `<option value="${item}" ${item === locale ? "selected" : ""}>${escapeHtml(t(`locale_${item}`))}</option>`).join("");
}

function bindEvents() {
  $("locale").addEventListener("change", async () => {
    locale = $("locale").value;
    localStorage.setItem("v19_oracle_locale", locale);
    await loadLabels(locale);
    renderLabels();
    await loadProfiles();
    if (draftStructure) renderConfirm(draftStructure);
    if (activeProfile) await renderTimeStep();
  });
  $("newProfile").addEventListener("click", () => startNewProfile());
  $("birthBack").addEventListener("click", () => showStep("listStep"));
  $("birthNext").addEventListener("click", nextBirth);
  $("confirmBack").addEventListener("click", () => showStep("birthStep"));
  $("confirmChart").addEventListener("click", confirmChart);
  $("timeBack").addEventListener("click", () => showStep("confirmStep"));
  $("enterAnalysis").addEventListener("click", () => {
    if (!activeProfile) return;
    window.location.href = `/oracle?profile_id=${encodeURIComponent(activeProfile.id)}&year=${encodeURIComponent($("flowYear").value)}&locale=${encodeURIComponent(locale)}`;
  });
  $("flowYear").addEventListener("input", () => {
    $("flowYearRange").value = String(Math.max(1984, Math.min(2050, Number($("flowYear").value || new Date().getFullYear()))));
    renderTimeStep();
  });
  $("flowYearRange").addEventListener("input", () => {
    $("flowYear").value = $("flowYearRange").value;
    renderTimeStep();
  });
  $("calendar").addEventListener("change", () => {
    updateCalendarUi();
    updateDayOptions(Number($("day").value || 1));
  });
  ["year", "month"].forEach((id) => $(id).addEventListener("change", () => updateDayOptions(Number($("day").value || 1))));
}

function initInputs() {
  const now = new Date();
  const currentYear = now.getFullYear();
  $("year").innerHTML = rangeOptions(1900, currentYear, currentYear);
  $("month").innerHTML = rangeOptions(1, 12, now.getMonth() + 1, 2);
  $("hour").innerHTML = rangeOptions(0, 23, now.getHours(), 2);
  $("minute").innerHTML = rangeOptions(0, 59, now.getMinutes(), 2);
  updateDayOptions(now.getDate());
  $("gender").innerHTML = ["male", "female", "unknown"].map((item) => `<option value="${item}">${escapeHtml(t(item))}</option>`).join("");
  $("calendar").innerHTML = ["solar", "lunar"].map((item) => `<option value="${item}">${escapeHtml(t(item))}</option>`).join("");
  updateCalendarUi();
  updateDayOptions(now.getDate());
  $("flowYear").value = String(currentYear);
  $("flowYearRange").value = String(currentYear);
}

async function loadProfiles() {
  const response = await fetch("/api/profiles");
  if (response.status === 401) {
    window.location.href = "/";
    return;
  }
  const result = await response.json();
  renderRoleNav(result.data?.role || "guest");
  const items = result.data?.items || [];
  $("profileList").innerHTML = items.length ? items.map(profileCard).join("") : `<div class="knowledge-empty">${escapeHtml(t("new_profile"))}</div>`;
  document.querySelectorAll("[data-open-profile]").forEach((button) => button.addEventListener("click", () => {
    const profileId = button.dataset.openProfile || "";
    window.location.href = `/oracle?profile_id=${encodeURIComponent(profileId)}&locale=${encodeURIComponent(locale)}`;
  }));
  document.querySelectorAll("[data-edit-profile]").forEach((button) => button.addEventListener("click", () => {
    const profileId = button.dataset.editProfile || "";
    const profile = items.find((item) => item.id === profileId);
    if (profile) startEditProfile(profile);
  }));
  document.querySelectorAll("[data-delete-profile]").forEach((button) => button.addEventListener("click", async () => {
    const profileId = button.dataset.deleteProfile || "";
    const profile = items.find((item) => item.id === profileId);
    if (!profile || !window.confirm(t("delete_profile_confirm"))) return;
    await deleteProfile(profileId);
  }));
}

function renderRoleNav(role) {
  const links = [];
  if (role === "admin") {
    links.push(`<a class="nav-link" href="/admin">治理台</a>`);
    links.push(`<a class="nav-link" href="/lab">分析台</a>`);
  } else if (role === "practitioner") {
    links.push(`<a class="nav-link" href="/lab">分析台</a>`);
  }
  links.push(`<a class="nav-link subtle" href="/">入口</a>`);
  $("roleNav").innerHTML = links.join("");
}

function profileCard(profile) {
  const birth = profile.birth_input || {};
  const calendarNote = birth.calendar_type === "lunar"
    ? `${t("lunar")}${birth.lunar_is_leap_month ? ` · ${t("lunar_leap_month")}` : ""}`
    : t("solar");
  return `<article class="profile-card">
    <h3>${escapeHtml(profile.name || "")}</h3>
    <p>${escapeHtml([birth.year, birth.month, birth.day].filter(Boolean).join("-"))} · ${escapeHtml(String(birth.hour ?? ""))}:${escapeHtml(String(birth.minute ?? 0).padStart(2, "0"))} · ${escapeHtml(calendarNote)}</p>
    <div class="profile-card-actions">
      <button type="button" data-open-profile="${escapeHtml(profile.id)}">${escapeHtml(t("enter_existing_profile"))}</button>
      <button type="button" class="secondary" data-edit-profile="${escapeHtml(profile.id)}">${escapeHtml(t("edit_profile"))}</button>
      <button type="button" class="secondary danger" data-delete-profile="${escapeHtml(profile.id)}">${escapeHtml(t("delete_profile"))}</button>
    </div>
  </article>`;
}

function startNewProfile() {
  editingProfile = null;
  activeProfile = null;
  draftBirth = null;
  $("profileName").value = "";
  showStep("birthStep");
}

function startEditProfile(profile) {
  editingProfile = profile;
  activeProfile = profile;
  $("profileName").value = profile.name || "";
  writeBirth(profile.birth_input || {});
  showStep("birthStep");
}

async function nextBirth() {
  draftBirth = readBirth();
  const result = await structurePreview(draftBirth, Number($("flowYear").value || new Date().getFullYear()));
  if (!result) return;
  draftStructure = result;
  renderConfirm(result);
  showStep("confirmStep");
}

async function confirmChart() {
  const url = editingProfile ? `/api/profiles/${encodeURIComponent(editingProfile.id)}` : "/api/profiles";
  const response = await fetch(url, {
    method: editingProfile ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: $("profileName").value || t("profile_list"), birth_input: draftBirth }),
  });
  const result = await response.json();
  activeProfile = result.data;
  editingProfile = null;
  await renderTimeStep();
  showStep("timeStep");
}

async function deleteProfile(profileId) {
  const response = await fetch(`/api/profiles/${encodeURIComponent(profileId)}`, {
    method: "DELETE",
  });
  const result = await response.json();
  if (!response.ok || !result.ok) {
    $("profileStatus").textContent = result.message || result.code || "delete failed";
    return;
  }
  $("profileStatus").textContent = t("delete_profile_done");
  await loadProfiles();
}

async function renderTimeStep() {
  const birth = activeProfile ? activeProfile.birth_input : draftBirth;
  if (!birth) return;
  const result = await structurePreview(birth, Number($("flowYear").value));
  if (!result) return;
  const activeLuck = (result.time_context || {}).luck_cycle;
  const flow = (result.time_context || {}).flow_year || {};
  $("timePreview").innerHTML = `<div class="time-readout"><span>${escapeHtml(t("current_luck_cycle"))}</span><strong>${escapeHtml(activeLuck?.pillar?.display || "-")}</strong><em>${activeLuck ? `${activeLuck.start_age}-${activeLuck.end_age}` : t("context_only")}</em></div><div class="time-readout"><span>${escapeHtml(t("flow_year"))}</span><strong>${escapeHtml(flow.pillar?.display || "-")}</strong><em>${escapeHtml(String(flow.year || ""))} · ${escapeHtml(t("context_only"))}</em></div>`;
}

function renderConfirm(data) {
  const pillars = data.chart?.pillars || {};
  $("confirmPillars").innerHTML = ["year", "month", "day", "hour"].map((key) => `<article class="structure-tag ${key === "day" ? "key-tag" : ""}"><span>${escapeHtml(t(key))}</span><strong>${escapeHtml(pillars[key]?.display || "-")}</strong><em>${key === "day" ? escapeHtml(t("day_master")) : escapeHtml(pillars[key]?.stem_element || "")}</em></article>`).join("");
}

async function structurePreview(birth, selectedYear) {
  $("profileStatus").textContent = "...";
  const response = await fetch("/api/agent/structure", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ birth_input: birth, selected_year: selectedYear }),
  });
  const result = await response.json();
  if (!result.ok) {
    $("profileStatus").textContent = result.message || result.code || "error";
    return null;
  }
  $("profileStatus").textContent = "";
  return result.data;
}

function readBirth() {
  const calendar = $("calendar").value;
  return {
    year: Number($("year").value), month: Number($("month").value), day: Number($("day").value), hour: Number($("hour").value), minute: Number($("minute").value), gender: $("gender").value, calendar, calendar_type: calendar, lunar_is_leap_month: calendar === "lunar" && $("lunarLeapMonth").checked,
  };
}

function writeBirth(birth) {
  if (birth.year) $("year").value = String(birth.year);
  if (birth.month) $("month").value = String(birth.month);
  updateDayOptions(Number(birth.day || 1));
  if (birth.day) $("day").value = String(birth.day);
  if (birth.hour !== undefined) $("hour").value = String(birth.hour);
  if (birth.minute !== undefined) $("minute").value = String(birth.minute);
  if (birth.gender) $("gender").value = String(birth.gender);
  const calendar = birth.calendar_type || birth.calendar;
  if (calendar) $("calendar").value = String(calendar);
  $("lunarLeapMonth").checked = Boolean(birth.lunar_is_leap_month);
  updateCalendarUi();
}

function showStep(id) {
  document.querySelectorAll(".profile-step").forEach((node) => node.classList.toggle("active", node.id === id));
}

function updateDayOptions(preferredDay) {
  const year = Number($("year").value || new Date().getFullYear());
  const month = Number($("month").value || 1);
  const maxDay = $("calendar")?.value === "lunar" ? 30 : new Date(year, month, 0).getDate();
  const day = Math.min(Math.max(Number(preferredDay || 1), 1), maxDay);
  $("day").innerHTML = rangeOptions(1, maxDay, day, 2);
}

function updateCalendarUi() {
  const isLunar = $("calendar")?.value === "lunar";
  $("lunarLeapMonth").disabled = !isLunar;
  if (!isLunar) $("lunarLeapMonth").checked = false;
}

function rangeOptions(start, end, selected, padLength = 0) {
  const rows = [];
  for (let value = start; value <= end; value += 1) {
    const label = padLength ? String(value).padStart(padLength, "0") : String(value);
    rows.push(`<option value="${value}" ${value === Number(selected) ? "selected" : ""}>${label}</option>`);
  }
  return rows.join("");
}

function t(key) { if (labels[key] && labels[key].label) return labels[key].label; console.warn(`Missing V19 label: ${key}`); return key; }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"})[char]); }
