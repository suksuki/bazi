const app = document.querySelector("#app");
const statusEl = document.querySelector("#status");
const localeSwitchEl = document.querySelector("#locale-switch");
const terminalStatusEl = document.querySelector("#terminal-status");
const PRODUCT_SESSION_KEY = "v30.product.session";
const PRODUCT_UI_PREFS_KEY = "v30.product.ui_prefs";
const QUESTION_TURN_HISTORY_KEY = "v30.product.question_turns";

let currentView = null;
let interactionNotice = null;
let readingHistory = null;
let historyNotice = "";
let localQuestionTurns = loadQuestionTurnHistory();
let hiddenFactorNotice = "";
let currentInteractionState = null;
let answerTypewriter = {
  key: "",
  fullText: "",
  visibleText: "",
  active: false,
  timer: null,
};
let activeReadingStep = initialReadingStep();
let productSession = loadStoredProductSession();
let productUiPrefs = loadStoredUiPrefs();
let productProfiles = null;
let productNotice = "";
let adminState = {
  loaded: false,
  loading: false,
  notice: "",
  activeTab: initialAdminTab(),
  health: null,
  capabilities: null,
  mainlineSelection: null,
  moduleReview: null,
  coreCalibrationS0: null,
  readingView: null,
  trace: null,
  searchReadingId: "",
  searchActorId: "",
  searchSessionId: "",
  searchHistory: null,
  runtimeConfig: null,
  dbStatus: null,
  redisStatus: null,
  dbConfigSave: null,
  redisConfigSave: null,
  dbSchemaApply: null,
  llmStatus: null,
  llmConfigSave: null,
  llmTest: null,
  trainingStatus: null,
  trainingRun: null,
  m3TrainingJob: null,
  m3TrainingJobId: "",
  m3TrainingPoll: null,
  validationStatus: null,
  endpointStatus: [],
};

const roleProfiles = {
  guest: { label: "游客", client: "mobile", helper: "查看命盘摘要和可继续追问的方向。" },
  user: { label: "普通用户", client: "web", helper: "排盘、看解读，并围绕命盘连续追问。" },
  practitioner: { label: "命理师", client: "web", helper: "查看命盘证据、结构路径和复核要点。" },
  admin: { label: "管理员", client: "admin", helper: "管理数据库、LLM、训练、验证和运行状态。" },
};

function detectClient() {
  return window.matchMedia("(max-width: 760px)").matches ? "mobile" : "web";
}

function terminalLabel(client) {
  return client === "mobile" ? "移动端自动适配" : client === "admin" ? "管理端" : "电脑端自动适配";
}

function localeLabel(locale) {
  const labels = { zh: "中文", en: "English", ko: "한국어" };
  return labels[locale] || "中文";
}

function setStatus(value) {
  const labels = {
    admin: "后台",
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
    training: "训练",
    updating: "生成中",
    validation: "验证",
  };
  statusEl.textContent = labels[value] || value || "就绪";
}

function initialRole() {
  const params = new URLSearchParams(window.location.search);
  const role = params.get("role") || "user";
  return roleProfiles[role] ? role : "user";
}

