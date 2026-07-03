const app = document.querySelector("#app");
const statusEl = document.querySelector("#status");
const systemMenuEl = document.querySelector("[data-system-menu]");
const systemLabelEl = document.querySelector("[data-system-label]");
const systemAuthEl = document.querySelector("[data-system-auth]");
const systemLogoutEl = document.querySelector("[data-system-logout]");
const PRODUCT_SESSION_KEY = "v30.product.session";
const PRODUCT_UI_PREFS_KEY = "v30.product.ui_prefs";
const STAGE_SUMMARY_STREAM_TIMEOUT_MS = 180000;
const MAIN_SYSTEM_ROLE_KEYS = ["guest", "user", "practitioner"];

let currentView = null;
let currentThinking = null;
let interactionNotice = null;
let readingHistory = null;
let historyNotice = "";
let hiddenFactorNotice = "";
let currentInteractionState = null;
let currentPractitionerState = null;
let answerTypewriter = {
  key: "",
  fullText: "",
  visibleText: "",
  active: false,
  timer: null,
};
let answerSubmissionState = {
  active: false,
  token: "",
  questionId: "",
};
let stageTypewriter = {
  key: "",
  fullText: "",
  visibleText: "",
  active: false,
  timer: null,
};
let stageSummaryEnhancementState = {};
let stageThinkingStreamText = {};
let stageThinkingRenderTimer = null;
let stageSummaryReadingId = "";
let dialogueChainState = {
  readingId: "",
  open: false,
  loaded: false,
  loading: false,
  submitting: false,
  notice: "",
  seeds: [],
  sessions: [],
  activeSession: null,
  input: "我今年财运如何？",
};
let activeReadingStep = initialReadingStep();
let productSession = loadStoredProductSession();
let productUiPrefs = loadStoredUiPrefs();
let authMode = initialAuthMode();
let productProfiles = null;
let productNotice = "";

const roleProfiles = {
  guest: { label: "游客", client: "mobile", helper: "查看命盘摘要和可继续追问的方向。" },
  user: { label: "普通用户", client: "web", helper: "排盘、看解读，并围绕命盘连续追问。" },
  practitioner: { label: "命理师", client: "web", helper: "查看命盘证据、结构路径和复核要点。" },
};

function normalizeMainSystemRole(role) {
  const key = String(role || "user");
  return MAIN_SYSTEM_ROLE_KEYS.includes(key) ? key : "user";
}

function mainSystemRoleProfile(role) {
  return roleProfiles[normalizeMainSystemRole(role)] || roleProfiles.user;
}

function productRoleLabel(role) {
  return mainSystemRoleProfile(role).label;
}

function productRoleHelper(role) {
  return mainSystemRoleProfile(role).helper;
}

function isPractitionerLikeRole(role = formState.role) {
  return String(role || "") === "practitioner";
}

function detectClient() {
  return window.matchMedia("(max-width: 760px)").matches ? "mobile" : "web";
}

function setStatus(value) {
  if (!statusEl) return;
  const labels = {
    calculating: "测算中",
    db: "数据库",
    error: "异常",
    history: "历史",
    "hidden-factor": "校准中",
    llm: "大模型",
    "llm-test": "大模型",
    login: "登录中",
    opening: "打开中",
    partial: "部分完成",
    profile: "保存中",
    profiles: "档案",
    reading: "读取中",
    ready: "就绪",
    redis: "缓存",
    refreshing: "刷新中",
    register: "注册中",
    runtime: "运行",
    schema: "建表",
    updating: "生成中",
  };
  statusEl.textContent = labels[value] || value || "就绪";
}

function initialRole() {
  const params = new URLSearchParams(window.location.search);
  const role = params.get("role") || "user";
  return normalizeMainSystemRole(role);
}

function initialState() {
  const role = initialRole();
  const session = productSession?.session || {};
  const user = productSession?.user || {};
  const locale = productUiPrefs.locale || "zh";
  const mainRole = normalizeMainSystemRole(user.main_system_role || user.role || role);
  const profile = mainSystemRoleProfile(mainRole);
  return {
    readingId: `v30-reading-${Date.now()}`,
    role: mainRole,
    locale,
    client: profile.client === "web" ? detectClient() : profile.client,
    actorId: session.actor_id || "guest-demo",
    sessionId: session.session_id || `session-${Date.now()}`,
    profileName: user.display_name || "当前命盘",
    calendarType: "solar",
    birthDate: "1990-02-04",
    birthTime: "23:30",
    timezone: "Asia/Shanghai",
    birthPlace: "北京",
    gender: "female",
    targetYear: new Date().getFullYear(),
    lunarIsLeapMonth: false,
    useTrueSolarTime: false,
    unknownHour: false,
  };
}

let formState = initialState();

function pad2(value) {
  return String(value).padStart(2, "0");
}

function parseBirthDate(value) {
  const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const now = new Date();
  return {
    year: match ? Number(match[1]) : 1990,
    month: match ? Number(match[2]) : 1,
    day: match ? Number(match[3]) : 1,
    currentYear: now.getFullYear(),
  };
}

function parseBirthTime(value) {
  const match = String(value || "").match(/^(\d{2}):(\d{2})$/);
  return {
    hour: match ? Number(match[1]) : 0,
    minute: match ? Number(match[2]) : 0,
  };
}

function daysInMonth(year, month) {
  return new Date(Number(year), Number(month), 0).getDate();
}

function renderOptions(start, end, selected, formatter = (value) => String(value)) {
  const rows = [];
  for (let value = start; value <= end; value += 1) {
    rows.push(`<option value="${value}"${Number(selected) === value ? " selected" : ""}>${escapeHtml(formatter(value))}</option>`);
  }
  return rows.join("");
}

function renderBirthDateSelects(value) {
  const parsed = parseBirthDate(value);
  const maxDay = daysInMonth(parsed.year, parsed.month);
  const selectedDay = Math.min(parsed.day, maxDay);
  return `
    <div class="birth-select-grid birth-date-selects" data-birth-date-selects>
      <label>年
        <select name="birthYear" data-birth-year>
          ${renderOptions(1900, parsed.currentYear, parsed.year)}
        </select>
      </label>
      <label>月
        <select name="birthMonth" data-birth-month>
          ${renderOptions(1, 12, parsed.month, (value) => `${value}月`)}
        </select>
      </label>
      <label>日
        <select name="birthDay" data-birth-day>
          ${renderOptions(1, maxDay, selectedDay, (value) => `${value}日`)}
        </select>
      </label>
    </div>
  `;
}

function renderBirthTimeSelects(value) {
  const parsed = parseBirthTime(value);
  return `
    <div class="birth-select-grid birth-time-selects">
      <label>时
        <select name="birthHour">
          ${renderOptions(0, 23, parsed.hour, (value) => `${pad2(value)}时`)}
        </select>
      </label>
      <label>分
        <select name="birthMinute">
          ${renderOptions(0, 59, parsed.minute, (value) => `${pad2(value)}分`)}
        </select>
      </label>
    </div>
  `;
}

function composeBirthDate(data) {
  const year = Number(data.get("birthYear") || 1990);
  const month = Number(data.get("birthMonth") || 1);
  const maxDay = daysInMonth(year, month);
  const day = Math.min(Number(data.get("birthDay") || 1), maxDay);
  return `${year}-${pad2(month)}-${pad2(day)}`;
}

function composeBirthTime(data) {
  return `${pad2(Number(data.get("birthHour") || 0))}:${pad2(Number(data.get("birthMinute") || 0))}`;
}

const STEM_ELEMENTS = {
  甲: "wood",
  乙: "wood",
  丙: "fire",
  丁: "fire",
  戊: "earth",
  己: "earth",
  庚: "metal",
  辛: "metal",
  壬: "water",
  癸: "water",
};

const STEM_POLARITY = {
  甲: "yang",
  乙: "yin",
  丙: "yang",
  丁: "yin",
  戊: "yang",
  己: "yin",
  庚: "yang",
  辛: "yin",
  壬: "yang",
  癸: "yin",
};

const ELEMENT_GENERATES = {
  wood: "fire",
  fire: "earth",
  earth: "metal",
  metal: "water",
  water: "wood",
};

const ELEMENT_CONTROLS = {
  wood: "earth",
  fire: "metal",
  earth: "water",
  metal: "wood",
  water: "fire",
};

const BRANCH_HIDDEN_STEMS = {
  子: ["癸"],
  丑: ["己", "癸", "辛"],
  寅: ["甲", "丙", "戊"],
  卯: ["乙"],
  辰: ["戊", "乙", "癸"],
  巳: ["丙", "戊", "庚"],
  午: ["丁", "己"],
  未: ["己", "丁", "乙"],
  申: ["庚", "壬", "戊"],
  酉: ["辛"],
  戌: ["戊", "辛", "丁"],
  亥: ["壬", "甲"],
};

function splitPillar(value) {
  const text = String(value || "").trim();
  return {
    stem: text.slice(0, 1),
    branch: text.slice(1, 2),
  };
}

function inferTenGod(dayMaster, targetStem) {
  if (!dayMaster || !targetStem) return "";
  if (dayMaster === targetStem) return "日主";
  const dayElement = STEM_ELEMENTS[dayMaster];
  const targetElement = STEM_ELEMENTS[targetStem];
  if (!dayElement || !targetElement) return "";
  const samePolarity = STEM_POLARITY[dayMaster] === STEM_POLARITY[targetStem];
  if (targetElement === dayElement) return samePolarity ? "比肩" : "劫财";
  if (ELEMENT_GENERATES[dayElement] === targetElement) return samePolarity ? "食神" : "伤官";
  if (ELEMENT_GENERATES[targetElement] === dayElement) return samePolarity ? "偏印" : "正印";
  if (ELEMENT_CONTROLS[dayElement] === targetElement) return samePolarity ? "偏财" : "正财";
  if (ELEMENT_CONTROLS[targetElement] === dayElement) return samePolarity ? "七杀" : "正官";
  return "";
}

function hiddenTenGodsForBranch(branch, dayMaster) {
  return (BRANCH_HIDDEN_STEMS[branch] || []).map((stem) => ({
    stem,
    ten_god: inferTenGod(dayMaster, stem),
  }));
}

function bindBirthDateSelects(root = document) {
  root.querySelectorAll("[data-birth-date-selects]").forEach((container) => {
    const yearEl = container.querySelector("[data-birth-year]");
    const monthEl = container.querySelector("[data-birth-month]");
    const dayEl = container.querySelector("[data-birth-day]");
    const syncDays = () => {
      const year = Number(yearEl?.value || 1990);
      const month = Number(monthEl?.value || 1);
      const selected = Number(dayEl?.value || 1);
      const maxDay = daysInMonth(year, month);
      if (!dayEl) return;
      dayEl.innerHTML = renderOptions(1, maxDay, Math.min(selected, maxDay), (value) => `${value}日`);
    };
    yearEl?.addEventListener("change", syncDays);
    monthEl?.addEventListener("change", syncDays);
  });
}

function renderShell() {
  renderGlobalChrome();
  if (isAuthPageRequested()) {
    renderAuthPage();
    return;
  }
  if (isProfilesPageRequested()) {
    renderProfilesPage();
    return;
  }
  app.innerHTML = `
    <section class="reading-shell">
      <aside class="profile-rail">
        ${renderUserSidebarCard()}
        ${renderProfileSidebarCard()}
        ${renderCurrentBaziSidebarCard()}
        ${renderSidebarMemoryCard()}
      </aside>
      <section class="workbench">
        ${renderReadingStepNav()}
        ${activeReadingStep === "input" ? `<section class="input-band">
          <div class="input-head">
            <div>
              <p class="eyebrow">出生信息</p>
              <h2>排四柱与建立测算上下文</h2>
            </div>
            <div class="role-brief">
              <strong>${escapeHtml(productRoleLabel(formState.role))}</strong>
              <span>${escapeHtml(productRoleHelper(formState.role))}</span>
            </div>
          </div>
          <form id="birth-form" class="birth-form">
            <fieldset>
              <legend>档案</legend>
              <label>档案名<input name="profileName" value="${escapeHtml(formState.profileName)}"></label>
            </fieldset>
            <fieldset>
              <legend>基础</legend>
              <label>性别
                <select name="gender">
                  <option value="female"${formState.gender === "female" ? " selected" : ""}>女</option>
                  <option value="male"${formState.gender === "male" ? " selected" : ""}>男</option>
                  <option value=""${formState.gender === "" ? " selected" : ""}>不填</option>
                </select>
              </label>
            </fieldset>
            <fieldset class="birth-fieldset">
              <legend>出生</legend>
              <label>历法
                <select name="calendarType">
                  <option value="solar"${formState.calendarType === "solar" ? " selected" : ""}>阳历</option>
                  <option value="lunar"${formState.calendarType === "lunar" ? " selected" : ""}>阴历</option>
                </select>
              </label>
              <div class="birth-composite-field">
                <span>出生日期</span>
                ${renderBirthDateSelects(formState.birthDate)}
              </div>
              <div class="birth-composite-field">
                <span>出生时间</span>
                ${renderBirthTimeSelects(formState.birthTime)}
              </div>
              <label>出生地<input name="birthPlace" value="${escapeHtml(formState.birthPlace)}"></label>
              <label>时区<input name="timezone" value="${escapeHtml(formState.timezone)}"></label>
              <label>流年<input name="targetYear" type="number" min="1900" max="2100" value="${formState.targetYear}"></label>
            </fieldset>
            <div class="toggle-row">
              <label class="check"><input name="lunarIsLeapMonth" type="checkbox"${formState.lunarIsLeapMonth ? " checked" : ""}>阴历闰月</label>
              <label class="check"><input name="useTrueSolarTime" type="checkbox"${formState.useTrueSolarTime ? " checked" : ""}>真太阳时</label>
              <label class="check"><input name="unknownHour" type="checkbox"${formState.unknownHour ? " checked" : ""}>时辰未知</label>
              <button type="submit">开始测算</button>
            </div>
          </form>
        </section>` : ""}
        <section id="reading" class="reading"></section>
        <section id="dialogue-chain" class="dialogue-chain"></section>
      </section>
    </section>
  `;
  document.querySelectorAll("[data-reading-step]").forEach((button) => {
    button.addEventListener("click", handleReadingStepChange);
  });
  document.querySelector("[data-load-history]")?.addEventListener("click", loadHistory);
  document.querySelector("[data-load-sidebar-profiles]")?.addEventListener("click", () => loadProductProfiles({ surface: "shell" }));
  document.querySelectorAll("[data-open-reading]").forEach((button) => {
    button.addEventListener("click", openHistoryReading);
  });
  document.querySelectorAll("[data-profile-measure]").forEach((button) => {
    button.addEventListener("click", startProfileReading);
  });
  document.querySelector("#birth-form")?.addEventListener("submit", submitBirth);
  bindBirthDateSelects(document);
  document.querySelectorAll("[data-ui-projection]").forEach((control) => {
    control.addEventListener("change", handleProjectionChange);
  });
  renderReading();
  if (productSession && !productProfiles) {
    loadProductProfiles({ surface: "shell", silent: true });
  }
}

function renderUserSidebarCard() {
  const user = productSession?.user || {};
  const roleKey = user.role || formState.role || "user";
  const displayName = user.display_name || user.username || "未登录";
  return `
    <div class="rail-card sidebar-user-card">
      <div class="sidebar-user-head">
        <span>${escapeHtml(displayName.slice(0, 1).toUpperCase() || "玄")}</span>
        <div>
          <p class="eyebrow">当前用户</p>
          <h2>${escapeHtml(displayName)}</h2>
        </div>
      </div>
      <div class="rail-meta-grid">
        <span>${escapeHtml(productRoleLabel(roleKey))}</span>
        <span>${escapeHtml(productSession ? "已登录" : "游客")}</span>
      </div>
      <div class="sidebar-actions">
        ${productSession ? `
          <a class="subtle-link" href="/v30/ui/?page=profiles">档案管理</a>
        ` : `
          <a class="subtle-link" href="/v30/ui/?page=auth">登录</a>
        `}
      </div>
    </div>
  `;
}

function renderProfileSidebarCard() {
  const profiles = Array.isArray(productProfiles?.items) ? productProfiles.items : [];
  return `
    <div class="rail-card sidebar-profile-card">
      <div class="rail-card-head">
        <div>
          <p class="eyebrow">八字档案</p>
          <strong>${productSession ? `${profiles.length} 个档案` : "登录后读取"}</strong>
        </div>
        ${productSession ? `<button type="button" class="subtle-button" data-load-sidebar-profiles>刷新</button>` : ""}
      </div>
      ${productNotice ? `<p class="history-notice">${escapeHtml(productNotice)}</p>` : ""}
      <div class="sidebar-profile-list">
        ${productSession
          ? profiles.length
            ? profiles.slice(0, 5).map(renderSidebarProfileItem).join("")
            : `<div class="history-empty">暂无档案。可以进入档案管理先保存出生资料。</div>`
          : `<div class="history-empty">请先登录，再同步或保存八字档案。</div>`}
      </div>
      <div class="sidebar-actions">
        <a class="subtle-link" href="/v30/ui/?page=profiles">管理档案</a>
        <button type="button" class="subtle-button" data-load-history>历史测算</button>
      </div>
      ${historyNotice ? `<p class="history-notice">${escapeHtml(historyNotice)}</p>` : ""}
    </div>
  `;
}

function renderSidebarProfileItem(profile) {
  const genderMark = formatProfileGenderMark(profile);
  const displayName = profile.display_name || "未命名档案";
  const isActive = displayName === formState.profileName;
  const baziPreview = sidebarProfileBaziPreviewText(profile);
  return `
    <article class="sidebar-profile-item ${isActive ? "active" : ""}">
      <button type="button" data-profile-measure="${escapeHtml(profile.profile_id)}" ${isActive ? 'aria-current="true"' : ""}>
        <span class="sidebar-profile-title">
          <strong>${escapeHtml(displayName)}</strong>
          ${genderMark ? `<em title="${escapeHtml(genderMark === "乾" ? "乾 · 男命" : "坤 · 女命")}">${escapeHtml(genderMark)}</em>` : ""}
        </span>
        <span class="sidebar-profile-hover-preview" aria-hidden="true">${escapeHtml(baziPreview)}</span>
      </button>
    </article>
  `;
}

function formatProfileGenderMark(profile) {
  const gender = String(profile.birth_input?.gender || "");
  if (gender === "male") return "乾";
  if (gender === "female") return "坤";
  return "";
}

function sidebarProfileBaziPreviewText(profile) {
  const preview = profile.bazi_preview || {};
  const display = String(preview.display || "").trim();
  const previewPillars = Array.isArray(preview.pillar_labels)
    ? preview.pillar_labels.map((row) => String(row.pillar || "").trim()).filter(Boolean)
    : [];
  const pillars = previewPillars.length ? previewPillars : display.split(/\s+/).filter(Boolean);
  if (pillars.length) return `八字 ${pillars.slice(0, 4).join(" ")}`;
  const status = String(preview.status || "");
  const failures = Array.isArray(preview.failures) ? preview.failures.map(String) : [];
  if (status === "pending" || failures.includes("unknown_hour_blocks_hour_pillar")) return "八字 时辰待补";
  return "八字 待排";
}

function renderCurrentBaziSidebarCard() {
  const surface = currentView?.reading_surface || {};
  const core = surface.core_bazi_reading || {};
  const time = surface.time_context || {};
  const pillars = Array.isArray(core.four_pillars) ? core.four_pillars : Array.isArray(core.pillars) ? core.pillars : [];
  return `
    <div class="rail-card sidebar-bazi-card">
      <p class="eyebrow">当前测算八字</p>
      <h2>${escapeHtml(formState.profileName || "当前命盘")}</h2>
      <div class="sidebar-pillars">
        ${pillars.length ? pillars.map((row) => `
          <span>
            <em>${escapeHtml(row.label || row.layer || "")}</em>
            <strong>${escapeHtml(row.pillar || "-")}</strong>
          </span>
        `).join("") : `
          <span><em>年</em><strong>待排</strong></span>
          <span><em>月</em><strong>待排</strong></span>
          <span><em>日</em><strong>待排</strong></span>
          <span><em>时</em><strong>待排</strong></span>
        `}
      </div>
      <div class="rail-meta-grid">
        <span>日主：${escapeHtml(core.day_master || "-")}</span>
        <span>流年：${escapeHtml(time.flow_year_pillar || formState.targetYear || "-")}</span>
        <span>大运：${escapeHtml(time.current_luck?.pillar || "待确认")}</span>
        <span>${escapeHtml(formState.calendarType === "lunar" ? "阴历" : "阳历")}</span>
      </div>
    </div>
  `;
}

