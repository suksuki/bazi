import type { AuthMode, ProductProfile } from "./api";


export type ProfileEditorMode = "none" | "create" | "edit";

export interface ProfileManagerView {
  accountName: string;
  profiles: ProductProfile[];
  activeProfileId: string;
  editorMode: ProfileEditorMode;
  editingProfileId: string;
  busy: boolean;
  error: string;
  canReturnToWorkspace: boolean;
}


export function renderAuthSurface(input: {
  mode: AuthMode;
  busy: boolean;
  error: string;
}): string {
  const registering = input.mode === "register";
  return `<main class="account-entry">
    <section class="account-scene" aria-label="DeepBeing 生命世界">
      <img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence">
      <div><p>DeepBeing</p><h1>进入同一个生命世界</h1><span>档案、命盘、阿布与研究镜头，都从这里继续。</span></div>
    </section>
    <section class="account-tool" aria-labelledby="authHeading">
      <div class="account-tool-inner">
        <p class="section-kicker">${registering ? "建立账户" : "欢迎回来"}</p>
        <h2 id="authHeading">${registering ? "第一次见，怎么称呼你？" : "继续你的命理档案"}</h2>
        <div class="account-mode" role="tablist" aria-label="账户操作">
          <button type="button" data-auth-mode="login" aria-selected="${!registering}" class="${!registering ? "active" : ""}">登录</button>
          <button type="button" data-auth-mode="register" aria-selected="${registering}" class="${registering ? "active" : ""}">注册</button>
        </div>
        <form class="account-form" data-auth-form>
          ${registering ? `<label><span>称呼</span><input name="display_name" autocomplete="name" value="DeepBazi 用户" required></label>` : ""}
          <label><span>邮箱</span><input type="email" name="email" autocomplete="email" placeholder="name@example.com" required></label>
          <label><span>密码</span><input type="password" name="password" autocomplete="${registering ? "new-password" : "current-password"}" minlength="8" required></label>
          ${registering ? `<label><span>使用方式</span><select name="role"><option value="member">看自己的命局</option><option value="practitioner">命理师实战</option><option value="research_master">命理研究</option></select></label>` : ""}
          <p class="account-error" role="alert">${escapeHtml(input.error)}</p>
          <button class="primary-command account-submit" type="submit"${input.busy ? " disabled" : ""}>${input.busy ? "正在连接" : registering ? "注册并继续" : "登录并继续"}</button>
        </form>
      </div>
    </section>
  </main>`;
}


export function renderProfileManager(view: ProfileManagerView): string {
  const editing = view.profiles.find((item) => item.profile_id === view.editingProfileId);
  return `<div class="profile-manager-shell">
    <header class="profile-manager-header">
      <a href="/experience" aria-label="DeepBeing"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence"></a>
      <div><span>${escapeHtml(view.accountName)}</span><button type="button" data-account-command="logout">退出</button></div>
    </header>
    <main class="profile-manager">
      <section class="profile-archive" aria-labelledby="profileArchiveTitle">
        <div class="profile-manager-title">
          <p class="section-kicker">命理档案</p>
          <h1 id="profileArchiveTitle">选择档案，就是进入命局</h1>
          <span>不再经过“开始测算”。四柱立即出现，整盘认知在后台按需补充。</span>
        </div>
        <div class="profile-actions">
          ${view.canReturnToWorkspace ? '<button type="button" class="text-command" data-account-command="return-workspace">返回命局</button>' : ""}
          <button type="button" class="primary-command compact" data-account-command="create-profile">新建档案</button>
        </div>
        <div class="profile-list">
          ${view.profiles.length ? view.profiles.map((profile) => renderProfileRow(profile, view.activeProfileId)).join("") : `<div class="profile-empty"><strong>还没有出生档案</strong><span>建立第一份档案后，会直接进入你的命局。</span><button type="button" class="primary-command" data-account-command="create-profile">建立档案</button></div>`}
        </div>
      </section>
      <section class="profile-editor" aria-live="polite">
        ${view.editorMode === "none"
          ? `<div class="profile-editor-idle"><img src="/assets/abu/v12-actor-pass/dream-standard-cycle/web/abu_dream_standard_cycle_v1.webp" alt="阿布"><p>阿布在这里</p><h2>选一份档案继续，或建立新的命局。</h2></div>`
          : renderProfileForm(view.editorMode, editing, view.busy, view.error)}
      </section>
    </main>
  </div>`;
}