function initialState() {
  const role = initialRole();
  const session = productSession?.session || {};
  const user = productSession?.user || {};
  const locale = productUiPrefs.locale || "zh";
  return {
    readingId: `v30-reading-${Date.now()}`,
    role: user.role || role,
    locale,
    client: roleProfiles[user.role || role]?.client === "web" ? detectClient() : roleProfiles[user.role || role]?.client,
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
  if (isAdminShellRequested()) {
    renderAdminShell();
    return;
  }
  app.innerHTML = `
    <section class="reading-shell">
      <aside class="profile-rail">
        <div class="rail-card current-profile">
          <p class="eyebrow">八字档案</p>
          <h2>${escapeHtml(formState.profileName)}</h2>
          <p>${productSession ? "已登录，可保存档案和连续问答。" : "游客测算，登录后可保存八字档案。"}</p>
          <div class="rail-tags">
            <span>${escapeHtml(roleProfiles[formState.role]?.label || "普通用户")}</span>
            <span>${escapeHtml(localeLabel(formState.locale))}</span>
            <span>${escapeHtml(terminalLabel(formState.client))}</span>
            <span>${productSession ? "账号档案" : "临时档案"}</span>
          </div>
        </div>
        <div class="rail-card history-card">
          <div class="rail-card-head">
            <div>
              <p class="eyebrow">历史测算</p>
              <strong>${readingHistory ? `${readingHistory.count || 0} 条记录` : "未读取"}</strong>
            </div>
            <button type="button" class="subtle-button" data-load-history>读取</button>
          </div>
          ${historyNotice ? `<p class="history-notice">${escapeHtml(historyNotice)}</p>` : ""}
          ${renderHistoryList()}
        </div>
        <div class="rail-card">
          <p class="eyebrow">语言与终端</p>
          <p>当前正式输出中文；英文、韩文已预留入口，后续统一补全文案、术语和提示词。页面会按电脑与移动端自动适配。</p>
        </div>
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
              <strong>${escapeHtml(roleProfiles[formState.role]?.label || "普通用户")}</strong>
              <span>${escapeHtml(roleProfiles[formState.role]?.helper || "")}</span>
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
      </section>
    </section>
  `;
  document.querySelectorAll("[data-reading-step]").forEach((button) => {
    button.addEventListener("click", handleReadingStepChange);
  });
  document.querySelector("[data-load-history]")?.addEventListener("click", loadHistory);
  document.querySelectorAll("[data-open-reading]").forEach((button) => {
    button.addEventListener("click", openHistoryReading);
  });
  document.querySelector("#birth-form")?.addEventListener("submit", submitBirth);
  bindBirthDateSelects(document);
  document.querySelectorAll("[data-ui-projection]").forEach((control) => {
    control.addEventListener("change", handleProjectionChange);
  });
  renderReading();
}

function initialReadingStep() {
  const params = new URLSearchParams(window.location.search);
  const step = params.get("step") || "input";
  const allowed = new Set(["input", "chart", "reading", "questions"]);
  return allowed.has(step) ? step : "input";
}

function renderReadingStepNav() {
  const steps = [
    ["input", "1", "出生资料", currentView ? "可修改" : "先填写"],
    ["chart", "2", "命盘", currentView ? "四柱/十神" : "待排盘"],
    ["reading", "3", "解读", currentView ? "事业/财运/关系" : "待生成"],
    ["questions", "4", "问答", currentView ? "继续追问" : "待生成"],
  ];
  return `
    <nav class="reading-stepper" aria-label="八字测算步骤">
      ${steps.map(([key, index, label, helper]) => `
        <button type="button" class="step-item ${activeReadingStep === key ? "active" : ""}" data-reading-step="${key}">
          <span>${escapeHtml(index)}</span>
          <strong>${escapeHtml(label)}</strong>
          <em>${escapeHtml(helper)}</em>
        </button>
      `).join("")}
    </nav>
  `;
}

function handleReadingStepChange(event) {
  activeReadingStep = event.currentTarget.getAttribute("data-reading-step") || "input";
  const url = new URL(window.location.href);
  url.searchParams.set("step", activeReadingStep);
  window.history.replaceState({}, "", url.toString());
  renderShell();
}

function isAuthPageRequested() {
  const params = new URLSearchParams(window.location.search);
  return params.get("page") === "auth";
}

function isProfilesPageRequested() {
  const params = new URLSearchParams(window.location.search);
  return params.get("page") === "profiles";
}

function renderAuthPage() {
  app.innerHTML = `
    <section class="product-page">
      <section class="admin-hero">
        <div>
          <p class="eyebrow">账户</p>
          <h2>登录 / 注册</h2>
          <p>账号用于保存八字档案、测算记录和连续问答。角色在注册时确定，后续不在测算页切换。</p>
        </div>
        ${productSession ? `<button type="button" data-product-logout>退出登录</button>` : ""}
      </section>
      ${productNotice ? `<section class="notice-band info">${escapeHtml(productNotice)}</section>` : ""}
      ${productSession ? renderCurrentSessionCard() : `
        <section class="admin-grid two">
          <article class="admin-panel">
            <p class="eyebrow">登录</p>
            <form class="admin-form" data-login-form>
              <label>用户名<input name="username" autocomplete="username" placeholder="user@example.com"></label>
              <label>密码<input name="password" type="password" autocomplete="current-password"></label>
              <button type="submit">登录</button>
            </form>
          </article>
          <article class="admin-panel">
            <p class="eyebrow">注册</p>
            <form class="admin-form" data-register-form>
              <label>用户名<input name="username" autocomplete="username" placeholder="user@example.com"></label>
              <label>显示名<input name="displayName" placeholder="例如 当前用户"></label>
              <label>角色
                <select name="role">
                  <option value="user">普通用户</option>
                  <option value="practitioner">命理师</option>
                </select>
              </label>
              <label>密码<input name="password" type="password" autocomplete="new-password"></label>
              <button type="submit">注册并登录</button>
            </form>
          </article>
        </section>
      `}
    </section>
  `;
  document.querySelector("[data-login-form]")?.addEventListener("submit", submitLogin);
  document.querySelector("[data-register-form]")?.addEventListener("submit", submitRegister);
  document.querySelector("[data-product-logout]")?.addEventListener("click", logoutProductSession);
}

function renderCurrentSessionCard() {
  const user = productSession?.user || {};
  const isAdmin = user.role === "admin";
  return `
    <section class="admin-panel">
      <p class="eyebrow">当前登录</p>
      <h2>${escapeHtml(user.display_name || user.username || "已登录用户")}</h2>
      <div class="admin-kv">
        ${renderKv("角色", roleProfiles[user.role]?.label || "普通用户")}
        ${renderKv("档案权限", user.role === "practitioner" ? "命理师测算" : isAdmin ? "系统管理" : "个人测算")}
      </div>
      <div class="admin-actions left">
        <a class="subtle-link" href="/v30/ui/?page=profiles">进入八字档案</a>
        <a class="subtle-link" href="/v30/ui/?role=user">开始测算</a>
        ${isAdmin ? `<a class="subtle-link" href="/v30/ui/?role=admin&surface=admin">进入管理台</a>` : ""}
      </div>
    </section>
  `;
}

function renderProfilesPage() {
  const profiles = Array.isArray(productProfiles?.items) ? productProfiles.items : [];
  app.innerHTML = `
    <section class="product-page">
      <section class="admin-hero">
        <div>
          <p class="eyebrow">八字档案</p>
          <h2>档案管理</h2>
          <p>保存出生资料、历法、时区、真太阳时和未知时辰说明；测算时再排盘。</p>
        </div>
        <div class="admin-actions">
          ${productSession ? `<button type="button" data-load-profiles>刷新档案</button>` : `<a class="subtle-link" href="/v30/ui/?page=auth">先登录</a>`}
        </div>
      </section>
      ${productNotice ? `<section class="notice-band info">${escapeHtml(productNotice)}</section>` : ""}
      ${!productSession ? `<section class="admin-panel"><p>需要登录后管理八字档案。</p></section>` : `
        <section class="admin-grid two">
          <article class="admin-panel">
            <p class="eyebrow">新增 / 更新档案</p>
            <form class="admin-form" data-profile-form>
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
          <article class="admin-panel">
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

function isAdminShellRequested() {
  const params = new URLSearchParams(window.location.search);
  return params.get("surface") === "admin" || params.get("admin") === "1";
}

function initialAdminTab() {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab") || "overview";
  const allowed = new Set(["overview", "modules", "readings", "db", "llm", "training", "validation", "contracts"]);
  return allowed.has(tab) ? tab : "overview";
}

function renderAdminShell() {
  app.innerHTML = `
    <section class="admin-shell">
      <aside class="admin-nav">
        <div class="rail-card current-profile">
          <p class="eyebrow">管理台</p>
          <h2>系统管理台</h2>
          <p>管理数据库、缓存、LLM、训练任务和验证结果。</p>
        </div>
        <nav class="role-tabs" aria-label="Admin navigation">
          ${[
            ["overview", "系统概览"],
            ["modules", "主模块"],
            ["readings", "测算记录"],
            ["db", "DB / Redis"],
            ["llm", "LLM"],
            ["training", "训练"],
            ["validation", "验证"],
            ["contracts", "接口状态"],
          ].map(([key, label]) => `
            <button type="button" class="role-tab ${adminState.activeTab === key ? "active" : ""}" data-admin-tab="${key}">
              ${escapeHtml(label)}
            </button>
          `).join("")}
        </nav>
        <div class="rail-card">
          <p class="eyebrow">测算入口</p>
          <p>管理员也可以进入测算页查看命盘。</p>
          <a class="text-link" href="/v30/ui/?role=admin">打开八字测算</a>
        </div>
      </aside>
      <section class="admin-workbench">
        <section class="admin-hero">
          <div>
            <p class="eyebrow">后台管理</p>
            <h2>运行、训练与验证</h2>
            <p>查看核心模块、测算记录、数据库、LLM、训练任务和验证状态；重任务只在明确操作时启动。</p>
          </div>
          <div class="admin-actions">
            <button type="button" data-admin-refresh>${adminState.loading ? "刷新中" : "刷新后台状态"}</button>
            <a class="subtle-link" href="/v30/ui/?role=user">用户测算页</a>
          </div>
        </section>
        ${adminState.notice ? `<section class="notice-band info">${escapeHtml(adminState.notice)}</section>` : ""}
        ${renderAdminTab()}
      </section>
    </section>
  `;
  document.querySelectorAll("[data-admin-tab]").forEach((button) => {
    button.addEventListener("click", handleAdminTabChange);
  });
  document.querySelector("[data-admin-refresh]")?.addEventListener("click", loadAdminOverview);
  document.querySelector("[data-admin-load-llm]")?.addEventListener("click", loadAdminLlmStatus);
  document.querySelector("[data-admin-load-runtime]")?.addEventListener("click", loadAdminRuntimeStatus);
  document.querySelector("[data-admin-db-config]")?.addEventListener("submit", submitAdminDbConfig);
  document.querySelector("[data-admin-redis-config]")?.addEventListener("submit", submitAdminRedisConfig);
  document.querySelector("[data-admin-db-schema]")?.addEventListener("click", applyAdminDbSchema);
  document.querySelector("[data-admin-llm-config]")?.addEventListener("submit", submitAdminLlmConfig);
  document.querySelector("[data-admin-llm-test]")?.addEventListener("submit", submitAdminLlmTest);
  document.querySelector("[data-admin-load-training]")?.addEventListener("click", loadAdminTrainingStatus);
  document.querySelector("[data-admin-load-validation]")?.addEventListener("click", loadAdminValidationStatus);
  document.querySelector("[data-admin-training-run]")?.addEventListener("submit", submitAdminTrainingRun);
  document.querySelector("[data-admin-m3-job-run]")?.addEventListener("submit", submitAdminM3TrainingJob);
  document.querySelector("[data-admin-m3-job-refresh]")?.addEventListener("click", refreshAdminM3TrainingJob);
  document.querySelector("[data-admin-reading-search]")?.addEventListener("submit", submitAdminReadingSearch);
  document.querySelector("[data-admin-history-search]")?.addEventListener("submit", submitAdminHistorySearch);
  document.querySelectorAll("[data-admin-open-reading]").forEach((button) => {
    button.addEventListener("click", openAdminHistoryReading);
  });
  if (!adminState.loaded && !adminState.loading) {
    loadAdminOverview();
  }
}

function renderAdminTab() {
  if (adminState.activeTab === "modules") return renderAdminModulesTab();
  if (adminState.activeTab === "readings") return renderAdminReadingsTab();
  if (adminState.activeTab === "db") return renderAdminRuntimeTab();
  if (adminState.activeTab === "llm") return renderAdminLlmTab();
  if (adminState.activeTab === "training") return renderAdminTrainingTab();
  if (adminState.activeTab === "validation") return renderAdminValidationTab();
  if (adminState.activeTab === "contracts") return renderAdminContractsTab();
  return renderAdminOverviewTab();
}

function renderAdminOverviewTab() {
  const health = adminState.health || {};
  const selection = adminState.mainlineSelection || {};
  const decision = selection.decision || {};
  const next = selection.next_mainline_selection || selection.next_task || {};
  const moduleReviewDecision = adminState.moduleReview?.decision || {};
  const s0 = adminState.coreCalibrationS0 || {};
  const s0Decision = s0.decision || {};
  return `
    <section class="admin-grid two">
      <article class="admin-panel">
        <p class="eyebrow">服务状态</p>
        <h3>${health.ok ? "运行中" : "未确认"}</h3>
        <div class="admin-kv">
          ${renderKv("存储", health.repository)}
          ${renderKv("缓存", health.redis_cache)}
        </div>
      </article>
      <article class="admin-panel">
        <p class="eyebrow">下一主线</p>
        <h3>${escapeHtml(next.task_id || decision.decision_status || "待读取")}</h3>
        <p>${escapeHtml(next.title || selection.status || "点击刷新后台状态读取主线选择。")}</p>
      </article>
      <article class="admin-panel">
        <p class="eyebrow">核心校准稳态</p>
        <h3>${escapeHtml(s0Decision.decision_status || "待读取")}</h3>
        <div class="admin-kv">
          ${renderKv("等待证据", s0Decision.waiting_for_new_calibration_evidence)}
          ${renderKv("候选", s0Decision.focused_fix_candidate_count)}
          ${renderKv("全量测试", s0Decision.full_pytest_required ? "需要" : "不需要")}
        </div>
      </article>
      <article class="admin-panel">
        <p class="eyebrow">主模块完成度</p>
        <h3>${escapeHtml(moduleReviewDecision.decision_status || "待读取")}</h3>
        <div class="admin-kv">
          ${renderKv("检查", `${moduleReviewDecision.passed_count ?? "-"} / ${moduleReviewDecision.check_count ?? "-"}`)}
          ${renderKv("全量测试", moduleReviewDecision.full_pytest_required ? "需要" : "不需要")}
          ${renderKv("合成全量", moduleReviewDecision.synthetic_all_required ? "需要" : "不需要")}
        </div>
      </article>
      <article class="admin-panel">
        <p class="eyebrow">操作范围</p>
        <h3>默认轻量运行</h3>
        <p>日常只跑目标验证和后台任务；全量测试、完整 518K 和策略发布需要单独确认。</p>
      </article>
    </section>
  `;
}

function renderAdminModulesTab() {
  const review = adminState.moduleReview || {};
  const rows = Array.isArray(review.module_completion_matrix) ? review.module_completion_matrix : [];
  const checks = Array.isArray(review.checks) ? review.checks : [];
  return `
    <section class="admin-panel">
      <div class="section-head">
        <p class="eyebrow">Main Module Completion</p>
        <h2>${escapeHtml(review.task?.title || "主模块完成度")}</h2>
      </div>
      <div class="module-table">
        ${rows.length ? rows.map(renderModuleRow).join("") : `<div class="history-empty">刷新后显示 M1-M8、IQ、LLM、BT、U 等主模块完成度。</div>`}
      </div>
    </section>
    <section class="admin-panel">
      <p class="eyebrow">Review Checks</p>
      <div class="admin-check-list">
        ${checks.length ? checks.map(renderAdminCheck).join("") : `<div class="history-empty">暂无检查结果。</div>`}
      </div>
    </section>
  `;
}

function renderAdminReadingsTab() {
  return `
    <section class="admin-grid two">
      <article class="admin-panel">
        <p class="eyebrow">测算查询</p>
        <form class="admin-form" data-admin-reading-search>
          <label>测算 ID<input name="readingId" value="${escapeHtml(adminState.searchReadingId || formState.readingId || "")}" placeholder="输入测算 ID"></label>
          <button type="submit">读取测算详情</button>
        </form>
      </article>
      <article class="admin-panel">
        <p class="eyebrow">历史查询</p>
        <form class="admin-form" data-admin-history-search>
          <label>用户 ID<input name="actorId" value="${escapeHtml(adminState.searchActorId || formState.actorId || "")}" placeholder="用户 ID"></label>
          <label>会话 ID<input name="sessionId" value="${escapeHtml(adminState.searchSessionId || formState.sessionId || "")}" placeholder="会话 ID"></label>
          <button type="submit">读取历史</button>
        </form>
      </article>
    </section>
    ${renderAdminReadingResult()}
  `;
}

function renderAdminContractsTab() {
  const caps = adminState.capabilities || {};
  const contract = caps.api_contract || {};
  return `
    <section class="admin-panel">
      <p class="eyebrow">接口状态</p>
      <h2>${escapeHtml(contract.version || caps.version || "待读取")}</h2>
      <div class="endpoint-list">
        ${adminState.endpointStatus.length ? adminState.endpointStatus.map(renderEndpointStatus).join("") : `<div class="history-empty">刷新后显示端点可用性。</div>`}
      </div>
    </section>
    <section class="admin-panel">
      <p class="eyebrow">角色与语言</p>
      <div class="policy-list">
        ${(caps.roles || []).map((role) => `<span>${escapeHtml(role.key)} · ${escapeHtml(role.surface)}</span>`).join("")}
      </div>
      <div class="policy-list">
        ${(caps.locales || []).map((locale) => `<span>${escapeHtml(locale.key)} · ${escapeHtml(locale.label)}</span>`).join("")}
      </div>
    </section>
  `;
}

function renderAdminRuntimeTab() {
  const config = adminState.runtimeConfig || {};
  const dbConfig = config.database || {};
  const redisConfig = config.redis || {};
  const db = adminState.dbStatus || {};
  const redis = adminState.redisStatus || {};
  return `
    <section class="admin-grid two">
      <article class="admin-panel">
        <div class="section-head">
          <p class="eyebrow">Postgres</p>
          <h2>数据库配置与状态</h2>
        </div>
        <div class="admin-actions left">
          <button type="button" data-admin-load-runtime>${adminState.loading ? "读取中" : "读取 DB / Redis 状态"}</button>
          <button type="button" data-admin-db-schema>应用 V30 Schema</button>
        </div>
        <form class="admin-form" data-admin-db-config>
          <label>Repository
            <select name="repository">
              ${["postgres", "local_json", "memory"].map((value) => `<option value="${value}"${(dbConfig.repository || "postgres") === value ? " selected" : ""}>${value}</option>`).join("")}
            </select>
          </label>
          <label>V30_DATABASE_URL
            <input name="database_url" placeholder="postgresql://qiazhi_v30_app:...@127.0.0.1:5432/qiazhi_v30?sslmode=prefer">
          </label>
          <button type="submit">保存数据库配置</button>
        </form>
        <div class="admin-kv">
          ${renderKv("status", db.status)}
          ${renderKv("repository", db.repository || dbConfig.repository)}
          ${renderKv("url", db.database_url_present ? "present" : "missing")}
          ${renderKv("host", db.postgres ? `${db.postgres.host || "-"}:${db.postgres.port || "-"}` : "-")}
          ${renderKv("database", db.postgres?.database)}
          ${renderKv("schema", db.missing_tables?.length ? `缺 ${db.missing_tables.length}` : db.schema_table_count ? "ready" : "-")}
        </div>
        ${adminState.dbConfigSave ? renderStatusCard("DB Config Save", adminState.dbConfigSave) : ""}
        ${adminState.dbSchemaApply ? renderStatusCard("Schema Apply", adminState.dbSchemaApply) : ""}
      </article>
      <article class="admin-panel">
        <div class="section-head">
          <p class="eyebrow">Redis</p>
          <h2>缓存配置与状态</h2>
        </div>
        <form class="admin-form" data-admin-redis-config>
          <label>V30_REDIS_URL
            <input name="redis_url" value="${escapeHtml(redisConfig.redis_url || "")}" placeholder="redis://127.0.0.1:6379/0">
          </label>
          <button type="submit">保存 Redis 配置</button>
        </form>
        <div class="admin-kv">
          ${renderKv("status", redis.status)}
          ${renderKv("url", redis.redis_url_present ? "present" : "missing")}
          ${renderKv("ping", redis.ping ? "ok" : "-")}
          ${renderKv("db", redis.db)}
          ${renderKv("keys", redis.key_count)}
          ${renderKv("keyspace", redis.keyspace)}
        </div>
        ${adminState.redisConfigSave ? renderStatusCard("Redis Config Save", adminState.redisConfigSave) : ""}
        <p class="admin-note">DB/Redis 配置保存后需要重启 9030，测算写入链路才会切到新的 repository/cache。</p>
      </article>
    </section>
  `;
}

function renderAdminLlmTab() {
  const status = adminState.llmStatus || {};
  const runtime = status.runtime || {};
  const readiness = runtime.readiness || {};
  const savedConfig = (adminState.runtimeConfig || {}).llm || {};
  const runtimeConfig = runtime.config || {};
  const cfg = Object.keys(savedConfig).length ? savedConfig : runtimeConfig;
  const models = Array.isArray(runtime.models) ? runtime.models : [];
  const currentModel = cfg.model || readiness.model || "";
  const cards = [
    ["运行配置", runtime],
    ["上下文/提示词", status.contextPrompt],
    ["回答生成器", status.answerGenerator],
    ["输出验收", status.outputAcceptance],
    ["训练/合成", status.trainingSynthetic],
    ["角色/语言 smoke", status.roleLocaleSmoke],
    ["Closeout", status.closeout],
  ];
  return `
    <section class="admin-panel">
      <div class="section-head">
        <p class="eyebrow">Bazi LLM</p>
        <h2>LLM 只润色八字表达，不改命盘事实</h2>
      </div>
      <div class="admin-actions left">
        <button type="button" data-admin-load-llm>${adminState.loading ? "读取中" : "读取 LLM 状态"}</button>
        <button type="button" data-admin-load-runtime>读取运行配置</button>
      </div>
      <section class="admin-grid two">
        <form class="admin-panel admin-form" data-admin-llm-config>
          <p class="eyebrow">LLM 配置</p>
          <label class="check"><input type="checkbox" name="enabled"${String(cfg.enabled || readiness.enabled || "") === "1" || readiness.enabled ? " checked" : ""}>启用 LLM</label>
          <label class="check"><input type="checkbox" name="execute_llm"${String(cfg.execute_llm || readiness.execute_llm || "") === "1" || readiness.execute_llm ? " checked" : ""}>实际调用 LLM</label>
          <label>Provider
            <select name="provider">
              ${["ollama_native", "ollama", "openai_compatible", "local_openai_compatible"].map((provider) => `
                <option value="${provider}"${(cfg.provider || readiness.provider || "ollama_native") === provider ? " selected" : ""}>${provider}</option>
              `).join("")}
            </select>
          </label>
          <label>Host<input name="host" value="${escapeHtml(cfg.host || "")}" placeholder="127.0.0.1 或 192.168.x.x"></label>
          <label>Port<input name="port" type="number" value="${escapeHtml(cfg.port || "")}" placeholder="11434"></label>
          <label>Base URL<input name="base_url" value="${escapeHtml(cfg.base_url || readiness.resolved_base_url || "")}" placeholder="http://127.0.0.1:11434/v1"></label>
          ${renderLlmModelControl(models, currentModel)}
          <label>API Key<input name="api_key" type="password" placeholder="不填则保持原值"></label>
          <label>Timeout<input name="http_timeout_sec" type="number" step="0.1" value="${escapeHtml(cfg.http_timeout_sec || "")}" placeholder="15"></label>
          <label>Temperature<input name="temperature" type="number" step="0.1" value="${escapeHtml(cfg.temperature || "")}" placeholder="0.2"></label>
          <label>Max Tokens<input name="max_tokens" type="number" value="${escapeHtml(cfg.max_tokens || "")}" placeholder="600"></label>
          <button type="submit">保存 LLM 配置</button>
        </form>
        <form class="admin-panel admin-form" data-admin-llm-test>
          <p class="eyebrow">连接测试</p>
          <div class="admin-kv">
            ${renderKv("ready", readiness.ready_for_connection)}
            ${renderKv("execute", readiness.execute_llm)}
            ${renderKv("provider", readiness.provider)}
            ${renderKv("model", readiness.model)}
            ${renderKv("base", readiness.resolved_base_url)}
          </div>
          <label>测试提示词<textarea name="prompt" rows="4">用一句中文回答：启智 V30 LLM 测试正常。</textarea></label>
          <button type="submit">测试 LLM</button>
          ${adminState.llmConfigSave ? renderStatusCard("LLM Config Save", adminState.llmConfigSave) : ""}
          ${renderLlmTestResult(adminState.llmTest)}
        </form>
      </section>
      <div class="admin-grid two">
        ${cards.map(([label, payload]) => renderStatusCard(label, payload)).join("")}
      </div>
    </section>
  `;
}

function renderLlmModelControl(models, currentModel) {
  const modelIds = models.map((row) => String(row.id || "")).filter(Boolean);
  if (!modelIds.length) {
    return `<label>Model<input name="model" value="${escapeHtml(currentModel || "")}" placeholder="先点击读取 LLM 状态探测 Ollama 模型"></label>`;
  }
  const allModelIds = modelIds.includes(currentModel) || !currentModel ? modelIds : [currentModel, ...modelIds];
  return `
    <label>Model
      <select name="model">
        ${allModelIds.map((modelId) => `<option value="${escapeHtml(modelId)}"${modelId === currentModel ? " selected" : ""}>${escapeHtml(modelId)}</option>`).join("")}
      </select>
    </label>
    <p class="admin-note">已探测到 ${modelIds.length} 个 Ollama 模型；保存后后续 LLM 调用会使用所选模型。</p>
  `;
}

function renderLlmTestResult(payload) {
  const result = payload || {};
  if (!result.version && !result.status && !result.error) return "";
  return `
    <article class="status-card ${result.error || result.status === "failed" ? "failed" : "passed"} llm-test-result">
      <p class="eyebrow">LLM Test</p>
      <h3>${escapeHtml(result.error || result.status || "unknown")}</h3>
      <div class="admin-kv">
        ${renderKv("provider", result.provider)}
        ${renderKv("model", result.model)}
        ${renderKv("executed", result.executed)}
        ${renderKv("duration", result.duration_ms !== undefined ? `${result.duration_ms}ms` : "-")}
        ${renderKv("timeout", result.timeout_sec)}
      </div>
      ${result.sample ? `<pre class="llm-test-sample">${escapeHtml(result.sample)}</pre>` : ""}
      <p class="admin-note">这是模型连通性测试样例，不代表八字测算回答质量；真实测算仍会经过命盘上下文、漂移和事实边界检查。</p>
    </article>
  `;
}

function renderAdminTrainingTab() {
  const status = adminState.trainingStatus || {};
  const run = adminState.trainingRun || {};
  const m3Job = adminState.m3TrainingJob || {};
  const families = [
    ["question_policy", "问答策略"],
    ["structure_policy", "结构策略"],
    ["mainline_policy", "主线策略"],
    ["rule_policy", "规则策略"],
  ];
  return `
    <section class="admin-grid two">
      <article class="admin-panel">
        <p class="eyebrow">Training Status</p>
        <h2>训练闭环与隔离</h2>
        <div class="admin-actions left">
          <button type="button" data-admin-load-training>${adminState.loading ? "读取中" : "读取训练状态"}</button>
        </div>
        <div class="admin-grid">
          ${renderStatusCard("系统收口", status.systemCloseout)}
          ${renderStatusCard("候选隔离", status.candidateQuarantine)}
          ${renderStatusCard("隐藏属性审核", status.latentAttributeReview)}
        </div>
      </article>
      <article class="admin-panel">
        <p class="eyebrow">训练任务</p>
        <h2>只跑已有训练族，不自动发布</h2>
        <form class="admin-form" data-admin-training-run>
          <label>Training Run ID<input name="trainingRunId" placeholder="ui6-training-${Date.now()}"></label>
          <div class="training-family-grid">
            ${families.map(([key, label]) => `
              <label class="check"><input type="checkbox" name="families" value="${escapeHtml(key)}">${escapeHtml(label)}</label>
            `).join("")}
          </div>
          <button type="submit">运行训练</button>
        </form>
        ${run.version || run.status ? renderStatusCard("最近训练", run) : `<div class="history-empty">未运行训练。默认不会发布策略。</div>`}
      </article>
      <article class="admin-panel">
        <p class="eyebrow">Latent Attribute Review</p>
        <h2>隐藏属性训练候选审核</h2>
        ${renderLatentAttributeTrainingReview(status.latentAttributeReview)}
      </article>
      <article class="admin-panel">
        <p class="eyebrow">M3 Long Run</p>
        <h2>M3、训练合成、518K 后台验证</h2>
        <form class="admin-form" data-admin-m3-job-run>
          <label>518K Sample Limit<input name="sampleLimit" type="number" min="1" max="256" value="8"></label>
          <div class="training-family-grid">
            <label class="check"><input type="checkbox" name="persistM3ToDb" checked> M3 快照写入 Postgres</label>
            <label class="check"><input type="checkbox" name="includeShard"> 同时跑 518K shard</label>
            <label>Shard ID<input name="shardId" type="number" min="0" value="7"></label>
            <label>Shard Limit<input name="shardLimit" type="number" min="1" max="512" value="16"></label>
            <label class="check"><input type="checkbox" name="includeReadiness"> 同时跑 readiness matrix</label>
          </div>
          <div class="admin-actions left">
            <button type="submit">启动 M3 后台任务</button>
            <button type="button" data-admin-m3-job-refresh>刷新进度</button>
          </div>
        </form>
        ${renderM3TrainingJobProgress(m3Job)}
      </article>
    </section>
  `;
}

function renderLatentAttributeTrainingReview(review) {
  if (!review || !review.version) {
    return `<div class="history-empty">读取训练状态后显示隐藏属性训练候选。</div>`;
  }
  const decision = review.decision || {};
  const summary = review.candidate_summary || {};
  const boundary = review.policy_boundary || {};
  const candidates = Array.isArray(review.candidates) ? review.candidates : [];
  const ready = decision.review_ready === true;
  return `
    <div class="latent-training-review ${ready ? "ready" : "blocked"}">
      <div class="admin-kv">
        ${renderKv("status", decision.decision_status || review.status || "-")}
        ${renderKv("candidates", decision.candidate_count ?? summary.candidate_count ?? "-")}
        ${renderKv("checks", `${decision.passed_check_count ?? 0}/${decision.check_count ?? 0}`)}
        ${renderKv("next", review.next_mainline_selection?.task_id || "-")}
      </div>
      <div class="training-boundary-strip">
        <span>${boundary.auto_apply_training_allowed ? "允许自动应用" : "禁止自动应用"}</span>
        <span>${boundary.policy_pointer_promotion_allowed ? "允许指针提升" : "禁止指针提升"}</span>
        <span>${boundary.chart_fact_mutation_allowed ? "允许改命盘事实" : "禁止改命盘事实"}</span>
      </div>
      <div class="latent-review-scope">
        <div>
          <p class="eyebrow">允许训练</p>
          ${(summary.allowed_training_scope || []).map((row) => `<span>${escapeHtml(latentTrainingScopeLabel(row))}</span>`).join("") || "<span>-</span>"}
        </div>
        <div>
          <p class="eyebrow">禁止训练</p>
          ${(summary.forbidden_training_scope || []).slice(0, 8).map((row) => `<span>${escapeHtml(latentTrainingScopeLabel(row))}</span>`).join("") || "<span>-</span>"}
        </div>
      </div>
      <div class="module-list compact latent-candidate-list">
        ${candidates.length ? candidates.map(renderLatentTrainingCandidate).join("") : `<div class="module-row"><strong>暂无候选</strong><span>没有可审核候选。</span></div>`}
      </div>
    </div>
  `;
}

function renderLatentTrainingCandidate(row) {
  return `
    <div class="module-row">
      <strong>${escapeHtml(latentCandidateLabel(row.candidate_type || row.target_domain || ""))}</strong>
      <span>${escapeHtml(row.evidence_summary || "")}</span>
      <em>${escapeHtml(row.requires_operator_review ? "人工复核" : "自动")} · ${escapeHtml(row.auto_apply_allowed ? "可自动应用" : "只读")}</em>
    </div>
  `;
}

function latentCandidateLabel(value) {
  const labels = {
    latent_reverse_inference_review: "隐藏属性反推审核",
    latent_question_strategy_review: "问答策略审核",
    latent_individualized_projection_review: "个体化投影审核",
    latent_attribute_inference: "隐藏属性反推",
    question_strategy: "问答策略",
    individualized_projection: "个体化投影",
  };
  return labels[value] || value;
}

function latentTrainingScopeLabel(value) {
  const labels = {
    latent_attribute_inference: "隐藏属性反推",
    question_strategy: "问答策略",
    individualized_projection: "个体化投影",
    chart_facts: "命盘事实",
    calendar_conversion: "历法转换",
    luck_cycle: "大运",
    flow_timing: "流年流月",
    four_pillars: "四柱",
    fixed_structure_verdict: "固定格局结论",
    fixed_useful_god_verdict: "固定用神结论",
  };
  return labels[value] || value;
}

function renderM3TrainingJobProgress(job) {
  if (!job || (!job.job_id && job.status !== "not_started")) {
    return `<div class="history-empty">未启动后台任务。默认链路：M3 快照写 DB、M3 synthetic、training_pipeline、518K sample。</div>`;
  }
  if (job.status === "not_started" || job.status === "not_found") {
    return `<div class="history-empty">暂无可读取的 M3 后台任务。</div>`;
  }
  const percent = Number(job.progress_percent || 0);
  const results = Array.isArray(job.results) ? job.results : [];
  const statusClass = job.status === "completed" ? "passed" : job.status === "failed" ? "failed" : "partial";
  return `
    <article class="status-card ${statusClass} m3-job-card">
      <p class="eyebrow">Job ${escapeHtml(job.job_id || "-")}</p>
      <h3>${escapeHtml(job.status || "unknown")} · ${Math.max(0, Math.min(100, percent))}%</h3>
      <div class="module-progress" aria-label="M3 job progress">
        <i style="width:${Math.max(0, Math.min(100, percent))}%"></i>
      </div>
      <div class="admin-kv">
        ${renderKv("current_step", job.current_step)}
        ${renderKv("steps", `${job.completed_steps || 0}/${job.total_steps || 0}`)}
        ${renderKv("created_at", job.created_at)}
        ${renderKv("finished_at", job.finished_at || "-")}
        ${job.error ? renderKv("error", job.error) : ""}
      </div>
      <div class="module-list compact">
        ${results.length ? results.map((row) => renderM3TrainingJobResult(row)).join("") : `<div class="module-row"><strong>等待结果</strong><span>任务启动后会逐步显示每个脚本的摘要。</span></div>`}
      </div>
    </article>
  `;
}

function renderM3TrainingJobResult(row) {
  const title = row.step || row.suite_id || row.run_id || "result";
  const detail = [
    row.snapshot_id,
    row.suite_id,
    row.run_id,
    row.passed !== undefined ? `passed=${row.passed}` : "",
    row.promotion_signal,
    row.case_count !== undefined ? `cases=${row.case_count}` : "",
    row.passed_count !== undefined ? `${row.passed_count}/${row.case_count}` : "",
    row.artifact_search_backend,
  ].filter(Boolean).join(" · ");
  return `
    <div class="module-row">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail || "completed")}</span>
    </div>
  `;
}

function renderAdminValidationTab() {
  const status = adminState.validationStatus || {};
  return `
    <section class="admin-panel">
      <div class="section-head">
        <p class="eyebrow">Validation</p>
        <h2>合成、518K、业务验收</h2>
      </div>
      <div class="admin-actions left">
        <button type="button" data-admin-load-validation>${adminState.loading ? "读取中" : "读取验证状态"}</button>
      </div>
      <div class="admin-grid two">
        ${renderStatusCard("合成覆盖", status.syntheticCoverage)}
        ${renderStatusCard("验证记录", status.validationArtifacts)}
        ${renderStatusCard("518K 准备度", status.corpus518k)}
        ${renderStatusCard("518K 记录", status.corpusArtifacts)}
        ${renderStatusCard("业务验收", status.businessAcceptance)}
        ${renderStatusCard("业务稳态", status.businessSteadyState)}
      </div>
    </section>
  `;
}

function renderModuleRow(row) {
  const completion = Number(row.completion) || 0;
  return `
    <article class="module-row">
      <div>
        <strong>${escapeHtml(row.module_id || "")}</strong>
        <span>${escapeHtml(row.name || "")}</span>
      </div>
      <div class="module-progress"><i style="width:${Math.max(0, Math.min(100, completion))}%"></i></div>
      <em>${completion}% · ${escapeHtml(row.status || "")}</em>
    </article>
  `;
}

function renderAdminCheck(row) {
  return `
    <article class="admin-check ${row.passed ? "passed" : "failed"}">
      <strong>${row.passed ? "通过" : "阻塞"}</strong>
      <span>${escapeHtml(row.check_id || "")}</span>
    </article>
  `;
}

function renderEndpointStatus(row) {
  return `
    <article class="endpoint-row ${row.ok ? "passed" : "failed"}">
      <strong>${row.ok ? "OK" : "ERR"}</strong>
      <span>${escapeHtml(row.label)}</span>
      <em>${escapeHtml(row.status || row.error || "")}</em>
    </article>
  `;
}

function renderStatusCard(label, payload) {
  const row = payload || {};
  if (!row || (!row.version && !row.status && !row.decision && !row.error)) {
    return `
      <article class="status-card empty-status">
        <p class="eyebrow">${escapeHtml(label)}</p>
        <h3>待读取</h3>
        <p>点击读取按钮后显示。</p>
      </article>
    `;
  }
  const decision = row.decision || {};
  const status = row.status || decision.decision_status || decision.status || row.version || "ready";
  return `
    <article class="status-card ${row.error ? "failed" : "passed"}">
      <p class="eyebrow">${escapeHtml(label)}</p>
      <h3>${escapeHtml(row.error || status)}</h3>
      <div class="admin-kv">
        ${renderKv("version", row.version)}
        ${renderKv("checks", formatCheckCount(row))}
        ${renderKv("边界", row.boundary || row.policy_boundary?.boundary)}
      </div>
    </article>
  `;
}

function formatCheckCount(row) {
  const decision = row.decision || {};
  if (decision.passed_count !== undefined || decision.check_count !== undefined) {
    return `${decision.passed_count ?? "-"} / ${decision.check_count ?? "-"}`;
  }
  if (Array.isArray(row.checks)) return String(row.checks.length);
  if (row.count !== undefined) return row.count;
  if (row.artifact_count !== undefined) return row.artifact_count;
  return "-";
}

function renderAdminReadingResult() {
  const view = adminState.readingView || {};
  const trace = adminState.trace || {};
  const history = adminState.searchHistory || {};
  const surface = view.reading_surface || {};
  const diagnostics = view.diagnostics || {};
  return `
    <section class="admin-grid two">
      <article class="admin-panel">
        <p class="eyebrow">测算详情</p>
        <h3>${escapeHtml(surface.reading_summary?.title || view.reading_id || "未读取")}</h3>
        <div class="admin-kv">
          ${renderKv("追踪", diagnostics.trace_id)}
          ${renderKv("问题数", diagnostics.recommendation_count)}
          ${renderKv("内部上下文", Boolean(diagnostics.internal_bazi_context || diagnostics.bazi_context))}
        </div>
      </article>
      <article class="admin-panel">
        <p class="eyebrow">运行追踪</p>
        <h3>${escapeHtml(trace.trace_id || "未读取")}</h3>
        <div class="admin-kv">
          ${renderKv("版本", trace.version)}
          ${renderKv("测算", trace.reading_id)}
          ${renderKv("事件", Array.isArray(trace.events) ? trace.events.length : trace.event_count)}
        </div>
      </article>
    </section>
    <section class="admin-panel">
      <p class="eyebrow">历史结果</p>
      <div class="history-list admin-history-list">
        ${(history.items || []).length ? history.items.slice(0, 10).map(renderAdminHistoryItem).join("") : `<div class="history-empty">暂无历史查询结果。</div>`}
      </div>
    </section>
  `;
}

function renderAdminHistoryItem(item) {
  const readingId = item.reading_id || "";
  const title = item.title || item.reading_title || readingId || "未命名测算";
  const status = item.chart_status || item.status || "ready";
  const trace = item.trace_id || "";
  return `
    <button type="button" class="history-item" data-admin-open-reading="${escapeHtml(readingId)}">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(status)}${trace ? ` · ${escapeHtml(trace)}` : ""}</span>
    </button>
  `;
}

function renderKv(key, value) {
  return `<div><span>${escapeHtml(key)}</span><strong>${escapeHtml(value ?? "-")}</strong></div>`;
}

async function handleAdminTabChange(event) {
  const activeTab = event.currentTarget.getAttribute("data-admin-tab") || "overview";
  adminState = {
    ...adminState,
    activeTab,
  };
  const url = new URL(window.location.href);
  url.searchParams.set("surface", "admin");
  url.searchParams.set("role", "admin");
  url.searchParams.set("tab", activeTab);
  window.history.replaceState({}, "", url.toString());
  renderAdminShell();
}

async function loadAdminOverview() {
  adminState = { ...adminState, loading: true, notice: "正在读取后台状态。" };
  setStatus("admin");
  renderAdminShell();
  const endpoints = [
    ["health", "/api/v30/health", 8000],
    ["capabilities", "/api/v30/ui/capabilities", 8000],
    ["mainlineSelection", "/api/v30/admin/mainline/selection", 10000],
    ["moduleReview", "/api/v30/admin/mainline/main-module-completion-review", 18000],
    ["coreCalibrationS0", "/api/v30/admin/mainline/core-calibration-steady-state-queue?sample_limit=8", 18000],
  ];
  const results = await Promise.all(endpoints.map(async ([key, url, timeoutMs]) => {
    try {
      const payload = await fetchJson(url, {}, timeoutMs);
      return { key, url, ok: true, payload };
    } catch (error) {
      return { key, url, ok: false, error: error.message || "request_failed" };
    }
  }));
  const nextState = { ...adminState };
  results.forEach((row) => {
    if (row.ok) nextState[row.key] = row.payload;
  });
  nextState.endpointStatus = results.map((row) => ({
    label: row.url,
    ok: row.ok,
    status: row.ok ? "ready" : "",
    error: row.error || "",
  }));
  const failed = results.filter((row) => !row.ok);
  adminState = {
    ...nextState,
    loaded: true,
    loading: false,
    notice: failed.length ? `部分后台端点未就绪：${failed.map((row) => row.key).join("、")}` : "后台状态已刷新。",
  };
  setStatus(failed.length ? "partial" : "ready");
  renderAdminShell();
}

async function loadAdminRuntimeStatus() {
  adminState = { ...adminState, loading: true, notice: "正在读取 DB / Redis / LLM 运行配置。" };
  setStatus("runtime");
  renderAdminShell();
  const rows = await loadEndpointGroup([
    ["config", "/api/v30/admin/runtime/config", 8000],
    ["db", "/api/v30/admin/runtime/db", 10000],
    ["redis", "/api/v30/admin/runtime/redis", 8000],
    ["llm", "/api/v30/admin/runtime/llm?probe_models=true", 12000],
  ]);
  adminState = {
    ...adminState,
    loading: false,
    runtimeConfig: rows.payload.config,
    dbStatus: rows.payload.db,
    redisStatus: rows.payload.redis,
    llmStatus: { ...(adminState.llmStatus || {}), runtime: rows.payload.llm },
    notice: rows.failed.length ? `运行配置部分端点未就绪：${rows.failed.join("、")}` : "DB / Redis / LLM 运行配置已读取。",
  };
  setStatus(rows.failed.length ? "partial" : "ready");
  renderAdminShell();
}

async function loadAdminLlmStatus() {
  adminState = { ...adminState, loading: true, notice: "正在读取 LLM readiness。" };
  setStatus("llm");
  renderAdminShell();
  const rows = await loadEndpointGroup([
    ["runtime", "/api/v30/admin/runtime/llm?probe_models=true", 12000],
    ["contextPrompt", "/api/v30/admin/llm/bazi-context-prompt-readiness", 12000],
    ["answerGenerator", "/api/v30/admin/llm/bazi-answer-generator-readiness", 12000],
    ["outputAcceptance", "/api/v30/admin/llm/bazi-output-acceptance-readiness", 12000],
    ["trainingSynthetic", "/api/v30/admin/llm/bazi-training-synthetic-readiness", 12000],
    ["roleLocaleSmoke", "/api/v30/admin/llm/bazi-role-locale-production-smoke", 12000],
    ["closeout", "/api/v30/admin/llm/bazi-closeout", 12000],
  ]);
  adminState = {
    ...adminState,
    loading: false,
    llmStatus: rows.payload,
    notice: rows.failed.length ? `LLM 部分端点未就绪：${rows.failed.join("、")}` : "LLM readiness 已读取。",
  };
  setStatus(rows.failed.length ? "partial" : "ready");
  renderAdminShell();
}

async function submitAdminDbConfig(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  adminState = { ...adminState, loading: true, notice: "正在保存数据库配置。" };
  setStatus("db");
  renderAdminShell();
  try {
    const payload = await fetchJson("/api/v30/admin/runtime/db/config", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        repository: String(data.get("repository") || "postgres"),
        database_url: String(data.get("database_url") || ""),
      }),
    }, 10000);
    adminState = { ...adminState, loading: false, dbConfigSave: payload, notice: "数据库配置已保存；重启 9030 后测算写入链路生效。" };
    setStatus("ready");
    await loadAdminRuntimeStatus();
  } catch (error) {
    adminState = { ...adminState, loading: false, dbConfigSave: { error: error.message }, notice: `数据库配置保存失败：${error.message}` };
    setStatus("error");
    renderAdminShell();
  }
}