function renderSidebarMemoryCard() {
  if (!currentView || !currentThinking?.sidebar_memory) return "";
  const items = visibleSidebarMemoryItems();
  const total = Array.isArray(currentThinking.sidebar_memory.items) ? currentThinking.sidebar_memory.items.length : 0;
  return `
    <div class="rail-card sidebar-memory-card">
      <div class="rail-card-head">
        <div>
          <p class="eyebrow">测算记忆</p>
          <strong>${items.length ? `${items.length}/${total} 个关键点` : "逐步生成"}</strong>
        </div>
      </div>
      <div class="sidebar-memory-list">
        ${items.length ? items.map(renderSidebarMemoryItem).join("") : `<p class="history-empty">进入分析后，规则、特征、画像、路径和用神取舍会逐步沉淀到这里。</p>`}
      </div>
    </div>
  `;
}

function visibleSidebarMemoryItems() {
  const memory = currentThinking?.sidebar_memory || {};
  const rows = Array.isArray(memory.items) ? memory.items : [];
  if (!rows.length) return [];
  const activeStage = activeSidebarStageId();
  const activeIndex = sidebarStageIndex(activeStage);
  if (activeStage === "final") return rows;
  return rows.filter((row) => {
    const visibilityStage = String(row.visibility_stage || row.stage_id || "");
    const index = sidebarStageIndex(visibilityStage);
    return index >= 0 && index <= activeIndex;
  });
}

function activeSidebarStageId() {
  const stage = currentAnalysisStage();
  const materialIds = Array.isArray(stage?.material_stage_ids) ? stage.material_stage_ids : [];
  if (materialIds.length) return String(materialIds[materialIds.length - 1] || "");
  if (activeReadingStep.startsWith("stage:")) return activeReadingStep.slice("stage:".length);
  const first = thinkingMaterialRows()[0] || thinkingJourneyRows()[0] || null;
  return String(first?.step_id || "");
}

function sidebarStageIndex(stageId) {
  const rows = thinkingMaterialRows();
  const index = rows.findIndex((step) => step?.step_id === stageId);
  if (index >= 0) return index;
  const journeyRows = thinkingJourneyRows();
  const journeyIndex = journeyRows.findIndex((step) => step?.step_id === stageId);
  if (journeyIndex >= 0) {
    const materialIds = Array.isArray(journeyRows[journeyIndex]?.material_stage_ids) ? journeyRows[journeyIndex].material_stage_ids : [];
    const lastMaterial = materialIds.length ? String(materialIds[materialIds.length - 1] || "") : "";
    const materialIndex = rows.findIndex((step) => step?.step_id === lastMaterial);
    if (materialIndex >= 0) return materialIndex;
  }
  if (stageId === "final") return rows.length + 1;
  return -1;
}

function thinkingJourneyRows() {
  if (Array.isArray(currentThinking?.journey_steps) && currentThinking.journey_steps.length) {
    return currentThinking.journey_steps;
  }
  return Array.isArray(currentThinking?.steps) ? currentThinking.steps : [];
}

function thinkingMaterialRows() {
  return Array.isArray(currentThinking?.steps) ? currentThinking.steps : [];
}

function renderSidebarMemoryItem(item) {
  const chips = Array.isArray(item.chips) ? item.chips : [];
  const evidence = Array.isArray(item.evidence) ? item.evidence : [];
  const counter = Array.isArray(item.counter_evidence) ? item.counter_evidence : [];
  return `
    <article class="sidebar-memory-item ${escapeHtml(item.kind || "")} ${escapeHtml(item.confidence_band || "low")}">
      <span>${escapeHtml(item.label || "关键点")}</span>
      <strong>${escapeHtml(item.value || "-")}</strong>
      ${item.detail ? `<p>${escapeHtml(item.detail)}</p>` : ""}
      ${chips.length ? `<div class="sidebar-memory-chips">${chips.slice(0, 4).map((chip) => `<em>${escapeHtml(chip)}</em>`).join("")}</div>` : ""}
      ${evidence.length || counter.length ? `
        <small>${escapeHtml([evidence[0], counter[0]].filter(Boolean).join(" · "))}</small>
      ` : ""}
    </article>
  `;
}

function renderSidebarJourneyNav() {
  const steps = analysisJourneySteps();
  const activeKey = normalizeActiveJourneyStep(steps);
  const canNavigate = Boolean(currentView && currentThinking);
  return `
    <nav class="rail-card sidebar-journey-card" aria-label="测算步骤">
      <div class="rail-card-head">
        <div>
          <p class="eyebrow">测算流程</p>
          <strong>${currentView ? "逐步分析中" : "等待排盘"}</strong>
        </div>
      </div>
      <div class="sidebar-step-list">
        ${steps.map((step, index) => `
          <button type="button" class="${step.key === activeKey ? "active" : ""}" data-reading-step="${escapeHtml(step.key)}"${!canNavigate && step.key !== "input" ? " disabled" : ""}>
            <span>${escapeHtml(index === 0 ? "准备" : String(index).padStart(2, "0"))}</span>
            <strong>${escapeHtml(step.label)}</strong>
          </button>
        `).join("")}
      </div>
    </nav>
  `;
}

function initialReadingStep() {
  const params = new URLSearchParams(window.location.search);
  const step = params.get("step") || "input";
  if (step === "input" || step.startsWith("stage:")) return step;
  return "input";
}

function renderReadingStepNav() {
  const steps = analysisJourneySteps();
  const activeKey = normalizeActiveJourneyStep(steps);
  const index = Math.max(0, steps.findIndex((step) => step.key === activeKey));
  const current = steps[index] || steps[0];
  const previous = steps[index - 1] || null;
  const next = steps[index + 1] || null;
  const canNavigate = Boolean(currentView && currentThinking);
  const analysisTotal = Math.max(1, steps.length - 1);
  const displayIndex = current.key === "input" ? 0 : Math.max(1, index);
  const progress = current.key === "input"
    ? 0
    : Math.round((displayIndex / analysisTotal) * 100);
  const stepLabel = current.key === "input" ? "准备" : `${displayIndex}/${analysisTotal}`;
  const previousLabel = previous ? (index === 1 ? "资料" : "上一步") : "";
  const nextLabel = next ? (current.key === "input" ? "开始" : "下一步") : "";
  const showStepActions = Boolean(previous || next);
  return `
    <nav class="reading-stepper" aria-label="八字测算导航">
      <div class="step-current">
        <span>${escapeHtml(stepLabel)}</span>
        <strong>${escapeHtml(current.label)}</strong>
        <em>${escapeHtml(current.key === "input" ? current.helper() : compactStageHint(current, displayIndex, analysisTotal))}</em>
      </div>
      <div class="step-progress" aria-hidden="true">
        <i style="width:${progress}%"></i>
      </div>
      ${showStepActions ? `<div class="step-actions">
        ${previous ? `
          <button type="button" class="subtle-button" data-reading-step="${previous.key}"${!canNavigate && previous.key !== "input" ? " disabled" : ""}>
            ${escapeHtml(previousLabel)}
          </button>
        ` : ""}
        ${next ? `
          <button type="button" data-reading-step="${next.key}"${!canNavigate ? " disabled" : ""}>
            ${escapeHtml(nextLabel)}
          </button>
        ` : ""}
      </div>` : ""}
    </nav>
  `;
}

function compactStageHint(current, displayIndex, total) {
  return "核心结论和建议";
}

function analysisJourneySteps() {
  const inputStep = {
    key: "input",
    label: "填写出生资料",
    helper: () => currentView ? "资料已生成测算，可以回到这里修改后重新排盘。" : "先填写出生信息，再逐步生成结论和建议。",
    nextLabel: "开始分析",
  };
  const journeyRows = thinkingJourneyRows();
  if (!currentView || !journeyRows.length) {
    return [inputStep];
  }
  const stageSteps = journeyRows.map((step, index, rows) => ({
    key: `stage:${step.step_id}`,
    step,
    label: step.title || `分析步骤 ${index + 1}`,
    helper: () => step.summary || "展示本步骤的核心结论和建议。",
    nextLabel: index >= rows.length - 1 ? "完成分析" : "下一步分析",
  }));
  return [inputStep, ...stageSteps];
}

function normalizeActiveJourneyStep(steps = analysisJourneySteps()) {
  const keys = new Set(steps.map((step) => step.key));
  if (keys.has(activeReadingStep)) return activeReadingStep;
  if (currentView && steps[1]) {
    activeReadingStep = steps[1].key;
    return activeReadingStep;
  }
  activeReadingStep = "input";
  return activeReadingStep;
}

function handleReadingStepChange(event) {
  const requested = event.currentTarget.getAttribute("data-reading-step") || "input";
  if (!currentView && requested !== "input") return;
  activeReadingStep = requested;
  const url = new URL(window.location.href);
  url.searchParams.set("step", activeReadingStep);
  window.history.replaceState({}, "", url.toString());
  renderShell();
}

function isAuthPageRequested() {
  const params = new URLSearchParams(window.location.search);
  return params.get("page") === "auth";
}

function initialAuthMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get("mode") === "register" ? "register" : "login";
}

function isProfilesPageRequested() {
  const params = new URLSearchParams(window.location.search);
  return params.get("page") === "profiles";
}

function renderAuthPage() {
  const mode = authMode === "register" ? "register" : "login";
  app.innerHTML = `
    <section class="product-page">
      <section class="product-hero">
        <div>
          <p class="eyebrow">账户</p>
          <h2>${mode === "login" ? "登录" : "注册账号"}</h2>
          <p>账号用于保存八字档案、测算记录和连续问答。</p>
        </div>
        ${productSession ? `<button type="button" data-product-logout>退出登录</button>` : ""}
      </section>
      ${productNotice ? `<section class="notice-band info">${escapeHtml(productNotice)}</section>` : ""}
      ${productSession ? renderCurrentSessionCard() : `
        <section class="auth-shell">
          <div class="auth-mode-switch" role="tablist" aria-label="账户操作">
            <button type="button" class="${mode === "login" ? "active" : ""}" data-auth-mode="login" role="tab" aria-selected="${mode === "login"}">登录</button>
            <button type="button" class="${mode === "register" ? "active" : ""}" data-auth-mode="register" role="tab" aria-selected="${mode === "register"}">注册</button>
          </div>
          ${mode === "login" ? renderLoginPanel() : renderRegisterPanel()}
        </section>
      `}
    </section>
  `;
  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.addEventListener("click", handleAuthModeChange);
  });
  document.querySelector("[data-login-form]")?.addEventListener("submit", submitLogin);
  document.querySelector("[data-register-form]")?.addEventListener("submit", submitRegister);
  document.querySelector("[data-product-logout]")?.addEventListener("click", logoutProductSession);
}

function renderLoginPanel() {
  return `
    <article class="product-panel auth-panel">
      <div>
        <p class="eyebrow">账号登录</p>
        <h2>进入掐指一算</h2>
        <p>普通用户和命理师从这里登录。</p>
      </div>
      <form class="product-form" data-login-form>
        <label>用户名<input name="username" autocomplete="username" placeholder="请输入用户名"></label>
        <label>密码<input name="password" type="password" autocomplete="current-password"></label>
        <button type="submit">登录</button>
      </form>
    </article>
  `;
}

function renderRegisterPanel() {
  return `
    <article class="product-panel auth-panel">
      <div>
        <p class="eyebrow">创建账号</p>
        <h2>选择使用角色</h2>
        <p>注册开放普通用户和命理师两种使用角色。</p>
      </div>
      <form class="product-form" data-register-form>
        <label>用户名<input name="username" autocomplete="username" placeholder="例如 jerry"></label>
        <label>显示名<input name="displayName" autocomplete="name" placeholder="页面显示名称"></label>
        <div class="auth-role-grid" role="radiogroup" aria-label="注册角色">
          <label class="auth-role-card">
            <input type="radio" name="role" value="user" checked>
            <span>
              <strong>普通用户</strong>
              <em>保存档案、测算八字、连续追问。</em>
            </span>
          </label>
          <label class="auth-role-card">
            <input type="radio" name="role" value="practitioner">
            <span>
              <strong>命理师</strong>
              <em>查看证据链、结构路径和命理师复核面板。</em>
            </span>
          </label>
        </div>
        <label>密码<input name="password" type="password" autocomplete="new-password" placeholder="至少 6 位"></label>
        <button type="submit">注册并登录</button>
      </form>
    </article>
  `;
}

function handleAuthModeChange(event) {
  authMode = event.currentTarget.getAttribute("data-auth-mode") === "register" ? "register" : "login";
  const url = new URL(window.location.href);
  url.searchParams.set("page", "auth");
  url.searchParams.set("mode", authMode);
  window.history.replaceState({}, "", url.toString());
  productNotice = "";
  renderAuthPage();
}

function renderCurrentSessionCard() {
  const user = productSession?.user || {};
  const capabilities = Array.isArray(user.capabilities) ? user.capabilities : [];
  return `
    <section class="product-panel">
      <p class="eyebrow">当前登录</p>
      <h2>${escapeHtml(user.display_name || user.username || "已登录用户")}</h2>
      <div class="product-kv">
        ${renderKv("主系统角色", productRoleLabel(user.role))}
        ${renderKv("测算能力", capabilities.includes("practitioner_reading") ? "命理师测算" : "个人测算")}
      </div>
      <div class="product-actions left">
        <a class="subtle-link" href="/v30/ui/?page=profiles">进入八字档案</a>
        <a class="subtle-link" href="/v30/ui/?role=user">开始测算</a>
        ${capabilities.includes("practitioner_reading") ? `<a class="subtle-link" href="/v30/ui/?role=practitioner">命理师测算</a>` : ""}
      </div>
    </section>
  `;
}

function renderProfilesPage() {
  const profiles = Array.isArray(productProfiles?.items) ? productProfiles.items : [];
  app.innerHTML = `
    <section class="product-page">
      <section class="product-hero">
        <div>
          <p class="eyebrow">八字档案</p>
          <h2>档案管理</h2>
          <p>保存出生资料、历法、时区、真太阳时和未知时辰说明；测算时再排盘。</p>
        </div>
        <div class="product-actions">
          ${productSession ? `<button type="button" data-load-profiles>刷新档案</button>` : `<a class="subtle-link" href="/v30/ui/?page=auth">先登录</a>`}
        </div>
      </section>
      ${productNotice ? `<section class="notice-band info">${escapeHtml(productNotice)}</section>` : ""}
      ${!productSession ? `<section class="product-panel"><p>需要登录后管理八字档案。</p></section>` : `
        <section class="product-grid two">
          <article class="product-panel">
            <p class="eyebrow">新增 / 更新档案</p>
            <form class="product-form" data-profile-form>
              <input type="hidden" name="profileId">
              <label>档案名<input name="displayName" placeholder="例如 张三命盘"></label>
              <label>性别
                <select name="gender">
                  <option value="">不填</option>
                  <option value="female">女</option>
                  <option value="male">男</option>
                </select>
              </label>
              <label>历法
                <select name="calendarType">
                  <option value="solar">阳历</option>
                  <option value="lunar">阴历</option>
                </select>
              </label>
              <div class="birth-composite-field">
                <span>出生日期</span>
                ${renderBirthDateSelects(formState.birthDate)}
              </div>
              <div class="birth-composite-field">
                <span>出生时间</span>
                ${renderBirthTimeSelects(formState.birthTime)}
              </div>
              <label>出生地<input name="birthPlace" value="${escapeHtml(formState.birthPlace)}"></label>
              <label>时区<input name="timezone" value="${escapeHtml(formState.timezone)}"></label>
              <label>流年<input name="targetYear" type="number" value="${escapeHtml(formState.targetYear)}"></label>
              <div class="training-family-grid">
                <label class="check"><input name="lunarIsLeapMonth" type="checkbox">阴历闰月</label>
                <label class="check"><input name="useTrueSolarTime" type="checkbox">真太阳时</label>
                <label class="check"><input name="unknownHour" type="checkbox">时辰未知</label>
              </div>
              <button type="submit">保存档案</button>
            </form>
          </article>
          <article class="product-panel">
            <p class="eyebrow">档案列表</p>
            <h2>${profiles.length} 个档案</h2>
            <div class="profile-list">
              ${profiles.length ? profiles.map(renderProfileCard).join("") : `<div class="history-empty">暂无档案。保存后会显示在这里。</div>`}
            </div>
          </article>
        </section>
      `}
    </section>
  `;
  document.querySelector("[data-load-profiles]")?.addEventListener("click", loadProductProfiles);
  document.querySelector("[data-profile-form]")?.addEventListener("submit", submitProfile);
  bindBirthDateSelects(document);
  document.querySelectorAll("[data-profile-measure]").forEach((button) => {
    button.addEventListener("click", startProfileReading);
  });
  if (productSession && !productProfiles) {
    loadProductProfiles();
  }
}

function renderProfileCard(profile) {
  const birth = profile.birth_input || {};
  return `
    <article class="profile-card">
      <div>
        <strong>${escapeHtml(profile.display_name || "未命名档案")}</strong>
        <span>${escapeHtml(birth.calendar_type || "")} · ${escapeHtml(birth.birth_date || "")} ${escapeHtml(birth.birth_time || "")}</span>
        <span>${escapeHtml(birth.birth_place || "")} · ${escapeHtml(birth.timezone || "")}</span>
      </div>
      <button type="button" data-profile-measure="${escapeHtml(profile.profile_id)}">测算</button>
    </article>
  `;
}

function renderKv(key, value) {
  return `<span><small>${escapeHtml(key)}</small><strong>${escapeHtml(value ?? "-")}</strong></span>`;
}

async function fetchJson(url, options = {}, timeoutMs = 12000) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  const res = await fetch(url, { ...options, signal: controller.signal }).finally(() => {
    window.clearTimeout(timeout);
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(payload.detail || `${res.status}`);
  return payload;
}

function loadStoredProductSession() {
  try {
    const raw = window.localStorage.getItem(PRODUCT_SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

function loadStoredUiPrefs() {
  try {
    const raw = window.localStorage.getItem(PRODUCT_UI_PREFS_KEY);
    return raw ? JSON.parse(raw) : { locale: "zh" };
  } catch (error) {
    return { locale: "zh" };
  }
}

function storeUiPrefs(nextPrefs) {
  productUiPrefs = { ...productUiPrefs, ...nextPrefs };
  window.localStorage.setItem(PRODUCT_UI_PREFS_KEY, JSON.stringify(productUiPrefs));
}

function renderGlobalChrome() {
  const client = detectClient();
  if (formState.client !== client) {
    formState = { ...formState, client };
  }
  renderSystemMenuState();
}

function renderSystemMenuState() {
  const user = productSession?.user || {};
  const isLoggedIn = Boolean(productSession?.session?.session_token);
  if (systemMenuEl) {
    systemMenuEl.hidden = false;
  }
  if (systemLabelEl) {
    const name = user.display_name || user.username || "系统";
    systemLabelEl.textContent = isLoggedIn ? `系统 · ${name}` : "系统";
  }
  if (systemAuthEl) {
    systemAuthEl.hidden = isLoggedIn;
  }
  if (systemLogoutEl) {
    systemLogoutEl.hidden = !isLoggedIn;
  }
  if (systemLogoutEl) {
    systemLogoutEl.onclick = logoutProductSession;
  }
}

function storeProductSession(payload) {
  productSession = payload;
  window.localStorage.setItem(PRODUCT_SESSION_KEY, JSON.stringify(payload));
  const session = payload.session || {};
  const user = payload.user || {};
  const mainRole = normalizeMainSystemRole(user.main_system_role || user.role || formState.role);
  const profile = mainSystemRoleProfile(mainRole);
  formState = {
    ...formState,
    actorId: session.actor_id || formState.actorId,
    sessionId: session.session_id || formState.sessionId,
    role: mainRole,
    client: profile.client === "web" ? detectClient() : profile.client,
    profileName: user.display_name || formState.profileName,
  };
}

async function submitLogin(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  setStatus("login");
  try {
    const payload = await fetchJson("/api/v30/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        username: String(data.get("username") || ""),
        password: String(data.get("password") || ""),
      }),
    });
    storeProductSession(payload);
    productProfiles = null;
    productNotice = "登录成功。";
    setStatus("ready");
  } catch (error) {
    productNotice = `登录失败：${error.message || "请检查账号密码"}`;
    setStatus("error");
  }
  renderAuthPage();
}

async function submitRegister(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  setStatus("register");
  try {
    const payload = await fetchJson("/api/v30/auth/register", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        username: String(data.get("username") || ""),
        password: String(data.get("password") || ""),
        display_name: String(data.get("displayName") || ""),
        role: String(data.get("role") || "user"),
      }),
    });
    storeProductSession(payload);
    productProfiles = null;
    productNotice = "注册成功，已登录。";
    setStatus("ready");
  } catch (error) {
    productNotice = `注册失败：${error.message || "请检查输入"}`;
    setStatus("error");
  }
  renderAuthPage();
}