function renderProfileRow(profile: ProductProfile, activeProfileId: string): string {
  const active = profile.profile_id === activeProfileId;
  const gender = profile.gender === "female" ? "坤造" : profile.gender === "male" ? "乾造" : "命造未定";
  const calendar = profile.calendar_type === "lunar" ? "农历" : "公历";
  return `<article class="profile-row${active ? " active" : ""}">
    <button type="button" class="profile-row-main" data-profile-use="${escapeAttr(profile.profile_id)}">
      <span><strong>${escapeHtml(profile.display_name || "未命名档案")}</strong>${active ? "<em>当前</em>" : ""}</span>
      <b>${escapeHtml(profile.pillars.filter(Boolean).join(" · ") || "四柱进入后自动排出")}</b>
      <small>${calendar} ${escapeHtml(profile.birth_date)} ${escapeHtml(profile.birth_time)} · ${gender}</small>
    </button>
    <div class="profile-row-tools">
      <button type="button" data-profile-edit="${escapeAttr(profile.profile_id)}" aria-label="编辑${escapeAttr(profile.display_name)}" title="编辑">编辑</button>
      <button type="button" data-profile-delete="${escapeAttr(profile.profile_id)}" aria-label="删除${escapeAttr(profile.display_name)}" title="删除">删除</button>
    </div>
  </article>`;
}


function renderProfileForm(
  mode: Exclude<ProfileEditorMode, "none">,
  profile: ProductProfile | undefined,
  busy: boolean,
  error: string,
): string {
  const approximate = profile?.warnings.includes("birth_time_approximate") || false;
  return `<form class="profile-form" data-profile-form data-profile-id="${escapeAttr(profile?.profile_id || "")}" data-editor-mode="${mode}">
    <header><p>${mode === "edit" ? "修正出生资料" : "建立命理档案"}</p><h2>${mode === "edit" ? `编辑${escapeHtml(profile?.display_name || "档案")}` : "四柱确认后直接进入命局"}</h2></header>
    <div class="profile-form-grid">
      <label><span>档案名称</span><input name="name" value="${escapeAttr(profile?.display_name || "我的命盘")}" required></label>
      <label><span>命造</span><select name="gender"><option value="male"${profile?.gender === "male" || !profile ? " selected" : ""}>乾造</option><option value="female"${profile?.gender === "female" ? " selected" : ""}>坤造</option><option value="unknown"${profile?.gender === "unknown" ? " selected" : ""}>暂未确定</option></select></label>
      <label><span>历法</span><select name="calendar_type"><option value="solar"${profile?.calendar_type !== "lunar" ? " selected" : ""}>公历</option><option value="lunar"${profile?.calendar_type === "lunar" ? " selected" : ""}>农历</option></select></label>
      <label><span>出生日期</span><input type="date" name="birth_date" value="${escapeAttr(profile?.birth_date || "1990-01-01")}" required></label>
      <label><span>出生时间</span><input type="time" name="birth_time" value="${escapeAttr(profile?.birth_time || "12:00")}" required></label>
      <label><span>时间把握</span><select name="time_precision"><option value="exact"${!approximate ? " selected" : ""}>准确</option><option value="approximate"${approximate ? " selected" : ""}>大约</option></select></label>
      <label><span>出生地点</span><input name="birth_location" value="${escapeAttr(profile?.birth_location || "首尔")}" required></label>
      <label><span>时区</span><select name="timezone">${["Asia/Seoul", "Asia/Shanghai", "Asia/Taipei", "Asia/Hong_Kong"].map((timezone) => `<option value="${timezone}"${(profile?.timezone || "Asia/Seoul") === timezone ? " selected" : ""}>${timezone}</option>`).join("")}</select></label>
      <label class="profile-checkbox"><input type="checkbox" name="lunar_leap_month"${profile?.lunar_leap_month ? " checked" : ""}><span>农历闰月</span></label>
    </div>
    <p class="profile-form-note">修改出生资料会建立新的命盘版本；旧认知保留为历史，不会继续套用。</p>
    <p class="account-error" role="alert">${escapeHtml(error)}</p>
    <footer><button type="button" class="text-command" data-account-command="cancel-profile">取消</button><button type="submit" class="primary-command"${busy ? " disabled" : ""}>${busy ? "正在保存" : mode === "edit" ? "保存并进入" : "建立并进入"}</button></footer>
  </form>`;
}


function escapeHtml(value: unknown): string {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character] || character);
}


function escapeAttr(value: unknown): string {
  return escapeHtml(value).replace(/`/g, "&#96;");
}