async function submitAdminRedisConfig(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  adminState = { ...adminState, loading: true, notice: "正在保存 Redis 配置。" };
  setStatus("redis");
  renderAdminShell();
  try {
    const payload = await fetchJson("/api/v30/admin/runtime/redis/config", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ redis_url: String(data.get("redis_url") || "") }),
    }, 10000);
    adminState = { ...adminState, loading: false, redisConfigSave: payload, notice: "Redis 配置已保存；重启 9030 后缓存链路生效。" };
    setStatus("ready");
    await loadAdminRuntimeStatus();
  } catch (error) {
    adminState = { ...adminState, loading: false, redisConfigSave: { error: error.message }, notice: `Redis 配置保存失败：${error.message}` };
    setStatus("error");
    renderAdminShell();
  }
}

async function applyAdminDbSchema() {
  adminState = { ...adminState, loading: true, notice: "正在应用 V30 Postgres schema。" };
  setStatus("schema");
  renderAdminShell();
  try {
    const payload = await fetchJson("/api/v30/admin/runtime/db/apply-schema", { method: "POST" }, 12000);
    adminState = { ...adminState, loading: false, dbSchemaApply: payload, notice: `Schema ${payload.status || "完成"}。` };
    setStatus(payload.status === "applied" ? "ready" : "partial");
    await loadAdminRuntimeStatus();
  } catch (error) {
    adminState = { ...adminState, loading: false, dbSchemaApply: { error: error.message }, notice: `Schema 应用失败：${error.message}` };
    setStatus("error");
    renderAdminShell();
  }
}