async function logoutProductSession() {
  const token = productSession?.session?.session_token || "";
  if (token) {
    await fetchJson("/api/v30/auth/logout", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ session_token: token }),
    }).catch(() => ({}));
  }
  productSession = null;
  productProfiles = null;
  window.localStorage.removeItem(PRODUCT_SESSION_KEY);
  productNotice = "已退出登录。";
  setStatus("ready");
  renderAuthPage();
}

async function loadProductProfiles(options = {}) {
  const surface = options.surface || "profiles";
  const silent = Boolean(options.silent);
  const token = productSession?.session?.session_token || "";
  if (!token) {
    productNotice = "请先登录。";
    if (surface === "shell") renderShell();
    else renderProfilesPage();
    return;
  }
  if (!silent) setStatus("profiles");
  try {
    productProfiles = await fetchJson(`/api/v30/profiles?session_token=${encodeURIComponent(token)}`);
    productNotice = productProfiles.count ? "档案已刷新。" : "暂无档案。";
    setStatus("ready");
  } catch (error) {
    if (String(error.message || "").includes("invalid session") || String(error.message || "").includes("401")) {
      productSession = null;
      productProfiles = { count: 0, items: [] };
      window.localStorage.removeItem(PRODUCT_SESSION_KEY);
      productNotice = "登录已过期，请重新登录。";
    } else {
      productProfiles = { count: 0, items: [] };
      productNotice = `档案读取失败：${error.message || "request_failed"}`;
    }
    setStatus("error");
  }
  if (surface === "shell") renderShell();
  else renderProfilesPage();
}

async function submitProfile(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const token = productSession?.session?.session_token || "";
  if (!token) return;
  setStatus("profile");
  try {
    await fetchJson("/api/v30/profiles", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        session_token: token,
        profile_id: String(data.get("profileId") || "") || null,
        display_name: String(data.get("displayName") || "未命名档案"),
        gender: String(data.get("gender") || ""),
        calendar_type: String(data.get("calendarType") || "solar"),
        birth_date: composeBirthDate(data),
        birth_time: composeBirthTime(data),
        timezone: String(data.get("timezone") || "Asia/Shanghai"),
        birth_place: String(data.get("birthPlace") || ""),
        target_year: Number(data.get("targetYear") || new Date().getFullYear()),
        lunar_is_leap_month: data.get("lunarIsLeapMonth") === "on",
        use_true_solar_time: data.get("useTrueSolarTime") === "on",
        unknown_hour: data.get("unknownHour") === "on",
      }),
    });
    productNotice = "档案已保存。";
    productProfiles = null;
    await loadProductProfiles();
  } catch (error) {
    productNotice = `保存失败：${error.message || "profile_save_failed"}`;
    setStatus("error");
    renderProfilesPage();
  }
}

async function startProfileReading(event) {
  const profileId = event.currentTarget.getAttribute("data-profile-measure") || "";
  const profile = (productProfiles?.items || []).find((row) => row.profile_id === profileId);
  if (!profile) return;
  const birth = profile.birth_input || {};
  formState = {
    ...formState,
    profileName: profile.display_name || formState.profileName,
    actorId: productSession?.session?.actor_id || profile.actor_id || formState.actorId,
    sessionId: productSession?.session?.session_id || formState.sessionId,
    calendarType: birth.calendar_type || "solar",
    birthDate: birth.birth_date || formState.birthDate,
    birthTime: birth.birth_time || formState.birthTime,
    birthPlace: birth.birth_place || formState.birthPlace,
    timezone: birth.timezone || formState.timezone,
    gender: birth.gender || "",
    targetYear: Number(profile.target_year || formState.targetYear),
    lunarIsLeapMonth: Boolean(birth.lunar_is_leap_month),
    useTrueSolarTime: Boolean(birth.use_true_solar_time),
    unknownHour: Boolean(birth.unknown_hour),
    readingId: `v30-reading-${Date.now()}`,
  };
  productNotice = "";
  window.history.replaceState({}, "", `/v30/ui/?role=${encodeURIComponent(normalizeMainSystemRole(formState.role))}`);
  await createReadingFromCurrentFormState();
}

async function handleRoleChange(event) {
  const role = normalizeMainSystemRole(event.currentTarget.getAttribute("data-role") || "user");
  if (productSession?.user?.role) return;
  const profile = mainSystemRoleProfile(role);
  formState = {
    ...formState,
    role,
    client: profile.client === "web" ? detectClient() : profile.client,
  };
  renderShell();
  if (!currentView) return;
  setStatus("refreshing");
  await refreshView(formState.readingId);
}

async function handleProjectionChange(event) {
  const control = event.currentTarget;
  formState = {
    ...formState,
    [control.name]: control.value,
  };
  if (!currentView) return;
  setStatus("refreshing");
  await refreshView(formState.readingId);
}

async function submitBirth(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const fixedRole = normalizeMainSystemRole(productSession?.user?.main_system_role || productSession?.user?.role || formState.role || "user");
  formState = {
    ...formState,
    actorId: productSession?.session?.actor_id || formState.actorId || "guest-demo",
    sessionId: productSession?.session?.session_id || formState.sessionId || `session-${Date.now()}`,
    role: fixedRole,
    profileName: String(data.get("profileName") || "当前命盘"),
    locale: String(data.get("locale") || formState.locale || "zh"),
    client: mainSystemRoleProfile(fixedRole).client === "web" ? detectClient() : mainSystemRoleProfile(fixedRole).client,
    birthDate: composeBirthDate(data),
    birthTime: composeBirthTime(data),
    calendarType: String(data.get("calendarType") || "solar"),
    birthPlace: String(data.get("birthPlace") || ""),
    timezone: String(data.get("timezone") || "Asia/Shanghai"),
    gender: String(data.get("gender") || ""),
    targetYear: Number(data.get("targetYear") || new Date().getFullYear()),
    lunarIsLeapMonth: data.get("lunarIsLeapMonth") === "on",
    useTrueSolarTime: data.get("useTrueSolarTime") === "on",
    unknownHour: data.get("unknownHour") === "on",
    readingId: `v30-reading-${Date.now()}`,
  };
  await createReadingFromCurrentFormState();
}

async function createReadingFromCurrentFormState() {
  setStatus("calculating");
  const payload = {
    reading_id: formState.readingId,
    locale: formState.locale,
    target_year: formState.targetYear,
    actor_id: formState.actorId,
    session_id: formState.sessionId,
    birth_input: {
      calendar_type: formState.calendarType,
      birth_date: formState.birthDate,
      birth_time: formState.unknownHour ? "00:00" : formState.birthTime,
      timezone: formState.timezone,
      birth_place: formState.birthPlace,
      gender: formState.gender || null,
      lunar_is_leap_month: formState.calendarType === "lunar" && formState.lunarIsLeapMonth,
      use_true_solar_time: formState.useTrueSolarTime,
      unknown_hour: formState.unknownHour,
      calendar_assumption: "user_selected",
      source: "v30_ui_customer_loop",
    },
  };
  const createRes = await fetch("/api/v30/readings", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  const created = await createRes.json();
  if (created.status && created.status !== "ready") {
    setStatus(created.status);
    activeReadingStep = "input";
    currentView = {
      reading_surface: {
        reading_summary: { title: "当前输入还不能完成排盘", boundary: "blocked_birth_input_projection" },
      },
      questions: [],
      answer_panel: { text: (created.failures || []).join("；") || "请检查出生信息。", boundary: "birth_input_blocked" },
    };
    renderReading();
    return;
  }
  await refreshView(created.reading_id);
  activeReadingStep = firstAnalysisStageKey();
  await loadHistory({ silent: true });
}

async function refreshView(readingId) {
  const params = new URLSearchParams({
    role: formState.role,
    locale: formState.locale,
    client: formState.client,
  });
  const viewRes = await fetch(`/api/v30/readings/${readingId}/view?${params.toString()}`);
  currentView = await viewRes.json();
  await refreshThinkingProjection(readingId);
  await refreshPractitionerOptionState(readingId);
  currentInteractionState = currentView.interaction_state || currentInteractionState;
  formState = {
    ...formState,
    readingId,
  };
  setStatus("ready");
  renderReading();
}

async function refreshThinkingProjection(readingId, options = {}) {
  const preserveCurrent = Boolean(options.preserveCurrent);
  const readingChanged = stageSummaryReadingId !== readingId;
  const thinkingRes = await fetch(`/api/v30/readings/${readingId}/thinking`).catch(() => null);
  if (thinkingRes && thinkingRes.ok) {
    const nextThinking = await thinkingRes.json();
    currentThinking = preserveCurrent
      ? mergeThinkingProjectionPreservingEnhancements(currentThinking, nextThinking)
      : nextThinking;
  } else if (!preserveCurrent) {
    currentThinking = null;
  }
  if (readingChanged) {
    stageSummaryEnhancementState = {};
    stageThinkingStreamText = {};
    stageSummaryReadingId = readingId;
  }
  normalizeActiveJourneyStep();
}

async function refreshPractitionerOptionState(readingId) {
  if (!isPractitionerLikeRole()) {
    currentPractitionerState = null;
    return;
  }
  const role = encodeURIComponent("practitioner");
  const res = await fetch(`/api/v30/readings/${encodeURIComponent(readingId)}/practitioner/options?role=${role}`).catch(() => null);
  if (!res || !res.ok) {
    currentPractitionerState = null;
    return;
  }
  currentPractitionerState = await res.json();
}

function mergeThinkingProjectionPreservingEnhancements(previous, next) {
  if (!previous || !next || !Array.isArray(previous.steps) || !Array.isArray(next.steps)) {
    return next || previous;
  }
  const previousSteps = new Map(previous.steps.map((step) => [step?.step_id, step]));
  return {
    ...next,
    steps: next.steps.map((step) => {
      const prior = previousSteps.get(step?.step_id);
      if (!prior) return step;
      const priorAccepted = visibleLlmThinkingSummary(prior);
      const nextAccepted = visibleLlmThinkingSummary(step);
      if (!priorAccepted || nextAccepted) return step;
      return {
        ...step,
        summary_panel: prior.summary_panel,
        analysis_result: prior.analysis_result || step.analysis_result,
        stage_point_set: prior.stage_point_set || step.stage_point_set,
        stage_points: Array.isArray(prior.stage_points) && prior.stage_points.length ? prior.stage_points : step.stage_points,
      };
    }),
  };
}

function firstAnalysisStageKey() {
  const first = thinkingJourneyRows()[0] || null;
  return first?.step_id ? `stage:${first.step_id}` : "input";
}

async function loadHistory(options = {}) {
  const silent = Boolean(options.silent);
  if (!formState.actorId || !formState.sessionId) {
    historyNotice = "请先登录或完成一次测算后再读取历史。";
    if (!silent) renderShell();
    return;
  }
  if (!silent) setStatus("history");
  const params = new URLSearchParams({
    actor_id: formState.actorId,
    session_id: formState.sessionId,
    role: formState.role,
    locale: formState.locale,
    client: formState.client,
    limit: "12",
  });
  try {
    const res = await fetch(`/api/v30/readings/history?${params.toString()}`);
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || "history_load_failed");
    readingHistory = payload;
    historyNotice = payload.count ? "已按当前用户和会话读取历史。" : "当前用户和会话暂无历史测算。";
    setStatus(currentView ? "ready" : "history");
  } catch (error) {
    historyNotice = `读取失败：${error.message || "请检查用户和会话"}`;
    setStatus("error");
  }
  renderShell();
}

async function openHistoryReading(event) {
  const readingId = event.currentTarget.getAttribute("data-open-reading") || "";
  if (!readingId) return;
  formState = {
    ...formState,
    readingId,
    profileName: event.currentTarget.getAttribute("data-profile-label") || formState.profileName,
  };
  setStatus("opening");
  await refreshView(readingId);
  activeReadingStep = firstAnalysisStageKey();
  renderShell();
}

function renderReading() {
  const target = document.querySelector("#reading");
  if (!target) return;
  if (!currentView) {
    target.innerHTML = `
      <div class="empty">
        <span class="empty-mark" aria-hidden="true">命</span>
        <strong>等待排盘</strong>
        <p>输入出生信息后，这里会先展示四柱、大运、流年、十神与核心测算，再进入智能问答。</p>
      </div>
    `;
    renderDialogueChain();
    return;
  }
  const surface = currentView.reading_surface || {};
  const finalSynthesis = surface.final_synthesis || {};
  const answer = currentView.answer_panel || {};
  target.innerHTML = renderReadingStepContent({
    surface,
    finalSynthesis,
    answer,
  });
  target.querySelectorAll("[data-answer-question]").forEach((form) => {
    form.addEventListener("submit", submitAnswer);
  });
  target.querySelectorAll("[data-practitioner-option-action]").forEach((button) => {
    button.addEventListener("click", submitPractitionerOptionAction);
  });
  target.querySelectorAll("[data-practitioner-option-note]").forEach((form) => {
    form.addEventListener("submit", submitPractitionerOptionNote);
  });
  prepareStageTypewriter(currentAnalysisStage());
  requestActiveStageSummaryEnhancement();
  renderDialogueChain();
}

function renderReadingStepContent(context) {
  if (activeReadingStep !== "input") {
    const stage = currentAnalysisStage();
    if (stage) return renderAnalysisStagePage(context, stage);
  }
  return `
    <section class="step-page input-support-step">
      <div class="history-empty">出生资料在上方表单中修改。提交后会自动进入命盘步骤。</div>
    </section>
  `;
}

function renderDialogueChain() {
  const target = document.querySelector("#dialogue-chain");
  if (!target) return;
  const readingId = currentView && formState.readingId ? formState.readingId : "";
  if (!readingId) {
    dialogueChainState = { ...dialogueChainState, readingId: "", open: false, loaded: false, activeSession: null, sessions: [], seeds: [] };
    target.innerHTML = "";
    return;
  }
  if (dialogueChainState.readingId !== readingId) {
    dialogueChainState = {
      ...dialogueChainState,
      readingId,
      open: false,
      loaded: false,
      loading: false,
      submitting: false,
      notice: "",
      seeds: [],
      sessions: [],
      activeSession: null,
      input: "我今年财运如何？",
    };
  }
  if (!dialogueSurfaceShouldRenderOpen()) {
    target.innerHTML = renderDialogueLauncher();
    target.querySelector("[data-dialogue-open]")?.addEventListener("click", openDialogueChain);
    return;
  }
  const session = dialogueChainState.activeSession || dialogueChainState.sessions?.[0] || null;
  target.innerHTML = `
    <section class="dialogue-chain-panel ${dialogueChainState.submitting ? "loading" : ""}">
      <div class="dialogue-chain-head">
        <div>
          <p class="eyebrow">问八字</p>
          <h3>连续智能对话</h3>
        </div>
        <div class="dialogue-chain-actions">
          <button type="button" class="subtle-button" data-dialogue-close>收起</button>
          ${session ? `<button type="button" class="subtle-button" data-dialogue-new>新问题</button>` : ""}
          <button type="button" class="subtle-button" data-dialogue-refresh>${dialogueChainState.loading ? "读取中" : "刷新"}</button>
        </div>
      </div>
      ${dialogueChainState.notice ? `<p class="dialogue-chain-notice">${escapeHtml(dialogueChainState.notice)}</p>` : ""}
      ${session ? renderDialogueSession(session) : renderDialogueSeedLauncher()}
      ${renderDialogueInput(session)}
    </section>
  `;
  target.querySelector("[data-dialogue-close]")?.addEventListener("click", closeDialogueChain);
  target.querySelector("[data-dialogue-refresh]")?.addEventListener("click", () => loadDialogueChain({ force: true }));
  target.querySelector("[data-dialogue-new]")?.addEventListener("click", () => {
    dialogueChainState = { ...dialogueChainState, open: true, activeSession: null, notice: "可以输入一个新问题，或点击下面的种子问题。" };
    renderDialogueChain();
  });
  target.querySelectorAll("[data-dialogue-seed]").forEach((button) => {
    button.addEventListener("click", startDialogueFromSeed);
  });
  target.querySelectorAll("[data-dialogue-option]").forEach((button) => {
    button.addEventListener("click", submitDialogueOption);
  });
  target.querySelector("[data-dialogue-form]")?.addEventListener("submit", submitDialogueInput);
  ensureDialogueChainLoaded();
}

function dialogueSurfaceShouldRenderOpen() {
  return Boolean(dialogueChainState.open || dialogueChainState.submitting);
}

function renderDialogueLauncher() {
  const surface = currentView?.reading_surface?.conversation_surface || {};
  const suggested = surface.suggested_question || {};
  const summary = surface.dialogue_summary || {};
  const prompt = suggested.label || dialogueChainState.input || "我今年财运如何？";
  return `
    <section class="dialogue-chain-launcher">
      <div>
        <p class="eyebrow">问八字</p>
        <h3>${escapeHtml(surface.title || "连续智能对话")}</h3>
        <p>${escapeHtml(summary.summary || "围绕当前命盘继续追问，系统会根据你的回答生成下一轮问题。")}</p>
        ${prompt ? `<span>可问：${escapeHtml(prompt)}</span>` : ""}
      </div>
      <button type="button" data-dialogue-open>开始追问</button>
    </section>
  `;
}

function openDialogueChain() {
  dialogueChainState = { ...dialogueChainState, open: true, notice: dialogueChainState.notice || "" };
  renderDialogueChain();
}

function closeDialogueChain() {
  dialogueChainState = { ...dialogueChainState, open: false, notice: "" };
  renderDialogueChain();
}

function renderDialogueSeedLauncher() {
  const seeds = Array.isArray(dialogueChainState.seeds) ? dialogueChainState.seeds : [];
  return `
    <div class="dialogue-seed-launcher">
      <div class="dialogue-seed-grid">
        ${seeds.length
          ? seeds.slice(0, 5).map((seed) => `
            <button type="button" data-dialogue-seed="${escapeHtml(seed.label || "")}">
              <span>${escapeHtml(seed.domain_label || seed.macro_domain || "问题")}</span>
              <strong>${escapeHtml(seed.label || "继续测算")}</strong>
            </button>
          `).join("")
          : `<div class="dialogue-chain-empty">${dialogueChainState.loading ? "正在读取推荐问题。" : "推荐问题会在命盘建立后出现。"}</div>`}
      </div>
    </div>
  `;
}

function renderDialogueSession(session) {
  const turns = Array.isArray(session?.turns) ? session.turns : [];
  const latest = turns[turns.length - 1] || null;
  return `
    <div class="dialogue-session">
      <div class="dialogue-session-meta">
        <span>${escapeHtml(domainLabel(session.active_domain))}</span>
        <span>${turns.length} 轮</span>
        <span>${escapeHtml(session.memory_summary?.summary || "持续追问")}</span>
      </div>
      <div class="dialogue-turn-list">
        ${turns.length ? turns.map(renderDialogueTurn).join("") : `<div class="dialogue-chain-empty">对话已经建立，正在等待第一轮回答。</div>`}
      </div>
      ${latest?.selected_next_question ? renderDialogueNextQuestion(latest.selected_next_question) : ""}
    </div>
  `;
}

function renderDialogueTurn(turn) {
  const seed = turn.interpreted_seed || {};
  const answer = turn.answer || {};
  return `
    <article class="dialogue-turn">
      <div class="dialogue-user-line">
        <span>${escapeHtml(domainLabel(seed.macro_domain))}</span>
        <strong>${escapeHtml(seed.normalized_question || turn.user_input?.text || "继续追问")}</strong>
      </div>
      ${answer.visual_hint ? renderAnswerVisualHint(answer.visual_hint) : ""}
      ${renderDialogueAnswerBlocks(answer)}
    </article>
  `;
}

function renderDialogueAnswerBlocks(answer) {
  const conclusions = Array.isArray(answer.conclusion_items) ? answer.conclusion_items : [];
  const advice = Array.isArray(answer.advice_items) ? answer.advice_items : [];
  const uncertainty = Array.isArray(answer.uncertainty_items) ? answer.uncertainty_items : [];
  if (conclusions.length || advice.length || uncertainty.length) {
    return `
      <div class="dialogue-answer-grid">
        ${renderDialogueAnswerList("断", conclusions)}
        ${renderDialogueAnswerList("策", advice)}
        ${uncertainty.length ? renderDialogueAnswerList("歧", uncertainty) : ""}
      </div>
    `;
  }
  return `<p class="dialogue-answer-text">${formatMultilineText(answer.display_text || "本轮暂无可展示结论。")}</p>`;
}

function renderDialogueAnswerList(icon, rows) {
  if (!Array.isArray(rows) || !rows.length) return "";
  return `
    <div class="dialogue-answer-list">
      <span>${escapeHtml(icon)}</span>
      <ul>${rows.map((row) => `<li>${escapeHtml(row)}</li>`).join("")}</ul>
    </div>
  `;
}