async function submitAdminLlmConfig(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const payload = {
    enabled: data.get("enabled") === "on",
    execute_llm: data.get("execute_llm") === "on",
    provider: String(data.get("provider") || ""),
    host: String(data.get("host") || ""),
    port: String(data.get("port") || ""),
    base_url: String(data.get("base_url") || ""),
    model: String(data.get("model") || ""),
    api_key: String(data.get("api_key") || ""),
    http_timeout_sec: String(data.get("http_timeout_sec") || ""),
    temperature: String(data.get("temperature") || ""),
    max_tokens: String(data.get("max_tokens") || ""),
  };
  adminState = { ...adminState, loading: true, notice: "正在保存 LLM 配置。" };
  setStatus("llm");
  renderAdminShell();
  try {
    const result = await fetchJson("/api/v30/admin/runtime/llm/config", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    }, 10000);
    adminState = { ...adminState, loading: false, llmConfigSave: result, notice: "LLM 配置已保存；后续 LLM 调用会读取新配置。" };
    setStatus("ready");
    await loadAdminLlmStatus();
  } catch (error) {
    adminState = { ...adminState, loading: false, llmConfigSave: { error: error.message }, notice: `LLM 配置保存失败：${error.message}` };
    setStatus("error");
    renderAdminShell();
  }
}

async function submitAdminLlmTest(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  adminState = { ...adminState, loading: true, notice: "正在测试 LLM 连接。" };
  setStatus("llm-test");
  renderAdminShell();
  try {
    const payload = await fetchJson("/api/v30/admin/runtime/llm/test", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ prompt: String(data.get("prompt") || "") }),
    }, 45000);
    adminState = { ...adminState, loading: false, llmTest: payload, notice: `LLM 测试：${payload.status || "完成"}` };
    setStatus(payload.status === "ok" ? "ready" : "partial");
  } catch (error) {
    adminState = { ...adminState, loading: false, llmTest: { error: error.message }, notice: `LLM 测试失败：${error.message}` };
    setStatus("error");
  }
  renderAdminShell();
}

async function loadAdminTrainingStatus() {
  adminState = { ...adminState, loading: true, notice: "正在读取训练状态。" };
  setStatus("training");
  renderAdminShell();
  const rows = await loadEndpointGroup([
    ["systemCloseout", "/api/v30/admin/training/system-closeout", 14000],
    ["candidateQuarantine", "/api/v30/admin/training/candidate-quarantine", 14000],
    ["latentAttributeReview", "/api/v30/admin/training/latent-attribute-review", 18000],
  ]);
  adminState = {
    ...adminState,
    loading: false,
    trainingStatus: rows.payload,
    notice: rows.failed.length ? `训练部分端点未就绪：${rows.failed.join("、")}` : "训练状态已读取。",
  };
  setStatus(rows.failed.length ? "partial" : "ready");
  renderAdminShell();
}

async function loadAdminValidationStatus() {
  adminState = { ...adminState, loading: true, notice: "正在读取验证状态。" };
  setStatus("validation");
  renderAdminShell();
  const rows = await loadEndpointGroup([
    ["syntheticCoverage", "/api/v30/admin/validation/synthetic-coverage-manifest", 14000],
    ["validationArtifacts", "/api/v30/admin/validation/artifacts?limit=10", 10000],
    ["corpus518k", "/api/v30/admin/validation/518k/readiness-matrix?sample_limit=8&shard_limit=16", 18000],
    ["corpusArtifacts", "/api/v30/admin/validation/518k/artifacts?limit=10", 10000],
    ["businessAcceptance", "/api/v30/admin/business/real-bazi-acceptance?case_limit=12", 18000],
    ["businessSteadyState", "/api/v30/admin/business/steady-state", 18000],
  ]);
  adminState = {
    ...adminState,
    loading: false,
    validationStatus: rows.payload,
    notice: rows.failed.length ? `验证部分端点未就绪：${rows.failed.join("、")}` : "验证状态已读取。",
  };
  setStatus(rows.failed.length ? "partial" : "ready");
  renderAdminShell();
}

async function loadEndpointGroup(endpoints) {
  const results = await Promise.all(endpoints.map(async ([key, url, timeoutMs]) => {
    try {
      const payload = await fetchJson(url, {}, timeoutMs);
      return { key, ok: true, payload };
    } catch (error) {
      return { key, ok: false, payload: { error: error.name === "AbortError" ? "timeout" : error.message || "request_failed" } };
    }
  }));
  const payload = {};
  results.forEach((row) => {
    payload[row.key] = row.payload;
  });
  return {
    payload,
    failed: results.filter((row) => !row.ok).map((row) => row.key),
  };
}