function renderDialogueNextQuestion(question) {
  const options = Array.isArray(question.options) ? question.options : [];
  return `
    <div class="dialogue-next-question">
      <span>下一问</span>
      <strong>${escapeHtml(question.label || question.prompt_text || "继续追问")}</strong>
      <div class="dialogue-next-options">
        ${options.length
          ? options.slice(0, 4).map((option) => `
            <button type="button"
              data-dialogue-option="${escapeHtml(option.option_id || option.value || "")}"
              data-dialogue-option-label="${escapeHtml(option.label || option.value || "")}"
              data-dialogue-question="${escapeHtml(question.label || question.prompt_text || "")}">
              ${escapeHtml(option.label || option.value || "继续")}
            </button>
          `).join("")
          : `<button type="button" data-dialogue-option="" data-dialogue-question="${escapeHtml(question.label || question.prompt_text || "")}">继续这一问</button>`}
      </div>
    </div>
  `;
}

function renderDialogueInput(session) {
  const disabled = dialogueChainState.submitting ? "disabled" : "";
  return `
    <form class="dialogue-input-row" data-dialogue-form>
      <input name="dialogueText" value="${escapeHtml(dialogueChainState.input || "")}" placeholder="比如：我今年财运如何？" ${disabled}>
      <button type="submit" ${disabled}>${dialogueChainState.submitting ? "推演中" : (session ? "继续问" : "开始问")}</button>
    </form>
  `;
}

function ensureDialogueChainLoaded() {
  if (!dialogueChainState.readingId || dialogueChainState.loaded || dialogueChainState.loading) return;
  loadDialogueChain({ silent: true });
}

async function loadDialogueChain(options = {}) {
  const readingId = dialogueChainState.readingId || formState.readingId;
  if (!readingId) return;
  dialogueChainState = { ...dialogueChainState, readingId, open: true, loading: true, notice: options.force ? "正在刷新问八字。" : dialogueChainState.notice };
  if (!options.silent) renderDialogueChain();
  try {
    const params = new URLSearchParams({ role: formState.role, locale: formState.locale, client: formState.client });
    const [seedPayload, sessionPayload] = await Promise.all([
      fetchJson(`/api/v30/readings/${encodeURIComponent(readingId)}/dialogue-seeds?${params.toString()}`),
      fetchJson(`/api/v30/readings/${encodeURIComponent(readingId)}/dialogues?limit=8`),
    ]);
    const sessions = Array.isArray(sessionPayload.items) ? sessionPayload.items : [];
    dialogueChainState = {
      ...dialogueChainState,
      loaded: true,
      loading: false,
      seeds: Array.isArray(seedPayload.items) ? seedPayload.items : [],
      sessions,
      activeSession: dialogueChainState.activeSession || sessions[0] || null,
      notice: options.force ? "问八字已刷新。" : dialogueChainState.notice,
    };
  } catch (error) {
    dialogueChainState = { ...dialogueChainState, loaded: true, loading: false, notice: `问八字读取失败：${error.message || "request_failed"}` };
  }
  renderDialogueChain();
}

async function startDialogueFromSeed(event) {
  const text = event.currentTarget.getAttribute("data-dialogue-seed") || "我今年财运如何？";
  dialogueChainState = { ...dialogueChainState, open: true, input: text };
  await createOrAppendDialogueTurn({ text, startNew: true });
}

async function submitDialogueInput(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const text = String(data.get("dialogueText") || "").trim();
  if (!text) return;
  dialogueChainState = { ...dialogueChainState, open: true, input: text };
  await createOrAppendDialogueTurn({ text, startNew: !dialogueChainState.activeSession });
}

async function submitDialogueOption(event) {
  const selectedOption = event.currentTarget.getAttribute("data-dialogue-option") || "";
  const optionLabel = event.currentTarget.getAttribute("data-dialogue-option-label") || selectedOption;
  const questionLabel = event.currentTarget.getAttribute("data-dialogue-question") || "";
  const text = [questionLabel, optionLabel].filter(Boolean).join("：");
  dialogueChainState = { ...dialogueChainState, open: true };
  await createOrAppendDialogueTurn({ text, selectedOption, startNew: false });
}

async function createOrAppendDialogueTurn({ text = "", selectedOption = "", startNew = false } = {}) {
  const readingId = dialogueChainState.readingId || formState.readingId;
  if (!readingId || dialogueChainState.submitting) return;
  dialogueChainState = { ...dialogueChainState, open: true, submitting: true, notice: "正在生成本轮问答。" };
  renderDialogueChain();
  try {
    let payload;
    if (startNew || !dialogueChainState.activeSession?.dialogue_id) {
      payload = await fetchJson(`/api/v30/readings/${encodeURIComponent(readingId)}/dialogues`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          seed_text: text || "我今年财运如何？",
          source: "user",
          role: formState.role,
          locale: formState.locale,
          client: formState.client,
          stage_id: currentAnalysisStage()?.step_id || "",
        }),
      });
    } else {
      const dialogueId = dialogueChainState.activeSession.dialogue_id;
      payload = await fetchJson(`/api/v30/readings/${encodeURIComponent(readingId)}/dialogues/${encodeURIComponent(dialogueId)}/turns`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          text,
          selected_option: selectedOption,
          structured_payload: selectedOption ? { selected_option: selectedOption } : {},
          role: formState.role,
          locale: formState.locale,
          client: formState.client,
          stage_id: currentAnalysisStage()?.step_id || "",
        }),
      });
    }
    const session = payload.session;
    const sessions = [session, ...(dialogueChainState.sessions || []).filter((row) => row.dialogue_id !== session.dialogue_id)];
    dialogueChainState = {
      ...dialogueChainState,
      submitting: false,
      activeSession: session,
      sessions,
      input: "",
      notice: "本轮已完成，可以继续追问。",
    };
  } catch (error) {
    dialogueChainState = { ...dialogueChainState, submitting: false, notice: `问答失败：${error.message || "request_failed"}` };
  }
  renderDialogueChain();
}

function domainLabel(domain) {
  const labels = {
    wealth: "财务",
    career: "事业",
    relationship: "关系",
    health: "健康",
    family: "亲情",
    timing: "时运",
    decision: "决策",
    useful_god: "用神",
    structure: "结构",
    overview: "总览",
  };
  return labels[String(domain || "")] || "八字";
}

function currentAnalysisStage() {
  const steps = thinkingJourneyRows();
  if (!steps.length) return null;
  const activeId = String(activeReadingStep || "").startsWith("stage:")
    ? activeReadingStep.slice("stage:".length)
    : "";
  return steps.find((step) => step.step_id === activeId) || steps[0];
}

async function requestActiveStageSummaryEnhancement() {
  const stage = currentAnalysisStage();
  if (!stage?.step_id || !formState.readingId || !currentThinking) return;
  if (!stageAllowsLlmEnhancement(stage)) return;
  const stageId = stage.step_id;
  const key = `${formState.readingId}:${stageId}`;
  if (stageSummaryEnhancementState[key]) return;
  stageSummaryEnhancementState[key] = "loading";
  stageThinkingStreamText[key] = "";
  renderReading();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), STAGE_SUMMARY_STREAM_TIMEOUT_MS);
  try {
    const res = await fetch(`/api/v30/readings/${encodeURIComponent(formState.readingId)}/thinking/${encodeURIComponent(stageId)}/summary/llm/stream`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        role: formState.role,
        locale: formState.locale,
        client: formState.client,
      }),
    });
    if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error(payload.detail || "thinking_summary_stream_failed");
    }
    await consumeStageSummaryStream(res, key, stageId);
    stageSummaryEnhancementState[key] = stageHasAcceptedLlmSummary(stageId) ? "done" : "failed";
    if (currentAnalysisStage()?.step_id === stage.step_id) {
      renderReading();
    }
  } catch (_error) {
    stageSummaryEnhancementState[key] = "failed";
    renderReading();
  } finally {
    window.clearTimeout(timeout);
  }
}

async function consumeStageSummaryStream(res, key, stageId) {
  const reader = res.body?.getReader();
  if (!reader) {
    const payload = await res.json();
    applyStageSummaryFinalPayload(payload, stageId);
    return;
  }
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const rows = buffer.split("\n");
    buffer = rows.pop() || "";
    rows.forEach((row) => applyStageSummaryStreamEvent(row, key, stageId));
  }
  if (buffer.trim()) applyStageSummaryStreamEvent(buffer, key, stageId);
}

function applyStageSummaryStreamEvent(row, key, stageId) {
  if (!row.trim()) return;
  const event = JSON.parse(row);
  if (event.event === "thinking_delta") {
    const current = stageThinkingStreamText[key] || "";
    stageThinkingStreamText[key] = `${current}${event.delta || ""}`.slice(-900);
    scheduleStageThinkingRender(stageId);
    return;
  }
  if (event.event === "final_step") {
    applyStageSummaryFinalPayload(event, stageId);
    return;
  }
  if (event.event === "stream_error") {
    throw new Error(event.error || "thinking_summary_stream_error");
  }
}

function applyStageSummaryFinalPayload(payload, stageId) {
  if (!payload?.step || !Array.isArray(currentThinking?.steps)) return;
  currentThinking = {
    ...currentThinking,
    steps: currentThinking.steps.map((row) => (
      row?.step_id === stageId ? payload.step : row
    )),
  };
}

function stageHasAcceptedLlmSummary(stageId) {
  const rows = Array.isArray(currentThinking?.steps) ? currentThinking.steps : [];
  const step = rows.find((row) => row?.step_id === stageId);
  return Boolean(visibleLlmThinkingSummary(step));
}

function scheduleStageThinkingRender(stageId) {
  if (stageThinkingRenderTimer) return;
  stageThinkingRenderTimer = window.setTimeout(() => {
    stageThinkingRenderTimer = null;
    if (currentAnalysisStage()?.step_id === stageId) renderReading();
  }, 180);
}

function stageAllowsLlmEnhancement(stage) {
  if (!stage?.step_id) return false;
  const policy = stage.summary_policy || stage.summary_panel?.summary_policy || {};
  if (policy.llm_enhancement !== "auto") return false;
  const metadata = stage.summary_panel?.llm_metadata || {};
  if (metadata.status === "accepted" || metadata.status === "fallback") return false;
  const key = `${formState.readingId}:${stage.step_id}`;
  return !stageSummaryEnhancementState[key];
}

function renderAnalysisStagePage(context, stage) {
  const steps = thinkingJourneyRows();
  const index = Math.max(0, steps.findIndex((row) => row.step_id === stage.step_id));
  const total = steps.length;
  return `
    <section class="step-page analysis-stage-page">
      ${renderInteractionNotice()}
      ${renderActiveAnalysisStage(stage, index, total)}
      ${renderStageAnalysisResult(stage)}
      ${renderDecisionWorkbenchStagePanel(context.surface, stage)}
      ${renderPractitionerOptionPanel(stage)}
      ${renderStageInteractionSlot(context, stage)}
    </section>
  `;
}

function renderInteractionNotice() {
  if (!interactionNotice) return "";
  const notice = typeof interactionNotice === "string" ? { type: "info", text: interactionNotice } : interactionNotice;
  const type = ["success", "warn", "info"].includes(notice.type) ? notice.type : "info";
  return `<section class="notice-band ${escapeHtml(type)}">${escapeHtml(notice.text || "")}</section>`;
}

function renderActiveAnalysisStage(stage, index, total) {
  const theme = stageCoreTheme(stage);
  return `
    <section class="analysis-stage-band compact">
      <div class="analysis-stage-head">
        <div>
          <p class="eyebrow">当前主题</p>
          <h2>${escapeHtml(stage.title || "八字分析步骤")}</h2>
          ${theme ? `<p>${escapeHtml(theme)}</p>` : ""}
        </div>
      </div>
    </section>
  `;
}

function renderStageAnalysisResult(stage) {
  const analysis = stage?.analysis_result || {};
  const thinkingState = stageLlmDisplayState(stage);
  const stageKey = stageTypewriterKey(stage);
  const decisionText = stageTypewriter.key === stageKey ? stageTypewriter.visibleText : "";
  const isTyping = stageTypewriter.key === stageKey && stageTypewriter.active;
  if (!stageFinalDecisionText(stage) && !analysis.conclusion && !analysis.next_focus) return "";
  if (thinkingState !== "accepted" && thinkingState !== "not_required") {
    return `
      <section class="xuanming-analysis-band pending">
        <div class="xuanming-analysis-main">
          <p class="eyebrow">${thinkingState === "failed" ? "推演结果" : "推演中"}</p>
          ${thinkingState === "failed" ? renderLlmThinkingFailed(stage) : renderLlmThinkingLoader()}
          ${thinkingState === "failed" ? "" : renderPendingThinkingStream(stage)}
        </div>
      </section>
    `;
  }
  return `
    <section class="xuanming-analysis-band">
      <div class="xuanming-analysis-main">
        <p class="eyebrow">本页要点</p>
        ${renderStageDecisionTypewriter(decisionText, isTyping, stageKey, stage)}
      </div>
    </section>
  `;
}

function renderDecisionWorkbenchStagePanel(surface, stage) {
  const workbench = surface?.decision_workbench || {};
  if (!workbench.version || !stage?.step_id) return "";
  if (stage.step_id === "journey_branch_calibration") {
    return renderDecisionConflictPanel(workbench);
  }
  if (stage.step_id === "journey_decision_verdicts") {
    return renderDecisionVerdictPanel(workbench, { title: "裁决卡片", compact: false });
  }
  if (stage.step_id === "journey_final_expression") {
    return renderDecisionFinalPanel(surface, workbench);
  }
  return "";
}

function renderDecisionConflictPanel(workbench) {
  const productCards = Array.isArray(workbench.product_projection?.branch_cards) ? workbench.product_projection.branch_cards : [];
  const cards = productCards.length ? productCards : (Array.isArray(workbench.conflict_cards) ? workbench.conflict_cards : []);
  const summary = workbench.summary || {};
  return `
    <section class="decision-workbench conflict">
      <div class="section-head compact">
        <p class="eyebrow">分支校准</p>
        <h3>需要确认的判断分支</h3>
      </div>
      <div class="decision-workbench-summary">
        ${renderDecisionMetric("分支", summary.branch_card_count ?? cards.length)}
        ${renderDecisionMetric("领域", summary.domain_count ?? "-")}
        ${renderDecisionMetric("证据覆盖", summary.signal_bound_candidate_count ?? "-")}
      </div>
      ${cards.length ? `
        <div class="decision-conflict-grid">
          ${cards.slice(0, 4).map(renderDecisionConflictCard).join("")}
        </div>
      ` : `<div class="history-empty">当前没有需要优先校准的高冲突分支，可以进入裁决。</div>`}
      ${workbench.calibration?.role_can_calibrate ? `
        <p class="decision-workbench-note">下方选择只用于校准判断权重，不改四柱、大运、流年和原始规则事实。</p>
      ` : ""}
    </section>
  `;
}

function renderDecisionConflictCard(card) {
  const types = Array.isArray(card.conflict_types) ? card.conflict_types : [];
  const gap = Number(card.confidence_gap || 0);
  const title = card.title || types.join("、") || "分支待校准";
  const summary = card.user_summary || card.resolution_policy || "先保留分支，等待更多证据。";
  const question = card.key_question || card.needed_question || "";
  return `
    <article class="decision-conflict-card">
      <div>
        <span>${escapeHtml(card.domain_label || domainLabel(card.domain || "整体"))}</span>
        <strong>${escapeHtml(title)}</strong>
      </div>
      <p>${escapeHtml(summary)}</p>
      ${question ? `<em>${escapeHtml(question)}</em>` : ""}
      <div class="decision-spark">
        <span style="--value:${Math.max(0, Math.min(1, Number(card.top_confidence || 0)))}"></span>
        <span style="--value:${Math.max(0, Math.min(1, Number(card.runner_up_confidence || 0)))}"></span>
      </div>
      <small>${escapeHtml(card.confidence_label || `差距 ${Math.round(gap * 100)}%`)}</small>
    </article>
  `;
}

function renderDecisionVerdictPanel(workbench, options = {}) {
  const cards = Array.isArray(workbench.verdict_cards) ? workbench.verdict_cards : [];
  if (!cards.length) return "";
  return `
    <section class="decision-workbench verdicts ${options.compact ? "compact" : ""}">
      <div class="section-head compact">
        <p class="eyebrow">Decision Engine</p>
        <h3>${escapeHtml(options.title || "裁决结果")}</h3>
      </div>
      <div class="decision-verdict-grid">
        ${cards.slice(0, options.compact ? 3 : 6).map(renderDecisionVerdictCard).join("")}
      </div>
    </section>
  `;
}