async function submitAdminTrainingRun(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const families = data.getAll("families").map((row) => String(row)).filter(Boolean);
  const trainingRunId = String(data.get("trainingRunId") || `ui6-training-${Date.now()}`).trim();
  adminState = { ...adminState, loading: true, notice: "正在运行训练任务。" };
  setStatus("training");
  renderAdminShell();
  try {
    const payload = await fetchJson("/api/v30/admin/training/run", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        training_run_id: trainingRunId,
        families,
      }),
    }, 20000);
    adminState = {
      ...adminState,
      loading: false,
      trainingRun: payload,
      notice: "训练任务已完成；未自动发布策略。",
    };
    setStatus("ready");
  } catch (error) {
    adminState = {
      ...adminState,
      loading: false,
      trainingRun: { error: error.name === "AbortError" ? "timeout" : error.message || "training_failed" },
      notice: `训练运行失败：${error.message || "training_failed"}`,
    };
    setStatus("error");
  }
  renderAdminShell();
}

async function submitAdminM3TrainingJob(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const payload = {
    sample_limit: Number(data.get("sampleLimit") || 8),
    persist_m3_to_db: data.get("persistM3ToDb") === "on",
    include_shard: data.get("includeShard") === "on",
    shard_id: Number(data.get("shardId") || 7),
    shard_limit: Number(data.get("shardLimit") || 16),
    include_readiness_matrix: data.get("includeReadiness") === "on",
  };
  adminState = { ...adminState, loading: true, notice: "正在启动 M3 后台训练/验证任务。" };
  setStatus("training");
  renderAdminShell();
  try {
    const job = await fetchJson("/api/v30/admin/training/m3-background/run", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    }, 12000);
    adminState = {
      ...adminState,
      loading: false,
      m3TrainingJob: job,
      m3TrainingJobId: job.job_id || "",
      notice: "M3 后台任务已启动；页面会自动刷新进度。",
    };
    setStatus("training");
    renderAdminShell();
    scheduleAdminM3TrainingPoll();
  } catch (error) {
    adminState = {
      ...adminState,
      loading: false,
      m3TrainingJob: { status: "failed", error: error.message || "job_start_failed" },
      notice: `M3 后台任务启动失败：${error.message || "job_start_failed"}`,
    };
    setStatus("error");
    renderAdminShell();
  }
}

async function refreshAdminM3TrainingJob() {
  const jobId = adminState.m3TrainingJobId || adminState.m3TrainingJob?.job_id || "";
  const suffix = jobId ? `?job_id=${encodeURIComponent(jobId)}` : "";
  try {
    const job = await fetchJson(`/api/v30/admin/training/m3-background/status${suffix}`, {}, 10000);
    adminState = {
      ...adminState,
      m3TrainingJob: job,
      m3TrainingJobId: job.job_id || jobId,
      notice: job.status === "completed" ? "M3 后台任务已完成。" : job.status === "failed" ? "M3 后台任务失败，查看失败步骤。" : "M3 后台任务进度已刷新。",
    };
    setStatus(job.status === "failed" ? "error" : job.status === "completed" ? "ready" : "training");
    renderAdminShell();
    if (job.status === "queued" || job.status === "running") {
      scheduleAdminM3TrainingPoll();
    }
  } catch (error) {
    adminState = {
      ...adminState,
      m3TrainingJob: { ...(adminState.m3TrainingJob || {}), error: error.message || "job_status_failed" },
      notice: `M3 后台任务进度读取失败：${error.message || "job_status_failed"}`,
    };
    setStatus("error");
    renderAdminShell();
  }
}

function scheduleAdminM3TrainingPoll() {
  if (adminState.m3TrainingPoll) {
    window.clearTimeout(adminState.m3TrainingPoll);
  }
  const poll = window.setTimeout(() => {
    adminState = { ...adminState, m3TrainingPoll: null };
    refreshAdminM3TrainingJob();
  }, 2500);
  adminState = { ...adminState, m3TrainingPoll: poll };
}

async function submitAdminReadingSearch(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const readingId = String(data.get("readingId") || "").trim();
  if (!readingId) return;
  adminState = { ...adminState, searchReadingId: readingId };
  await loadAdminReading(readingId);
}

async function openAdminHistoryReading(event) {
  const readingId = event.currentTarget.getAttribute("data-admin-open-reading") || "";
  if (!readingId) return;
  adminState = { ...adminState, searchReadingId: readingId };
  await loadAdminReading(readingId);
}

async function loadAdminReading(readingId) {
  adminState = { ...adminState, notice: "正在读取测算详情和运行追踪。" };
  setStatus("reading");
  renderAdminShell();
  const [view, trace] = await Promise.all([
    fetchJson(`/api/v30/readings/${encodeURIComponent(readingId)}/view?role=admin&locale=zh&client=admin`, {}, 10000).catch((error) => ({ error: error.message })),
    fetchJson(`/api/v30/admin/runs/${encodeURIComponent(readingId)}/trace`, {}, 10000).catch((error) => ({ error: error.message })),
  ]);
  adminState = {
    ...adminState,
    readingView: view.error ? null : view,
    trace: trace.error ? null : trace,
    notice: view.error || trace.error ? `读取完成，但存在缺失：${[view.error, trace.error].filter(Boolean).join("；")}` : "测算详情和运行追踪已读取。",
  };
  setStatus("ready");
  renderAdminShell();
}