function renderDecisionVerdictCard(card) {
  const advice = Array.isArray(card.advice_points) ? card.advice_points : [];
  const level = assertionLevelLabel(card.assertion_level);
  return `
    <article class="decision-verdict-card ${escapeHtml(card.assertion_level || "")}">
      <div class="decision-card-head">
        <span>${escapeHtml(card.domain_label || domainLabel(card.domain || "整体"))}</span>
        <em>${escapeHtml(level)}</em>
      </div>
      <strong>${escapeHtml(card.headline || card.primary_text || "")}</strong>
      ${advice.length ? `<ul>${advice.slice(0, 2).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}
      <div class="decision-card-foot">
        <span>${Math.round(Number(card.confidence || 0) * 100)}%</span>
        ${card.has_alternative_branch ? "<i>有备选分支</i>" : ""}
        ${card.next_question_count ? "<i>可追问</i>" : ""}
      </div>
    </article>
  `;
}

function renderDecisionFinalPanel(surface, workbench) {
  const finalSynthesis = surface?.final_synthesis || {};
  const cards = Array.isArray(workbench.verdict_cards) ? workbench.verdict_cards : [];
  return `
    <section class="decision-workbench final">
      <div class="section-head compact">
        <p class="eyebrow">最终收束</p>
        <h3>${escapeHtml(finalSynthesis.decision_focus || "结论、建议与下一步问答")}</h3>
      </div>
      ${finalSynthesis.visual_hint ? renderDialogueVisualHint(finalSynthesis.visual_hint) : ""}
      ${cards.length ? `
        <div class="decision-verdict-grid">
          ${cards.slice(0, 3).map(renderDecisionVerdictCard).join("")}
        </div>
      ` : ""}
    </section>
  `;
}

function renderDecisionMetric(label, value) {
  return `
    <span>
      <em>${escapeHtml(label)}</em>
      <strong>${escapeHtml(value === undefined || value === null || value === "" ? "-" : value)}</strong>
    </span>
  `;
}

function assertionLevelLabel(level) {
  const labels = {
    confirmed: "确定",
    supported: "支持",
    mixed: "分支",
    weak_candidate: "候选",
    blocked: "暂缓",
  };
  return labels[String(level || "")] || level || "裁决";
}

function renderPractitionerOptionPanel(stage) {
  if (!isPractitionerLikeRole() || !stageReadyForInteraction(stage)) return "";
  const optionSets = practitionerStageOptionSets(stage);
  if (!optionSets.length) return "";
  return `
    <section class="practitioner-option-panel">
      <div class="section-head compact">
        <p class="eyebrow">命理师校准</p>
        <h3>选择更贴近实际的分支</h3>
      </div>
      <div class="practitioner-option-grid">
        ${optionSets.slice(0, 4).map(renderPractitionerOptionSet).join("")}
      </div>
    </section>
  `;
}

function practitionerStageOptionSets(stage) {
  const stageId = String(stage?.step_id || "");
  const stateRows = Array.isArray(currentPractitionerState?.option_sets) ? currentPractitionerState.option_sets : [];
  const byId = new Map(stateRows.map((row) => [row?.option_set_id, row]));
  const rawRows = Array.isArray(stage?.stage_point_set?.option_sets) ? stage.stage_point_set.option_sets : [];
  return uniquePractitionerOptionSets(rawRows
    .map((row) => ({ ...row, ...(byId.get(row?.option_set_id) || {}) }))
    .filter((row) => String(row?.stage_id || stageId) === stageId && Array.isArray(row?.options) && row.options.length));
}

function uniquePractitionerOptionSets(rows) {
  const seen = new Set();
  return rows.filter((row) => {
    const optionKey = (row.options || [])
      .map((option) => `${option.label || ""}:${option.meaning || ""}`.replace(/\s+/g, ""))
      .join("|");
    const key = `${row.title || ""}|${row.question || ""}|${optionKey}`.replace(/\s+/g, "");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function renderPractitionerOptionSet(optionSet) {
  const state = optionSet.selection_state || {};
  const latestAction = practitionerActionLabel(state.latest_action || "");
  return `
    <article class="practitioner-option-card" data-option-set-id="${escapeHtml(optionSet.option_set_id || "")}">
      <div class="practitioner-option-head">
        <div>
          <span>${escapeHtml(optionSet.title || "测算选项")}</span>
          <strong>${escapeHtml(optionSet.question || "这条判断如何处理？")}</strong>
        </div>
        ${latestAction ? `<em>${escapeHtml(latestAction)}</em>` : ""}
      </div>
      <div class="practitioner-option-list">
        ${(optionSet.options || []).slice(0, 5).map((option) => renderPractitionerOption(optionSet, option, state)).join("")}
      </div>
      <form class="practitioner-note-form" data-practitioner-option-note="${escapeHtml(optionSet.option_set_id || "")}">
        <input name="practitionerNote" maxlength="120" placeholder="备注给中枢，不改命盘事实" value="${escapeHtml(state.note || "")}">
        <button type="submit">备注</button>
      </form>
    </article>
  `;
}

function renderPractitionerOption(optionSet, option, state = {}) {
  const optionId = String(option.option_id || "");
  const selected = Array.isArray(state.selected_option_ids) && state.selected_option_ids.includes(optionId);
  const rejected = Array.isArray(state.rejected_option_ids) && state.rejected_option_ids.includes(optionId);
  const actions = practitionerOptionActions(option);
  return `
    <div class="practitioner-option-row ${selected ? "selected" : ""} ${rejected ? "rejected" : ""}">
      <div>
        <strong>${escapeHtml(option.label || option.value || optionId)}</strong>
        ${option.meaning ? `<span>${escapeHtml(option.meaning)}</span>` : ""}
      </div>
      <div class="practitioner-option-actions">
        ${actions.map((action) => `
          <button type="button" data-practitioner-option-action="${escapeHtml(action.action)}" data-option-set-id="${escapeHtml(optionSet.option_set_id || "")}" data-option-id="${escapeHtml(optionId)}">${escapeHtml(action.label)}</button>
        `).join("")}
      </div>
    </div>
  `;
}

function practitionerOptionActions(option) {
  const label = String(option?.label || "");
  if (/追问|待问/.test(label)) {
    return [{ action: "needs_question", label: "转追问" }];
  }
  if (/保留|备选/.test(label)) {
    return [
      { action: "select", label: "保留" },
      { action: "downrank", label: "降权" },
    ];
  }
  if (/采纳|主分支|优先/.test(label)) {
    return [
      { action: "select", label: "采纳" },
      { action: "rank", label: "置顶" },
    ];
  }
  return [
    { action: "select", label: "采纳" },
    { action: "needs_question", label: "追问" },
  ];
}

function practitionerActionLabel(action) {
  const labels = {
    select: "已采纳",
    rank: "已置顶",
    downrank: "已降权",
    reject: "已排除",
    needs_question: "待追问",
    note: "已备注",
  };
  return labels[String(action || "")] || "";
}

function renderStageDecisionTypewriter(text, isTyping, stageKey, stage) {
  return `
    <div class="final-decision-typewriter ${isTyping ? "typing" : ""}" data-stage-typewriter data-stage-key="${escapeHtml(stageKey)}">
      ${renderStageDecisionRows(text, isTyping, stage)}
    </div>
  `;
}

function renderStageDecisionRows(text, isTyping, stage = null) {
  const rows = stageDecisionRows(text, stage);
  if (!rows.length) {
    return `
      <ul class="stage-decision-list">
        <li class="stage-decision-item verdict">
          <span class="stage-decision-icon" aria-hidden="true">断</span>
          <span class="stage-decision-copy">${isTyping ? `<span class="typing-cursor"></span>` : ""}</span>
        </li>
      </ul>
    `;
  }
  return `
    <ul class="stage-decision-list">
      ${rows.map((row, index) => `
        <li class="stage-decision-item ${escapeHtml(row.kind)}">
          <span class="stage-decision-icon" aria-hidden="true">${escapeHtml(row.icon)}</span>
          <span class="stage-decision-copy">${escapeHtml(row.text)}${isTyping && index === rows.length - 1 ? `<span class="typing-cursor"></span>` : ""}</span>
        </li>
      `).join("")}
    </ul>
  `;
}

function stageDecisionRows(text, stage = null) {
  const reference = stageFinalDecisionPoints(stage);
  return String(text || "")
    .split(/\n+/)
    .map((line) => line.replace(/^[-•]\s*/, "").trim())
    .filter(Boolean)
    .map((line, index) => ({
      text: line,
      kind: stagePointUiKind(reference[index]?.kind || (index === 0 ? "verdict" : "advice")),
      icon: stagePointIcon(reference[index]?.kind || (index === 0 ? "verdict" : "advice")),
    }));
}

function renderLlmThinkingFailed(stage) {
  const message = stageLlmFailureMessage(stage);
  return `
    <div class="llm-thinking-loader failed" aria-live="polite">
      <div class="thinking-orbit" aria-hidden="true"><span></span><span></span><span></span></div>
      <div>
        <strong>推演未完成</strong>
        <p>${escapeHtml(message)}</p>
      </div>
    </div>
  `;
}

function stageLlmFailureMessage(stage) {
  const metadata = stage?.summary_panel?.llm_metadata || {};
  const reason = String(metadata.fallback_reason || "").trim();
  if (reason.includes("URLError") || reason.includes("Connection") || reason.includes("provider_not_ready")) {
    return metadata.user_message || "本页需要大模型推演，但当前没有连接到可用模型。请检查 Ollama/SSH 隧道后重试。";
  }
  if (reason.includes("timed") || reason.includes("Timeout")) {
    return "LLM 推演超时，本页没有收到可用结果。";
  }
  if (reason.includes("hard_boundary")) {
    return "LLM 返回内容触碰事实或安全边界，本页未采用。请重试这一页。";
  }
  if (reason.includes("acceptance")) {
    return "LLM 返回内容缺少本页需要的关键结论，本页暂不采用。";
  }
  if (reason.includes("stage_summary_policy")) {
    return "本页不需要 LLM 推演，已使用中枢规则小结。";
  }
  return "这一页暂时没有形成可用 LLM 结论，请检查模型连接后重试。";
}

function renderLlmThinkingLoader() {
  return `
    <div class="llm-thinking-loader" aria-live="polite">
      <div class="thinking-orbit" aria-hidden="true"><span></span><span></span><span></span></div>
      <div>
        <strong>正在推演</strong>
        <p>正在整理这一页的结论和建议。</p>
      </div>
    </div>
  `;
}

function renderPendingThinkingStream(stage) {
  const liveRows = liveStageThinkingRows(stage);
  const rows = liveRows.length ? liveRows : pendingStageThinkingRows(stage);
  if (!rows.length) return "";
  return `
    <div class="pending-thinking-stream" aria-live="polite">
      <strong>${liveRows.length ? "推演片段" : "正在核对"}</strong>
      <div>
        ${rows.slice(0, 3).map((row, index) => `<span style="--delay:${index * 1.25}s">${escapeHtml(row)}</span>`).join("")}
      </div>
    </div>
  `;
}

function visibleLlmThinkingSummary(stage) {
  const panel = stage?.summary_panel || {};
  const metadata = panel.llm_metadata || {};
  const body = String(panel.body || "").trim();
  if (!body) return "";
  if (metadata.status === "accepted") return body;
  const review = metadata.central_brain_review || {};
  if (panel.source === "central_brain_llm_expression" && review.status === "accepted") return body;
  return "";
}

function stageEnhancementState(stage) {
  if (!stage?.step_id || !formState.readingId) return "";
  return stageSummaryEnhancementState[`${formState.readingId}:${stage.step_id}`] || "";
}

function stageLlmDisplayState(stage) {
  if (!stage?.step_id) return "not_required";
  const policy = stage.summary_policy || stage.summary_panel?.summary_policy || {};
  if (policy.llm_enhancement !== "auto") return "not_required";
  if (visibleLlmThinkingSummary(stage)) return "accepted";
  const metadata = stage.summary_panel?.llm_metadata || {};
  const localState = stageEnhancementState(stage);
  if (["failed", "done"].includes(localState) || ["fallback", "unavailable"].includes(metadata.status)) return "failed";
  return "loading";
}

function renderPublicTrace(rows) {
  return `
    <div class="public-trace">
      <strong>本步公开推演</strong>
      ${rows.slice(0, 5).map((row) => `
        <span>
          <em>${escapeHtml(row.label || "推演")}</em>
          ${escapeHtml(row.text || "")}
        </span>
      `).join("")}
    </div>
  `;
}

function stageCoreTheme(stage) {
  const summary = String(stage?.summary || "").trim();
  if (summary) return surfaceDecisionText(summary);
  const panel = stage?.summary_panel || {};
  const title = String(panel.title || "").trim();
  return title && title !== stage?.title ? surfaceDecisionText(title) : "";
}

function stageFinalDecisionText(stage) {
  const points = stageFinalDecisionPoints(stage);
  if (points.length) {
    return points.map((point) => point.text).join("\n");
  }
  return "";
}

function stageFinalDecisionPoints(stage) {
  const analysis = stage?.analysis_result || {};
  const finalDecision = analysis.final_decision || {};
  const decision = analysis.summary_decision || {};
  const rawPoints = Array.isArray(stage?.stage_points) && stage.stage_points.length
    ? stage.stage_points
    : Array.isArray(finalDecision.stage_points) && finalDecision.stage_points.length
      ? finalDecision.stage_points
      : Array.isArray(stage?.stage_point_set?.selected_points) && stage.stage_point_set.selected_points.length
        ? stage.stage_point_set.selected_points
        : [];
  const points = rawPoints
    .map(normalizeStageDecisionPoint)
    .filter((point) => point.text);
  if (points.length) return projectStageDecisionPointsByRole(uniqueDecisionPoints(points));
  const conclusion = cleanStageDecisionLine(finalDecision.conclusion || analysis.conclusion || decision.conclusion || "");
  const advice = cleanStageDecisionLine(finalDecision.advice || analysis.next_focus || decision.advice || "");
  return uniqueDecisionLines([conclusion, advice]).map((line, index) => ({
    text: line,
    kind: index === 0 ? "verdict" : "advice",
    shortLabel: "",
  }));
}

function normalizeStageDecisionPoint(point) {
  const kind = String(point?.kind || "mechanism");
  const branchProbability = Number(point?.branch_probability || point?.probability || point?.confidence || 0);
  const isBranch = kind === "branch" || point?.is_branch_candidate === true || branchProbability > 0 && /候选|分支|取向|权重|概率|置信|可能/.test(String(point?.text || ""));
  const normalized = {
    text: cleanStageDecisionLine(point?.text || ""),
    kind: isBranch ? "branch" : kind,
    shortLabel: String(point?.short_label || ""),
    branchProbability: Number.isFinite(branchProbability) ? branchProbability : 0,
    isBranchCandidate: isBranch,
  };
  if (normalized.kind === "branch") {
    normalized.text = withBranchProbabilityLabel(normalized.text, normalized.branchProbability);
  }
  return normalized;
}

function projectStageDecisionPointsByRole(points) {
  const branchPoints = points.filter((point) => point.isBranchCandidate || point.kind === "branch");
  if (!branchPoints.length) return points.slice(0, isPractitionerLikeRole() ? 6 : 4);
  if (isPractitionerLikeRole()) return points.slice(0, 6);
  const primaryBranch = [...branchPoints].sort((a, b) => (b.branchProbability || 0) - (a.branchProbability || 0))[0];
  const nonBranch = points.filter((point) => !(point.isBranchCandidate || point.kind === "branch"));
  const projected = [];
  for (const point of points) {
    if (projected.length >= 4) break;
    if (point.isBranchCandidate || point.kind === "branch") {
      if (primaryBranch && point.text === primaryBranch.text && !projected.some((row) => row.text === point.text)) {
        projected.push(point);
      }
      continue;
    }
    projected.push(point);
  }
  if (primaryBranch && !projected.some((row) => row.text === primaryBranch.text)) {
    const insertAt = Math.min(projected.length, nonBranch.length ? 1 : 0);
    projected.splice(insertAt, 0, primaryBranch);
  }
  return projected.slice(0, 4);
}

function withBranchProbabilityLabel(text, probability) {
  const clean = String(text || "").trim();
  if (!clean) return "";
  if (!Number.isFinite(probability) || probability <= 0 || /权重|概率|置信|%/.test(clean)) return clean;
  const pct = Math.round(Math.min(1, Math.max(0, probability)) * 100);
  return `${clean}（权重约${pct}%）`;
}

function uniqueDecisionPoints(rows) {
  const seen = new Set();
  return rows.filter((row) => {
    const key = row.text.replace(/[，。；;,.]/g, "").slice(0, 36);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function stagePointUiKind(kind) {
  const normalized = String(kind || "");
  if (normalized === "advice") return "action";
  if (["verdict", "branch", "mechanism", "evidence", "risk", "question"].includes(normalized)) return normalized;
  return "mechanism";
}

function stagePointIcon(kind) {
  const icons = {
    verdict: "断",
    mechanism: "机",
    branch: "枝",
    evidence: "证",
    advice: "策",
    risk: "戒",
    question: "问",
  };
  return icons[String(kind || "")] || "点";
}

function uniqueDecisionLines(rows) {
  const seen = new Set();
  return rows
    .map((row) => String(row || "").trim())
    .filter(Boolean)
    .filter((row) => {
      const key = row.replace(/[，。；;,.]/g, "").slice(0, 36);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function cleanStageDecisionLine(value) {
  return surfaceDecisionText(value)
    .replace(/^(结论|建议|依据|判断|要点)\s*[：:]\s*/g, "")
    .replace(/^(先按|按照)([^，。；;]{1,18})(框架|口径)(复核|处理)/, "围绕$2核对")
    .replace(/若后续证据冲突[，,]?再降权修正。?/g, "证据不合的规则直接降权。")
    .replace(/强弱先判为/g, "强弱暂定为")
    .replace(/中和待复核/g, "中和偏平")
    .replace(/\s+/g, " ")
    .trim();
}

function surfaceDecisionText(value) {
  return String(value || "")
    .replace(/Gemma4|token|JSON|boundary|metadata|fallback|quality gate|质量门槛/gi, "")
    .replace(/keep_both_branches_until_decision_engine_or_practitioner_calibration_separates_weight/g, "主分支和备选先同时保留，等待反馈拉开权重")
    .replace(/ask_only_if_value_of_information_exceeds_user_cost/g, "只有这个问题能明显改变判断时再追问")
    .replace(/downgrade_assertion_level_unless_counter_evidence_is_resolved/g, "反证未解决前，断语先降一档")
    .replace(/请提供/g, "补充")
    .replace(/请您/g, "")
    .replace(/本次分析|当前阶段|目前阶段|当前|目前/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function renderStageEvidenceDigest(evidence, stage) {
  const digest = stage?.evidence_digest || {};
  const digestItems = Array.isArray(digest.items) ? digest.items.filter(Boolean) : [];
  const labels = digestItems.length ? digestItems : evidence.slice(0, 5).map((row) => readableEvidenceLabel(row, stage));
  const title = String(digest.title || "依据");
  const body = String(digest.body || `影响本步结论的关键依据有 ${evidence.length} 条；只展示可读要点。`);
  return `
    <div class="stage-evidence-digest">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(body)}</p>
      <div>
        ${labels.map((row, index) => `<span style="--delay:${520 + index * 70}ms">${escapeHtml(row)}</span>`).join("")}
      </div>
    </div>
  `;
}

function readableEvidenceLabel(value, stage) {
  const raw = String(value || "");
  const stepId = String(stage?.step_id || "");
  if (stepId === "chart_build") {
    if (raw.includes("context_id")) return "命盘上下文已建立";
    if (raw.includes("source=")) return "出生资料来自本次用户输入";
    return "排盘基础证据";
  }
  if (stepId === "knowledge_library") {
    if (raw.includes("branch_relation")) return "地支关系与动态作用知识";
    if (raw.includes("career")) return "事业路径判断知识";
    if (raw.includes("domain_rule")) return "领域规则门槛";
    if (raw.includes("boundary")) return "命盘事实边界规则";
    if (raw.includes("counterevidence")) return "反证与复核规则";
    return "知识库条目";
  }
  if (stepId === "rule_matching") {
    if (raw.includes("useful_god")) return "用神候选需要复核";
    if (raw.includes("hidden_factor")) return "存在需要用户校准的隐藏线索";
    if (raw.includes("ten_god")) return "十神显隐关系参与判断";
    if (raw.includes("branch_relation")) return "地支关系触发结构复核";
    return "规则命中项";
  }
  if (stepId === "feature_extraction") {
    if (raw.includes("day_master")) return "日主与五行基础特征";
    if (raw.includes("ten_god")) return "十神显隐特征";
    if (raw.includes("element")) return "五行分布特征";
    return "八字特征证据";
  }
  if (stepId === "portrait_projection") return "画像倾向证据";
  if (stepId === "path_reasoning") return "结构或做功路径证据";
  if (stepId === "useful_god_arbitration") {
    if (raw.includes("avoidance") || raw.includes("risk")) return "忌避风险边界";
    if (raw.includes("candidate") || raw.includes("strategy")) return "用神候选策略";
    return "用神忌神取舍证据";
  }
  return raw.length > 46 ? `${raw.slice(0, 45)}...` : raw;
}

function stageTypewriterKey(stage) {
  if (!stage) return "";
  return `${stage.step_id || ""}:${stageLlmDisplayState(stage)}:${stageNarrationText(stage).length}`;
}

function prepareStageTypewriter(stage) {
  if (!stage || !stage.step_id) {
    if (stageTypewriter.timer) window.clearTimeout(stageTypewriter.timer);
    stageTypewriter = { key: "", fullText: "", visibleText: "", active: false, timer: null };
    return;
  }
  const key = stageTypewriterKey(stage);
  const fullText = stageNarrationText(stage);
  if (stageTypewriter.key === key) return;
  if (stageTypewriter.timer) window.clearTimeout(stageTypewriter.timer);
  stageTypewriter = {
    key,
    fullText,
    visibleText: "",
    active: Boolean(fullText),
    timer: null,
  };
  updateStageTypewriterDom();
  scheduleStageTypewriterTick();
}

function scheduleStageTypewriterTick() {
  if (!stageTypewriter.active) return;
  stageTypewriter.timer = window.setTimeout(() => {
    const remaining = stageTypewriter.fullText.length - stageTypewriter.visibleText.length;
    if (remaining <= 0) {
      stageTypewriter = { ...stageTypewriter, active: false, timer: null };
      updateStageTypewriterDom();
      renderReading();
      return;
    }
    const step = 1;
    stageTypewriter = {
      ...stageTypewriter,
      visibleText: stageTypewriter.fullText.slice(0, stageTypewriter.visibleText.length + step),
    };
    updateStageTypewriterDom();
    scheduleStageTypewriterTick();
  }, 42);
}

function updateStageTypewriterDom() {
  const el = document.querySelector("[data-stage-typewriter]");
  if (!el || el.getAttribute("data-stage-key") !== stageTypewriter.key) return;
  el.innerHTML = renderStageDecisionRows(stageTypewriter.visibleText, stageTypewriter.active, currentAnalysisStage());
}

function stageNarrationText(stage) {
  if (!stage) return "";
  const policy = stage.summary_policy || stage.summary_panel?.summary_policy || {};
  if (policy.llm_enhancement === "auto") {
    const state = stageLlmDisplayState(stage);
    if (state === "accepted" || state === "not_required") return stageFinalDecisionText(stage);
    return state === "failed" ? "" : pendingStageThinkingText(stage);
  }
  return stageFinalDecisionText(stage);
}

function pendingStageThinkingText(stage) {
  return pendingStageThinkingRows(stage).join(" ");
}

function liveStageThinkingRows(stage) {
  if (!stage?.step_id || !formState.readingId) return [];
  const key = `${formState.readingId}:${stage.step_id}`;
  const raw = String(stageThinkingStreamText[key] || "").replace(/\s+/g, " ").trim();
  if (!raw) return [];
  const chunks = raw
    .split(/(?<=[。！？.!?])\s+/)
    .map((row) => row.trim())
    .filter(isCustomerVisibleThinkingRow);
  const rows = chunks.length >= 2 ? chunks.slice(-3) : raw.match(/.{1,54}/g) || [];
  return rows.filter(isCustomerVisibleThinkingRow).slice(-3);
}

function isCustomerVisibleThinkingRow(row) {
  const text = String(row || "").trim();
  if (!text) return false;
  if (!/[\u3400-\u9fff]/.test(text)) return false;
  const lowered = text.toLowerCase();
  const blocked = [
    "json",
    "required key",
    "required keys",
    "is it ",
    "is the ",
    "concrete",
    "structure correct",
    "markdown",
    "schema",
    "internal id",
  ];
  if (blocked.some((token) => lowered.includes(token))) return false;
  if (/^[*#>\-\s]+/.test(text)) return false;
  return true;
}

function pendingStageThinkingRows(stage) {
  const analysis = stage?.analysis_result || {};
  const trace = Array.isArray(analysis.public_trace) ? analysis.public_trace : [];
  const usefulRows = trace.filter((row) => {
    const label = String(row?.label || "");
    return label && !label.includes("结论") && !label.includes("执行建议") && !label.includes("报告");
  }).slice(0, 4);
  if (usefulRows.length) {
    return usefulRows.map((row) => {
      const label = String(row?.label || "证据").trim();
      const text = String(row?.text || "").trim();
      return text ? `核对${label}：${text}` : "";
    }).filter(Boolean);
  }
  const reasoning = Array.isArray(analysis.reasoning_points) ? analysis.reasoning_points : [];
  if (reasoning.length) {
    return reasoning.slice(0, 3).map((row) => `核对依据：${row}`);
  }
  return ["正在核对本页命盘证据、规则信号和路径关系。"];
}

function renderStageInteractionSlot(context, stage) {
  if (!stageReadyForInteraction(stage)) return "";
  const shouldShowAnswer = shouldRenderAnswerForStage(context.answer, stage);
  const answerHtml = shouldShowAnswer ? renderAnswerPanel(context.answer) : "";
  const probe = calibrationProbeForStage(context.surface, stage);
  const question = shouldRenderQuestionAfterAnswer(shouldShowAnswer ? context.answer : null, probe ? calibrationProbeQuestion(probe) : null)
    ? calibrationProbeQuestion(probe)
    : null;
  if (!answerHtml && !question?.question_id) return "";
  return `
    ${answerHtml}
    ${question?.question_id ? renderFocusedQuestionPanel(question, stage, calibrationProbeTurn(probe)) : ""}
  `;
}

function shouldRenderQuestionAfterAnswer(answer, question) {
  if (!question?.question_id) return false;
  const answerQuestionId = String(answer?.question_id || "").trim();
  if (answerQuestionId && answerQuestionId === String(question.question_id || "").trim()) return false;
  return true;
}

function stageReadyForInteraction(stage) {
  if (!stage?.step_id) return false;
  const state = stageLlmDisplayState(stage);
  if (!(state === "accepted" || state === "not_required")) return false;
  return stageConclusionTypewriterComplete(stage);
}

function stageConclusionTypewriterComplete(stage) {
  const text = stageNarrationText(stage);
  if (!text) return true;
  const key = stageTypewriterKey(stage);
  if (stageTypewriter.key !== key) return false;
  return !stageTypewriter.active && stageTypewriter.visibleText.length >= stageTypewriter.fullText.length;
}

function calibrationProbeForStage(surface, stage) {
  const calibration = surface?.calibration_surface || surface?.surface_orchestrator?.calibration_surface || {};
  const cards = Array.isArray(calibration.visible_probe_cards) ? calibration.visible_probe_cards : [];
  if (!stage?.step_id || calibration.status !== "available" || !cards.length) return null;
  const materialIds = Array.isArray(stage.material_stage_ids) ? stage.material_stage_ids.map((row) => String(row || "")) : [];
  return cards.find((card) => {
    const stageId = String(card?.stage_id || "").trim();
    if (!stageId) return false;
    return stageId === stage.step_id || materialIds.includes(stageId);
  }) || null;
}

function calibrationProbeQuestion(probe) {
  if (!probe?.question_id) return null;
  return {
    question_id: probe.question_id,
    label: probe.prompt || probe.title || "校准这个判断",
    topic: probe.topic || "hidden_factor",
    answer_constraints: probe.answer_constraints || {},
    response_option_set: probe.response_option_set || {},
    submit_contract: probe.submit_contract || {
      version: "v30.surface_submit_contract.v1",
      submit_surface: "calibration_surface",
      submit_source_id: probe.card_id || `probe:${probe.question_id}`,
    },
    options: Array.isArray(probe.options) ? probe.options : [],
  };
}

function calibrationProbeTurn(probe) {
  if (!probe) return null;
  return {
    action: "ask",
    stage_id: probe.stage_id || "",
    why_now: probe.reason || "只补一个会影响本页判断的关键背景。",
    visual_hint: probe.visual_hint || {},
    surface_source: "calibration_surface",
  };
}

function renderFocusedQuestionPanel(question, stage, turn = null) {
  return `
    <section class="question-band focused-question-panel">
      <div class="section-head compact">
        <p class="eyebrow">智能追问</p>
        <h3>${escapeHtml(focusedQuestionTitle(stage, turn))}</h3>
      </div>
      ${turn?.visual_hint ? renderDialogueVisualHint(turn.visual_hint) : ""}
      <div class="question-action-list focused">
        ${renderQuestionAction(question, 0)}
      </div>
    </section>
  `;
}

function focusedQuestionTitle(stage, turn = null) {
  if (turn?.why_now) return turn.why_now;
  return "这里只补一个关键背景";
}

function renderDialogueVisualHint(visual) {
  const chips = Array.isArray(visual?.chips) ? visual.chips : [];
  const markers = Array.isArray(visual?.markers) ? visual.markers : [];
  if (!chips.length && !markers.length && !visual?.guidance) return "";
  return `
    <div class="dialogue-visual-hint ${escapeHtml(visual.kind || "advice_compass")}">
      <div>
        <strong>${escapeHtml(visual.title || "本轮判断焦点")}</strong>
        ${visual.guidance ? `<p>${escapeHtml(visual.guidance)}</p>` : ""}
      </div>
      ${chips.length ? `
        <div class="dialogue-visual-chips">
          ${chips.slice(0, 4).map((chip) => `<span>${escapeHtml(chip)}</span>`).join("")}
        </div>
      ` : ""}
      ${markers.length ? `
        <div class="dialogue-visual-markers">
          ${markers.slice(0, 2).map((marker) => {
            const value = Math.max(0, Math.min(1, Number(marker.value || 0)));
            return `<span><em>${escapeHtml(marker.label || "")}</em><i style="--value:${value}"></i></span>`;
          }).join("")}
        </div>
      ` : ""}
    </div>
  `;
}

function shouldRenderAnswerForStage(answer, stage) {
  if (!answer?.text || !stage?.step_id) return false;
  if (!answerHasUserSubmission(answer)) return false;
  return answerBelongsToStage(answer, stage);
}

function answerHasUserSubmission(answer) {
  if (!answer?.text) return false;
  if (answer.user_submitted === true) return true;
  if (String(answer.user_reply || "").trim()) return true;
  const source = String(answer.source || "");
  const stageId = String(answer.question_stage_id || answer.stage_id || "").trim();
  return Boolean(stageId && ["pending", "llm_pending", "llm_not_ready"].includes(source));
}

function answerBelongsToStage(answer, stage) {
  const answerStageId = String(answer?.question_stage_id || answer?.stage_id || "").trim();
  return Boolean(answerStageId && stage?.step_id && answerStageId === stage.step_id);
}

function readableQuestionGain(value) {
  const key = String(value || "").trim().toLowerCase().replace(/\s+/g, "_");
  const labels = {
    answer_career_direction: "确认事业方向",
    answer_wealth_tendency: "确认财务关注点",
    answer_relationship_pattern: "确认关系模式",
    answer_timing_pressure: "确认近期时运压力",
    answer_decision_blindspot: "确认决策盲点",
  };
  return labels[key] || key.replace(/_/g, " ");
}

function renderHistoryList() {
  const items = Array.isArray(readingHistory?.items) ? readingHistory.items : [];
  if (!items.length) {
    return `<div class="history-empty">读取后会显示当前用户/会话下的测算档案。</div>`;
  }
  return `
    <div class="history-list">
      ${items.slice(0, 8).map(renderHistoryItem).join("")}
    </div>
  `;
}

function renderHistoryItem(item) {
  const readingId = item.reading_id || "";
  const title = item.title || item.reading_title || readingId || "未命名测算";
  const status = item.chart_status || item.status || "ready";
  const next = item.visible_next_question_id || "";
  const label = title === readingId ? `档案 ${readingId.slice(-6)}` : title;
  return `
    <button type="button" class="history-item" data-open-reading="${escapeHtml(readingId)}" data-profile-label="${escapeHtml(label)}">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(status)}${next ? ` · ${escapeHtml(next)}` : ""}</span>
    </button>
  `;
}

function renderCoreBaziReading(core) {
  if (!core || core.surface_type !== "core_bazi_calculation") return "";
  const pillars = Array.isArray(core.four_pillars) ? core.four_pillars : [];
  const visible = Array.isArray(core.visible_ten_gods) ? core.visible_ten_gods : [];
  const hidden = Array.isArray(core.hidden_ten_gods) ? core.hidden_ten_gods : [];
  const visibleByPosition = Object.fromEntries(visible.map((row) => [row.position, row]));
  const hiddenByBranch = hidden.reduce((acc, row) => {
    const key = row.branch || "";
    if (!acc[key]) acc[key] = [];
    acc[key].push(row);
    return acc;
  }, {});
  const relations = Array.isArray(core.relations) ? core.relations : [];
  const decisions = core.ranked_decisions || {};
  const elements = core.five_elements || {};
  const modelSignal = core.model_signal_summary || {};
  const domains = Array.isArray(core.practical_domains) ? core.practical_domains : [];
  const explanations = core.base_fact_explanations || {};
  const integrity = core.fact_integrity || {};
  return `
    <section class="core-bazi-band">
      <div class="section-head">
        <p class="eyebrow">核心八字测算</p>
        <h2>日主 ${escapeHtml(core.day_master || "-")} · ${escapeHtml(core.day_master_element || "")}</h2>
      </div>
      ${renderCalculationStatusStrip(integrity)}
      <div class="core-pillar-grid">
        ${pillars.map((row) => renderCorePillar(row, visibleByPosition, hiddenByBranch, core.day_master)).join("")}
      </div>
      ${renderBaseExplanationPanel(explanations)}
      <div class="core-detail-grid">
        ${renderElementPanel(elements)}
        ${renderTenGodPanel("天干十神", visible)}
        ${renderTenGodPanel("地支藏干", hidden)}
      </div>
      ${renderDecisionPanel(decisions)}
      ${relations.length ? `
        <div class="relation-list">
          ${relations.map(renderRelation).join("")}
        </div>
      ` : ""}
      ${modelSignal.top_energy?.length ? `
        <div class="signal-line">
          <span>十神重点</span>
          <strong>${modelSignal.top_energy.slice(0, 4).map((row) => escapeHtml(row)).join(" / ")}</strong>
        </div>
      ` : ""}
      ${domains.length ? `
        <div class="practical-list">
          ${domains.slice(0, 3).map(renderPracticalSummary).join("")}
        </div>
      ` : ""}
    </section>
  `;
}

function renderCalculationStatusStrip(integrity) {
  const facts = [
    integrity.deterministic === false ? "资料待确认" : "四柱已排定",
    integrity.llm_generated ? "表达含润色" : "命盘由规则排定",
    integrity.training_generated ? "含训练参考" : "训练不改命盘",
  ];
  return `
    <div class="fact-integrity-strip">
      ${facts.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
    </div>
  `;
}

function renderCorePillar(row, visibleByPosition = {}, hiddenByBranch = {}, dayMaster = "") {
  const layer = row.layer || "";
  const stem = row.stem || splitPillar(row.pillar).stem;
  const branch = row.branch || splitPillar(row.pillar).branch;
  const stemTenGod = layer === "day" ? "日主" : visibleByPosition[layer]?.ten_god || inferTenGod(dayMaster, stem);
  const hiddenRows = hiddenByBranch[layer] || hiddenTenGodsForBranch(branch, dayMaster);
  return `
    <div class="core-pillar">
      <span>${escapeHtml(row.label || row.layer || "")}</span>
      <div class="pillar-stack">
        <div class="pillar-cell stem-cell">
          <em>${escapeHtml(stemTenGod || "-")}</em>
          <strong>${escapeHtml(stem || "-")}</strong>
          <small>天干</small>
        </div>
        <div class="pillar-cell branch-cell">
          <em>${escapeHtml(formatHiddenTenGods(hiddenRows))}</em>
          <strong>${escapeHtml(branch || "-")}</strong>
          <small>地支</small>
        </div>
      </div>
    </div>
  `;
}

function formatHiddenTenGods(rows) {
  const values = (Array.isArray(rows) ? rows : [])
    .map((row) => row.ten_god || (row.stem ? inferTenGod("", row.stem) : ""))
    .filter(Boolean);
  return values.length ? `藏 ${values.slice(0, 3).join("/")}` : "藏干";
}

function renderElementPanel(elements) {
  const rows = Object.entries(elements || {}).slice(0, 8);
  const max = Math.max(...rows.map(([, value]) => Number(value) || 0), 1);
  return `
    <div class="core-panel element-panel">
      <p class="eyebrow">五行分布</p>
      <div class="element-bars">
        ${rows.length ? rows.map(([key, value]) => {
          const pct = Math.max(4, Math.round(((Number(value) || 0) / max) * 100));
          return `
            <div class="element-row">
              <span>${escapeHtml(elementLabel(key))}</span>
              <div class="bar"><i style="width:${pct}%"></i></div>
              <strong>${escapeHtml(value)}</strong>
            </div>
          `;
        }).join("") : "<span>待生成</span>"}
      </div>
    </div>
  `;
}

function renderTenGodPanel(title, rows) {
  return `
    <div class="core-panel ten-god-panel">
      <p class="eyebrow">${escapeHtml(title)}</p>
      <div class="ten-god-list">
        ${rows.length ? rows.slice(0, 8).map((row) => `
          <div>
            <span>${escapeHtml(positionLabel(row.position || row.branch || ""))}</span>
            <strong>${escapeHtml(row.stem || "")}</strong>
            <em>${escapeHtml(row.ten_god || "")}${row.weight ? ` · ${escapeHtml(row.weight)}` : ""}</em>
          </div>
        `).join("") : "<span>待生成</span>"}
      </div>
    </div>
  `;
}

function renderDecisionPanel(decisions) {
  const rows = [
    ["旺衰强弱", decisions.strength],
    ["结构格局", decisions.structure_pattern],
    ["用神取向", decisions.useful_god],
  ].filter(([, row]) => Boolean(row));
  return `
    <div class="decision-panel">
      <div class="section-head compact">
        <p class="eyebrow">命局判断</p>
        <h3>旺衰、格局、用神取向</h3>
      </div>
      <div class="decision-card-grid">
        ${rows.length ? rows.map(([fallbackLabel, row]) => renderDecisionCard(fallbackLabel, row)).join("") : "<span>待生成命局判断</span>"}
      </div>
    </div>
  `;
}

function renderDecisionCard(fallbackLabel, row) {
  const alternatives = Array.isArray(row.alternatives) ? row.alternatives : [];
  const confidence = typeof row.confidence === "number" ? Math.round(row.confidence * 100) : "";
  return `
    <article class="decision-card">
      <span>${escapeHtml(row.label || fallbackLabel)}</span>
      <strong>${escapeHtml(candidateLabel(row.primary_candidate || row.status || ""))}</strong>
      ${confidence !== "" ? `<div class="confidence-meter"><i style="width:${confidence}%"></i></div>` : ""}
      ${alternatives.length ? `<p>${alternatives.slice(0, 3).map(candidateLabel).map(escapeHtml).join(" / ")}</p>` : ""}
    </article>
  `;
}

function renderStructureDynamics(payload) {
  if (!payload || payload.version !== "v30.structure_dynamics_surface.v1") return "";
  const domains = payload.domain_path_counts || {};
  const mechanisms = payload.mechanism_counts || {};
  const paths = Array.isArray(payload.top_paths) ? payload.top_paths : [];
  return `
    <section class="structure-dynamics-band">
      <div class="section-head">
        <p class="eyebrow">${escapeHtml(payload.label || "结构动态")}</p>
        <h2>${escapeHtml(payload.summary || "结构动态已进入当前测算。")}</h2>
        <p>${escapeHtml(payload.emphasis || "结合四柱、大运和流年观察结构如何变化。")}</p>
      </div>
      <div class="structure-metric-grid">
        ${renderStructureMetric("动态路径", payload.dynamic_path_count)}
        ${renderStructureMetric("承接类型", payload.resolution_family_count)}
        ${renderStructureMetric("冲突类型", payload.conflict_family_count)}
        ${renderStructureMetric("通关/制化", `${mechanisms.tongguan || 0}/${mechanisms.zhihua || 0}`)}
      </div>
      <div class="structure-domain-grid">
        ${renderStructureDomain("财运", domains.wealth)}
        ${renderStructureDomain("事业", domains.career)}
        ${renderStructureDomain("关系", domains.relationship)}
        ${renderStructureDomain("健康", domains.health)}
        ${renderStructureDomain("用神", domains.useful_god)}
      </div>
      ${paths.length ? `
        <div class="structure-path-list">
          ${paths.map(renderStructurePath).join("")}
        </div>
      ` : `<div class="history-empty">当前结构动态路径仍待更多证据校准。</div>`}
    </section>
  `;
}

function renderBasicAssertions(rows) {
  const items = Array.isArray(rows) ? rows : [];
  if (!items.length) return "";
  return `
    <section class="product-reading-band assertion-band">
      <div class="section-head">
        <p class="eyebrow">基本断语</p>
        <h2>先看命盘给出的明确倾向</h2>
      </div>
      <div class="assertion-grid">
        ${items.slice(0, 6).map((row) => `
          <article class="assertion-card">
            <span>${escapeHtml(domainLabel(row.domain || row.kind || ""))}</span>
            <strong>${escapeHtml(row.title || row.assertion || row.statement || "命盘判断")}</strong>
            <p>${escapeHtml(row.text || row.summary || row.evidence || "")}</p>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderProductLayerBand(title, subtitle, rows, renderer) {
  const items = Array.isArray(rows) ? rows : [];
  if (!items.length) return "";
  return `
    <section class="product-reading-band">
      <div class="section-head">
        <p class="eyebrow">${escapeHtml(title)}</p>
        <h2>${escapeHtml(subtitle)}</h2>
      </div>
      <div class="product-card-grid">
        ${items.slice(0, 6).map(renderer).join("")}
      </div>
    </section>
  `;
}

function renderBaziFeatureCard(row) {
  const body = row.statement || row.summary || row.description || row.evidence_summary || "";
  const evidence = Array.isArray(row.evidence_labels) ? row.evidence_labels.slice(0, 3).join(" · ") : "";
  return `
    <article class="product-card feature-card">
      <span>${escapeHtml(domainLabel(row.domain || row.feature_domain || ""))}</span>
      <strong>${escapeHtml(row.title || row.label || "八字特征")}</strong>
      <p>${escapeHtml(body)}</p>
      ${evidence ? `<em>${escapeHtml(evidence)}</em>` : ""}
    </article>
  `;
}

function renderBaziPortraitCard(row) {
  const body = row.statement || row.summary || row.expression || row.description || "";
  const evidence = Array.isArray(row.evidence_labels) ? row.evidence_labels.slice(0, 3).join(" · ") : "";
  return `
    <article class="product-card portrait-card">
      <span>${escapeHtml(domainLabel(row.domain || row.portrait_domain || ""))}</span>
      <strong>${escapeHtml(row.title || row.label || "八字画像")}</strong>
      <p>${escapeHtml(body)}</p>
      ${evidence ? `<em>${escapeHtml(evidence)}</em>` : ""}
    </article>
  `;
}

function renderBaziPathCard(row) {
  const tags = [
    row.domain ? domainLabel(row.domain) : "",
    Array.isArray(row.domain_impact) ? row.domain_impact.slice(0, 2).join(" / ") : "",
    row.state ? pathStateLabel(row.state) : "",
    row.strength_band ? strengthBandLabel(row.strength_band) : "",
    row.confidence_band ? strengthBandLabel(row.confidence_band) : "",
  ].filter(Boolean);
  const body = row.meaning || row.summary || row.path_summary || row.action_boundary || "";
  const detail = row.why_active || row.uncertainty_boundary || "";
  return `
    <article class="product-card path-card">
      <span>${tags.map(escapeHtml).join(" · ") || "动态路径"}</span>
      <strong>${escapeHtml(row.title || row.label || row.path_label || row.path_summary || "动态路径")}</strong>
      <p>${escapeHtml(body)}</p>
      ${detail ? `<em>${escapeHtml(detail)}</em>` : ""}
      ${Array.isArray(row.path_assertions) && row.path_assertions.length ? `
        <div class="path-mini-list">
          ${row.path_assertions.slice(0, 3).map((item) => `<i>${escapeHtml(item)}</i>`).join("")}
        </div>
      ` : ""}
    </article>
  `;
}

function renderStructureMetric(label, value) {
  return `
    <div class="structure-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value ?? 0)}</strong>
    </div>
  `;
}

function renderStructureDomain(label, value) {
  return `
    <span class="structure-domain-chip">
      ${escapeHtml(label)} · ${escapeHtml(value ?? 0)}
    </span>
  `;
}

function renderStructurePath(row) {
  const chain = Array.isArray(row.chain) ? row.chain.join(" → ") : "";
  const resolutions = Array.isArray(row.resolution_labels) ? row.resolution_labels : [];
  const conflicts = Array.isArray(row.conflict_labels) ? row.conflict_labels : [];
  return `
    <article class="structure-path-card ${escapeHtml(row.strength_band || "medium")}">
      <div>
        <span>${escapeHtml(pathStateLabel(row.state || ""))} · ${escapeHtml(strengthBandLabel(row.strength_band || ""))}</span>
        <strong>${escapeHtml(chain || "结构路径")}</strong>
        <p>${escapeHtml(row.summary || "")}</p>
      </div>
      <div class="structure-path-tags">
        ${resolutions.slice(0, 3).map((item) => `<em>${escapeHtml(item)}</em>`).join("")}
        ${conflicts.slice(0, 2).map((item) => `<em class="warn">${escapeHtml(item)}</em>`).join("")}
      </div>
    </article>
  `;
}

function renderBaseExplanationPanel(explanations) {
  if (!explanations || explanations.version !== "v30.base_bazi_fact_explanations.v1") return "";
  const tenGods = explanations.ten_gods || {};
  const elements = explanations.five_elements || {};
  const roots = explanations.roots_and_vaults || {};
  return `
    <div class="base-explain-grid">
      ${renderExplainCard(explanations.day_master)}
      ${renderExplainCard({
        label: tenGods.label || "十神",
        value: `${tenGods.visible_count || 0} 透出 / ${tenGods.hidden_count || 0} 藏干`,
        explanation: tenGods.explanation || "",
      })}
      ${renderExplainCard({
        label: elements.label || "五行",
        value: `${(elements.strongest_elements || []).map(elementLabel).join("/") || "-"} 旺 · ${(elements.weakest_elements || []).map(elementLabel).join("/") || "-"} 弱`,
        explanation: elements.explanation || "",
      })}
      ${renderExplainCard({
        label: roots.label || "根气 / 库墓",
        value: `${roots.same_element_root_count || 0} 根 · ${(roots.vault_branches || []).length} 库`,
        explanation: roots.explanation || "",
      })}
    </div>
  `;
}

function renderExplainCard(row) {
  if (!row) return "";
  return `
    <article class="explain-card">
      <span>${escapeHtml(row.label || "")}</span>
      <strong>${escapeHtml(row.value || row.element || "-")}</strong>
      <p>${escapeHtml(row.explanation || "")}</p>
    </article>
  `;
}

function renderRelation(row) {
  const branches = Array.isArray(row.branches) ? row.branches.join("/") : row.branches || "";
  return `<span>${escapeHtml(relationLabel(row.relation || "关系"))} ${escapeHtml(branches)}</span>`;
}

function renderPracticalSummary(row) {
  return `
    <article>
      <strong>${escapeHtml(row.label || row.domain || "")}</strong>
      <p>${escapeHtml(row.customer_takeaway || row.summary || "")}</p>
    </article>
  `;
}

function elementLabel(key) {
  const labels = { wood: "木", fire: "火", earth: "土", metal: "金", water: "水" };
  return labels[key] || key;
}

function positionLabel(key) {
  const labels = { year: "年", month: "月", day: "日", hour: "时" };
  return labels[key] || key;
}

function relationLabel(key) {
  const labels = {
    harmony: "合",
    clash: "冲",
    punishment: "刑",
    harm: "害",
    break: "破",
    three_meeting: "三会",
    half_combo: "半合",
    combo: "合",
    six_harmony: "六合",
    three_harmony: "三合",
  };
  return labels[key] || key;
}

function candidateLabel(key) {
  const labels = {
    weak: "偏弱",
    slightly_weak: "略弱",
    balanced: "平衡",
    slightly_strong: "略强",
    strong: "偏强",
    dynamic_structure_review: "动态结构",
    ordinary_structure_review: "常规格局",
    special_structure_boundary_review: "特殊格局",
    follow_structure_boundary_review: "从格边界",
    resource_or_self_support_review: "印比扶身",
    balance_review: "平衡调候",
    output_or_wealth_release_review: "食伤财星泄秀",
    authority_regulation_review: "官杀约束",
    needs_time_layer_review: "看大运流年",
    mediation_path_review: "通关承接",
    regulation_climate_boundary_review: "调候制化",
    disputed_structure_review: "结构分歧",
  };
  return labels[key] || key;
}

function boundaryLabel(value) {
  return "";
}

function structureBoundaryLabel(value) {
  if (!value) return "";
  return "";
}

function pathStateLabel(value) {
  const labels = {
    closed: "闭合路径",
    open: "开放路径",
    blocked: "受阻路径",
    volatile: "波动路径",
    partial: "部分成立",
  };
  return labels[value] || value || "路径";
}

function strengthBandLabel(value) {
  const labels = {
    high: "强",
    medium: "中",
    low: "弱",
  };
  return labels[value] || value || "中";
}

function renderRoleSurface(roleProfile) {
  if (!roleProfile || !roleProfile.surface) return "";
  const roleKey = normalizeMainSystemRole(roleProfile.role_key || formState.role);
  const facts = roleKey === "practitioner"
      ? ["命理师视图", "结构路径与复核要点"]
      : ["用户测算", "展示命盘摘要、领域解读和连续问答"];
  return `
    <section class="role-surface-band ${escapeHtml(roleKey)}">
      <div>
        <p class="eyebrow">当前页面</p>
        <h2>${escapeHtml(roleProfile.label || productRoleLabel(formState.role))}</h2>
        <p>${escapeHtml(productRoleHelper(formState.role))}</p>
      </div>
      <div class="facts">
        ${facts.map((row) => `<span>${escapeHtml(row)}</span>`).join("")}
      </div>
    </section>
  `;
}

function renderSixPillarBand(timeContext, coreReading = {}) {
  const sixPillars = Array.isArray(timeContext.six_pillars) ? timeContext.six_pillars : [];
  const cycles = Array.isArray(timeContext.luck_cycles) ? timeContext.luck_cycles : [];
  if (!sixPillars.length && !cycles.length) return "";
  const currentLuck = timeContext.current_luck || {};
  const currentPillar = currentLuck.pillar || "";
  const dayMaster = coreReading.day_master || "";
  const latent = coreReading.latent_bazi_attributes || {};
  return `
    <section class="time-band">
      <div class="section-head">
        <p class="eyebrow">六柱与流年</p>
        <h2>${escapeHtml(timeContext.target_year || formState.targetYear)} 流年 · ${escapeHtml(timeContext.flow_year_pillar || "")}</h2>
      </div>
      <div class="pillar-grid">
        ${sixPillars.map((row) => renderPillarTile(row, dayMaster)).join("")}
      </div>
      ${renderLatentAttributeSummary(latent)}
      <div class="luck-panel">
        <div>
          <p class="eyebrow">当前大运</p>
          ${currentPillar ? renderMiniPillarStack(currentPillar, dayMaster, "大运") : `<strong>待确认</strong>`}
          <span>${escapeHtml(formatLuckRange(currentLuck))}</span>
        </div>
        <div class="luck-list">
          ${cycles.slice(0, 10).map((cycle) => renderLuckCycle(cycle, currentPillar, dayMaster)).join("")}
        </div>
      </div>
      ${timeContext.missing_requirements?.length ? `<p class="time-note">${escapeHtml(timeContext.missing_requirements.join(" / "))}</p>` : ""}
    </section>
  `;
}

function renderLatentAttributeSummary(latent) {
  const sections = Array.isArray(latent.debug_sections) ? latent.debug_sections : [];
  if (!sections.length) return "";
  return `
    <div class="latent-attribute-panel">
      <div>
        <p class="eyebrow">DEBUG · 临时</p>
        <strong>隐藏属性数值</strong>
        <span>${escapeHtml(latent.status === "inferred" ? "已校准" : "默认中性")}</span>
        <small>以后删除</small>
      </div>
      <div class="latent-debug-sections">
        ${sections.map((section) => `
          <div class="latent-debug-section">
            <p>${escapeHtml(section.label || section.section_id || "")}</p>
            <div class="latent-attribute-grid">
              ${(Array.isArray(section.rows) ? section.rows : []).map((row) => `
                <span>
                  <em>${escapeHtml(row.key || "")}</em>
                  <strong>${escapeHtml(formatLatentScore(row.score))}</strong>
                  <small>conf ${escapeHtml(formatLatentScore(row.confidence))} · ev ${escapeHtml(row.evidence_count ?? 0)}</small>
                </span>
              `).join("")}
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function formatLatentScore(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return number.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

function renderPillarTile(row, dayMaster = "") {
  const pillar = row.pillar || "";
  const parts = splitPillar(pillar);
  const stemTenGod = layerPosition(row.layer) === "day" ? "日主" : inferTenGod(dayMaster, parts.stem);
  const hiddenRows = hiddenTenGodsForBranch(parts.branch, dayMaster);
  return `
    <div class="pillar-tile ${escapeHtml(row.layer || "")}">
      <span>${escapeHtml(layerLabel(row.layer || ""))}</span>
      <div class="pillar-stack compact">
        <div class="pillar-cell stem-cell">
          <em>${escapeHtml(stemTenGod || "-")}</em>
          <strong>${escapeHtml(parts.stem || "-")}</strong>
          <small>天干</small>
        </div>
        <div class="pillar-cell branch-cell">
          <em>${escapeHtml(formatHiddenTenGods(hiddenRows))}</em>
          <strong>${escapeHtml(parts.branch || "-")}</strong>
          <small>地支</small>
        </div>
      </div>
    </div>
  `;
}

function renderLuckCycle(cycle, currentPillar, dayMaster = "") {
  const active = cycle.pillar && cycle.pillar === currentPillar;
  return `
    <div class="luck-cycle ${active ? "active" : ""}">
      ${cycle.pillar ? renderMiniPillarStack(cycle.pillar, dayMaster, "大运") : `<strong>-</strong>`}
      <span>${escapeHtml(formatLuckRange(cycle))}</span>
    </div>
  `;
}

function renderMiniPillarStack(pillar, dayMaster = "", label = "") {
  const parts = splitPillar(pillar);
  return `
    <div class="mini-pillar-stack" aria-label="${escapeHtml(label || pillar)}">
      <span><em>${escapeHtml(inferTenGod(dayMaster, parts.stem) || "-")}</em><strong>${escapeHtml(parts.stem || "-")}</strong></span>
      <span><em>${escapeHtml(formatHiddenTenGods(hiddenTenGodsForBranch(parts.branch, dayMaster)))}</em><strong>${escapeHtml(parts.branch || "-")}</strong></span>
    </div>
  `;
}

function layerPosition(layer) {
  const text = String(layer || "");
  if (text.includes("year")) return "year";
  if (text.includes("month")) return "month";
  if (text.includes("day")) return "day";
  if (text.includes("hour")) return "hour";
  return text;
}

function formatLuckRange(cycle) {
  if (!cycle || !cycle.start_year || !cycle.end_year) return "";
  return `${cycle.start_year}-${cycle.end_year}`;
}

function layerLabel(layer) {
  const labels = {
    natal_year: "年柱",
    natal_month: "月柱",
    natal_day: "日柱",
    natal_hour: "时柱",
    luck: "大运",
    flow_year: "流年",
  };
  return labels[layer] || layer;
}

function renderAnswerPanel(answer) {
  if (!answer || !answer.text) return "";
  const key = answerPanelKey(answer);
  const rawText = answerDisplayText(answer);
  const text = answerTypewriter.active && answerTypewriter.key === key ? answerTypewriter.visibleText : rawText;
  const typing = answerTypewriter.active && answerTypewriter.key === key && answerTypewriter.visibleText.length < answerTypewriter.fullText.length;
  const questionLabel = answerQuestionLabel(answer);
  return `
    <section id="answer-panel" class="answer-band ${typing ? "typing" : ""}">
      <p class="eyebrow">测算反馈</p>
      <h2>${questionLabel ? "本次问题" : "已根据你的选择生成回答"}</h2>
      ${questionLabel ? `<div class="answer-question-context">${escapeHtml(questionLabel)}</div>` : ""}
      ${answer.visual_hint ? renderAnswerVisualHint(answer.visual_hint) : ""}
      ${renderAnswerThinkingPanel(answer)}
      <div class="answer-text">${formatMultilineText(text)}${typing ? `<span class="typing-cursor"></span>` : ""}</div>
    </section>
  `;
}

function answerDisplayText(answer) {
  const metadata = answer?.llm_metadata || {};
  const status = String(metadata.status || "");
  const source = String(answer?.source || "");
  if (status === "deferred" || status === "loading" || source === "rule_bound_llm_deferred" || source === "llm_pending") {
    return "正在等待大模型推演，完成后会只展示本轮结论和建议。";
  }
  return String(answer?.text || "");
}

function renderAnswerThinkingPanel(answer) {
  const rows = answerThinkingRows(answer);
  if (!rows.length) return "";
  const metadata = answer?.llm_metadata || {};
  const status = String(metadata.status || answer.source || "");
  const isPending = status.includes("loading") || status.includes("deferred") || answer.source === "pending" || answer.source === "llm_pending";
  return `
    <div class="pending-thinking-stream answer-thinking-stream" aria-live="polite">
      <strong>${isPending ? "推演中" : "推演完成"}</strong>
      <div>
        ${rows.slice(0, 3).map((row, index) => `<span style="--delay:${index * 1.25}s">${escapeHtml(row)}</span>`).join("")}
      </div>
    </div>
  `;
}

function answerThinkingRows(answer) {
  const metadata = answer?.llm_metadata || {};
  const summary = metadata.context_pack_summary || {};
  const layerCounts = summary.layer_counts || {};
  const layers = Array.isArray(summary.layers) ? summary.layers : [];
  const thinkingMode = metadata.thinking_mode || {};
  const question = answerQuestionLabel(answer) || "本轮问题";
  const status = String(metadata.status || answer?.source || "");
  if (status === "accepted") {
    return [
      `已围绕「${question}」完成大模型推演。`,
      thinkingMode.trace_available ? `Gemma thinking 已返回，推演轨迹约 ${thinkingMode.trace_chars || 0} 字符。` : "已通过中枢审核，结论只保留可公开依据。",
      `核对上下文：${readableContextLayerSummary(layers, layerCounts)}。`,
    ].filter(Boolean);
  }
  if (status === "failed" || status === "fallback") {
    return [
      `已核对「${question}」的命盘上下文。`,
      "本轮推演未通过中枢验收，暂不展示无依据结论。",
    ];
  }
  return [
    `正在围绕「${question}」组织推演。`,
    `核对上下文：${readableContextLayerSummary(layers, layerCounts)}。`,
    "等待 Gemma 返回后，由中枢大脑清洗成结论和建议。",
  ];
}

function readableContextLayerSummary(layers, layerCounts) {
  const labels = {
    basic_assertions: "基础判断",
    domain_card: "领域卡",
    bazi_features: "特征",
    bazi_portraits: "画像",
    bazi_paths: "路径",
    time_context: "时运",
    role_contract: "表达边界",
  };
  const active = (Array.isArray(layers) ? layers : [])
    .map((layer) => labels[layer] || layer)
    .filter(Boolean)
    .slice(0, 4);
  if (active.length) return active.join("、");
  const counted = Object.entries(layerCounts || {})
    .filter(([, count]) => Number(count || 0) > 0)
    .map(([layer]) => labels[layer] || layer)
    .slice(0, 4);
  return counted.length ? counted.join("、") : "命盘事实、路径证据、表达边界";
}

function renderAnswerVisualHint(visual) {
  const chips = Array.isArray(visual?.chips) ? visual.chips : [];
  if (!chips.length && !visual?.guidance) return "";
  return `
    <div class="answer-visual-hint">
      <strong>${escapeHtml(visual.title || "本轮建议方向")}</strong>
      ${chips.length ? `<div>${chips.slice(0, 4).map((chip) => `<span>${escapeHtml(chip)}</span>`).join("")}</div>` : ""}
      ${visual.guidance ? `<p>${escapeHtml(visual.guidance)}</p>` : ""}
    </div>
  `;
}

function answerQuestionLabel(answer) {
  const explicit = String(answer.question_label || answer.question || "").trim();
  if (explicit) return explicit;
  const questionId = String(answer.question_id || "").trim();
  const calibrationCards = currentView?.reading_surface?.calibration_surface?.visible_probe_cards || [];
  const calibration = Array.isArray(calibrationCards)
    ? calibrationCards.find((card) => String(card?.question_id || "") === questionId)
    : null;
  if (calibration) return calibration.prompt || calibration.title || questionId;
  return questionId;
}

function renderDomainCard(card) {
  const pathAssertions = Array.isArray(card.path_assertions) ? card.path_assertions : [];
  return `
    <article class="domain-card">
      <p class="eyebrow">${escapeHtml(card.label || card.domain || "")}</p>
      <h3>${escapeHtml(card.summary || "")}</h3>
      <p>${escapeHtml(card.customer_takeaway || "")}</p>
      ${card.path_summary ? `<div class="domain-path-summary">${escapeHtml(card.path_summary)}</div>` : ""}
      ${pathAssertions.length ? `
        <div class="path-mini-list">
          ${pathAssertions.slice(0, 3).map((item) => `<i>${escapeHtml(item)}</i>`).join("")}
        </div>
      ` : ""}
      <small>${escapeHtml(card.action_prompt || "")}</small>
    </article>
  `;
}

function renderQuestionAction(question, index) {
  if (isHiddenFactorQuestion(question)) return renderHiddenFactorQuestionAction(question, index);
  const options = compactQuestionOptions(question).slice(0, 4);
  return `
    <article class="question-action">
      <div class="question-action-copy">
        <span>${escapeHtml(questionActionKicker(question, index))}</span>
        <strong>${escapeHtml(question.label || question.question_id || "继续测算")}</strong>
        <p>${escapeHtml(readableQuestionHint(question))}</p>
        ${renderQuestionOptionSetVisual(question)}
      </div>
      <div class="question-action-buttons">
        ${options.length
          ? options.map((option) => renderQuestionOptionForm(question, option)).join("")
          : renderQuestionOptionForm(question, { label: "生成回答", value: "" })}
      </div>
    </article>
  `;
}

function renderQuestionOptionSetVisual(question) {
  const optionSet = question?.response_option_set || {};
  const options = Array.isArray(optionSet.options) ? optionSet.options : [];
  if (!options.length) return "";
  return `
    <div class="question-option-visual">
      <em>${escapeHtml(optionSet.title || "可选方向")}</em>
      ${options.slice(0, 4).map((option) => `<i>${escapeHtml(option.label || option.value || "")}</i>`).join("")}
    </div>
  `;
}

function renderQuestionOptionForm(question, option) {
  const selectedOption = option.option_id || option.value || "";
  const disabled = answerSubmissionState.active ? "disabled" : "";
  const label = answerSubmissionState.active ? "推演中" : (option.label || "生成回答");
  const submit = questionSubmitContract(question);
  return `
    <form class="question-action-form" data-answer-question="${escapeHtml(question.question_id)}" data-question-label="${escapeHtml(question.label || question.question_id)}" data-selected-option="${escapeHtml(selectedOption)}" data-answer-surface="${escapeHtml(submit.submit_surface)}" data-answer-source-id="${escapeHtml(submit.submit_source_id)}" data-answer-contract-version="${escapeHtml(submit.version)}">
      <button type="submit" ${disabled}>${escapeHtml(label)}</button>
    </form>
  `;
}

function questionSubmitContract(question) {
  const submit = question?.submit_contract || {};
  return {
    version: submit.version || "v30.surface_submit_contract.v1",
    submit_surface: submit.submit_surface || "",
    submit_source_id: submit.submit_source_id || "",
  };
}

function renderHiddenFactorQuestionAction(question, index) {
  const constraints = question.answer_constraints || {};
  const stateTags = hiddenFactorStateTagRows(constraints).slice(0, 6);
  const skipOptions = compactQuestionOptions(question).filter((option) => isHiddenFactorSkipOption(option.option_id || option.value || ""));
  return `
    <article class="question-action hidden-factor-action">
      <div class="question-action-copy">
        <span>${escapeHtml(questionActionKicker(question, index))}</span>
        <strong>${escapeHtml(question.label || "校准一个隐藏线索")}</strong>
        <p>${escapeHtml(readableQuestionHint(question))}</p>
      </div>
      <form class="hidden-factor-form" data-answer-question="${escapeHtml(question.question_id)}" data-question-label="${escapeHtml(question.label || question.question_id)}" data-selected-option="hidden_factor:has_repeated_state" data-answer-surface="${escapeHtml(questionSubmitContract(question).submit_surface)}" data-answer-source-id="${escapeHtml(questionSubmitContract(question).submit_source_id)}" data-answer-contract-version="${escapeHtml(questionSubmitContract(question).version)}">
        <fieldset class="hidden-factor-fieldset" data-answer-constraints="structured_hidden_factor">
          <input type="hidden" name="constraintRecurrence" value="repeated">
          <input type="hidden" name="constraintIntensity" value="medium">
          <input type="hidden" name="constraintConfidence" value="approximate">
          <div class="quick-chip-grid">
            ${stateTags.map((row) => `
              <label class="quick-choice">
                <input type="radio" name="constraintStateTags" value="${escapeHtml(row.value || row.key || "")}" ${answerSubmissionState.active ? "disabled" : ""}>
                <span>${escapeHtml(row.label || row.value || "")}</span>
              </label>
            `).join("")}
          </div>
          <div class="quick-number-row">
            <label>
              <span>明显年份</span>
              <input name="constraintYears" inputmode="numeric" placeholder="如 2024" ${answerSubmissionState.active ? "disabled" : ""}>
            </label>
            <button type="submit" ${answerSubmissionState.active ? "disabled" : ""}>${answerSubmissionState.active ? "推演中" : "提交线索"}</button>
          </div>
        </fieldset>
      </form>
      ${skipOptions.length ? `
        <div class="quick-skip-actions">
          ${skipOptions.slice(0, 3).map((option) => renderQuestionOptionForm(question, option)).join("")}
        </div>
      ` : ""}
    </article>
  `;
}

function compactQuestionOptions(question) {
  const optionSetOptions = Array.isArray(question?.response_option_set?.options)
    ? question.response_option_set.options
    : [];
  const sourceOptions = optionSetOptions.length
    ? optionSetOptions
    : (Array.isArray(question?.options) ? question.options : []);
  return sourceOptions
    .map((option) => ({
      option_id: String(option?.option_id || "").trim(),
      value: String(option?.value || option?.option_id || "").trim(),
      label: String(option?.label || option?.value || option?.option_id || "").trim(),
    }))
    .filter((option) => option.label || option.value || option.option_id);
}

function hiddenFactorStateTagRows(constraints) {
  const rows = Array.isArray(constraints?.allowed_state_tags) ? constraints.allowed_state_tags : [];
  if (rows.length) return rows;
  return [
    { value: "career_pressure", label: "事业压力" },
    { value: "wealth_fluctuation", label: "财务波动" },
    { value: "relationship_repetition", label: "关系反复" },
    { value: "family_pressure", label: "家庭压力" },
    { value: "health_rhythm", label: "身心节律波动" },
    { value: "relocation_change", label: "迁移变化" },
  ];
}

function isHiddenFactorQuestion(question) {
  const constraints = question?.answer_constraints || {};
  const topic = String(question?.topic || question?.domain || "").trim();
  return topic === "hidden_factor" || constraints.constraint_type === "structured_hidden_factor";
}

function isHiddenFactorSkipOption(value) {
  return ["hidden_factor:not_sure", "hidden_factor:skip", "hidden_factor:default"].includes(String(value || ""));
}

async function submitPractitionerOptionAction(event) {
  event.preventDefault();
  const button = event.currentTarget;
  const action = button.getAttribute("data-practitioner-option-action") || "select";
  const optionSetId = button.getAttribute("data-option-set-id") || "";
  const optionId = button.getAttribute("data-option-id") || "";
  if (!formState.readingId || !optionSetId) return;
  const card = button.closest(".practitioner-option-card");
  const note = String(card?.querySelector("[name='practitionerNote']")?.value || "").trim();
  await sendPractitionerSelection({
    option_set_id: optionSetId,
    action,
    selected_option_ids: optionId ? [optionId] : [],
    ranked_option_ids: action === "rank" && optionId ? [optionId] : [],
    rejected_option_ids: ["reject", "downrank"].includes(action) && optionId ? [optionId] : [],
    note,
    confidence: action === "select" || action === "rank" ? 0.82 : 0.7,
    actor_id: productSession?.session?.actor_id || formState.actorId || "practitioner",
  });
}

async function submitPractitionerOptionNote(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const optionSetId = form.getAttribute("data-practitioner-option-note") || "";
  const note = String(new FormData(form).get("practitionerNote") || "").trim();
  if (!formState.readingId || !optionSetId || !note) return;
  await sendPractitionerSelection({
    option_set_id: optionSetId,
    action: "note",
    selected_option_ids: [],
    ranked_option_ids: [],
    rejected_option_ids: [],
    note,
    confidence: 0.66,
    actor_id: productSession?.session?.actor_id || formState.actorId || "practitioner",
  });
}

async function sendPractitionerSelection(payload) {
  setStatus("updating");
  try {
    const res = await fetch(`/api/v30/readings/${encodeURIComponent(formState.readingId)}/practitioner/selections`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "practitioner_selection_failed");
    currentPractitionerState = result.interaction_state || currentPractitionerState;
    currentThinking = result.thinking || currentThinking;
    interactionNotice = { type: "success", text: "命理师校准已写入中枢权重。" };
    setStatus("ready");
    renderReading();
  } catch (error) {
    interactionNotice = { type: "warn", text: `命理师校准失败：${error.message || "request_failed"}` };
    setStatus("error");
    renderReading();
  }
}

function questionActionKicker(question, index) {
  const topic = domainLabel(question.topic_label || question.topic || question.domain || "");
  return topic ? `本次聚焦 · ${topic}` : "本次聚焦";
}

function readableQuestionHint(question) {
  const topic = domainLabel(question.topic_label || question.topic || question.domain || "");
  const gain = String(question.question_value || question.expected_information_gain?.primary_gain || "").trim();
  const readableGain = readableQuestionGain(gain)
    .replace(/\bhidden factor\b/i, "隐藏线索")
    .replace(/\bstructure\b/i, "结构")
    .replace(/\btiming\b/i, "时运");
  return [topic, readableGain].filter(Boolean).join(" · ") || "根据当前命盘继续细看";
}

function domainLabel(value) {
  const key = String(value || "").toLowerCase();
  const labels = {
    wealth: "财运",
    career: "事业",
    relationship: "关系",
    health: "健康",
    timing: "时运",
    structure: "结构",
    useful_god: "用神",
    hidden_factor: "校准线索",
    risk: "风险",
    decision: "决策",
    overview: "总览",
  };
  return labels[key] || String(value || "");
}

async function submitAnswer(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const questionId = form.getAttribute("data-answer-question");
  const questionLabel = form.getAttribute("data-question-label") || questionId || "";
  const submitSurface = form.getAttribute("data-answer-surface") || "";
  const submitSourceId = form.getAttribute("data-answer-source-id") || "";
  const submitContractVersion = form.getAttribute("data-answer-contract-version") || "";
  if (submitSurface !== "calibration_surface") {
    interactionNotice = { type: "warn", text: "这个旧问题入口已经停用；请从校准卡或问八字入口继续。" };
    renderReading();
    return;
  }
  const selectedOption = event.submitter?.getAttribute("data-selected-option") || form.getAttribute("data-selected-option") || "";
  const data = new FormData(form);
  const freeText = String(data.get("answerText") || "").trim();
  const structuredPayload = collectStructuredPayload(form, selectedOption);
  const validationError = validateAnswerConstraintForm(form, structuredPayload, selectedOption);
  if (validationError) {
    interactionNotice = { type: "warn", text: validationError };
    renderReading();
    return;
  }
  const answerParts = [`用户选择了问题：${questionLabel}`];
  if (selectedOption) answerParts.push(`结构化选择：${selectedOption}`);
  if (structuredPayload.state_tags?.length) answerParts.push(`状态线索：${structuredPayload.state_tags.join(",")}`);
  if (structuredPayload.years?.length) answerParts.push(`年份线索：${structuredPayload.years.join(",")}`);
  if (freeText) answerParts.push(`补充回答：${freeText}`);
  const answer = answerParts.join("；");
  if (!questionId) return;
  if (answerSubmissionState.active) {
    interactionNotice = { type: "warn", text: "上一轮智能问答还在推演，请等本轮完成后再继续。" };
    renderReading();
    scrollToAnswer();
    return;
  }
  const requestToken = `${Date.now()}:${questionId}`;
  answerSubmissionState = { active: true, token: requestToken, questionId };
  const answerStageId = currentAnalysisStage()?.step_id || "";
  setAnswerFormsDisabled(true);
  if (event.submitter) event.submitter.textContent = "提交中";
  interactionNotice = { type: "info", text: "正在生成本轮回答。" };
  setStatus("updating");
  currentView = {
    ...currentView,
    answer_panel: {
      text: "正在生成回答，请稍等。",
      question_id: questionId,
      question_label: questionLabel,
      question_stage_id: answerStageId,
      user_reply: freeText || selectedOption || "",
      source: "pending",
      llm_metadata: {
        status: "loading",
        context_pack_summary: { layers: [], layer_counts: {} },
      },
    },
  };
  renderReading();
  scrollToAnswer();
  try {
    const res = await fetch(`/api/v30/readings/${formState.readingId}/questions/${questionId}/answer`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        answer,
        role: formState.role,
        locale: formState.locale,
        client: formState.client,
        submit_surface: submitSurface,
        submit_source_id: submitSourceId,
        submit_contract_version: submitContractVersion,
        outcome_status: "answered",
        selected_option: selectedOption,
        structured_payload: structuredPayload,
        confidence: 0.7,
        feedback_tags: buildAnswerFeedbackTags(selectedOption, structuredPayload),
      }),
    });
    const payload = await res.json();
    if (!res.ok || !payload.view) {
      throw new Error(payload.detail || "answer_submit_failed");
    }
    if (payload.question_id && payload.question_id !== questionId) {
      throw new Error("answer_question_mismatch");
    }
    const nextView = payload.view;
    currentView = mergeDialogueView(currentView, nextView);
    const rawAnswerPanel = currentView.answer_panel || {};
    currentView.answer_panel = {
      ...rawAnswerPanel,
      question_id: questionId,
      question_label: questionLabel,
      question_stage_id: answerStageId,
      user_reply: freeText || selectedOption || "",
    };
    if (answerNeedsLlmResolution(rawAnswerPanel)) {
      currentView.answer_panel = pendingLlmAnswerPanel(currentView.answer_panel);
      lastAnswerLlmFailure = {};
      renderReading();
      scrollToAnswer();
      const enhanced = await requestLlmAnswerEnhancementIfDeferred(questionId, questionLabel, freeText || selectedOption || "", {
        answerPanel: rawAnswerPanel,
        questionStageId: answerStageId,
        requestToken,
        render: false,
      });
      if (!enhanced) {
        currentView.answer_panel = failedLlmAnswerPanel(currentView.answer_panel, lastAnswerLlmFailure);
        interactionNotice = { type: "warn", text: "LLM 推演暂未完成，本次不展示规则兜底结论。" };
      } else {
        interactionNotice = { type: "success", text: "LLM 推演已完成。" };
      }
    } else {
      prepareAnswerTypewriter(currentView.answer_panel || {});
      interactionNotice = { type: "success", text: "已收到回答。" };
    }
    currentInteractionState = payload.interaction_state || currentView.interaction_state || currentInteractionState;
    setStatus("ready");
  } catch (error) {
    interactionNotice = { type: "warn", text: `提交失败：${error.message || "请稍后重试"}` };
    setStatus("error");
  }
  if (answerSubmissionState.token === requestToken) {
    answerSubmissionState = { active: false, token: "", questionId: "" };
  }
  setAnswerFormsDisabled(false);
  renderReading();
  scrollToAnswer();
}

function setAnswerFormsDisabled(disabled) {
  document.querySelectorAll("[data-answer-question] button").forEach((button) => {
    button.disabled = disabled;
  });
}

function mergeDialogueView(previous, next) {
  if (!previous || !next) return next || previous;
  const previousSurface = previous.reading_surface || {};
  const nextSurface = next.reading_surface || {};
  return {
    ...previous,
    answer_panel: next.answer_panel || previous.answer_panel,
    questions: next.questions || previous.questions,
    interaction_state: next.interaction_state || previous.interaction_state,
    reading_surface: {
      ...previousSurface,
      surface_orchestrator: nextSurface.surface_orchestrator || previousSurface.surface_orchestrator,
      surface_policy: nextSurface.surface_policy || previousSurface.surface_policy,
      calibration_surface: nextSurface.calibration_surface || previousSurface.calibration_surface,
      conversation_surface: nextSurface.conversation_surface || previousSurface.conversation_surface,
      thinking_surface: nextSurface.thinking_surface || previousSurface.thinking_surface,
      legacy_dialogue_surface: nextSurface.legacy_dialogue_surface || previousSurface.legacy_dialogue_surface,
      interaction_state: nextSurface.interaction_state || previousSurface.interaction_state,
      dialogue_visual_hint: nextSurface.dialogue_visual_hint || previousSurface.dialogue_visual_hint,
      answer_visual_hint: nextSurface.answer_visual_hint || previousSurface.answer_visual_hint,
    },
    diagnostics: next.diagnostics || previous.diagnostics,
  };
}

function answerNeedsLlmResolution(answerPanel) {
  const metadata = answerPanel?.llm_metadata || {};
  const source = String(answerPanel?.source || "");
  const fallbackReason = String(metadata.fallback_reason || "");
  return metadata.status === "deferred" || source.includes("deferred") || fallbackReason.includes("sync_mode_fast_llm_deferred");
}

function pendingLlmAnswerPanel(answerPanel) {
  return {
    ...(answerPanel || {}),
    text: "正在调用 LLM 推演，请稍等。",
    source: "llm_pending",
    llm_metadata: {
      ...((answerPanel || {}).llm_metadata || {}),
      status: "loading",
    },
  };
}

function failedLlmAnswerPanel(answerPanel, failure = {}) {
  const reason = String(failure.fallback_reason || answerPanel?.llm_metadata?.fallback_reason || "").trim();
  const message = answerLlmFailureMessage(reason);
  return {
    ...(answerPanel || {}),
    text: message,
    source: "llm_not_ready",
    llm_metadata: {
      ...((answerPanel || {}).llm_metadata || {}),
      status: "failed",
      fallback_reason: reason,
    },
  };
}

let lastAnswerLlmFailure = {};

function answerLlmFailureMessage(reason) {
  if (reason.includes("sync_mode_fast_llm_deferred")) {
    return "本次回答正在等待大模型推演，请稍后重试这一问。";
  }
  if (reason.includes("provider_not_ready") || reason.includes("URLError") || reason.includes("call_failed")) {
    return "本次回答需要大模型推演，但当前没有连接到可用模型。请检查 Ollama/SSH 隧道后重试这一问。";
  }
  if (reason.includes("prompt_request_rejected")) {
    return "本次回答的大模型提示词上下文没有通过系统校验，暂不展示规则兜底结论。";
  }
  if (reason.includes("output_acceptance_failed") || reason.includes("drift_check_failed")) {
    return "大模型已返回内容，但没有通过中枢审核，暂不展示本次回答。";
  }
  return "LLM 推演暂未完成，本次不展示规则兜底结论。请稍后重试这一问。";
}

async function requestLlmAnswerEnhancementIfDeferred(questionId, questionLabel, userReply, options = {}) {
  const metadata = (options.answerPanel || currentView?.answer_panel || {}).llm_metadata || {};
  const source = String((options.answerPanel || currentView?.answer_panel || {}).source || "");
  const fallbackReason = String(metadata.fallback_reason || "");
  const deferred = metadata.status === "deferred" || source.includes("deferred") || fallbackReason.includes("sync_mode_fast_llm_deferred");
  if (!formState.readingId || !deferred) return false;
  try {
    const res = await fetch(`/api/v30/readings/${formState.readingId}/questions/${questionId}/answer/llm`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        role: formState.role,
        locale: formState.locale,
        client: formState.client,
      }),
    });
    const payload = await res.json();
    if (!res.ok || !payload.accepted || !payload.view) {
      lastAnswerLlmFailure = payload || {};
      return false;
    }
    const returnedQuestionId = payload.question_id || payload.view?.answer_panel?.question_id || "";
    if (returnedQuestionId && returnedQuestionId !== questionId) {
      lastAnswerLlmFailure = { fallback_reason: "answer_question_mismatch" };
      return false;
    }
    if (options.requestToken && answerSubmissionState.token && answerSubmissionState.token !== options.requestToken) {
      lastAnswerLlmFailure = { fallback_reason: "stale_answer_request_ignored" };
      return false;
    }
    lastAnswerLlmFailure = {};
    currentView = payload.view;
    currentView.answer_panel = {
      ...(currentView.answer_panel || {}),
      question_id: questionId,
      question_label: questionLabel,
      question_stage_id: options.questionStageId || currentView.answer_panel?.question_stage_id || "",
      user_reply: userReply,
    };
    prepareAnswerTypewriter(currentView.answer_panel || {});
    if (options.render !== false) {
      renderReading();
      scrollToAnswer();
    }
    return true;
  } catch (error) {
    lastAnswerLlmFailure = { fallback_reason: error.message || "answer_llm_request_failed" };
    return false;
  }
}

function collectStructuredPayload(form, selectedOption) {
  const data = new FormData(form);
  const payload = {};
  const stateTags = data.getAll("constraintStateTags").map((row) => String(row || "").trim()).filter(Boolean);
  const years = parseConstraintYears(String(data.get("constraintYears") || ""));
  const recurrence = String(data.get("constraintRecurrence") || "").trim();
  const intensity = String(data.get("constraintIntensity") || "").trim();
  const confidence = String(data.get("constraintConfidence") || "").trim();
  const selectedDomain = String(data.get("constraintSelectedDomain") || "").trim();
  if (stateTags.length) payload.state_tags = stateTags;
  if (years.length) payload.years = years;
  if (recurrence) payload.recurrence = recurrence;
  if (intensity) payload.intensity = intensity;
  if (confidence) payload.confidence = confidence;
  if (selectedDomain) payload.selected_domain = selectedDomain;
  if (!payload.selected_domain && selectedOption.startsWith("domain:")) {
    payload.selected_domain = selectedOption.split(":", 2)[1] || "";
  }
  return payload;
}

function parseConstraintYears(value) {
  return String(value || "")
    .split(/[,，、\s]+/)
    .map((row) => Number(row))
    .filter((row) => Number.isInteger(row) && row >= 1900 && row <= 2100);
}

function validateAnswerConstraintForm(form, payload, selectedOption = "") {
  const type = form.querySelector("[data-answer-constraints]")?.getAttribute("data-answer-constraints") || "";
  if (type !== "structured_hidden_factor") return "";
  if (isHiddenFactorSkipOption(selectedOption)) return "";
  if (!Array.isArray(payload.state_tags) || !payload.state_tags.length) {
    return "请选择一个现实中反复出现的状态，再继续测算。";
  }
  if (!payload.recurrence) {
    return "请选择这个状态是否反复出现。";
  }
  return "";
}

function buildAnswerFeedbackTags(selectedOption, structuredPayload) {
  const tags = ["v30_ui_customer_loop"];
  if (selectedOption) tags.push("structured_option");
  if (structuredPayload.state_tags?.length) tags.push("structured_hidden_factor");
  if (structuredPayload.years?.length) tags.push("structured_years");
  return tags;
}

function answerPanelKey(answer) {
  return `${answer.answer_id || ""}:${answer.question_id || ""}:${answer.source || ""}:${String(answer.text || "").length}`;
}

function prepareAnswerTypewriter(answer) {
  const text = String(answer?.text || "");
  if (!text || text === "正在生成回答，请稍等。") return;
  if (answerTypewriter.timer) window.clearTimeout(answerTypewriter.timer);
  answerTypewriter = {
    key: answerPanelKey(answer),
    fullText: text,
    visibleText: "",
    active: true,
    timer: null,
  };
  scheduleAnswerTypewriterTick();
}

function scheduleAnswerTypewriterTick() {
  if (!answerTypewriter.active) return;
  answerTypewriter.timer = window.setTimeout(() => {
    const remaining = answerTypewriter.fullText.length - answerTypewriter.visibleText.length;
    if (remaining <= 0) {
      answerTypewriter = { ...answerTypewriter, active: false, timer: null };
      renderReading();
      return;
    }
    const step = remaining > 240 ? 12 : remaining > 80 ? 8 : 4;
    answerTypewriter = {
      ...answerTypewriter,
      visibleText: answerTypewriter.fullText.slice(0, answerTypewriter.visibleText.length + step),
      timer: null,
    };
    renderReading();
    scheduleAnswerTypewriterTick();
  }, 24);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMultilineText(value) {
  return escapeHtml(value).replace(/\n/g, "<br>");
}

function scrollToAnswer() {
  window.requestAnimationFrame(() => {
    const answerPanel = document.querySelector("#answer-panel");
    if (answerPanel) {
      answerPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}

window.addEventListener("resize", renderGlobalChrome);

renderShell();