async function submitAdminHistorySearch(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const actorId = String(data.get("actorId") || "").trim();
  const sessionId = String(data.get("sessionId") || "").trim();
  if (!actorId && !sessionId) return;
  adminState = { ...adminState, searchActorId: actorId, searchSessionId: sessionId, notice: "正在读取 admin history。" };
  setStatus("history");
  renderAdminShell();
  try {
    const params = new URLSearchParams({ actor_id: actorId, session_id: sessionId, role: "admin", locale: "zh", client: "admin", limit: "20" });
    const history = await fetchJson(`/api/v30/readings/history?${params.toString()}`, {}, 10000);
    adminState = { ...adminState, searchHistory: history, notice: "Admin history 已读取。" };
    setStatus("ready");
  } catch (error) {
    adminState = { ...adminState, notice: `历史读取失败：${error.message || "request_failed"}` };
    setStatus("error");
  }
  renderAdminShell();
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

function loadQuestionTurnHistory() {
  try {
    const raw = window.localStorage.getItem(QUESTION_TURN_HISTORY_KEY);
    const rows = raw ? JSON.parse(raw) : [];
    return Array.isArray(rows) ? rows.slice(-20) : [];
  } catch (error) {
    return [];
  }
}

function saveQuestionTurnHistory() {
  try {
    window.localStorage.setItem(QUESTION_TURN_HISTORY_KEY, JSON.stringify(localQuestionTurns.slice(-20)));
  } catch (error) {
    // In-memory history still works if localStorage is unavailable.
  }
}

function storeUiPrefs(nextPrefs) {
  productUiPrefs = { ...productUiPrefs, ...nextPrefs };
  window.localStorage.setItem(PRODUCT_UI_PREFS_KEY, JSON.stringify(productUiPrefs));
}

function renderGlobalChrome() {
  const client = detectClient();
  if (formState.client !== "admin" && formState.client !== client) {
    formState = { ...formState, client };
  }
  if (localeSwitchEl) {
    localeSwitchEl.value = formState.locale || "zh";
  }
  if (terminalStatusEl) {
    terminalStatusEl.textContent = terminalLabel(formState.client);
  }
}

async function handleLocaleSwitch(event) {
  const locale = event.currentTarget.value || "zh";
  if (locale !== "zh") {
    event.currentTarget.value = "zh";
    return;
  }
  storeUiPrefs({ locale });
  formState = { ...formState, locale };
  renderGlobalChrome();
  if (currentView) {
    setStatus("refreshing");
    await refreshView(formState.readingId);
  } else {
    renderShell();
  }
}

function storeProductSession(payload) {
  productSession = payload;
  window.localStorage.setItem(PRODUCT_SESSION_KEY, JSON.stringify(payload));
  const session = payload.session || {};
  const user = payload.user || {};
  formState = {
    ...formState,
    actorId: session.actor_id || formState.actorId,
    sessionId: session.session_id || formState.sessionId,
    role: user.role || formState.role,
    client: roleProfiles[user.role]?.client || formState.client,
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

async function loadProductProfiles() {
  const token = productSession?.session?.session_token || "";
  if (!token) {
    productNotice = "请先登录。";
    renderProfilesPage();
    return;
  }
  setStatus("profiles");
  try {
    productProfiles = await fetchJson(`/api/v30/profiles?session_token=${encodeURIComponent(token)}`);
    productNotice = productProfiles.count ? "档案已刷新。" : "暂无档案。";
    setStatus("ready");
  } catch (error) {
    productNotice = `档案读取失败：${error.message || "request_failed"}`;
    setStatus("error");
  }
  renderProfilesPage();
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
  };
  activeReadingStep = "input";
  productNotice = "";
  window.history.replaceState({}, "", "/v30/ui/?role=user&step=input");
  renderShell();
}

async function handleRoleChange(event) {
  const role = event.currentTarget.getAttribute("data-role") || "user";
  if (productSession?.user?.role) return;
  const profile = roleProfiles[role] || roleProfiles.user;
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
  const fixedRole = productSession?.user?.role || formState.role || "user";
  formState = {
    ...formState,
    actorId: productSession?.session?.actor_id || formState.actorId || "guest-demo",
    sessionId: productSession?.session?.session_id || formState.sessionId || `session-${Date.now()}`,
    role: fixedRole,
    profileName: String(data.get("profileName") || "当前命盘"),
    locale: String(data.get("locale") || formState.locale || "zh"),
    client: roleProfiles[fixedRole]?.client === "admin" ? "admin" : detectClient(),
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
  activeReadingStep = "chart";
  await refreshView(created.reading_id);
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
  currentInteractionState = currentView.interaction_state || currentInteractionState;
  formState = {
    ...formState,
    readingId,
  };
  setStatus("ready");
  renderReading();
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
  activeReadingStep = "chart";
  setStatus("opening");
  await refreshView(readingId);
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
    return;
  }
  const surface = currentView.reading_surface || {};
  const summary = surface.reading_summary || {};
  const domainCards = surface.domain_cards || [];
  const answer = currentView.answer_panel || {};
  const questions = currentView.questions || [];
  const options = surface.options || [];
  const timeContext = surface.time_context || {};
  const coreReading = surface.core_bazi_reading || {};
  const structureDynamics = surface.structure_dynamics || {};
  const basicAssertions = Array.isArray(surface.basic_assertions) ? surface.basic_assertions : [];
  const baziFeatures = Array.isArray(surface.bazi_features) ? surface.bazi_features : [];
  const baziPortraits = Array.isArray(surface.bazi_portraits) ? surface.bazi_portraits : [];
  const baziPaths = Array.isArray(surface.bazi_paths) ? surface.bazi_paths : [];
  const roleProfile = currentView.layout?.role_profile || {};
  target.innerHTML = renderReadingStepContent({
    surface,
    summary,
    domainCards,
    answer,
    questions,
    options,
    timeContext,
    coreReading,
    structureDynamics,
    basicAssertions,
    baziFeatures,
    baziPortraits,
    baziPaths,
    roleProfile,
  });
  target.querySelectorAll("[data-answer-question]").forEach((form) => {
    form.addEventListener("submit", submitAnswer);
  });
  target.querySelectorAll("[data-option]").forEach((button) => {
    button.addEventListener("click", submitOption);
  });
  target.querySelector("[data-clear-question-history]")?.addEventListener("click", clearQuestionHistory);
}

function renderReadingStepContent(context) {
  const {
    surface,
    summary,
    domainCards,
    answer,
    questions,
    options,
    timeContext,
    coreReading,
    structureDynamics,
    basicAssertions,
    baziFeatures,
    baziPortraits,
    baziPaths,
    roleProfile,
  } = context;
  if (activeReadingStep === "chart") {
    return `
      <section class="step-page chart-step">
        ${renderRoleSurface(roleProfile)}
        ${renderSummaryBand(summary, answer)}
        ${renderCoreBaziReading(coreReading)}
        ${renderSixPillarBand(timeContext, coreReading)}
        ${renderDiagnosticsPanel(currentView)}
      </section>
    `;
  }
  if (activeReadingStep === "reading") {
    return `
      <section class="step-page reading-step">
        ${renderSummaryBand(summary, answer)}
        ${renderBasicAssertions(basicAssertions)}
        ${renderStructureDynamics(structureDynamics)}
        ${renderProductLayerBand("八字特征", "从命盘证据抽出的可用特征", baziFeatures, renderBaziFeatureCard)}
        ${renderProductLayerBand("八字画像", "由 M3 画像系统投影的命主倾向", baziPortraits, renderBaziPortraitCard)}
        ${renderProductLayerBand("动态路径", "结构、领域与时运形成的判断路径", baziPaths, renderBaziPathCard)}
        ${domainCards.length ? `
          <section class="domain-band">
            ${domainCards.slice(0, 5).map(renderDomainCard).join("")}
          </section>
        ` : `<div class="history-empty">当前还没有领域解读，请先完成排盘。</div>`}
        ${renderAnswerPanel(answer)}
        ${options.length ? `
          <section class="option-band">
            <p class="eyebrow">快速选择</p>
            <div class="option-list">
              ${options.slice(0, 4).map(renderOption).join("")}
            </div>
          </section>
        ` : ""}
        ${renderDiagnosticsPanel(currentView)}
      </section>
    `;
  }
  if (activeReadingStep === "questions") {
    return `
      <section class="step-page question-step">
        ${renderSummaryBand(summary, answer)}
        ${renderAnswerPanel(answer)}
        ${interactionNotice ? `
          <section class="notice-band ${escapeHtml(interactionNotice.type)}">
            ${escapeHtml(interactionNotice.text)}
          </section>
        ` : ""}
        ${options.length ? `
          <section class="option-band">
            <p class="eyebrow">快速选择</p>
            <div class="option-list">
              ${options.slice(0, 4).map(renderOption).join("")}
            </div>
          </section>
        ` : ""}
        ${renderQuestionUxPanel(surface, questions)}
        ${renderDiagnosticsPanel(currentView)}
      </section>
    `;
  }
  return `
    <section class="step-page input-support-step">
      ${renderSummaryBand(summary, answer)}
      <div class="history-empty">出生资料在上方表单中修改。提交后会自动进入命盘步骤。</div>
    </section>
  `;
}

function renderSummaryBand(summary, answer) {
  const facts = [
    formState.profileName || "当前命盘",
    `${formState.targetYear} 流年`,
    localeLabel(formState.locale),
  ];
  return `
    <section class="summary-band">
      <div>
        <p class="eyebrow">测算摘要</p>
        <h2>${escapeHtml(summary.title || "八字测算已生成")}</h2>
        <p>${escapeHtml(summary.primary_message || "系统已生成基础测算，可按步骤查看命盘、解读和问答。")}</p>
      </div>
      <div class="facts">
        ${facts.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
      </div>
    </section>
  `;
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
      ${formState.role === "admin" ? `<small>${escapeHtml(structureBoundaryLabel(payload.boundary || ""))}</small>` : ""}
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
  const roleKey = roleProfile.role_key || formState.role;
  const facts = roleKey === "admin"
    ? ["管理视图", "可查看后台状态"]
    : roleKey === "practitioner"
      ? ["命理师视图", "结构路径与复核要点"]
      : ["用户测算", "展示命盘摘要、领域解读和连续问答"];
  return `
    <section class="role-surface-band ${escapeHtml(roleKey)}">
      <div>
        <p class="eyebrow">当前页面</p>
        <h2>${escapeHtml(roleProfile.label || roleProfiles[formState.role]?.label || "普通用户")}</h2>
        <p>${escapeHtml(roleProfiles[formState.role]?.helper || "")}</p>
      </div>
      <div class="facts">
        ${facts.map((row) => `<span>${escapeHtml(row)}</span>`).join("")}
      </div>
    </section>
  `;
}

function renderDiagnosticsPanel(view) {
  const diagnostics = view.diagnostics || {};
  if (!diagnostics.trace_id) return "";
  if (formState.role !== "admin" && formState.role !== "practitioner") return "";
  const activePolicies = diagnostics.active_policy_versions || {};
  const policyRows = Object.entries(activePolicies).slice(0, 4);
  const bazi = diagnostics.bazi_context || {};
  const ranked = diagnostics.ranked_decisions || {};
  if (formState.role === "practitioner") {
    return `
      <section class="diagnostic-band practitioner-review">
        <div class="section-head">
          <p class="eyebrow">命理师复核</p>
          <h2>结构、问答与隐藏线索</h2>
        </div>
        <div class="diagnostic-grid">
          <div>
            <span>推荐追问</span>
            <strong>${escapeHtml(diagnostics.recommendation_count ?? "-")}</strong>
          </div>
          <div>
            <span>隐藏线索</span>
            <strong>${escapeHtml(diagnostics.hidden_factor_probe_count ?? "-")}</strong>
          </div>
          <div>
            <span>旺衰</span>
            <strong>${escapeHtml(candidateLabel(ranked.strength?.primary_candidate || ""))}</strong>
          </div>
          <div>
            <span>用神</span>
            <strong>${escapeHtml(candidateLabel(ranked.useful_god?.primary_candidate || ""))}</strong>
          </div>
        </div>
      </section>
    `;
  }
  return `
    <section class="diagnostic-band">
      <div class="section-head">
        <p class="eyebrow">管理诊断</p>
        <h2>运行、策略与追踪</h2>
      </div>
      <div class="diagnostic-grid">
        <div>
          <span>Trace</span>
          <strong>${escapeHtml(diagnostics.trace_id)}</strong>
        </div>
        <div>
          <span>推荐数</span>
          <strong>${escapeHtml(diagnostics.recommendation_count ?? "-")}</strong>
        </div>
        <div>
          <span>校准线索探针</span>
          <strong>${escapeHtml(diagnostics.hidden_factor_probe_count ?? "-")}</strong>
        </div>
        <div>
          <span>结构上下文</span>
          <strong>${escapeHtml(bazi.version || "available")}</strong>
        </div>
      </div>
      ${policyRows.length ? `
        <div class="policy-list">
          ${policyRows.map(([key, value]) => `<span>${escapeHtml(key)}: ${escapeHtml(value)}</span>`).join("")}
        </div>
      ` : ""}
      ${ranked.version ? `<p class="time-note">${escapeHtml(ranked.version)}</p>` : ""}
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
  const text = answerTypewriter.active && answerTypewriter.key === key ? answerTypewriter.visibleText : answer.text;
  const typing = answerTypewriter.active && answerTypewriter.key === key && answerTypewriter.visibleText.length < answerTypewriter.fullText.length;
  const questionLabel = answerQuestionLabel(answer);
  return `
    <section id="answer-panel" class="answer-band ${typing ? "typing" : ""}">
      <p class="eyebrow">测算反馈</p>
      <h2>${questionLabel ? "本次问题" : "已根据你的选择生成回答"}</h2>
      ${questionLabel ? `<div class="answer-question-context">${escapeHtml(questionLabel)}</div>` : ""}
      <div class="answer-text">${formatMultilineText(text)}${typing ? `<span class="typing-cursor"></span>` : ""}</div>
    </section>
  `;
}

function answerQuestionLabel(answer) {
  const explicit = String(answer.question_label || answer.question || "").trim();
  if (explicit) return explicit;
  const questionId = String(answer.question_id || "").trim();
  const rows = [
    ...(Array.isArray(currentView?.questions) ? currentView.questions : []),
    currentView?.reading_surface?.next_question || {},
  ];
  const matched = rows.find((row) => row && row.question_id === questionId);
  if (matched) return matched.label || matched.question || matched.question_id || "";
  const last = localQuestionTurns.slice().reverse().find((turn) => !questionId || turn.question_id === questionId);
  return last?.question || "";
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

function renderQuestion(question, index) {
  const gain = question.expected_information_gain || {};
  const options = Array.isArray(question.options) ? question.options : [];
  return `
    <form class="question-row" data-answer-question="${escapeHtml(question.question_id)}" data-question-label="${escapeHtml(question.label || question.question_id)}">
      <div>
        <strong>${index + 1}. ${escapeHtml(question.label || question.question_id)}</strong>
        <p>${escapeHtml(question.topic_label || question.topic || "")} · ${escapeHtml(gain.primary_gain || question.question_value || "")}</p>
      </div>
      <p class="question-hint">点击后系统会直接回答，并推荐下一步。</p>
      ${options.length ? `
        <div class="question-options">
          ${options.slice(0, 3).map((option) => `
            <button type="submit" data-selected-option="${escapeHtml(option.option_id || option.value || "")}">
              ${escapeHtml(option.label || option.value || "")}
            </button>
          `).join("")}
        </div>
      ` : ""}
      <button type="submit">查看回答</button>
    </form>
  `;
}

function renderQuestionUxPanel(surface, questions) {
  const next = surface.next_question || questions[0] || {};
  const queue = questions.filter((row) => row.question_id !== next.question_id).slice(0, 3);
  const state = currentInteractionState || surface.interaction_state || {};
  const options = Array.isArray(next.options) ? next.options : [];
  const constraints = next.answer_constraints || {};
  return `
    <section class="question-band">
      <div class="section-head">
        <p class="eyebrow">智能问答与校准</p>
        <h2>围绕这张命盘继续追问</h2>
      </div>
      ${next.question_id ? `
        <form class="current-question-card" data-answer-question="${escapeHtml(next.question_id)}" data-question-label="${escapeHtml(next.label || next.question_id)}">
          <div>
            <span>建议先看</span>
            <strong>${escapeHtml(next.label || next.question_id)}</strong>
            <p>${escapeHtml(readableQuestionHint(next))}</p>
          </div>
          ${options.length ? `
            <div class="structured-options">
              ${options.slice(0, 5).map((option) => `
                <button type="submit" data-selected-option="${escapeHtml(option.option_id || option.value || "")}">
                  ${escapeHtml(option.label || option.value || "")}
                </button>
              `).join("")}
            </div>
          ` : ""}
          ${renderAnswerConstraintControls(constraints)}
          <label class="free-answer">补充回答
            <textarea name="answerText" rows="3" placeholder="可补充一句背景；关键年份、状态和强度请优先用上方选项"></textarea>
          </label>
          <button type="submit">继续解读</button>
        </form>
      ` : `<div class="history-empty">当前没有可提交的问题。</div>`}
      ${renderKnownSignalSummary(state)}
      ${renderLocalQuestionTurns()}
      ${queue.length ? `
        <div class="question-queue">
          <p class="eyebrow">也可以继续看</p>
          <div class="question-list">
            ${queue.map(renderQueueQuestion).join("")}
          </div>
        </div>
      ` : ""}
    </section>
  `;
}

function renderAnswerConstraintControls(constraints) {
  const type = String(constraints.constraint_type || "");
  if (type === "structured_hidden_factor") {
    const stateTags = Array.isArray(constraints.allowed_state_tags) ? constraints.allowed_state_tags : [];
    return `
      <fieldset class="constraint-panel" data-answer-constraints="${escapeHtml(type)}">
        <legend>选择命盘校准线索</legend>
        <div class="constraint-grid">
          <label>反复状态
            <select name="constraintRecurrence" data-required-constraint="recurrence">
              <option value="">请选择</option>
              ${renderConstraintOptions(constraints.allowed_recurrence)}
            </select>
          </label>
          <label>年份
            <input name="constraintYears" inputmode="numeric" placeholder="例如 2021, 2024">
          </label>
          <label>强度
            <select name="constraintIntensity">
              <option value="">不确定</option>
              ${renderConstraintOptions(constraints.allowed_intensity)}
            </select>
          </label>
          <label>把握度
            <select name="constraintConfidence">
              <option value="">不确定</option>
              ${renderConstraintOptions(constraints.allowed_confidence)}
            </select>
          </label>
          <label>关联领域
            <select name="constraintSelectedDomain">
              <option value="">不指定</option>
              ${renderConstraintOptions(constraints.allowed_domains || defaultDomainOptions())}
            </select>
          </label>
        </div>
        <div class="constraint-choice-grid" data-required-constraint="state_tags">
          ${stateTags.map((row) => `
            <label class="constraint-check">
              <input type="checkbox" name="constraintStateTags" value="${escapeHtml(row.value || row.key || "")}">
              <span>${escapeHtml(row.label || row.value || "")}</span>
            </label>
          `).join("")}
        </div>
      </fieldset>
    `;
  }
  if (type === "domain_followup") {
    return `
      <fieldset class="constraint-panel compact-constraint" data-answer-constraints="${escapeHtml(type)}">
        <legend>本次追问方向</legend>
        <label>关注领域
          <select name="constraintSelectedDomain">
            <option value="">按当前问题</option>
            ${renderConstraintOptions(constraints.allowed_domains || defaultDomainOptions())}
          </select>
        </label>
      </fieldset>
    `;
  }
  if (type === "timing_context_check") {
    return `
      <fieldset class="constraint-panel compact-constraint" data-answer-constraints="${escapeHtml(type)}">
        <legend>年份线索</legend>
        <label>相关年份
          <input name="constraintYears" inputmode="numeric" placeholder="例如 2020, 2023">
        </label>
      </fieldset>
    `;
  }
  return "";
}

function renderConstraintOptions(rows) {
  const options = Array.isArray(rows) ? rows : [];
  return options.map((row) => {
    const value = row.value || row.key || "";
    return `<option value="${escapeHtml(value)}">${escapeHtml(row.label || value)}</option>`;
  }).join("");
}

function defaultDomainOptions() {
  return [
    { value: "career", label: "事业" },
    { value: "wealth", label: "财务" },
    { value: "relationship", label: "关系" },
    { value: "health", label: "健康" },
    { value: "timing", label: "时运" },
    { value: "decision", label: "决策" },
  ];
}

function renderKnownSignalSummary(state) {
  const known = state.known_user_signals || {};
  const answered = Array.isArray(state.answered_question_ids) ? state.answered_question_ids : [];
  const selected = Array.isArray(state.selected_option_ids) ? state.selected_option_ids : [];
  const chips = [
    state.selected_domain ? `关注 ${domainLabel(state.selected_domain)}` : "",
    answered.length ? `已答 ${answered.length}` : "",
    selected.length ? `已选 ${selected.length}` : "",
    known.answered_question_count ? `线索 ${known.answered_question_count}` : "",
  ].filter(Boolean);
  if (!chips.length) return "";
  return `
    <div class="known-signal-strip">
      ${chips.map((chip) => `<span>${escapeHtml(chip)}</span>`).join("")}
    </div>
  `;
}

function renderLocalQuestionTurns() {
  if (!localQuestionTurns.length) return "";
  const rows = localQuestionTurns.slice(-8).reverse();
  return `
    <div class="turn-chain">
      <div class="turn-chain-head">
        <div>
          <p class="eyebrow">历史问答</p>
          <strong>${rows.length} 条最近记录</strong>
        </div>
        <button type="button" class="subtle-button" data-clear-question-history>清空</button>
      </div>
      ${rows.map((turn) => `
        <article>
          <span>${escapeHtml(turn.created_at || "")}</span>
          <strong>${escapeHtml(turn.question)}</strong>
          ${turn.user_reply ? `<p>补充：${escapeHtml(turn.user_reply)}</p>` : ""}
          <p>${escapeHtml(turn.answer || "已生成回答")}</p>
          ${renderTurnSignalSummary(turn)}
          ${turn.next ? `<em>下一问：${escapeHtml(turn.next)}</em>` : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function renderTurnSignalSummary(turn) {
  const absorbed = Array.isArray(turn.absorbed) ? turn.absorbed : [];
  const rejected = Array.isArray(turn.rejected) ? turn.rejected : [];
  const rows = [];
  if (absorbed.length) rows.push(`已吸收 ${absorbed.length} 条结构线索`);
  if (rejected.length) rows.push(`需重选 ${rejected.length} 条`);
  if (!rows.length) return "";
  return `<div class="turn-signal-summary">${rows.map((row) => `<span>${escapeHtml(row)}</span>`).join("")}</div>`;
}

function clearQuestionHistory() {
  localQuestionTurns = [];
  saveQuestionTurnHistory();
  renderReading();
}

function renderQueueQuestion(question, index) {
  return `
    <form class="question-row compact" data-answer-question="${escapeHtml(question.question_id)}" data-question-label="${escapeHtml(question.label || question.question_id)}">
      <div>
        <strong>${index + 1}. ${escapeHtml(question.label || question.question_id)}</strong>
        <p>${escapeHtml(readableQuestionHint(question))}</p>
      </div>
      <button type="submit">查看</button>
    </form>
  `;
}

function renderOption(option) {
  return `
    <button type="button" class="option-button" data-option="${escapeHtml(option.value || option.option_id)}">
      ${escapeHtml(option.label || option.value || "")}
    </button>
  `;
}

function readableQuestionHint(question) {
  const topic = domainLabel(question.topic_label || question.topic || question.domain || "");
  const gain = String(question.question_value || question.expected_information_gain?.primary_gain || "").trim();
  const readableGain = gain
    .replace(/_/g, " ")
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
    overview: "总览",
  };
  return labels[key] || String(value || "");
}

async function submitAnswer(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const questionId = form.getAttribute("data-answer-question");
  const questionLabel = form.getAttribute("data-question-label") || questionId || "";
  const selectedOption = event.submitter?.getAttribute("data-selected-option") || form.getAttribute("data-selected-option") || "";
  const data = new FormData(form);
  const freeText = String(data.get("answerText") || "").trim();
  const structuredPayload = collectStructuredPayload(form, selectedOption);
  const validationError = validateAnswerConstraintForm(form, structuredPayload);
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
  form.querySelectorAll("button").forEach((button) => {
    button.disabled = true;
  });
  if (event.submitter) event.submitter.textContent = "提交中";
  interactionNotice = { type: "info", text: "正在提交回答并刷新测算。" };
  setStatus("updating");
  currentView = {
    ...currentView,
    answer_panel: {
      text: "正在生成回答，请稍等。",
      question_id: questionId,
      question_label: questionLabel,
      user_reply: freeText || selectedOption || "",
      source: "pending",
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
    currentView = payload.view;
    const responseText = String(currentView.answer_panel?.text || "");
    currentView.answer_panel = {
      ...(currentView.answer_panel || {}),
      question_id: questionId,
      question_label: questionLabel,
      user_reply: freeText || selectedOption || "",
    };
    prepareAnswerTypewriter(currentView.answer_panel || {});
    requestLlmAnswerEnhancementIfDeferred(questionId, questionLabel, freeText || selectedOption || "");
    currentInteractionState = payload.interaction_state || currentView.interaction_state || currentInteractionState;
    localQuestionTurns.push({
      question_id: questionId,
      question: questionLabel,
      user_reply: freeText || selectedOption || "",
      answer: responseText,
      next: payload.next_question_id || "",
      absorbed: payload.interaction_brain_result?.absorbed_signals || [],
      rejected: payload.interaction_brain_result?.rejected_signals || [],
      created_at: new Date().toLocaleString("zh-CN", { hour12: false }),
    });
    localQuestionTurns = localQuestionTurns.slice(-20);
    saveQuestionTurnHistory();
    interactionNotice = { type: "success", text: "已收到回答，测算已刷新。" };
    setStatus("ready");
  } catch (error) {
    interactionNotice = { type: "warn", text: `提交失败：${error.message || "请稍后重试"}` };
    setStatus("error");
  }
  renderReading();
  scrollToAnswer();
}

async function requestLlmAnswerEnhancementIfDeferred(questionId, questionLabel, userReply) {
  const metadata = currentView?.answer_panel?.llm_metadata || {};
  if (!formState.readingId || metadata.status !== "deferred") return;
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
    if (!res.ok || !payload.accepted || !payload.view) return;
    currentView = payload.view;
    const responseText = String(currentView.answer_panel?.text || "");
    currentView.answer_panel = {
      ...(currentView.answer_panel || {}),
      question_id: questionId,
      question_label: questionLabel,
      user_reply: userReply,
    };
    prepareAnswerTypewriter(currentView.answer_panel || {});
    if (localQuestionTurns.length) {
      localQuestionTurns[localQuestionTurns.length - 1] = {
        ...localQuestionTurns[localQuestionTurns.length - 1],
        answer: responseText,
        enhanced: true,
      };
      saveQuestionTurnHistory();
    }
    renderReading();
    scrollToAnswer();
  } catch (error) {
    // The rule/RBD answer is already visible; LLM enhancement is optional.
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

function validateAnswerConstraintForm(form, payload) {
  const type = form.querySelector("[data-answer-constraints]")?.getAttribute("data-answer-constraints") || "";
  if (type !== "structured_hidden_factor") return "";
  if (!Array.isArray(payload.state_tags) || !payload.state_tags.length) {
    return "请选择至少一个反复状态，再继续解读。";
  }
  if (!payload.recurrence) {
    return "请选择这个状态是单次、反复还是持续。";
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

async function submitOption(event) {
  const value = event.currentTarget.getAttribute("data-option") || "";
  const nextQuestion = currentView?.reading_surface?.next_question || currentView?.questions?.[0] || {};
  if (!value || !nextQuestion.question_id) return;
  const syntheticForm = document.createElement("form");
  syntheticForm.setAttribute("data-answer-question", nextQuestion.question_id);
  syntheticForm.setAttribute("data-question-label", `用户选择关注方向：${value}`);
  syntheticForm.setAttribute("data-selected-option", `domain:${value}`);
  await submitAnswer({ preventDefault() {}, currentTarget: syntheticForm });
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

localeSwitchEl?.addEventListener("change", handleLocaleSwitch);
window.addEventListener("resize", renderGlobalChrome);

renderShell();
