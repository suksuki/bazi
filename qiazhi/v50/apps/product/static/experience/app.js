// apps/product/experience_shell/src/api.ts
async function requestJson(url, init) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...init?.headers || {} },
    ...init
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(String(payload.detail || `request_failed_${response.status}`));
  }
  return response.json();
}
function authenticate(input) {
  const payload = input.mode === "register" ? {
    email: input.email,
    password: input.password,
    display_name: input.displayName || "DeepBazi \u7528\u6237",
    role: input.role || "member"
  } : { email: input.email, password: input.password };
  return requestJson(`/api/v50/product/auth/${input.mode}`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
function logout() {
  return requestJson("/api/v50/product/auth/logout", { method: "POST", body: "{}" });
}
async function loadProfiles() {
  const payload = await requestJson("/api/v50/product/profiles");
  return payload.profiles;
}
async function saveProfile(birthInput, profileId = "") {
  const payload = await requestJson(
    profileId ? `/api/v50/product/profiles/${encodeURIComponent(profileId)}` : "/api/v50/product/profiles",
    {
      method: profileId ? "PUT" : "POST",
      body: JSON.stringify({ birth_input: birthInput })
    }
  );
  return payload.profile;
}
function deleteProfile(profileId) {
  return requestJson(`/api/v50/product/profiles/${encodeURIComponent(profileId)}`, {
    method: "DELETE"
  });
}
function loadWorkspaceBootstrap(input = {}) {
  return requestJson("/api/v50/experience/workspace/bootstrap", {
    method: "POST",
    body: JSON.stringify({
      case_id: input.caseId || "",
      profile_id: input.profileId || ""
    })
  });
}
function startMissingBaseline(caseId) {
  return requestJson(`/api/v50/experience/workspace/cases/${encodeURIComponent(caseId)}/baseline`, {
    method: "POST",
    body: "{}"
  });
}
function loadCognitiveJob(jobId) {
  return requestJson(`/api/v50/experience/workspace/jobs/${encodeURIComponent(jobId)}`);
}
function loadReadOnlyCanvas(caseId) {
  return requestJson(`/api/v50/experience/cases/${encodeURIComponent(caseId)}/canvas`);
}
async function loadCanvasContext(caseId, stage, selectedObjectRef, layer) {
  const params = new URLSearchParams({ stage, selected: selectedObjectRef, layer });
  const payload = await requestJson(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/canvas/context?${params.toString()}`
  );
  return payload.context;
}
async function loadNarration(caseId) {
  const payload = await requestJson(`/api/v50/narration/cases/${encodeURIComponent(caseId)}/baseline`);
  return { manifest: payload.manifest, speechAssets: payload.speech_assets };
}
async function prepareNarrationSegment(caseId, segmentId) {
  const payload = await requestJson(
    `/api/v50/narration/cases/${encodeURIComponent(caseId)}/baseline/segments/${encodeURIComponent(segmentId)}`,
    { method: "POST" }
  );
  return payload.speech_asset;
}

// apps/product/experience_shell/src/account_components.ts
function renderAuthSurface(input) {
  const registering = input.mode === "register";
  return `<main class="account-entry">
    <section class="account-scene" aria-label="DeepBeing \u751F\u547D\u4E16\u754C">
      <img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence">
      <div><p>DeepBeing</p><h1>\u8FDB\u5165\u540C\u4E00\u4E2A\u751F\u547D\u4E16\u754C</h1><span>\u6863\u6848\u3001\u547D\u76D8\u3001\u963F\u5E03\u4E0E\u7814\u7A76\u955C\u5934\uFF0C\u90FD\u4ECE\u8FD9\u91CC\u7EE7\u7EED\u3002</span></div>
    </section>
    <section class="account-tool" aria-labelledby="authHeading">
      <div class="account-tool-inner">
        <p class="section-kicker">${registering ? "\u5EFA\u7ACB\u8D26\u6237" : "\u6B22\u8FCE\u56DE\u6765"}</p>
        <h2 id="authHeading">${registering ? "\u7B2C\u4E00\u6B21\u89C1\uFF0C\u600E\u4E48\u79F0\u547C\u4F60\uFF1F" : "\u7EE7\u7EED\u4F60\u7684\u547D\u7406\u6863\u6848"}</h2>
        <div class="account-mode" role="tablist" aria-label="\u8D26\u6237\u64CD\u4F5C">
          <button type="button" data-auth-mode="login" aria-selected="${!registering}" class="${!registering ? "active" : ""}">\u767B\u5F55</button>
          <button type="button" data-auth-mode="register" aria-selected="${registering}" class="${registering ? "active" : ""}">\u6CE8\u518C</button>
        </div>
        <form class="account-form" data-auth-form>
          ${registering ? `<label><span>\u79F0\u547C</span><input name="display_name" autocomplete="name" value="DeepBazi \u7528\u6237" required></label>` : ""}
          <label><span>\u90AE\u7BB1</span><input type="email" name="email" autocomplete="email" placeholder="name@example.com" required></label>
          <label><span>\u5BC6\u7801</span><input type="password" name="password" autocomplete="${registering ? "new-password" : "current-password"}" minlength="8" required></label>
          ${registering ? `<label><span>\u4F7F\u7528\u65B9\u5F0F</span><select name="role"><option value="member">\u770B\u81EA\u5DF1\u7684\u547D\u5C40</option><option value="practitioner">\u547D\u7406\u5E08\u5B9E\u6218</option><option value="research_master">\u547D\u7406\u7814\u7A76</option></select></label>` : ""}
          <p class="account-error" role="alert">${escapeHtml(input.error)}</p>
          <button class="primary-command account-submit" type="submit"${input.busy ? " disabled" : ""}>${input.busy ? "\u6B63\u5728\u8FDE\u63A5" : registering ? "\u6CE8\u518C\u5E76\u7EE7\u7EED" : "\u767B\u5F55\u5E76\u7EE7\u7EED"}</button>
        </form>
      </div>
    </section>
  </main>`;
}
function renderProfileManager(view) {
  const editing = view.profiles.find((item) => item.profile_id === view.editingProfileId);
  return `<div class="profile-manager-shell">
    <header class="profile-manager-header">
      <a href="/experience" aria-label="DeepBeing"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence"></a>
      <div><span>${escapeHtml(view.accountName)}</span><button type="button" data-account-command="logout">\u9000\u51FA</button></div>
    </header>
    <main class="profile-manager">
      <section class="profile-archive" aria-labelledby="profileArchiveTitle">
        <div class="profile-manager-title">
          <p class="section-kicker">\u547D\u7406\u6863\u6848</p>
          <h1 id="profileArchiveTitle">\u9009\u62E9\u6863\u6848\uFF0C\u5C31\u662F\u8FDB\u5165\u547D\u5C40</h1>
          <span>\u4E0D\u518D\u7ECF\u8FC7\u201C\u5F00\u59CB\u6D4B\u7B97\u201D\u3002\u56DB\u67F1\u7ACB\u5373\u51FA\u73B0\uFF0C\u6574\u76D8\u8BA4\u77E5\u5728\u540E\u53F0\u6309\u9700\u8865\u5145\u3002</span>
        </div>
        <div class="profile-actions">
          ${view.canReturnToWorkspace ? '<button type="button" class="text-command" data-account-command="return-workspace">\u8FD4\u56DE\u547D\u5C40</button>' : ""}
          <button type="button" class="primary-command compact" data-account-command="create-profile">\u65B0\u5EFA\u6863\u6848</button>
        </div>
        <div class="profile-list">
          ${view.profiles.length ? view.profiles.map((profile) => renderProfileRow(profile, view.activeProfileId)).join("") : `<div class="profile-empty"><strong>\u8FD8\u6CA1\u6709\u51FA\u751F\u6863\u6848</strong><span>\u5EFA\u7ACB\u7B2C\u4E00\u4EFD\u6863\u6848\u540E\uFF0C\u4F1A\u76F4\u63A5\u8FDB\u5165\u4F60\u7684\u547D\u5C40\u3002</span><button type="button" class="primary-command" data-account-command="create-profile">\u5EFA\u7ACB\u6863\u6848</button></div>`}
        </div>
      </section>
      <section class="profile-editor" aria-live="polite">
        ${view.editorMode === "none" ? `<div class="profile-editor-idle"><img src="/assets/abu/v12-actor-pass/quiet-sit-reaction/web/abu_quiet_sit_reaction_v1.webp" alt="\u963F\u5E03"><p>\u963F\u5E03\u5728\u8FD9\u91CC</p><h2>\u9009\u4E00\u4EFD\u6863\u6848\u7EE7\u7EED\uFF0C\u6216\u5EFA\u7ACB\u65B0\u7684\u547D\u5C40\u3002</h2></div>` : renderProfileForm(view.editorMode, editing, view.busy, view.error)}
      </section>
    </main>
  </div>`;
}
function renderProfileRow(profile, activeProfileId2) {
  const active = profile.profile_id === activeProfileId2;
  const gender = profile.gender === "female" ? "\u5764\u9020" : profile.gender === "male" ? "\u4E7E\u9020" : "\u547D\u9020\u672A\u5B9A";
  const calendar = profile.calendar_type === "lunar" ? "\u519C\u5386" : "\u516C\u5386";
  return `<article class="profile-row${active ? " active" : ""}">
    <button type="button" class="profile-row-main" data-profile-use="${escapeAttr(profile.profile_id)}">
      <span><strong>${escapeHtml(profile.display_name || "\u672A\u547D\u540D\u6863\u6848")}</strong>${active ? "<em>\u5F53\u524D</em>" : ""}</span>
      <b>${escapeHtml(profile.pillars.filter(Boolean).join(" \xB7 ") || "\u56DB\u67F1\u8FDB\u5165\u540E\u81EA\u52A8\u6392\u51FA")}</b>
      <small>${calendar} ${escapeHtml(profile.birth_date)} ${escapeHtml(profile.birth_time)} \xB7 ${gender}</small>
    </button>
    <div class="profile-row-tools">
      <button type="button" data-profile-edit="${escapeAttr(profile.profile_id)}" aria-label="\u7F16\u8F91${escapeAttr(profile.display_name)}" title="\u7F16\u8F91">\u7F16\u8F91</button>
      <button type="button" data-profile-delete="${escapeAttr(profile.profile_id)}" aria-label="\u5220\u9664${escapeAttr(profile.display_name)}" title="\u5220\u9664">\u5220\u9664</button>
    </div>
  </article>`;
}
function renderProfileForm(mode, profile, busy, error) {
  const approximate = profile?.warnings.includes("birth_time_approximate") || false;
  return `<form class="profile-form" data-profile-form data-profile-id="${escapeAttr(profile?.profile_id || "")}" data-editor-mode="${mode}">
    <header><p>${mode === "edit" ? "\u4FEE\u6B63\u51FA\u751F\u8D44\u6599" : "\u5EFA\u7ACB\u547D\u7406\u6863\u6848"}</p><h2>${mode === "edit" ? `\u7F16\u8F91${escapeHtml(profile?.display_name || "\u6863\u6848")}` : "\u56DB\u67F1\u786E\u8BA4\u540E\u76F4\u63A5\u8FDB\u5165\u547D\u5C40"}</h2></header>
    <div class="profile-form-grid">
      <label><span>\u6863\u6848\u540D\u79F0</span><input name="name" value="${escapeAttr(profile?.display_name || "\u6211\u7684\u547D\u76D8")}" required></label>
      <label><span>\u547D\u9020</span><select name="gender"><option value="male"${profile?.gender === "male" || !profile ? " selected" : ""}>\u4E7E\u9020</option><option value="female"${profile?.gender === "female" ? " selected" : ""}>\u5764\u9020</option><option value="unknown"${profile?.gender === "unknown" ? " selected" : ""}>\u6682\u672A\u786E\u5B9A</option></select></label>
      <label><span>\u5386\u6CD5</span><select name="calendar_type"><option value="solar"${profile?.calendar_type !== "lunar" ? " selected" : ""}>\u516C\u5386</option><option value="lunar"${profile?.calendar_type === "lunar" ? " selected" : ""}>\u519C\u5386</option></select></label>
      <label><span>\u51FA\u751F\u65E5\u671F</span><input type="date" name="birth_date" value="${escapeAttr(profile?.birth_date || "1990-01-01")}" required></label>
      <label><span>\u51FA\u751F\u65F6\u95F4</span><input type="time" name="birth_time" value="${escapeAttr(profile?.birth_time || "12:00")}" required></label>
      <label><span>\u65F6\u95F4\u628A\u63E1</span><select name="time_precision"><option value="exact"${!approximate ? " selected" : ""}>\u51C6\u786E</option><option value="approximate"${approximate ? " selected" : ""}>\u5927\u7EA6</option></select></label>
      <label><span>\u51FA\u751F\u5730\u70B9</span><input name="birth_location" value="${escapeAttr(profile?.birth_location || "\u9996\u5C14")}" required></label>
      <label><span>\u65F6\u533A</span><select name="timezone">${["Asia/Seoul", "Asia/Shanghai", "Asia/Taipei", "Asia/Hong_Kong"].map((timezone) => `<option value="${timezone}"${(profile?.timezone || "Asia/Seoul") === timezone ? " selected" : ""}>${timezone}</option>`).join("")}</select></label>
      <label class="profile-checkbox"><input type="checkbox" name="lunar_leap_month"${profile?.lunar_leap_month ? " checked" : ""}><span>\u519C\u5386\u95F0\u6708</span></label>
    </div>
    <p class="profile-form-note">\u4FEE\u6539\u51FA\u751F\u8D44\u6599\u4F1A\u5EFA\u7ACB\u65B0\u7684\u547D\u76D8\u7248\u672C\uFF1B\u65E7\u8BA4\u77E5\u4FDD\u7559\u4E3A\u5386\u53F2\uFF0C\u4E0D\u4F1A\u7EE7\u7EED\u5957\u7528\u3002</p>
    <p class="account-error" role="alert">${escapeHtml(error)}</p>
    <footer><button type="button" class="text-command" data-account-command="cancel-profile">\u53D6\u6D88</button><button type="submit" class="primary-command"${busy ? " disabled" : ""}>${busy ? "\u6B63\u5728\u4FDD\u5B58" : mode === "edit" ? "\u4FDD\u5B58\u5E76\u8FDB\u5165" : "\u5EFA\u7ACB\u5E76\u8FDB\u5165"}</button></footer>
  </form>`;
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character] || character);
}
function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

// apps/product/experience_shell/src/account_interactions.ts
function bindAccountInteractions(root2, handlers) {
  root2.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.addEventListener("click", () => handlers.setAuthMode(button.dataset.authMode || "login"));
  });
  root2.querySelector("[data-auth-form]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    handlers.submitAuth(event.currentTarget);
  });
  root2.querySelectorAll("[data-account-command]").forEach((button) => {
    button.addEventListener("click", () => handlers.command(button.dataset.accountCommand || ""));
  });
  root2.querySelectorAll("[data-profile-use]").forEach((button) => {
    button.addEventListener("click", () => handlers.useProfile(button.dataset.profileUse || ""));
  });
  root2.querySelectorAll("[data-profile-edit]").forEach((button) => {
    button.addEventListener("click", () => handlers.editProfile(button.dataset.profileEdit || ""));
  });
  root2.querySelectorAll("[data-profile-delete]").forEach((button) => {
    button.addEventListener("click", () => handlers.deleteProfile(button.dataset.profileDelete || ""));
  });
  root2.querySelector("[data-profile-form]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    handlers.submitProfile(event.currentTarget);
  });
}

// apps/product/experience_shell/src/components.ts
var elementLabel = {
  wood: "\u6728",
  fire: "\u706B",
  earth: "\u571F",
  metal: "\u91D1",
  water: "\u6C34"
};
var polarityLabel = { yin: "\u9634", yang: "\u9633" };
function renderExperience(view) {
  const claim = view.envelope.approved_claims[0];
  const steps = view.envelope.approved_reasoning_steps;
  const fullThesis = claim?.approved_meaning || "\u56DB\u67F1\u5DF2\u7ECF\u5C31\u7EEA\uFF0C\u963F\u5E03\u6B63\u5728\u7406\u89E3\u6574\u76D8\u3002";
  const thesis = firstSentence(fullThesis);
  const pathSummary = steps[steps.length - 1]?.conclusion || "\u5148\u4ECE\u786E\u5B9A\u6027\u7684\u56DB\u67F1\u5F00\u59CB\u3002";
  const condition = claim?.conditions[0] || "\u5F53\u524D\u8FD8\u6CA1\u6709\u8DB3\u591F\u4F9D\u636E\u5199\u4E0B\u6210\u7ACB\u6761\u4EF6\u3002";
  const uncertainty = view.envelope.uncertainty.reasons[0] || "\u5F53\u524D\u6CA1\u6709\u989D\u5916\u672A\u51B3\u9879\u3002";
  return `<div class="deepbeing-shell" data-product-area-current="${escapeAttr2(view.ui.productArea)}">
    ${renderProductSidebar(view)}
    <div class="deepbeing-stage">
      ${renderMobileHeader(view)}
      <main class="product-main">
        ${view.ui.productArea === "world" ? renderLifeWorld(view, thesis, fullThesis, pathSummary, condition, uncertainty) : ""}
        ${view.ui.productArea === "workbench" ? renderWorkbench(view) : ""}
        ${view.ui.productArea === "lab" ? renderMingliLab(view) : ""}
      </main>
    </div>
    ${renderMobileNavigation(view)}
    ${renderAbuDock(view)}
  </div>`;
}
function renderWorkbench(view) {
  const claim = view.envelope.approved_claims[0];
  const hasFormalCognition = Boolean(claim);
  const steps = view.envelope.approved_reasoning_steps;
  const condition = claim?.conditions[0] || "\u5F53\u524D\u8FD8\u6CA1\u6709\u8DB3\u591F\u4F9D\u636E\u5199\u4E0B\u6210\u7ACB\u6761\u4EF6\u3002";
  const uncertainty = view.envelope.uncertainty.reasons[0] || "\u5F53\u524D\u6CA1\u6709\u989D\u5916\u672A\u51B3\u9879\u3002";
  const pathSummary = steps[steps.length - 1]?.conclusion || "\u5148\u4ECE\u786E\u5B9A\u6027\u7684\u56DB\u67F1\u5F00\u59CB\u3002";
  const fullThesis = claim?.approved_meaning || "\u56DB\u67F1\u5DF2\u7ECF\u5C31\u7EEA\uFF0C\u963F\u5E03\u6B63\u5728\u7406\u89E3\u6574\u76D8\u3002";
  const thesis = firstSentence(fullThesis);
  return `
    ${renderWorkspaceNavigation(view)}

    <div class="workbench-surface" data-workspace-current-surface="${escapeAttr2(view.ui.workspaceSurface)}">
      ${view.ui.workspaceSurface === "overview" ? `<section class="opening-band" id="baseline-summary" data-anchor="baseline-summary">
        <div class="opening-copy">
          <p class="section-kicker">\u770B\u89C1\u547D\u5C40 \xB7 \u5F53\u524D\u57FA\u7EBF</p>
          <h1>${escapeHtml2(thesis)}</h1>
          <p class="opening-lede">${escapeHtml2(view.cognition.message)}</p>
          <div class="opening-actions">
            <button class="primary-command" type="button" data-command="listen">
              ${view.ui.narrationStatus === "playing" ? "\u6682\u505C\u963F\u5E03" : "\u542C\u963F\u5E03\u8BB2"}
            </button>
            <button class="text-command" type="button" data-command="focus-pillars">\u5148\u770B\u56DB\u67F1</button>
          </div>
        </div>
        ${hasFormalCognition ? `<div class="scan-strip" aria-label="\u6574\u76D8\u5FEB\u901F\u6458\u8981">
          ${summaryItem("\u4E3B\u8DEF\u5F84", pathSummary, "baseline-work-path")}
          ${summaryItem("\u6210\u7ACB\u6761\u4EF6", condition, "baseline-condition")}
          ${summaryItem("\u6700\u5927\u672A\u51B3", uncertainty, "baseline-uncertainty")}
        </div>` : `<div class="cognition-progress" data-cognition-status="${escapeAttr2(view.cognition.status)}"><i></i><span><strong>\u547D\u76D8\u5148\u5230\uFF0C\u8BA4\u77E5\u968F\u540E</strong><small>\u56DB\u67F1\u5DF2\u786E\u8BA4\uFF1B\u963F\u5E03\u53EA\u4F1A\u8865\u5145\u4F9D\u636E\u5145\u5206\u7684\u90E8\u5206\u3002</small></span></div>`}
      </section>

      ${renderCollapsibleSection({
    id: "pillars",
    anchor: "four-pillars",
    tone: "facts",
    eyebrow: "\u547D\u76D8\u4E8B\u5B9E",
    title: "\u56DB\u67F1\u662F\u8FD9\u4EFD\u547D\u5C40\u7684\u5E95\u56FE",
    summary: view.envelope.allowed_chart_facts.map((item) => item.stem + item.branch).join(" \xB7 "),
    expanded: view.ui.expandedSections.pillars,
    body: renderPillars(view.envelope, view.ui.selectedAnchor)
  })}

      ${hasFormalCognition ? `${renderCollapsibleSection({
    id: "path",
    anchor: "baseline-work-path",
    tone: "cognition",
    eyebrow: "\u6574\u76D8\u8BA4\u77E5",
    title: "\u8FD9\u5F20\u76D8\u5982\u4F55\u8FD0\u884C",
    summary: pathSummary,
    expanded: view.ui.expandedSections.path,
    body: renderPath(fullThesis, steps, view.ui.selectedAnchor)
  })}

      ${renderCollapsibleSection({
    id: "boundaries",
    anchor: "baseline-condition",
    tone: "boundaries",
    eyebrow: "\u6761\u4EF6\u4E0E\u672A\u51B3",
    title: "\u5224\u65AD\u6210\u7ACB\uFF0C\u4E5F\u8981\u77E5\u9053\u8FB9\u754C\u5728\u54EA\u91CC",
    summary: condition,
    expanded: view.ui.expandedSections.boundaries,
    body: renderBoundaries(claim, view.envelope, view.ui.selectedAnchor)
  })}` : ""}
      ` : ""}

      ${view.ui.workspaceSurface === "onecanvas" ? `${renderCollapsibleSection({
    id: "canvas",
    anchor: "temporal-canvas",
    tone: "canvas",
    eyebrow: "\u65F6\u95F4\u7ED3\u6784",
    title: "\u770B\u7ED3\u6784\u600E\u6837\u8FDB\u5165\u5F53\u524D\u65F6\u95F4",
    summary: view.canvas ? `${view.canvas.source.luck_pillar}\u5927\u8FD0 \xB7 ${view.canvas.source.analysis_year || "\u5F53\u524D"}${view.canvas.source.annual_pillar}\u6D41\u5E74` : "\u56DB\u67F1\u9AA8\u67B6\u5DF2\u7ECF\u5C31\u7EEA",
    expanded: view.ui.expandedSections.canvas ?? true,
    body: view.canvas ? renderReadOnlyCanvas(
      view.canvas,
      view.ui,
      view.canvasContext,
      view.cognition.status === "preparing"
    ) : renderDeterministicCanvasSkeleton(view.envelope, view.cognition)
  })}` : ""}

      ${view.ui.workspaceSurface === "theater" ? renderNarrationWorkspace(view, thesis) : ""}

      <section class="closing-band">
        <p>\u77E5\u547D\uFF0C\u800C\u540E\u77E5\u5DF1</p>
        <span>\u53EA\u8BF4\u5DF2\u7ECF\u6709\u5145\u5206\u4F9D\u636E\u7684\u90E8\u5206\uFF0C\u4E5F\u4FDD\u7559\u4ECD\u9700\u9A8C\u8BC1\u7684\u5730\u65B9\u3002</span>
      </section>
    </div>
  `;
}
function renderWorkspaceNavigation(view) {
  const labels = {
    overview: "\u547D\u5C40\u6982\u89C8",
    onecanvas: "\u7ED3\u6784",
    theater: "\u963F\u5E03\u8BB2\u89E3"
  };
  const detail = view.ui.workspaceSurface === "onecanvas" ? "\u539F\u5C40\u3001\u5927\u8FD0\u4E0E\u6D41\u5E74\u6CBF\u540C\u4E00\u7EC4\u8BED\u4E49\u5BF9\u8C61\u5C55\u5F00" : view.ui.workspaceSurface === "theater" ? "\u6587\u5B57\u5148\u5230\uFF0C\u963F\u5E03\u6CBF\u540C\u4E00\u4EFD\u6B63\u5F0F\u8BA4\u77E5\u8BB2\u89E3" : "\u5148\u770B\u6574\u76D8\u91CD\u5FC3\uFF0C\u518D\u6309\u9700\u5C55\u5F00\u7ED3\u6784\u4E0E\u8FB9\u754C";
  return `<header class="workbench-header">
    <div><p>\u547D\u76D8\u5DE5\u4F5C\u53F0 \xB7 ${escapeHtml2(activeCaseName(view))}</p><h1>${labels[view.ui.workspaceSurface]}</h1><span>${detail}</span></div>
    <nav class="workspace-navigation" aria-label="\u547D\u76D8\u5DE5\u4F5C\u53F0\u89C6\u56FE">
      <div class="workspace-tabs">${view.availableSurfaces.map((surface) => `<button type="button" data-workspace-surface="${surface}" aria-pressed="${surface === view.ui.workspaceSurface}" class="${surface === view.ui.workspaceSurface ? "active" : ""}">${labels[surface]}</button>`).join("")}</div>
    </nav>
  </header>`;
}
function renderLifeWorld(view, thesis, fullThesis, pathSummary, condition, uncertainty) {
  const pillars = view.envelope.allowed_chart_facts.filter((item) => item.fact_type === "pillar").map((item) => item.stem + item.branch).join(" \xB7 ");
  return `<div class="life-world">
    <section class="world-hero" data-anchor="baseline-summary">
      <div class="world-copy">
        <p class="section-kicker">\u6211\u7684\u751F\u547D\u4E16\u754C \xB7 ${escapeHtml2(activeCaseName(view))}</p>
        <h1>${escapeHtml2(thesis)}</h1>
        <p>${escapeHtml2(firstSentence(pathSummary))}</p>
        <div class="world-actions">
          <button class="primary-command" type="button" data-command="listen">${view.ui.narrationStatus === "playing" ? "\u6682\u505C\u963F\u5E03" : "\u542C\u963F\u5E03\u8BB2"}</button>
          <button class="text-command" type="button" data-product-area="workbench">\u6253\u5F00\u547D\u76D8</button>
          ${view.dreamStatus?.enabled && view.dreamStatus.available ? `<button class="dream-entry-command" type="button" data-command="enter-dream">${view.dreamStatus.resumable ? "\u7EE7\u7EED\u4E0A\u6B21\u7684\u68A6" : "\u968F\u963F\u5E03\u5165\u68A6"}</button>` : ""}
        </div>
        ${renderDreamConsent(view)}
      </div>
      <div class="life-tree" aria-label="\u547D\u3001\u4E8B\u3001\u4EBA\u7684\u751F\u547D\u8109\u7EDC">
        <span class="tree-line tree-line-left" aria-hidden="true"></span>
        <span class="tree-line tree-line-right" aria-hidden="true"></span>
        <button type="button" class="tree-node tree-nature" data-product-area="workbench">
          <small>\u547D</small><strong>${escapeHtml2(pillars || "\u56DB\u67F1\u5F85\u786E\u8BA4")}</strong><span>\u5148\u5929\u5E95\u56FE</span>
        </button>
        <button type="button" class="tree-node tree-events" data-select-anchor="baseline-work-path" data-message="${escapeAttr2(pathSummary)}">
          <small>\u4E8B</small><strong>${escapeHtml2(firstSentence(pathSummary))}</strong><span>${escapeHtml2(view.workspace?.state.selected_period || "\u5F53\u524D\u9636\u6BB5")}</span>
        </button>
        <button type="button" class="tree-node tree-growth" data-command="toggle-abu">
          <small>\u4EBA</small><strong>${escapeHtml2(firstSentence(condition))}</strong><span>\u5F53\u524D\u884C\u52A8\u6761\u4EF6</span>
        </button>
        <div class="tree-trunk" aria-hidden="true"><i></i><i></i><i></i></div>
        <img src="/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp" alt="\u963F\u5E03\u5728\u751F\u547D\u6811\u65C1\u7B49\u5F85">
      </div>
    </section>
    <section class="world-ledger" aria-label="\u751F\u547D\u8BB0\u5F55">
      <header><p>\u751F\u547D\u8BB0\u5F55</p><h2>\u547D\u662F\u8D77\u70B9\uFF0C\u73B0\u5B9E\u8BA9\u7406\u89E3\u7EE7\u7EED\u751F\u957F</h2></header>
      <div class="world-ledger-flow">
        <button type="button" data-product-area="workbench"><span>\u547D\u76D8\u57FA\u7EBF</span><strong>${escapeHtml2(pillars || "\u7B49\u5F85\u5EFA\u6863")}</strong><small>${escapeHtml2(view.envelope.source.life_case_version || "\u547D\u76D8\u4E8B\u5B9E")}</small></button>
        <button type="button" data-select-anchor="baseline-work-path" data-message="${escapeAttr2(fullThesis)}"><span>\u5F53\u524D\u8BA4\u77E5</span><strong>${escapeHtml2(thesis)}</strong><small>\u6765\u81EA\u6B63\u5F0F LifeCase</small></button>
        <button type="button" data-command="toggle-abu"><span>\u7EE7\u7EED\u89C2\u5BDF</span><strong>${escapeHtml2(firstSentence(uncertainty))}</strong><small>\u4E0E\u963F\u5E03\u4E00\u8D77\u9A8C\u8BC1</small></button>
      </div>
    </section>
  </div>`;
}
function renderDreamConsent(view) {
  const status = view.dreamStatus;
  if (!status?.enabled || status.consent_state === "case_unavailable") return "";
  if (status.consent_state === "active") {
    return `<div class="dream-consent-control is-active">
      <div><strong>\u5F53\u524D\u6863\u6848\u5DF2\u533F\u540D\u6388\u6743\u5165\u68A6</strong><span>\u4EC5\u7528\u4E8E\u672C\u5730\u5C01\u95ED\u4E09\u6811\u4F53\u9A8C\uFF0C\u53EF\u968F\u65F6\u64A4\u56DE\u3002</span></div>
      <button type="button" data-command="withdraw-dream-consent">\u64A4\u56DE\u6388\u6743</button>
    </div>`;
  }
  const changed = status.consent_state === "source_changed";
  return `<div class="dream-consent-control">
    <div><strong>${changed ? "\u547D\u76D8\u7248\u672C\u5DF2\u53D8\u5316\uFF0C\u8BF7\u91CD\u65B0\u786E\u8BA4" : "\u8BA9\u8FD9\u68F5\u751F\u547D\u6811\u8FDB\u5165\u5C01\u95ED\u68A6\u5883"}</strong><span>\u533F\u540D\u5C55\u793A\u786E\u5B9A\u6027\u547D\u76D8\u4E0E\u53EA\u8BFB\u6811\u8C61\uFF1B\u4E0D\u516C\u5F00\u8EAB\u4EFD\uFF0C\u4E0D\u9ED8\u8BA4\u7528\u4E8E\u8BAD\u7EC3\uFF0C\u6388\u6743\u540E\u4ECD\u53EF\u64A4\u56DE\u3002</span></div>
    <button type="button" data-command="grant-dream-consent">${changed ? "\u91CD\u65B0\u6388\u6743" : "\u6388\u6743\u5F53\u524D\u6863\u6848"}</button>
  </div>`;
}
function renderMingliLab(view) {
  if (!view.canvas) return `<section class="lab-empty"><p>Mingli Lab</p><h1>\u56DB\u67F1\u5DF2\u7ECF\u5C31\u7EEA</h1><span>\u7814\u7A76\u955C\u5934\u53EA\u5728\u6B63\u5F0F\u5173\u7CFB\u6295\u5F71\u53EF\u7528\u65F6\u6309\u9700\u5C55\u5F00\uFF0C\u4E0D\u4F1A\u4E3A Lab \u53E6\u7B97\u4E00\u5957\u547D\u76D8\u3002</span></section>`;
  const stage = view.canvas.stages[view.ui.canvasStage];
  const potentialCount = stage.spec.relations.filter((item) => item.relation_state === "potential").length;
  const sourceCount = new Set(stage.spec.relations.flatMap((item) => item.trace.source_refs)).size;
  const hiddenCount = stage.spec.nodes.filter((item) => item.node_type.includes("hidden")).length;
  return `<div class="mingli-lab">
    <header class="lab-header">
      <div><p>Mingli Lab \xB7 ${escapeHtml2(activeCaseName(view))}</p><h1>\u540C\u4E00\u547D\u5C40\u7684\u7814\u7A76\u955C\u5934</h1><span>\u5019\u9009\u5173\u7CFB\u4E0E\u8BC1\u636E\u7559\u5728\u7814\u7A76\u5C42\uFF1B\u6B63\u5F0F Case \u4E0D\u5728\u8FD9\u91CC\u88AB\u6539\u5199\u3002</span></div>
      <code>${escapeHtml2((view.workspace?.state.scene_source_hash || view.envelope.source.source_hash).slice(0, 18))}</code>
    </header>
    <div class="lab-evidence-rail" aria-label="\u5F53\u524D\u7814\u7A76\u8303\u56F4">
      <span><small>\u6F5C\u5728\u5173\u7CFB</small><strong>${potentialCount}</strong></span>
      <span><small>\u85CF\u5E72\u8282\u70B9</small><strong>${hiddenCount}</strong></span>
      <span><small>\u6765\u6E90\u5F15\u7528</small><strong>${sourceCount}</strong></span>
      <span><small>\u6B63\u5F0F\u5199\u5165</small><strong>\u5173\u95ED</strong></span>
    </div>
    <section class="lab-canvas"><p class="lab-lens-label">\u547D\u7406\u5E08 Lens \xB7 \u6F5C\u5728\u5173\u7CFB\u573A</p>${renderReadOnlyCanvas(view.canvas, view.ui, view.canvasContext, view.cognition.status === "preparing")}</section>
  </div>`;
}
function renderProductSidebar(view) {
  return `<aside class="product-sidebar">
    <a class="brand" href="/experience" aria-label="DeepBeing \u9996\u9875"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence"><span>DeepBeing</span></a>
    ${renderProductNavigation(view, "sidebar")}
    <div class="sidebar-context">${renderProfileSelector(view.cases, view.activeProfileId)}<small>${escapeHtml2(view.envelope.source.life_case_version || "\u547D\u76D8\u4E8B\u5B9E")}</small></div>
    <div class="sidebar-account"><span>${escapeHtml2(view.accountName)}</span><button type="button" data-command="manage-profiles">\u6863\u6848</button></div>
  </aside>`;
}
function renderMobileHeader(view) {
  const labels = { world: "\u6211\u7684\u751F\u547D\u4E16\u754C", workbench: "\u547D\u76D8\u5DE5\u4F5C\u53F0", lab: "Mingli Lab" };
  return `<header class="mobile-header"><a href="/experience"><img src="/assets/deepbazi_symbol.png" alt="DeepBazi"></a><strong>${labels[view.ui.productArea]}</strong><div class="mobile-header-actions">${renderProfileSelector(view.cases, view.activeProfileId)}<button type="button" data-command="manage-profiles" aria-label="\u7BA1\u7406\u6863\u6848" title="\u7BA1\u7406\u6863\u6848">\u6863</button></div></header>`;
}
function renderMobileNavigation(view) {
  return `<nav class="mobile-product-navigation" aria-label="DeepBeing \u4E3B\u8981\u533A\u57DF">${renderProductNavigation(view, "mobile")}</nav>`;
}
function renderProductNavigation(view, placement) {
  const items = [
    { area: "world", index: "01", label: "\u6211\u7684\u751F\u547D\u4E16\u754C", detail: "\u751F\u547D\u6811\u4E0E\u73B0\u5B9E\u8BB0\u5F55" },
    { area: "workbench", index: "02", label: "\u547D\u76D8\u5DE5\u4F5C\u53F0", detail: "\u6982\u89C8\u3001\u7ED3\u6784\u4E0E\u963F\u5E03" },
    { area: "lab", index: "03", label: "Mingli Lab", detail: "\u5019\u9009\u3001\u53CD\u4F8B\u4E0E\u8BC1\u636E" }
  ];
  return `<div class="product-navigation is-${placement}">${items.filter((item) => view.availableAreas.includes(item.area)).map((item) => `<button type="button" data-product-area="${item.area}" aria-current="${view.ui.productArea === item.area ? "page" : "false"}" class="${view.ui.productArea === item.area ? "active" : ""}"><i>${item.index}</i><span><strong>${item.label}</strong><small>${item.detail}</small></span></button>`).join("")}</div>`;
}
function activeCaseName(view) {
  return view.cases.find((item) => item.profile_id === view.activeProfileId)?.display_name || "\u5F53\u524D\u547D\u76D8";
}
function renderNarrationWorkspace(view, thesis) {
  const segments = view.narrationManifest?.segments || [];
  return `<section class="narration-workspace" data-anchor="abu-narration">
    <header><p>\u963F\u5E03\u8BB2\u89E3</p><h1>${escapeHtml2(thesis)}</h1><span>${segments.length ? "\u4ECE\u6574\u76D8\u91CD\u5FC3\u5F00\u59CB\uFF0C\u6CBF\u56DB\u67F1\u3001\u8DEF\u5F84\u3001\u6761\u4EF6\u4E0E\u672A\u51B3\u9010\u6BB5\u5C55\u5F00\u3002" : "\u6587\u5B57\u5DF2\u7ECF\u53EF\u8BFB\uFF1B\u70B9\u64AD\u653E\u540E\u624D\u51C6\u5907\u58F0\u97F3\uFF0C\u4E0D\u963B\u585E\u5F53\u524D\u9875\u9762\u3002"}</span></header>
    <div class="narration-workspace-actions">
      <button class="primary-command" type="button" data-command="listen">${view.ui.narrationStatus === "playing" ? "\u6682\u505C" : "\u4ECE\u5934\u542C"}</button>
      ${view.ui.narrationStatus !== "idle" ? '<button class="text-command" type="button" data-command="stop">\u505C\u6B62</button>' : ""}
    </div>
    ${segments.length ? `<ol>${segments.map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><small>${String(index + 1).padStart(2, "0")}</small><span><strong>${escapeHtml2(item.title)}</strong><em>${escapeHtml2(item.text)}</em></span><b aria-hidden="true">\u25B6</b></button></li>`).join("")}</ol>` : `<div class="narration-pending"><i></i><p>${escapeHtml2(view.cognition.message)}</p></div>`}
  </section>`;
}
function renderDeterministicCanvasSkeleton(envelope2, cognition2) {
  const pillars = envelope2.allowed_chart_facts.filter((item) => item.fact_type === "pillar");
  return `<div class="deterministic-canvas-skeleton">
    <header><span>\u786E\u5B9A\u6027\u547D\u76D8</span><strong>\u56DB\u67F1\u5148\u663E\u793A\uFF0C\u5173\u7CFB\u6309\u6B63\u5F0F\u6765\u6E90\u9010\u6B65\u8FDB\u5165</strong></header>
    <div class="skeleton-pillar-rail">${pillars.map((pillar) => `<article>
      <small>${escapeHtml2(pillar.pillar_label)}</small>
      <b class="element-${escapeAttr2(pillar.stem_element)}" data-polarity="${escapeAttr2(pillar.stem_polarity)}">${escapeHtml2(pillar.stem)}</b>
      <i></i>
      <b class="element-${escapeAttr2(pillar.branch_element)}" data-polarity="${escapeAttr2(pillar.branch_polarity)}">${escapeHtml2(pillar.branch)}</b>
      <em>${escapeHtml2(pillar.visible_ten_god || "\u547D\u76D8\u4E8B\u5B9E")}</em>
    </article>`).join("")}</div>
    <p><i></i>${escapeHtml2(cognition2.message)}</p>
  </div>`;
}
function renderReadOnlyCanvas(canvas2, ui2, context, pathTaskRunning) {
  const stage = canvas2.stages[ui2.canvasStage];
  const allowedVisibility = canvas2.renderer_policy.available_visibility_layers;
  const requestedVisibility = ui2.canvasVisibilityLayer;
  const visibility = allowedVisibility.includes(requestedVisibility) ? requestedVisibility : canvas2.renderer_policy.default_visibility_layer;
  const selected = ui2.selectedCanvasObject || stage.scene_slots[0]?.slot_ref || "";
  const displayLayers = stage.layers.map((item) => {
    const relationRefs = visibility === "lab_audit" ? item.relation_refs : item.formal_relation_refs;
    const pathRefs = visibility === "lab_audit" ? item.path_refs : item.formal_path_refs;
    const focusedRelationRefs = visibility === "focus" ? focusRelationRefs(stage.spec, relationRefs, selected) : relationRefs;
    const focusedPathRefs = visibility === "focus" ? focusPathRefs(stage.spec, pathRefs, selected) : pathRefs;
    return {
      ...item,
      relation_refs: focusedRelationRefs,
      path_refs: focusedPathRefs,
      count: focusedRelationRefs.length,
      available: focusedRelationRefs.length > 0 || focusedPathRefs.length > 0
    };
  });
  const layer = displayLayers.find((item) => item.layer_id === ui2.canvasLayer) || displayLayers.find((item) => item.layer_id === stage.default_layer_id) || displayLayers[0];
  const visibleRelationRefs = new Set(layer?.relation_refs || []);
  const visiblePathRefs = new Set(layer?.path_refs || []);
  const activeRelations = stage.spec.relations.filter((item) => visibleRelationRefs.has(item.relation_ref));
  const activePaths = stage.spec.paths.filter((item) => visiblePathRefs.has(item.path_ref));
  const range = canvas2.source.luck_year_range.length === 2 ? `${canvas2.source.luck_year_range[0]}\u2013${canvas2.source.luck_year_range[1]}` : "\u5F53\u524D\u9636\u6BB5";
  return `<div class="temporal-viewer" data-canvas-stage-root="${escapeAttr2(ui2.canvasStage)}">
    <div class="temporal-toolbar">
      <div class="stage-switch" role="tablist" aria-label="\u67E5\u770B\u65F6\u95F4\u9636\u6BB5">
        ${canvas2.stage_order.map((item, index) => {
    const projection = canvas2.stages[item];
    return `<button type="button" role="tab" data-canvas-stage="${item}" aria-selected="${item === ui2.canvasStage}" class="${item === ui2.canvasStage ? "active" : ""}">
            <small>0${index + 1}</small><span>${escapeHtml2(projection.title)}</span>
          </button>`;
  }).join("")}
      </div>
      <div class="temporal-status">
        <span>${escapeHtml2(ui2.canvasStage === "natal" ? "\u539F\u5C40\u57FA\u7EBF" : ui2.canvasStage === "luck" ? range : `${canvas2.source.analysis_year || "\u5F53\u524D"}\u5E74`)}</span>
        <strong>${escapeHtml2(stage.summary)}</strong>
      </div>
    </div>

    <div class="canvas-lens-controls">
      <div class="layer-switch" role="tablist" aria-label="\u547D\u5C40\u89C2\u5BDF\u955C\u5934">
        ${displayLayers.map((item) => `<button type="button" role="tab" data-canvas-layer="${escapeAttr2(item.layer_id)}" aria-selected="${item.layer_id === layer?.layer_id}" class="${item.layer_id === layer?.layer_id ? "active" : ""}"${item.available || item.layer_id === "overview" || item.layer_id === "work_path" ? "" : " disabled"}>
          <span>${escapeHtml2(item.label)}</span>${item.count > 0 ? `<small>${item.count}</small>` : ""}
        </button>`).join("")}
      </div>
      <div class="visibility-switch" role="tablist" aria-label="\u5173\u7CFB\u62AB\u9732\u5C42">
        ${allowedVisibility.map((item) => `<button type="button" role="tab" data-canvas-visibility="${item}" aria-selected="${item === visibility}" class="${item === visibility ? "active" : ""}">${visibilityLabel(item)}</button>`).join("")}
      </div>
    </div>

    <div class="canvas-board" data-layer="${escapeAttr2(layer?.layer_id || "")}" data-visibility="${escapeAttr2(visibility)}">
      <div class="six-pillar-scroll">
        ${renderCanonicalCanvasScene(
    stage.scene_slots,
    stage.spec.nodes,
    activeRelations,
    activePaths,
    selected,
    visibility === "lab_audit"
  )}
      </div>
      <p class="layer-caption"><strong>${escapeHtml2(layer?.label || "\u5F53\u524D\u56FE\u5C42")}</strong>${escapeHtml2(layer?.description || "\u5F53\u524D\u6CA1\u6709\u53EF\u663E\u793A\u7684\u5173\u7CFB\u3002")}</p>
    </div>

    <div class="canvas-reading-grid">
      ${renderCanvasChanges(stage.change_groups, selected, ui2.canvasStage)}
      ${renderCanvasInspector(stage.spec, selected, context, ui2.canvasContextStatus)}
    </div>

    <div class="canvas-boundary ${canvas2.path_availability.status === "available" ? "is-ready" : "is-limited"}">
      <span>${canvas2.path_availability.status === "available" ? "\u6B63\u5F0F\u8DEF\u5F84\u5DF2\u786E\u8BA4" : pathTaskRunning ? "\u6B63\u5F0F\u4E3B\u8DEF\u5F84\u6B63\u5728\u5F62\u6210" : "\u5F53\u524D\u6682\u65E0\u5DF2\u786E\u8BA4\u4E3B\u8DEF\u5F84"}</span>
      <p>${escapeHtml2(
    canvas2.path_availability.status !== "available" && pathTaskRunning ? "\u540E\u53F0\u6B63\u5728\u5F62\u6210\u6700\u5C0F\u6574\u76D8\u4E3B\u7EBF\uFF0C\u5DF2\u7ECF\u786E\u8BA4\u7684\u7ED3\u6784\u4F1A\u81EA\u52A8\u51FA\u73B0\u3002" : canvas2.path_availability.message
  )}</p>
      ${canvas2.path_availability.disclosure_level === "audit" && canvas2.path_availability.diagnostic ? `<small>${escapeHtml2(pathDiagnosticLabel(canvas2.path_availability.diagnostic.rejection_reason))}</small>` : ""}
      ${visibility === "lab_audit" && canvas2.path_availability.diagnostic ? `<code>${escapeHtml2(canvas2.path_availability.diagnostic.rejection_reason)}</code>` : ""}
    </div>
  </div>`;
}
function renderCanonicalCanvasScene(slots, nodes, relations, paths, selected, showHiddenStems) {
  const nodesByRef = new Map(nodes.map((item) => [item.node_ref, item]));
  const anchors = canvasAnchorRegistry(slots, nodes);
  const pathRelationRefs = new Set(paths.flatMap((item) => item.relation_refs));
  const requiredNodeRefs = /* @__PURE__ */ new Set([
    ...relations.flatMap((item) => [
      item.from_node_ref,
      item.to_node_ref,
      ...item.participant_node_refs
    ]),
    ...paths.flatMap((item) => item.node_refs)
  ]);
  const relationMarkup = relations.flatMap((relation, index) => {
    const source = anchors.get(relation.from_node_ref);
    const target = anchors.get(relation.to_node_ref);
    if (!source || !target) return [];
    const route = routeCanvasRelation(source, target, index);
    const classes = [
      "canvas-relation",
      `state-${relation.semantic_state}`,
      pathRelationRefs.has(relation.relation_ref) ? "is-work-path" : "",
      selected === relation.relation_ref ? "is-selected" : ""
    ].filter(Boolean).join(" ");
    return [`<g class="${classes}">
      <path d="${route.d}" marker-end="url(#canvas-arrow)" data-canvas-object="${escapeAttr2(relation.relation_ref)}"></path>
      <text x="${route.labelX}" y="${route.labelY}" text-anchor="middle" tabindex="0" role="button" data-canvas-object="${escapeAttr2(relation.relation_ref)}" aria-label="${escapeAttr2(relation.label)}">${escapeHtml2(shortRelationLabel(relation))}</text>
    </g>`];
  }).join("");
  const pathMarkup = paths.map((path, pathIndex) => renderCanvasPath(path, anchors, selected, pathIndex)).join("");
  const nodeMarkup = slots.map((slot) => renderCanvasSceneSlot(
    slot,
    nodesByRef,
    anchors,
    selected,
    showHiddenStems,
    requiredNodeRefs
  )).join("");
  return `<svg class="canonical-canvas-scene" viewBox="0 0 1320 640" preserveAspectRatio="xMidYMid meet" aria-label="\u516D\u67F1\u540C\u4E00\u547D\u5C40\u573A\u666F">
    <defs>
      <marker id="canvas-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker>
      <marker id="canvas-path-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z"></path></marker>
    </defs>
    <g class="canvas-scene-tracks" aria-hidden="true"><line x1="44" y1="185" x2="1276" y2="185"></line><line x1="44" y1="390" x2="1276" y2="390"></line><text x="46" y="171">\u5929\u5E72</text><text x="46" y="376">\u5730\u652F</text></g>
    <g class="canvas-scene-relations">${relationMarkup}</g>
    <g class="canvas-scene-paths">${pathMarkup}</g>
    <g class="canvas-scene-nodes">${nodeMarkup}</g>
    ${!relationMarkup && !pathMarkup ? `<g class="canvas-scene-empty"><text x="660" y="292" text-anchor="middle">\u6B64\u955C\u5934\u6CA1\u6709\u5DF2\u62AB\u9732\u5173\u7CFB</text><text x="660" y="315" text-anchor="middle">\u9875\u9762\u4E0D\u4F1A\u4E3A\u4E86\u586B\u6EE1\u753B\u9762\u800C\u8865\u7EBF</text></g>` : ""}
  </svg>`;
}
function canvasAnchorRegistry(slots, nodes) {
  const anchors = /* @__PURE__ */ new Map();
  slots.forEach((slot, index) => {
    const x = 110 + index * 220;
    if (slot.stem_node_ref) anchors.set(slot.stem_node_ref, { x, y: 185, level: "stem", slotIndex: index });
    if (slot.branch_node_ref) anchors.set(slot.branch_node_ref, { x, y: 390, level: "branch", slotIndex: index });
    const hiddenNodes = orderedHiddenStemNodes(slot, nodes);
    const offsets = hiddenNodes.length === 1 ? [0] : hiddenNodes.length === 2 ? [-30, 30] : [-44, 0, 44];
    hiddenNodes.forEach((node, hiddenIndex) => {
      anchors.set(node.node_ref, {
        x: x + (offsets[hiddenIndex] ?? (hiddenIndex - 1) * 44),
        y: 515,
        level: "hidden",
        slotIndex: index
      });
    });
  });
  return anchors;
}
function orderedHiddenStemNodes(slot, nodes) {
  return nodes.filter((item) => item.node_type === "hidden_stem" && item.semantic_slot_ref === slot.slot_ref).sort((left, right) => {
    const leftIndex = slot.hidden_stems.indexOf(left.label);
    const rightIndex = slot.hidden_stems.indexOf(right.label);
    if (leftIndex !== rightIndex) return leftIndex - rightIndex;
    return left.node_ref.localeCompare(right.node_ref);
  });
}
function renderCanvasSceneSlot(slot, nodesByRef, anchors, selected, showHiddenStems, requiredNodeRefs) {
  const x = 110 + slot.position_index * 220;
  const temporal = slot.slot_type === "luck" || slot.slot_type === "year";
  const active = slot.state === "active";
  const stemNode = nodesByRef.get(slot.stem_node_ref);
  const branchNode = nodesByRef.get(slot.branch_node_ref);
  const slotAction = active ? ` tabindex="0" role="button" data-canvas-object="${escapeAttr2(slot.slot_ref)}"` : "";
  return `<g class="canvas-scene-slot${temporal ? " is-temporal" : ""} state-${slot.state}" transform="translate(${x} 0)">
    <g class="canvas-slot-label${selected === slot.slot_ref ? " is-selected" : ""}"${slotAction}>
      <text x="0" y="70" text-anchor="middle">${escapeHtml2(slot.label)}</text>
      <text class="canvas-slot-state" x="0" y="91" text-anchor="middle">${slot.state === "active" ? slot.immutable ? "\u539F\u5C40" : "\u65F6\u95F4\u8FDB\u5165" : slot.state === "inactive" ? "\u5C1A\u672A\u8FDB\u5165" : "\u672A\u8F7D\u5165"}</text>
    </g>
    <line class="canvas-column-guide" x1="0" y1="117" x2="0" y2="548"></line>
    ${renderCanvasSceneNode(slot, stemNode, anchors.get(slot.stem_node_ref), selected, "stem")}
    ${renderCanvasSceneNode(slot, branchNode, anchors.get(slot.branch_node_ref), selected, "branch")}
    ${active ? renderCanvasHiddenStemNodes(
    slot,
    [...nodesByRef.values()],
    anchors,
    selected,
    showHiddenStems,
    requiredNodeRefs
  ) : ""}
  </g>`;
}
function renderCanvasHiddenStemNodes(slot, nodes, anchors, selected, showAll, requiredNodeRefs) {
  const hiddenNodes = orderedHiddenStemNodes(slot, nodes).filter((item) => showAll || requiredNodeRefs.has(item.node_ref));
  if (!hiddenNodes.length) return "";
  const slotX = 110 + slot.position_index * 220;
  return `<g class="canvas-hidden-stems">
    <text class="canvas-hidden-label" x="0" y="474" text-anchor="middle">\u85CF\u5E72</text>
    ${hiddenNodes.map((node) => {
    const anchor = anchors.get(node.node_ref);
    if (!anchor) return "";
    return `<g class="canvas-hidden-node element-${escapeAttr2(node.element)}${selected === node.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr2(node.polarity)}" transform="translate(${anchor.x - slotX} 515)" tabindex="0" role="button" data-canvas-object="${escapeAttr2(node.node_ref)}" aria-label="${escapeAttr2(`${slot.label}\u85CF\u5E72${node.label}`)}">
        <circle r="21"></circle>
        <text text-anchor="middle" dominant-baseline="central">${escapeHtml2(node.label)}</text>
      </g>`;
  }).join("")}
  </g>`;
}
function renderCanvasSceneNode(slot, node, anchor, selected, level) {
  const y = level === "stem" ? 185 : 390;
  const value = level === "stem" ? slot.stem : slot.branch;
  if (!node || !anchor) {
    return `<g class="canvas-scene-node is-inactive" transform="translate(0 ${y})"><text class="canvas-node-character" text-anchor="middle" dominant-baseline="central">${escapeHtml2(value || "\xB7")}</text></g>`;
  }
  const label = level === "stem" ? node.ten_god === "day_master" ? "\u65E5\u4E3B" : tenGodLabel(node.ten_god || "\u5929\u5E72") : "\u5730\u652F";
  return `<g class="canvas-scene-node element-${escapeAttr2(node.element)}${selected === node.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr2(node.polarity)}" transform="translate(0 ${y})" tabindex="0" role="button" data-canvas-object="${escapeAttr2(node.node_ref)}" aria-label="${escapeAttr2(`${slot.label}${label}${value}`)}">
    <rect x="-56" y="-58" width="112" height="116" rx="6"></rect>
    <text class="canvas-node-role" x="0" y="-33" text-anchor="middle">${escapeHtml2(label)}</text>
    <text class="canvas-node-character" x="0" y="11" text-anchor="middle" dominant-baseline="central">${escapeHtml2(value)}</text>
  </g>`;
}
function routeCanvasRelation(source, target, index) {
  const lane = index % 4;
  const sameLevel = source.level === target.level;
  const sameSlot = source.slotIndex === target.slotIndex;
  if (sameSlot && !sameLevel) {
    const side = source.slotIndex % 2 === 0 ? -70 : 70;
    const x = source.x + side;
    return {
      d: `M ${source.x} ${source.y} C ${x} ${source.y}, ${x} ${target.y}, ${target.x} ${target.y}`,
      labelX: x,
      labelY: (source.y + target.y) / 2
    };
  }
  if (sameLevel) {
    const trackY = source.level === "stem" ? 118 - lane * 15 : source.level === "branch" ? 457 + lane * 15 : 570 + lane * 15;
    return {
      d: `M ${source.x} ${source.y} C ${source.x} ${trackY}, ${target.x} ${trackY}, ${target.x} ${target.y}`,
      labelX: (source.x + target.x) / 2,
      labelY: trackY + (source.level === "stem" ? -7 : 15)
    };
  }
  const middleY = (source.y + target.y) / 2 + (lane - 1.5) * 13;
  return {
    d: `M ${source.x} ${source.y} C ${source.x} ${middleY}, ${target.x} ${middleY}, ${target.x} ${target.y}`,
    labelX: (source.x + target.x) / 2,
    labelY: middleY - 7
  };
}
function renderCanvasPath(path, anchors, selected, pathIndex) {
  const points = path.node_refs.flatMap((ref) => {
    const anchor = anchors.get(ref);
    return anchor ? [anchor] : [];
  });
  if (points.length < 2) return "";
  const segments = points.slice(0, -1).map((source, index) => {
    const target = points[index + 1];
    const laneY = 286 + pathIndex * 18;
    return `<path d="M ${source.x} ${source.y} C ${source.x} ${laneY}, ${target.x} ${laneY}, ${target.x} ${target.y}" marker-end="url(#canvas-path-arrow)"></path>`;
  }).join("");
  const candidate = path.trace.epistemic_status !== "committed";
  return `<g class="canvas-work-path${candidate ? " is-candidate" : ""}${selected === path.path_ref ? " is-selected" : ""}" tabindex="0" role="button" data-canvas-object="${escapeAttr2(path.path_ref)}" aria-label="${escapeAttr2(path.label)}">
    ${segments}
    <text x="${points[Math.floor(points.length / 2)].x}" y="${274 + pathIndex * 18}" text-anchor="middle">${candidate ? "\u5019\u9009\u8DEF\u5F84" : "\u6B63\u5F0F\u4E3B\u8DEF\u5F84"}</text>
  </g>`;
}
function focusRelationRefs(spec, relationRefs, selected) {
  if (!selected) return [];
  const selectedRefs = focusNodeRefs(spec, selected);
  return relationRefs.filter((ref) => {
    const relation = spec.relations.find((item) => item.relation_ref === ref);
    return relation && (relation.relation_ref === selected || relation.participant_node_refs.some((nodeRef) => selectedRefs.has(nodeRef)));
  });
}
function focusPathRefs(spec, pathRefs, selected) {
  if (!selected) return [];
  const selectedRefs = focusNodeRefs(spec, selected);
  return pathRefs.filter((ref) => {
    const path = spec.paths.find((item) => item.path_ref === ref);
    return path && (path.path_ref === selected || path.node_refs.some((nodeRef) => selectedRefs.has(nodeRef)) || path.relation_refs.includes(selected));
  });
}
function focusNodeRefs(spec, selected) {
  const refs = /* @__PURE__ */ new Set();
  const node = spec.nodes.find((item) => item.node_ref === selected);
  if (node) refs.add(node.node_ref);
  spec.nodes.filter((item) => item.semantic_slot_ref === selected).forEach((item) => refs.add(item.node_ref));
  const relation = spec.relations.find((item) => item.relation_ref === selected);
  relation?.participant_node_refs.forEach((item) => refs.add(item));
  const path = spec.paths.find((item) => item.path_ref === selected);
  path?.node_refs.forEach((item) => refs.add(item));
  return refs;
}
function shortRelationLabel(relation) {
  return {
    generates: "\u751F",
    controls: "\u514B",
    same_element_support: "\u540C\u6C14",
    stores: "\u85CF",
    roots: "\u6839",
    forms_half_combination: "\u534A\u5408",
    forms_triple_combination: "\u4E09\u5408",
    clashes: "\u51B2",
    harmonizes: "\u5408",
    harms: "\u5BB3",
    breaks: "\u7834",
    punishes: "\u5211",
    position_link: "\u540C\u67F1"
  }[relation.relation_type] || relation.label;
}
function visibilityLabel(value) {
  return { formal: "\u6B63\u5F0F", focus: "\u805A\u7126", lab_audit: "\u5BA1\u8BA1" }[value] || value;
}
function pathDiagnosticLabel(value) {
  return {
    none: "\u5F53\u524D\u8DEF\u5F84\u7684\u8282\u70B9\u3001\u5173\u7CFB\u4E0E\u6743\u9650\u5F15\u7528\u5747\u5DF2\u95ED\u5408\u3002",
    no_cognitive_path: "\u5F53\u524D\u8BA4\u77E5\u8BB0\u5F55\u5C1A\u672A\u5F62\u6210\u505A\u529F\u8DEF\u5F84\u3002",
    natural_language_only: "\u76EE\u524D\u53EA\u6709\u6587\u5B57\u63CF\u8FF0\uFF0C\u8FD8\u6CA1\u6709\u7ED3\u6784\u5316\u8DEF\u5F84\u5F15\u7528\u3002",
    candidate_not_committed: "\u5DF2\u6709\u7ED3\u6784\u5019\u9009\uFF0C\u4F46\u5C1A\u672A\u63D0\u4EA4\u4E3A\u6B63\u5F0F\u8DEF\u5F84\u3002",
    missing_path_ref: "\u6B63\u5F0F\u65AD\u8A00\u7F3A\u5C11\u53EF\u6295\u5F71\u7684\u8DEF\u5F84\u8EAB\u4EFD\u3002",
    invalid_node_ref: "\u8DEF\u5F84\u5F15\u7528\u7684\u8282\u70B9\u672A\u80FD\u843D\u5230\u5F53\u524D\u573A\u666F\u3002",
    invalid_relation_ref: "\u8DEF\u5F84\u5F15\u7528\u7684\u5173\u7CFB\u672A\u80FD\u843D\u5230\u5F53\u524D\u573A\u666F\u3002",
    relation_still_potential: "\u8DEF\u5F84\u7EC4\u6210\u5173\u7CFB\u4ECD\u662F\u6F5C\u5728\u72B6\u6001\uFF0C\u4E0D\u80FD\u8FDB\u5165\u6B63\u5F0F\u5C42\u3002",
    authority_not_allowed: "\u5F53\u524D\u8DEF\u5F84\u72B6\u6001\u6CA1\u6709\u6B63\u5F0F\u6295\u5F71\u6743\u9650\u3002",
    role_visibility_filtered: "\u6B63\u5F0F\u8DEF\u5F84\u4E0D\u5728\u5F53\u524D\u89D2\u8272\u7684\u62AB\u9732\u8303\u56F4\u5185\u3002",
    timing_scope_mismatch: "\u8DEF\u5F84\u7684\u65F6\u95F4\u4F5C\u7528\u57DF\u4E0E\u5F53\u524D\u9636\u6BB5\u4E0D\u4E00\u81F4\u3002"
  }[value] || "\u5F53\u524D\u6CA1\u6709\u53EF\u6295\u5F71\u7684\u6B63\u5F0F\u8DEF\u5F84\u3002";
}
function renderCanvasChanges(groups, selected, stage) {
  const visible = groups.filter((item) => item.count > 0);
  return `<section class="canvas-diff-panel" aria-label="\u9636\u6BB5\u53D8\u5316">
    <header><span>\u9636\u6BB5\u5DEE\u5F02</span><strong>${stage === "natal" ? "\u8FD9\u662F\u6BD4\u8F83\u57FA\u7EBF" : "\u53EA\u5217\u5408\u540C\u5DF2\u7ECF\u7ED9\u51FA\u7684\u53D8\u5316"}</strong></header>
    ${visible.length ? `<div class="change-list">${visible.map((group) => `<div class="change-group change-${escapeAttr2(group.change_type)}">
      <span><b>${escapeHtml2(group.label)}</b><em>${group.count}</em></span>
      ${group.items.slice(0, 5).map((item) => `<button type="button" data-canvas-object="${escapeAttr2(item.target_ref)}" class="${selected === item.target_ref ? "is-selected" : ""}">${escapeHtml2(item.label)}</button>`).join("")}
    </div>`).join("")}</div>` : `<div class="baseline-diff"><b>\u539F\u5C40</b><p>\u5148\u5EFA\u7ACB\u56DB\u67F1\u3001\u5173\u7CFB\u4E0E\u6B63\u5F0F\u4E3B\u8DEF\u5F84\u7684\u6BD4\u8F83\u8D77\u70B9\u3002</p></div>`}
    <details><summary>\u516B\u79CD\u53D8\u5316\u8BED\u4E49</summary><p>${groups.map((item) => `${item.label} ${item.count}`).join(" \xB7 ")}</p></details>
  </section>`;
}
function renderCanvasInspector(spec, selected, context, status) {
  const slot = spec.semantic_slots.find((item2) => item2.slot_ref === selected);
  const node = spec.nodes.find((item2) => item2.node_ref === selected);
  const relation = spec.relations.find((item2) => item2.relation_ref === selected);
  const path = spec.paths.find((item2) => item2.path_ref === selected);
  const cluster = spec.clusters.find((item2) => item2.cluster_ref === selected);
  const item = slot || node || relation || path || cluster;
  if (!item) return `<section class="canvas-inspector"><p>\u70B9\u51FB\u4E00\u67F1\u3001\u4E00\u4E2A\u5E72\u652F\u6216\u4E00\u6761\u5173\u7CFB\uFF0C\u67E5\u770B\u5B83\u5728\u5F53\u524D\u6B63\u5F0F\u72B6\u6001\u4E2D\u7684\u4F4D\u7F6E\u3002</p></section>`;
  const trace = item.trace;
  const label = slot ? `${slot.label} ${slot.stem}${slot.branch}` : item.label;
  const type = slot ? "\u8BED\u4E49\u67F1\u4F4D" : node ? nodeTypeLabel(node.node_type) : relation ? "\u7ED3\u6784\u5173\u7CFB" : path ? "\u547D\u5C40\u8DEF\u5F84" : "\u7ED3\u6784\u5019\u9009";
  const semanticState = relation?.semantic_state || path?.semantic_state || trace.epistemic_status;
  const contextMatches = context?.selected_object_refs.includes(selected);
  return `<section class="canvas-inspector" aria-label="\u5BF9\u8C61\u89E3\u91CA">
    <header><span>${escapeHtml2(type)}</span><b class="epistemic-${escapeAttr2(trace.epistemic_status)}">${escapeHtml2(epistemicLabel(trace.epistemic_status))}</b></header>
    <h3>${escapeHtml2(label)}</h3>
    <p>${status === "loading" ? "\u6B63\u5728\u53D6\u56DE\u8FD9\u4E2A\u5BF9\u8C61\u7684\u53D7\u63A7\u4E0A\u4E0B\u6587\u3002" : contextMatches ? objectExplanation(slot, node, relation, path) : "\u9009\u62E9\u5DF2\u5B9A\u4F4D\uFF1B\u53D7\u63A7\u4E0A\u4E0B\u6587\u5C06\u5728\u8FD9\u91CC\u663E\u793A\u3002"}</p>
    <dl><div><dt>\u5F53\u524D\u72B6\u6001</dt><dd>${escapeHtml2(stateLabel(semanticState))}</dd></div><div><dt>\u6765\u6E90</dt><dd>${trace.source_refs.length} \u6761\u53EF\u8FFD\u6EAF\u5F15\u7528</dd></div><div><dt>\u5F53\u524D\u9636\u6BB5</dt><dd>${escapeHtml2(spec.stage)}</dd></div></dl>
    ${trace.uncertainty.length || trace.rejection_or_block_reasons.length ? `<div class="inspector-caution"><span>\u4ECD\u9700\u4FDD\u7559</span><p>${escapeHtml2([...trace.uncertainty, ...trace.rejection_or_block_reasons][0])}</p></div>` : ""}
    <details><summary>\u67E5\u770B\u6765\u6E90</summary><ul>${trace.source_refs.map((ref) => `<li>${escapeHtml2(ref)}</li>`).join("")}</ul></details>
  </section>`;
}
function objectExplanation(slot, node, relation, path) {
  if (slot) return slot.immutable ? "\u8FD9\u662F\u539F\u5C40\u56FA\u5B9A\u67F1\u4F4D\uFF1B\u89C6\u89C9\u91CD\u6392\u4E0D\u4F1A\u6539\u53D8\u5B83\u7684\u5E74\u3001\u6708\u3001\u65E5\u3001\u65F6\u8EAB\u4EFD\u3002" : "\u8FD9\u662F\u6B63\u5F0F\u5386\u6CD5\u65F6\u95F4\u67F1\uFF1B\u51FA\u73B0\u4E0D\u7B49\u4E8E\u5DF2\u7ECF\u5F62\u6210\u73B0\u5B9E\u4E8B\u4EF6\u5224\u65AD\u3002";
  if (node) return `${node.label}\u5C5E\u4E8E${elementLabel[node.element] || "\u672A\u6807\u6CE8\u4E94\u884C"}${node.ten_god ? `\uFF0C\u5F53\u524D\u5341\u795E\u6807\u8BB0\u4E3A${tenGodLabel(node.ten_god)}` : ""}\u3002`;
  if (relation) return `${relation.label}\u7531 Compiler \u63D0\u4F9B\uFF0C\u9875\u9762\u53EA\u8D1F\u8D23\u5B9A\u4F4D\u4E0E\u663E\u793A\u3002`;
  if (path) return path.label;
  return "\u8FD9\u662F\u5F53\u524D\u89D2\u8272\u83B7\u51C6\u67E5\u770B\u7684\u7ED3\u6784\u5019\u9009\u3002";
}
function epistemicLabel(value) {
  return { fact: "\u6B63\u5F0F\u4E8B\u5B9E", derived: "\u7ED3\u6784\u63A8\u5BFC", candidate: "\u5019\u9009", committed: "\u5DF2\u63D0\u4EA4", blocked: "\u5DF2\u963B\u6B62", hypothetical: "\u5047\u8BBE", presentation_only: "\u4EC5\u5C55\u793A" }[value] || value;
}
function stateLabel(value) {
  return { latent: "\u6F5C\u5728", active: "\u53C2\u4E0E\u4E2D", reinforced: "\u83B7\u5F97\u652F\u6301", weakened: "\u53D7\u5230\u5236\u7EA6", blocked: "\u65E0\u6CD5\u95ED\u5408", fact: "\u4E8B\u5B9E", derived: "\u63A8\u5BFC", candidate: "\u5019\u9009", committed: "\u5DF2\u63D0\u4EA4" }[value] || value;
}
function nodeTypeLabel(value) {
  if (value.includes("hidden")) return "\u85CF\u5E72\u8282\u70B9";
  if (value.includes("stem")) return "\u5929\u5E72\u8282\u70B9";
  if (value.includes("branch")) return "\u5730\u652F\u8282\u70B9";
  return "\u7ED3\u6784\u8282\u70B9";
}
function tenGodLabel(value) {
  return {
    day_master: "\u65E5\u4E3B",
    bi_jian: "\u6BD4\u80A9",
    jie_cai: "\u52AB\u8D22",
    shi_shen: "\u98DF\u795E",
    shang_guan: "\u4F24\u5B98",
    pian_cai: "\u504F\u8D22",
    zheng_cai: "\u6B63\u8D22",
    qi_sha: "\u4E03\u6740",
    zheng_guan: "\u6B63\u5B98",
    pian_yin: "\u504F\u5370",
    zheng_yin: "\u6B63\u5370"
  }[value] || value;
}
function renderLoading(message) {
  return `<main class="system-state"><div class="state-mark"></div><p>\u770B\u89C1\u547D\u5C40</p><h1>${escapeHtml2(message)}</h1></main>`;
}
function renderUnavailable(title, detail, actionLabel) {
  return `
    <main class="system-state unavailable">
      <img src="/assets/abu/v11-designer-sad-tears/web/abu_sad_tears_v11.webp" alt="\u963F\u5E03\u6B63\u5728\u7B49\u5F85">
      <p>\u963F\u5E03\u5728\u8FD9\u91CC</p>
      <h1>${escapeHtml2(title)}</h1>
      <span>${escapeHtml2(detail)}</span>
      <a class="primary-command" href="/experience?manage=1">${escapeHtml2(actionLabel)}</a>
    </main>`;
}
function renderProfileSelector(cases2, activeProfileId2) {
  if (cases2.length <= 1) {
    const active = cases2.find((item) => item.profile_id === activeProfileId2);
    return `<span class="active-case"><i></i>${escapeHtml2(active?.display_name || "\u5F53\u524D\u547D\u76D8")}</span>`;
  }
  return `<label class="case-select-label"><span>\u5F53\u524D\u547D\u76D8</span><select data-profile-select>${cases2.map((item) => `<option value="${escapeAttr2(item.profile_id)}"${item.profile_id === activeProfileId2 ? " selected" : ""}>${escapeHtml2(item.display_name)}</option>`).join("")}</select></label>`;
}
function summaryItem(label, value, anchor) {
  return `<button type="button" class="scan-item" data-select-anchor="${escapeAttr2(anchor)}" data-message="${escapeAttr2(value)}"><span>${escapeHtml2(label)}</span><strong>${escapeHtml2(value)}</strong></button>`;
}
function renderCollapsibleSection(input) {
  return `
    <section class="experience-section tone-${escapeAttr2(input.tone)}${input.expanded ? " is-expanded" : " is-collapsed"}" id="${escapeAttr2(input.anchor)}" data-anchor="${escapeAttr2(input.anchor)}">
      <button class="section-heading" type="button" data-toggle-section="${escapeAttr2(input.id)}" aria-expanded="${input.expanded}">
        <span><small>${escapeHtml2(input.eyebrow)}</small><strong>${escapeHtml2(input.title)}</strong><em>${escapeHtml2(input.summary)}</em></span>
        <b aria-hidden="true">${input.expanded ? "\u2212" : "+"}</b>
      </button>
      <div class="section-body"${input.expanded ? "" : " hidden"}>${input.body}</div>
    </section>`;
}
function renderPillars(envelope2, selectedAnchor) {
  const pillars = envelope2.allowed_chart_facts.filter((item) => item.fact_type === "pillar");
  if (!pillars.length) return `<p class="empty-note">\u56DB\u67F1\u4E8B\u5B9E\u5C1A\u672A\u8FDB\u5165\u8FD9\u4EFD\u4F53\u9A8C\u3002</p>`;
  return `<div class="pillar-stage">${pillars.map((pillar) => {
    const message = `${pillar.pillar_label}\u662F${pillar.stem}${pillar.branch}\u3002${pillar.visible_ten_god ? `\u5929\u5E72\u5173\u7CFB\u4E3A${pillar.visible_ten_god}\u3002` : ""}${pillar.hidden_stems.length ? `\u5730\u652F\u85CF${pillar.hidden_stems.map((item) => item.stem).join("\u3001")}\u3002` : ""}`;
    return `<button type="button" class="pillar${selectedAnchor === pillar.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr2(pillar.visual_anchor)}" data-message="${escapeAttr2(message)}">
      <span class="pillar-label">${escapeHtml2(pillar.pillar_label)}</span>
      <span class="ten-god">${escapeHtml2(pillar.visible_ten_god || "\u5929\u5E72")}</span>
      <strong class="stem element-${escapeAttr2(pillar.stem_element)}" data-polarity="${escapeAttr2(pillar.stem_polarity)}">${escapeHtml2(pillar.stem)}</strong>
      <strong class="branch element-${escapeAttr2(pillar.branch_element)}" data-polarity="${escapeAttr2(pillar.branch_polarity)}">${escapeHtml2(pillar.branch)}</strong>
      <span class="nature">${polarityLabel[pillar.stem_polarity] || ""}${elementLabel[pillar.stem_element] || ""} \xB7 ${polarityLabel[pillar.branch_polarity] || ""}${elementLabel[pillar.branch_element] || ""}</span>
      <span class="hidden-stems">${pillar.hidden_stems.map((item) => `<i class="element-${escapeAttr2(item.element)}"><b>${escapeHtml2(item.stem)}</b><em>${escapeHtml2(item.ten_god)}</em></i>`).join("")}</span>
    </button>`;
  }).join("")}</div>`;
}
function renderPath(fullThesis, steps, selectedAnchor) {
  if (!steps.length) return `<p class="empty-note">\u4E3B\u8DEF\u5F84\u4ECD\u5728\u53EF\u9760\u6027\u95E8\u7981\u5185\uFF0C\u6CA1\u6709\u88AB\u5305\u88C5\u6210\u786E\u5B9A\u7ED3\u8BBA\u3002</p>`;
  return `<button type="button" class="baseline-thesis${selectedAnchor === "baseline-summary" ? " is-selected" : ""}" data-select-anchor="baseline-summary" data-message="${escapeAttr2(fullThesis)}">
    <span>\u6574\u76D8\u603B\u65AD</span><strong>${escapeHtml2(fullThesis)}</strong>
  </button><div class="path-stage">${steps.map((step, index) => {
    const message = `${step.premise}\uFF0C\u56E0\u6B64\u5F53\u524D\u5F97\u5230\u7684\u5224\u65AD\u662F\uFF1A${step.conclusion}`;
    return `<button type="button" class="path-step${selectedAnchor === step.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr2(step.visual_anchor)}" data-message="${escapeAttr2(message)}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <small>${escapeHtml2(step.premise)}</small>
      <strong>${escapeHtml2(step.conclusion)}</strong>
    </button>`;
  }).join('<span class="path-arrow" aria-hidden="true">\u2192</span>')}</div>`;
}
function firstSentence(value) {
  const match = value.match(/^.*?[。！？](?:[”’"])?/u);
  return match?.[0] || value;
}
function renderBoundaries(claim, envelope2, selectedAnchor) {
  const condition = claim?.conditions[0] || "\u6B63\u5F0F\u6761\u4EF6\u5C1A\u672A\u63D0\u4EA4\u3002";
  const uncertainty = envelope2.uncertainty.reasons[0] || "\u5F53\u524D\u6CA1\u6709\u989D\u5916\u672A\u51B3\u9879\u3002";
  const counter = claim?.counter_signals[0] || envelope2.competing_hypotheses[0]?.approved_meaning || "\u5C1A\u65E0\u5DF2\u63D0\u4EA4\u7684\u53CD\u5411\u4FE1\u53F7\u3002";
  return `<div class="boundary-grid">
    ${boundaryItem("\u6210\u7ACB\u6761\u4EF6", condition, "baseline-condition", selectedAnchor)}
    ${boundaryItem("\u6700\u5927\u672A\u51B3", uncertainty, "baseline-uncertainty", selectedAnchor)}
    ${boundaryItem("\u53CD\u5411\u4FE1\u53F7", counter, "baseline-counter-signal", selectedAnchor)}
  </div>`;
}
function boundaryItem(label, text, anchor, selectedAnchor) {
  return `<button type="button" class="boundary-item${selectedAnchor === anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr2(anchor)}" data-message="${escapeAttr2(text)}"><span>${escapeHtml2(label)}</span><strong>${escapeHtml2(text)}</strong></button>`;
}
function renderAbuDock(view) {
  const segment = view.narrationManifest?.segments[view.ui.narrationIndex];
  const isBusy = view.ui.narrationStatus === "preparing";
  return `<aside class="abu-dock${view.ui.abuExpanded ? " is-open" : ""}${isBusy ? " is-thinking" : ""}" aria-label="\u963F\u5E03\u540C\u6B65\u8BBA\u547D">
    <button class="abu-avatar" type="button" data-command="toggle-abu" aria-label="${view.ui.abuExpanded ? "\u6536\u8D77\u963F\u5E03" : "\u6253\u5F00\u963F\u5E03"}">
      <img class="${isBusy ? "" : "abu-avatar-standard"}" src="${isBusy ? "/assets/abu/v9-designer-taoist-divination/web/abu_taoist_divination_v9.webp" : "/assets/abu/v12-actor-pass/quiet-sit-reaction/web/abu_quiet_sit_reaction_v1.webp"}" alt="\u963F\u5E03">
    </button>
    <div class="abu-bubble" role="status"><span>${segment ? escapeHtml2(segment.title) : "\u963F\u5E03"}</span><p>${escapeHtml2(view.ui.abuMessage)}</p></div>
    <div class="abu-panel"${view.ui.abuExpanded ? "" : " hidden"}>
      <div class="abu-panel-heading"><span>\u963F\u5E03\u540C\u6B65\u8BBA\u547D</span><button type="button" data-command="toggle-abu" aria-label="\u6536\u8D77">\xD7</button></div>
      <p>${escapeHtml2(view.ui.abuMessage)}</p>
      <div class="narration-controls">
        <button type="button" class="primary-command compact" data-command="listen">${view.ui.narrationStatus === "playing" ? "\u6682\u505C" : "\u7EE7\u7EED\u542C"}</button>
        <button type="button" class="text-command" data-command="stop">\u505C\u6B62</button>
      </div>
      <ol class="chapter-list">${(view.narrationManifest?.segments || []).map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><span>${escapeHtml2(item.title)}</span><small>${escapeHtml2(item.text)}</small></button></li>`).join("")}</ol>
    </div>
  </aside>`;
}
function escapeHtml2(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character] || character);
}
function escapeAttr2(value) {
  return escapeHtml2(value).replace(/`/g, "&#96;");
}

// apps/product/experience_shell/src/state.ts
var initialUiState = {
  productArea: "world",
  workspaceSurface: "overview",
  selectedAnchor: "baseline-summary",
  expandedSections: {
    baseline: true,
    pillars: true,
    canvas: true,
    path: true,
    boundaries: true
  },
  abuExpanded: false,
  narrationStatus: "idle",
  narrationIndex: -1,
  abuMessage: "\u6211\u5148\u966A\u4F60\u770B\u6574\u76D8\u91CD\u5FC3\u3002\u60F3\u542C\u7684\u65F6\u5019\uFF0C\u70B9\u6211\u5C31\u597D\u3002",
  canvasStage: "natal",
  canvasLayer: "overview",
  canvasVisibilityLayer: "formal",
  selectedCanvasObject: "",
  canvasContextStatus: "idle"
};
function reduceUi(state, action) {
  switch (action.type) {
    case "product-area":
      return { ...state, productArea: action.area };
    case "workspace-surface":
      return { ...state, workspaceSurface: action.surface };
    case "select":
      return { ...state, selectedAnchor: action.anchor, abuMessage: action.message };
    case "toggle-section":
      return {
        ...state,
        expandedSections: {
          ...state.expandedSections,
          [action.section]: !state.expandedSections[action.section]
        }
      };
    case "toggle-abu":
      return { ...state, abuExpanded: action.expanded ?? !state.abuExpanded };
    case "narration":
      return {
        ...state,
        narrationStatus: action.status,
        narrationIndex: action.index ?? state.narrationIndex,
        abuMessage: action.message ?? state.abuMessage
      };
    case "canvas-stage":
      return {
        ...state,
        canvasStage: action.stage,
        canvasLayer: action.layer,
        selectedCanvasObject: action.selected,
        canvasContextStatus: "ready"
      };
    case "canvas-layer":
      return { ...state, canvasLayer: action.layer };
    case "canvas-visibility":
      return { ...state, canvasVisibilityLayer: action.visibility };
    case "canvas-select":
      return {
        ...state,
        selectedCanvasObject: action.selected,
        canvasContextStatus: action.status
      };
    case "canvas-context-status":
      return { ...state, canvasContextStatus: action.status };
  }
}

// apps/product/experience_shell/src/experience_data.ts
async function loadExperienceCase(selection, params, previousUi) {
  const bootstrap = await loadWorkspaceBootstrap(selection);
  const role = bootstrap.account.role;
  const profileRequired = bootstrap.status === "workspace_profile_required";
  const availableSurfaces2 = profileRequired ? ["overview"] : ["overview", "onecanvas", "theater"];
  const researchAllowed = bootstrap.workspace?.allowed_surfaces.includes("mingli_lab") || ["admin", "research", "research_master", "practitioner"].includes(role);
  const availableAreas2 = researchAllowed ? ["world", "workbench", "lab"] : ["world", "workbench"];
  let ui2 = previousUi ? structuredClone(previousUi) : structuredClone(initialUiState);
  const requestedSurface = params.get("surface");
  const preferredSurface = requestedSurface || bootstrap.workspace?.state.current_surface || ui2.workspaceSurface;
  ui2 = reduceUi(ui2, {
    type: "workspace-surface",
    surface: availableSurfaces2.includes(preferredSurface) ? preferredSurface : "overview"
  });
  const requestedArea = params.get("area");
  const preferredArea = requestedArea || (requestedSurface || ui2.workspaceSurface !== "overview" ? "workbench" : ui2.productArea);
  ui2 = reduceUi(ui2, {
    type: "product-area",
    area: availableAreas2.includes(preferredArea) ? preferredArea : "world"
  });
  return {
    account: bootstrap.account,
    cases: bootstrap.cases,
    selectedCaseId: bootstrap.selected_case_id,
    selectedProfileId: bootstrap.selected_profile_id,
    workspace: bootstrap.workspace,
    envelope: bootstrap.envelope,
    cognition: bootstrap.cognition,
    availableSurfaces: availableSurfaces2,
    availableAreas: availableAreas2,
    ui: ui2,
    profileRequired
  };
}

// apps/product/experience_shell/src/experience_dom.ts
function applyActiveAnchor(anchor) {
  document.querySelectorAll(".narration-active").forEach((element) => element.classList.remove("narration-active"));
  document.querySelectorAll(`[data-anchor="${CSS.escape(anchor)}"], [data-select-anchor="${CSS.escape(anchor)}"]`).forEach((element) => element.classList.add("narration-active"));
}
function updateExperienceLocation(activeCaseId2, ui2) {
  const params = new URLSearchParams({ case: activeCaseId2 });
  if (ui2.productArea !== "world") params.set("area", ui2.productArea);
  if (ui2.productArea === "workbench" && ui2.workspaceSurface !== "overview") {
    params.set("surface", ui2.workspaceSurface);
  }
  history.replaceState({}, "", `/experience?${params.toString()}`);
}
function humanizeError(message) {
  return message.replace(/^formal_life_case_not_available$/, "\u56DB\u67F1\u5DF2\u7ECF\u5C31\u7EEA\uFF0C\u6574\u76D8\u4E3B\u7EBF\u8FD8\u5728\u6574\u7406\u4E2D\u3002").replace(/^experience_case_not_found$/, "\u6CA1\u6709\u627E\u5230\u8FD9\u4EFD\u6848\u4F8B\uFF0C\u6216\u5B83\u4E0D\u5C5E\u4E8E\u5F53\u524D\u8D26\u6237\u3002").replace(/^canvas_official_timing_required$/, "\u8FD9\u4EFD\u6848\u4F8B\u8FD8\u6CA1\u6709\u5B8C\u6574\u7684\u5927\u8FD0\u4E0E\u6D41\u5E74\u8BA1\u7B97\u3002").replace(/_/g, " ");
}

// apps/product/experience_shell/src/experience_interactions.ts
function bindExperienceInteractions(root2, handlers) {
  root2.querySelectorAll("[data-product-area]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectArea(button.dataset.productArea));
  });
  root2.querySelectorAll("[data-workspace-surface]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectSurface(button.dataset.workspaceSurface));
  });
  root2.querySelectorAll("[data-select-anchor]").forEach((element) => {
    element.addEventListener("click", () => handlers.selectAnchor(
      element.dataset.selectAnchor || "baseline-summary",
      element.dataset.message || "\u8FD9\u4E00\u5904\u6765\u81EA\u6B63\u5F0F\u547D\u5C40\u8BA4\u77E5\u3002"
    ));
  });
  root2.querySelectorAll("[data-toggle-section]").forEach((button) => {
    button.addEventListener("click", () => handlers.toggleSection(button.dataset.toggleSection || "baseline"));
  });
  root2.querySelectorAll("[data-command]").forEach((button) => {
    button.addEventListener("click", () => handlers.command(button.dataset.command || ""));
  });
  root2.querySelectorAll("[data-play-segment]").forEach((button) => {
    button.addEventListener("click", () => handlers.playSegment(Number(button.dataset.playSegment || 0)));
  });
  root2.querySelectorAll("[data-canvas-stage]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectCanvasStage(
      button.dataset.canvasStage || "natal"
    ));
  });
  root2.querySelectorAll("[data-canvas-layer]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!button.disabled) handlers.selectCanvasLayer(
        button.dataset.canvasLayer || "overview"
      );
    });
  });
  root2.querySelectorAll("[data-canvas-visibility]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!button.disabled) handlers.selectCanvasVisibility(
        button.dataset.canvasVisibility || "formal"
      );
    });
  });
  root2.querySelectorAll("[data-canvas-object]").forEach((element) => {
    const select = () => {
      const selected = element.getAttribute("data-canvas-object") || "";
      if (selected) handlers.selectCanvasObject(selected);
    };
    element.addEventListener("click", select);
    element.addEventListener("keydown", (event) => {
      if (event instanceof KeyboardEvent && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        select();
      }
    });
  });
  root2.querySelectorAll("[data-profile-select]").forEach((select) => {
    select.addEventListener("change", (event) => {
      handlers.selectProfile(event.currentTarget.value);
    });
  });
}

// apps/product/experience_shell/src/audio.ts
var NarrationTimeline = class {
  constructor(caseId, manifest, statuses, events) {
    this.caseId = caseId;
    this.manifest = manifest;
    this.statuses = statuses;
    this.events = events;
  }
  audio = null;
  index = -1;
  cueTimers = [];
  stopped = false;
  async play() {
    if (this.audio?.paused && this.index >= 0) {
      await this.audio.play();
      this.scheduleCues(this.manifest.segments[this.index]);
      return;
    }
    this.stopped = false;
    this.index = this.index >= 0 ? this.index : 0;
    await this.playIndex(this.index);
  }
  pause() {
    this.clearCues();
    this.audio?.pause();
    const segment = this.manifest.segments[this.index];
    if (segment) this.events.onPaused(segment, this.index);
  }
  stop() {
    this.stopped = true;
    this.clearCues();
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
    }
    this.index = -1;
  }
  async playSegment(index) {
    this.stop();
    this.stopped = false;
    this.index = index;
    await this.playIndex(index);
  }
  async playIndex(index) {
    const segment = this.manifest.segments[index];
    if (!segment || this.stopped) {
      this.events.onComplete();
      return;
    }
    try {
      this.events.onPreparing(segment, index);
      const audioUrl = await this.resolveAudioUrl(segment);
      if (this.stopped) return;
      this.audio = new Audio(audioUrl);
      this.audio.preload = "auto";
      this.audio.addEventListener("play", () => {
        this.events.onPlaying(segment, index);
        this.scheduleCues(segment);
      });
      this.audio.addEventListener("ended", () => {
        this.clearCues();
        this.index = index + 1;
        void this.playIndex(this.index);
      });
      this.audio.addEventListener("error", () => this.events.onError(new Error("audio_playback_failed")));
      await this.audio.play();
    } catch (error) {
      this.events.onError(error instanceof Error ? error : new Error(String(error)));
    }
  }
  async resolveAudioUrl(segment) {
    const status = this.statuses[segment.segment_id];
    if (status?.status === "ready" && status.audio_url) return status.audio_url;
    const asset = await prepareNarrationSegment(this.caseId, segment.segment_id);
    const opus = asset.media.playback_variants.find((item) => item.format === "opus");
    return opus?.audio_url || asset.media.audio_url;
  }
  scheduleCues(segment) {
    this.clearCues();
    for (const cue of segment.visual_cues || []) {
      const remaining = Math.max(0, cue.at_ms - Math.round((this.audio?.currentTime || 0) * 1e3));
      this.cueTimers.push(window.setTimeout(() => this.events.onCue(cue.target), remaining));
    }
  }
  clearCues() {
    this.cueTimers.forEach((timer) => window.clearTimeout(timer));
    this.cueTimers = [];
  }
};

// apps/product/experience_shell/src/experience_timeline.ts
function createNarrationTimeline(caseId, manifest, statuses, dispatch2, focusAnchor2, humanizeError2) {
  return new NarrationTimeline(caseId, manifest, statuses, {
    onPreparing(segment, index) {
      dispatch2({ type: "narration", status: "preparing", index, message: `\u6211\u6B63\u5728\u51C6\u5907\u201C${segment.title}\u201D\u3002\u9875\u9762\u53EF\u4EE5\u5148\u770B\uFF0C\u4E0D\u7528\u7B49\u6211\u3002` });
    },
    onPlaying(segment, index) {
      dispatch2({ type: "narration", status: "playing", index, message: segment.text });
      focusAnchor2(segment.visual_anchor_ids[0] || "baseline-summary", false);
    },
    onPaused(segment, index) {
      dispatch2({ type: "narration", status: "paused", index, message: `\u505C\u5728\u201C${segment.title}\u201D\u3002\u4F60\u53EF\u4EE5\u5148\u770B\u9875\u9762\uFF0C\u4E5F\u53EF\u4EE5\u7EE7\u7EED\u542C\u3002` });
    },
    onComplete() {
      dispatch2({ type: "narration", status: "complete", index: -1, message: "\u8FD9\u6B21\u5148\u8BB2\u5230\u8FD9\u91CC\u3002\u4F60\u53EF\u4EE5\u70B9\u56DB\u67F1\u3001\u8DEF\u5F84\u6216\u672A\u51B3\u9879\u7EE7\u7EED\u95EE\u3002" });
    },
    onError(error) {
      dispatch2({ type: "narration", status: "error", message: `\u58F0\u97F3\u6682\u65F6\u6CA1\u6709\u51C6\u5907\u597D\uFF1A${humanizeError2(error.message)}\u3002\u6587\u5B57\u5185\u5BB9\u4ECD\u7136\u5B8C\u6574\u53EF\u8BFB\u3002` });
    },
    onCue(anchor) {
      focusAnchor2(anchor, false);
    }
  });
}

// apps/product/experience_shell/src/dream_api.ts
async function dreamRequest(url, init) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...init?.headers || {} },
    ...init
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(String(payload.detail || `dream_request_failed_${response.status}`));
  }
  return response.json();
}
function loadDreamStatus(caseId = "") {
  const query = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
  return dreamRequest(`/api/v50/dream/status${query}`);
}
function grantDreamConsent(caseId) {
  return dreamRequest("/api/v50/dream/consent", {
    method: "POST",
    body: JSON.stringify({
      case_id: caseId,
      accepted: true,
      consent_version: "deepbazi.dream_pilot_consent.v1"
    })
  });
}
function withdrawDreamConsent(caseId) {
  return dreamRequest("/api/v50/dream/consent/withdraw", {
    method: "POST",
    body: JSON.stringify({ case_id: caseId, confirmed: true })
  });
}
function createDreamVisit(homeCaseId) {
  return dreamRequest("/api/v50/dream/visits", {
    method: "POST",
    body: JSON.stringify({ home_case_id: homeCaseId })
  });
}
function loadDreamVisit(visitId) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}`);
}
function enterDreamVisit(visitId) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/enter`, {
    method: "POST",
    body: "{}"
  });
}
function loadDreamEncounter(visitId) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/encounter`);
}
function selectDreamTree(visitId, sceneRef) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/select-tree`, {
    method: "POST",
    body: JSON.stringify({ scene_ref: sceneRef })
  });
}
function loadDreamTree(visitId, sceneRef) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}`);
}
function openDreamMirror(visitId) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/open`, {
    method: "POST",
    body: "{}"
  });
}
function closeDreamMirror(visitId) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/close`, {
    method: "POST",
    body: "{}"
  });
}
function loadDreamMirror(visitId, sceneRef) {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/mirror`);
}
async function loadDreamMirrorContext(visitId, sceneRef, stage, selected, layer) {
  const params = new URLSearchParams({ stage, selected, layer });
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/mirror/context?${params.toString()}`
  );
}

// apps/product/experience_shell/src/dream_i18n.ts
var messages = {
  zh: {
    "dream.entry": "\u968F\u963F\u5E03\u5165\u68A6",
    "dream.resume": "\u7EE7\u7EED\u4E0A\u6B21\u7684\u68A6",
    "dream.loading": "\u96FE\u8DEF\u6B63\u5728\u663E\u73B0",
    "dream.encounter.eyebrow": "\u963F\u5E03\u68A6\u5883 \xB7 \u4E09\u6811\u7F18\u5883",
    "dream.encounter.title": "\u4E09\u68F5\u751F\u547D\u6811\uFF0C\u6B63\u5B89\u9759\u5730\u751F\u957F",
    "dream.encounter.lede": "\u4E00\u68F5\u6765\u81EA\u5DF2\u6388\u6743\u7684\u533F\u540D\u771F\u4EBA\u6863\u6848\uFF0C\u4E24\u68F5\u6765\u81EA\u660E\u786E\u6807\u8BC6\u7684 Canonical NPC\u3002\u9009\u62E9\u4E00\u68F5\uFF0C\u53EA\u89C2\u5BDF\uFF0C\u4E0D\u6539\u5199\u3002",
    "dream.tree.choose": "\u8D70\u8FD1\u8FD9\u68F5\u6811",
    "dream.tree.eyebrow": "\u5355\u6811\u89C2\u5BDF",
    "dream.tree.title": "\u4E00\u6BB5\u751F\u547D\uFF0C\u5728\u96FE\u91CC\u7559\u4E0B\u81EA\u5DF1\u7684\u5F62\u72B6",
    "dream.tree.lede": "\u6811\u8C61\u53EA\u6295\u5F71\u540C\u4E00\u4EFD\u6B63\u5F0F\u547D\u7406\u72B6\u6001\uFF0C\u4E0D\u4F1A\u81EA\u884C\u589E\u52A0\u5173\u7CFB\u6216\u7ED3\u8BBA\u3002",
    "dream.mirror.open": "\u6253\u5F00\u547D\u76D8\u955C",
    "dream.mirror.close": "\u56DE\u5230\u6811\u4E0B",
    "dream.workspace.back": "\u56DE\u5230\u751F\u547D\u4E16\u754C",
    "dream.path.none_confirmed": "\u5F53\u524D\u6682\u65E0\u5DF2\u786E\u8BA4\u4E3B\u8DEF\u5F84",
    "dream.source.authorized_human": "\u5DF2\u6388\u6743\u771F\u4EBA \xB7 \u533F\u540D",
    "dream.source.canonical_npc": "Canonical NPC \xB7 \u4EBA\u5DE5\u751F\u547D",
    "dream.unavailable.title": "\u8FD9\u6761\u68A6\u8DEF\u6682\u65F6\u6CA1\u6709\u5F00\u653E",
    "dream.unavailable.detail": "\u53EA\u6709\u4E09\u4EFD\u771F\u5B9E\u3001\u5DF2\u6388\u6743\u4E14\u53EF\u64A4\u56DE\u7684\u533F\u540D\u573A\u666F\u540C\u65F6\u5C31\u7EEA\u65F6\uFF0C\u963F\u5E03\u624D\u4F1A\u5E26\u4F60\u8FDB\u5165\u3002",
    "dream.error.title": "\u96FE\u8DEF\u6682\u65F6\u770B\u4E0D\u6E05"
  },
  en: {
    "dream.entry": "Enter the dream with Abu",
    "dream.resume": "Continue the dream",
    "dream.loading": "The mist path is appearing",
    "dream.encounter.eyebrow": "Abu's Dream \xB7 Three Trees",
    "dream.encounter.title": "Three life trees are quietly growing",
    "dream.encounter.lede": "One tree is an authorized anonymous human scene; two are clearly identified Canonical NPCs. Observe, never rewrite.",
    "dream.tree.choose": "Approach this tree",
    "dream.tree.eyebrow": "Tree observation",
    "dream.tree.title": "A life leaves its own shape in the mist",
    "dream.tree.lede": "The tree only projects the same formal Mingli state. It adds no relationships or conclusions.",
    "dream.mirror.open": "Open the chart mirror",
    "dream.mirror.close": "Return to the tree",
    "dream.workspace.back": "Return to Life World",
    "dream.path.none_confirmed": "No confirmed primary path yet",
    "dream.source.authorized_human": "Authorized human \xB7 anonymous",
    "dream.source.canonical_npc": "Canonical NPC \xB7 artificial life",
    "dream.unavailable.title": "This dream path is not open yet",
    "dream.unavailable.detail": "Abu enters only when three real, authorized, revocable, anonymized scenes are ready together.",
    "dream.error.title": "The mist path is unclear for now"
  },
  ko: {
    "dream.entry": "\uC544\uBD80\uC640 \uAFC8\uC73C\uB85C",
    "dream.resume": "\uC9C0\uB09C \uAFC8 \uC774\uC5B4\uAC00\uAE30",
    "dream.loading": "\uC548\uAC1C \uAE38\uC774 \uC5F4\uB9AC\uACE0 \uC788\uC5B4\uC694",
    "dream.encounter.eyebrow": "\uC544\uBD80\uC758 \uAFC8 \xB7 \uC138 \uADF8\uB8E8 \uC778\uC5F0",
    "dream.encounter.title": "\uC138 \uC0DD\uBA85\uB098\uBB34\uAC00 \uC870\uC6A9\uD788 \uC790\uB77C\uACE0 \uC788\uC5B4\uC694",
    "dream.encounter.lede": "\uD55C \uADF8\uB8E8\uB294 \uD5C8\uAC00\uB41C \uC775\uBA85 \uC2E4\uC81C \uC0AC\uC6A9\uC790, \uB450 \uADF8\uB8E8\uB294 \uBA85\uD655\uD788 \uD45C\uC2DC\uB41C Canonical NPC\uC785\uB2C8\uB2E4. \uAD00\uCC30\uD558\uB418 \uBC14\uAFB8\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
    "dream.tree.choose": "\uC774 \uB098\uBB34\uC5D0 \uB2E4\uAC00\uAC00\uAE30",
    "dream.tree.eyebrow": "\uD55C \uADF8\uB8E8 \uAD00\uCC30",
    "dream.tree.title": "\uD55C \uC0DD\uBA85\uC774 \uC548\uAC1C \uC18D\uC5D0 \uACE0\uC720\uD55C \uD615\uD0DC\uB97C \uB0A8\uAE41\uB2C8\uB2E4",
    "dream.tree.lede": "\uB098\uBB34 \uD615\uC0C1\uC740 \uB3D9\uC77C\uD55C \uACF5\uC2DD \uBA85\uB9AC \uC0C1\uD0DC\uB9CC \uBE44\uCD94\uBA70 \uAD00\uACC4\uB098 \uACB0\uB860\uC744 \uB367\uBD99\uC774\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
    "dream.mirror.open": "\uBA85\uC2DD \uAC70\uC6B8 \uC5F4\uAE30",
    "dream.mirror.close": "\uB098\uBB34 \uC544\uB798\uB85C",
    "dream.workspace.back": "\uC0DD\uBA85 \uC138\uACC4\uB85C \uB3CC\uC544\uAC00\uAE30",
    "dream.path.none_confirmed": "\uD604\uC7AC \uD655\uC778\uB41C \uC8FC \uACBD\uB85C\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4",
    "dream.source.authorized_human": "\uD5C8\uAC00\uB41C \uC2E4\uC81C \uC0AC\uC6A9\uC790 \xB7 \uC775\uBA85",
    "dream.source.canonical_npc": "Canonical NPC \xB7 \uC778\uACF5 \uC0DD\uBA85",
    "dream.unavailable.title": "\uC774 \uAFC8\uAE38\uC740 \uC544\uC9C1 \uC5F4\uB9AC\uC9C0 \uC54A\uC558\uC5B4\uC694",
    "dream.unavailable.detail": "\uC2E4\uC81C \uC790\uB8CC \uC138 \uAC74\uC774 \uD5C8\uAC00, \uCCA0\uD68C \uAC00\uB2A5, \uC775\uBA85\uD654 \uC870\uAC74\uC744 \uBAA8\uB450 \uCDA9\uC871\uD560 \uB54C\uB9CC \uC544\uBD80\uAC00 \uC548\uB0B4\uD569\uB2C8\uB2E4.",
    "dream.error.title": "\uC548\uAC1C \uAE38\uC774 \uC7A0\uC2DC \uD750\uB824\uC84C\uC5B4\uC694"
  }
};
function dreamLocale() {
  const language = navigator.language.toLowerCase();
  if (language.startsWith("ko")) return "ko";
  if (language.startsWith("en")) return "en";
  return "zh";
}
function dreamText(key, locale = dreamLocale()) {
  return messages[locale][key] || messages.zh[key];
}

// apps/product/experience_shell/src/dream_runtime.ts
async function bootDreamExperience(root2) {
  const runtime = new DreamRuntime(root2);
  await runtime.boot();
}
var DreamRuntime = class {
  constructor(root2) {
    this.root = root2;
    root2.addEventListener("click", (event) => void this.handleClick(event));
  }
  visit = null;
  encounter = null;
  tree = null;
  mirror = null;
  context = null;
  ui = structuredClone(initialUiState);
  async boot() {
    this.renderLoading();
    try {
      const route = parseDreamRoute();
      this.visit = route.visitId ? await loadDreamVisit(route.visitId) : await createDreamVisit("");
      if (["HOME_GROVE", "PATH_OFFERED", "DREAM_ENTERING"].includes(this.visit.state)) {
        this.visit = await enterDreamVisit(this.visit.visit_id);
      }
      const sceneRef = route.sceneRef || this.visit.selected_scene_ref;
      if (sceneRef) {
        await this.showTree(sceneRef, route.mirror || this.visit.state === "MIRROR_OPEN");
      } else {
        await this.showEncounter();
      }
    } catch (error) {
      this.renderError(error);
    }
  }
  async showEncounter() {
    if (!this.visit) return;
    this.encounter = await loadDreamEncounter(this.visit.visit_id);
    this.tree = null;
    this.mirror = null;
    this.context = null;
    history.replaceState({}, "", `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}`);
    this.root.innerHTML = renderEncounter(this.encounter);
  }
  async showTree(sceneRef, showMirror = false) {
    if (!this.visit) return;
    this.tree = await loadDreamTree(this.visit.visit_id, sceneRef);
    this.mirror = null;
    this.context = null;
    history.replaceState(
      {},
      "",
      `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(sceneRef)}`
    );
    if (showMirror) {
      await this.showMirror(sceneRef);
      return;
    }
    this.root.innerHTML = renderTree(this.tree);
  }
  async showMirror(sceneRef) {
    if (!this.visit) return;
    this.visit = await openDreamMirror(this.visit.visit_id);
    this.mirror = await loadDreamMirror(this.visit.visit_id, sceneRef);
    const canvas2 = this.mirror.canvas;
    const stage = canvas2.stages[canvas2.default_stage];
    this.ui = {
      ...structuredClone(initialUiState),
      workspaceSurface: "onecanvas",
      canvasStage: canvas2.default_stage,
      canvasLayer: stage.default_layer_id,
      canvasVisibilityLayer: "formal",
      selectedCanvasObject: stage.context.selected_object_refs[0] || stage.spec.semantic_slots[0]?.slot_ref || "",
      canvasContextStatus: "ready"
    };
    this.context = stage.context;
    history.replaceState(
      {},
      "",
      `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(sceneRef)}/mirror`
    );
    this.renderMirror();
  }
  renderMirror() {
    if (!this.mirror) return;
    this.root.innerHTML = renderMirror(
      renderReadOnlyCanvas(this.mirror.canvas, this.ui, this.context, false),
      dreamText(this.mirror.source_label_key)
    );
  }
  async handleClick(event) {
    const target = event.target instanceof Element ? event.target.closest("button, a") : null;
    if (!target || !this.visit) return;
    const sceneRef = target.dataset.dreamSelect;
    if (sceneRef) {
      this.renderLoading();
      try {
        this.visit = await selectDreamTree(this.visit.visit_id, sceneRef);
        await this.showTree(sceneRef);
      } catch (error) {
        this.renderError(error);
      }
      return;
    }
    if (target.dataset.dreamCommand === "open-mirror" && this.visit.selected_scene_ref) {
      this.renderLoading();
      try {
        await this.showMirror(this.visit.selected_scene_ref);
      } catch (error) {
        this.renderError(error);
      }
      return;
    }
    if (target.dataset.dreamCommand === "close-mirror" && this.visit.selected_scene_ref) {
      this.renderLoading();
      try {
        this.visit = await closeDreamMirror(this.visit.visit_id);
        await this.showTree(this.visit.selected_scene_ref);
      } catch (error) {
        this.renderError(error);
      }
      return;
    }
    const stage = target.dataset.canvasStage;
    if (stage && this.mirror?.canvas.stages[stage]) {
      const projection = this.mirror.canvas.stages[stage];
      this.ui = reduceUi(this.ui, {
        type: "canvas-stage",
        stage,
        layer: projection.default_layer_id,
        selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || ""
      });
      this.context = projection.context;
      this.renderMirror();
      return;
    }
    const layer = target.dataset.canvasLayer;
    if (layer) {
      this.ui = reduceUi(this.ui, { type: "canvas-layer", layer });
      this.renderMirror();
      return;
    }
    const visibility = target.dataset.canvasVisibility;
    if (visibility === "formal" || visibility === "focus") {
      this.ui = reduceUi(this.ui, { type: "canvas-visibility", visibility });
      this.renderMirror();
      return;
    }
    const selected = target.dataset.canvasObject;
    if (selected && this.visit.selected_scene_ref) await this.refreshContext(selected);
  }
  async refreshContext(selected) {
    if (!this.mirror || !this.visit) return;
    this.ui = reduceUi(this.ui, { type: "canvas-select", selected, status: "loading" });
    this.renderMirror();
    try {
      this.context = await loadDreamMirrorContext(
        this.visit.visit_id,
        this.visit.selected_scene_ref,
        this.ui.canvasStage,
        selected,
        this.ui.canvasLayer
      );
      this.ui = reduceUi(this.ui, { type: "canvas-context-status", status: "ready" });
    } catch {
      this.context = null;
      this.ui = reduceUi(this.ui, { type: "canvas-context-status", status: "error" });
    }
    this.renderMirror();
  }
  renderLoading() {
    this.root.innerHTML = `<main class="dream-state"><div class="dream-mist-mark" aria-hidden="true"></div><p>ABU DREAM</p><h1>${escapeHtml3(dreamText("dream.loading"))}</h1></main>`;
  }
  renderError(error) {
    const detail = error instanceof Error ? error.message : String(error);
    const unavailable = detail.includes("DREAM_ENCOUNTER_UNAVAILABLE") || detail.includes("dream_feature_disabled");
    this.root.innerHTML = `<main class="dream-state dream-error">
      <img src="/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp" alt="Abu">
      <p>ABU DREAM</p>
      <h1>${escapeHtml3(dreamText(unavailable ? "dream.unavailable.title" : "dream.error.title"))}</h1>
      <span>${escapeHtml3(unavailable ? dreamText("dream.unavailable.detail") : detail)}</span>
      <a class="dream-command" href="/experience">${escapeHtml3(dreamText("dream.workspace.back"))}</a>
    </main>`;
  }
};
function renderEncounter(encounter) {
  return `<main class="dream-world dream-encounter">
    ${dreamHeader()}
    <section class="dream-copy">
      <p>${escapeHtml3(dreamText("dream.encounter.eyebrow"))}</p>
      <h1>${escapeHtml3(dreamText("dream.encounter.title"))}</h1>
      <span>${escapeHtml3(dreamText("dream.encounter.lede"))}</span>
    </section>
    <section class="dream-tree-grove" aria-label="Three anonymous life trees">
      ${encounter.trees.map((tree, index) => `<button type="button" class="dream-tree-card is-${tree.art_variant} element-${tree.primary_element}" data-dream-select="${escapeAttr3(tree.scene_ref)}" aria-label="${escapeAttr3(dreamText("dream.tree.choose"))}">
        <em class="dream-source-badge">${escapeHtml3(dreamText(tree.source_label_key))}</em>
        <span class="dream-tree-crown"><i></i><i></i><i></i><i></i></span>
        <span class="dream-tree-trunk"><i></i></span>
        <strong>0${index + 1}</strong>
        <small>${escapeHtml3(dreamText("dream.tree.choose"))}</small>
      </button>`).join("")}
    </section>
    <img class="dream-abu-guide" src="/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp" alt="Abu guides the way">
  </main>`;
}
function renderTree(tree) {
  const variant = String(tree.visual_tokens.art_variant || "mist");
  const element = String(tree.visual_tokens.primary_element || "unknown");
  return `<main class="dream-world dream-tree-observation is-${escapeAttr3(variant)} element-${escapeAttr3(element)}">
    ${dreamHeader()}
    <section class="dream-copy compact">
      <p>${escapeHtml3(dreamText("dream.tree.eyebrow"))}</p>
      <h1>${escapeHtml3(dreamText("dream.tree.title"))}</h1>
      <span>${escapeHtml3(dreamText(tree.source_label_key))} \xB7 ${escapeHtml3(dreamText("dream.tree.lede"))}</span>
    </section>
    <section class="dream-single-tree" aria-label="Anonymous life tree">
      <div class="dream-tree-crown"><i></i><i></i><i></i><i></i><i></i></div>
      <div class="dream-tree-trunk"><i></i><i></i></div>
      <div class="dream-tree-roots"><i></i><i></i><i></i></div>
      <p>${escapeHtml3(dreamText(tree.work_path_message_key))}</p>
    </section>
    <div class="dream-tree-actions">
      <button class="dream-command" type="button" data-dream-command="open-mirror">${escapeHtml3(dreamText("dream.mirror.open"))}</button>
      <a href="/experience">${escapeHtml3(dreamText("dream.workspace.back"))}</a>
    </div>
    <img class="dream-abu-observer" src="/assets/abu/v12-actor-pass/turn-and-point/web/abu_turn_and_point_v1.webp" alt="Abu observes the tree">
  </main>`;
}
function renderMirror(canvasMarkup, sourceLabel) {
  return `<main class="dream-world dream-mirror-world">
    ${dreamHeader()}
    <section class="dream-mirror-heading"><div><p>ONECANVAS \xB7 DREAM MIRROR</p><h1>${escapeHtml3(dreamText("dream.mirror.open"))}</h1><span>${escapeHtml3(sourceLabel)}</span></div><button type="button" data-dream-command="close-mirror">${escapeHtml3(dreamText("dream.mirror.close"))}</button></section>
    <section class="dream-mirror-surface">${canvasMarkup}</section>
  </main>`;
}
function dreamHeader() {
  return `<header class="dream-header"><a href="/experience"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi"></a><span>ABU DREAM \xB7 READ ONLY</span></header>`;
}
function parseDreamRoute() {
  const parts = location.pathname.split("/").filter(Boolean);
  const visitIndex = parts.indexOf("visits");
  const treeIndex = parts.indexOf("trees");
  return {
    visitId: visitIndex >= 0 ? decodeURIComponent(parts[visitIndex + 1] || "") : "",
    sceneRef: treeIndex >= 0 ? decodeURIComponent(parts[treeIndex + 1] || "") : "",
    mirror: parts.includes("mirror")
  };
}
function escapeHtml3(value) {
  return value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character] || character);
}
function escapeAttr3(value) {
  return escapeHtml3(value);
}

// apps/product/experience_shell/src/main.ts
var rootElement = document.querySelector("#experienceRoot");
if (!rootElement) throw new Error("experience_root_missing");
var root = rootElement;
var account = { display_name: "", role: "member" };
var cases = [];
var activeCaseId = "";
var activeProfileId = "";
var workspace = null;
var cognition = null;
var availableSurfaces = ["overview"];
var availableAreas = ["world", "workbench"];
var envelope = null;
var canvas = null;
var canvasContext = null;
var narrationManifest = null;
var narrationAssets = {};
var timeline = null;
var ui = structuredClone(initialUiState);
var canvasLoading = false;
var narrationLoading = false;
var cognitionEpoch = 0;
var openCaseEpoch = 0;
var localReconciliationAttempted = /* @__PURE__ */ new Set();
var authMode = "login";
var accountProfiles = [];
var profileEditorMode = "none";
var editingProfileId = "";
var accountBusy = false;
var accountError = "";
var dreamStatus = null;
if (location.pathname.startsWith("/experience/dream")) void bootDreamExperience(root);
else void boot();
async function boot() {
  root.innerHTML = renderLoading("\u6B63\u5728\u6253\u5F00\u4F60\u7684\u547D\u5C40");
  try {
    const params = new URLSearchParams(location.search);
    await openCase({
      caseId: params.get("case") || "",
      profileId: params.get("profile") || ""
    });
    if (params.get("manage") === "1" && envelope) await openProfileManager();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const unauthenticated = message.includes("authentication_required");
    if (unauthenticated) showAuth();
    else root.innerHTML = renderUnavailable(
      "\u8FD9\u4EFD\u547D\u5C40\u6682\u65F6\u6CA1\u6709\u51C6\u5907\u597D",
      humanizeError(message),
      "\u7BA1\u7406\u6863\u6848"
    );
  }
}
async function openCase(selection, preserveUi = false) {
  const requestEpoch = ++openCaseEpoch;
  cognitionEpoch += 1;
  const previousCaseId = activeCaseId;
  const loaded = await loadExperienceCase(
    selection,
    new URLSearchParams(location.search),
    preserveUi ? ui : void 0
  );
  if (requestEpoch !== openCaseEpoch) return;
  if (loaded.profileRequired || !loaded.envelope) {
    account = loaded.account;
    cases = loaded.cases;
    await openProfileManager("create");
    return;
  }
  const caseChanged = Boolean(previousCaseId && previousCaseId !== loaded.selectedCaseId);
  timeline?.stop();
  if (caseChanged || preserveUi) {
    canvas = null;
    canvasContext = null;
    narrationManifest = null;
    narrationAssets = {};
    timeline = null;
  }
  account = loaded.account;
  cases = loaded.cases;
  activeCaseId = loaded.selectedCaseId;
  activeProfileId = loaded.selectedProfileId;
  workspace = loaded.workspace;
  envelope = loaded.envelope;
  cognition = loaded.cognition;
  availableSurfaces = loaded.availableSurfaces;
  availableAreas = loaded.availableAreas;
  ui = loaded.ui;
  updateExperienceLocation(activeCaseId, ui);
  render();
  void loadSelectedProjection();
  void refreshDreamStatus();
  scheduleBackgroundCognition();
}
function render() {
  if (!envelope || !cognition) return;
  root.innerHTML = renderExperience({
    accountName: account.display_name,
    accountRole: account.role,
    cases,
    activeCaseId,
    activeProfileId,
    availableAreas,
    availableSurfaces,
    workspace,
    envelope,
    cognition,
    narrationManifest,
    canvas,
    canvasContext,
    ui,
    dreamStatus
  });
  bindExperienceInteractions(root, {
    selectArea,
    selectSurface,
    selectAnchor(anchor, message) {
      dispatch({ type: "select", anchor, message });
      focusAnchor(anchor);
    },
    toggleSection(section) {
      dispatch({ type: "toggle-section", section });
    },
    command(command) {
      void handleCommand(command);
    },
    playSegment(index) {
      void playNarrationSegment(index);
    },
    selectCanvasStage,
    selectCanvasLayer,
    selectCanvasVisibility,
    selectCanvasObject(selected) {
      void refreshCanvasContext(selected);
    },
    selectProfile(profileId) {
      root.innerHTML = renderLoading("\u6B63\u5728\u5207\u6362\u547D\u76D8");
      void openCase({ profileId });
    }
  });
  requestAnimationFrame(() => applyActiveAnchor(ui.selectedAnchor));
}
function selectArea(area) {
  if (!availableAreas.includes(area)) return;
  ui = reduceUi(ui, { type: "product-area", area });
  if (area === "lab") {
    selectLabLayer();
    void ensureCanvas();
  } else {
    ui = reduceUi(ui, { type: "canvas-visibility", visibility: "formal" });
  }
  updateExperienceLocation(activeCaseId, ui);
  render();
}
function selectSurface(surface) {
  if (!availableSurfaces.includes(surface)) return;
  ui = reduceUi(ui, { type: "workspace-surface", surface });
  updateExperienceLocation(activeCaseId, ui);
  render();
  void loadSelectedProjection();
}
async function loadSelectedProjection() {
  if (ui.productArea === "lab" || ui.workspaceSurface === "onecanvas") await ensureCanvas();
  if (ui.workspaceSurface === "theater") await ensureNarration();
}
async function ensureCanvas() {
  if (canvas || canvasLoading || !activeCaseId) return;
  canvasLoading = true;
  try {
    canvas = await loadReadOnlyCanvas(activeCaseId);
    const projection = canvas.stages[canvas.default_stage];
    canvasContext = projection.context;
    ui = reduceUi(ui, {
      type: "canvas-stage",
      stage: canvas.default_stage,
      layer: projection.default_layer_id,
      selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || ""
    });
    if (ui.productArea === "lab") selectLabLayer();
  } catch {
    canvas = null;
    canvasContext = null;
  } finally {
    canvasLoading = false;
    render();
  }
}
async function ensureNarration() {
  if (narrationManifest && timeline) return true;
  if (narrationLoading || !activeCaseId) return false;
  narrationLoading = true;
  try {
    const loaded = await loadNarration(activeCaseId);
    narrationManifest = loaded.manifest;
    narrationAssets = loaded.speechAssets;
    timeline = createNarrationTimeline(
      activeCaseId,
      narrationManifest,
      narrationAssets,
      dispatch,
      focusAnchor,
      humanizeError
    );
    return true;
  } catch {
    narrationManifest = null;
    narrationAssets = {};
    timeline = null;
    return false;
  } finally {
    narrationLoading = false;
    render();
  }
}
function selectCanvasStage(stage) {
  if (!canvas) return;
  const projection = canvas.stages[stage];
  canvasContext = projection.context;
  ui = reduceUi(ui, {
    type: "canvas-stage",
    stage,
    layer: projection.default_layer_id,
    selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || ""
  });
  render();
}
function selectCanvasLayer(layer) {
  if (!canvas) return;
  ui = reduceUi(ui, { type: "canvas-layer", layer });
  render();
  if (ui.selectedCanvasObject) void refreshCanvasContext(ui.selectedCanvasObject);
}
function selectCanvasVisibility(visibility) {
  if (!canvas || !canvas.renderer_policy.available_visibility_layers.includes(visibility)) return;
  ui = reduceUi(ui, { type: "canvas-visibility", visibility });
  render();
}
async function refreshCanvasContext(selected) {
  if (!canvas) return;
  ui = reduceUi(ui, { type: "canvas-select", selected, status: "loading" });
  render();
  try {
    canvasContext = await loadCanvasContext(activeCaseId, ui.canvasStage, selected, ui.canvasLayer);
    ui = reduceUi(ui, { type: "canvas-context-status", status: "ready" });
  } catch {
    canvasContext = null;
    ui = reduceUi(ui, { type: "canvas-context-status", status: "error" });
  }
  render();
}
async function playNarrationSegment(index) {
  if (await ensureNarration()) await timeline?.playSegment(index);
}
async function handleCommand(command) {
  if (command === "manage-profiles") {
    await openProfileManager();
    return;
  }
  if (command === "toggle-abu") {
    dispatch({ type: "toggle-abu" });
    return;
  }
  if (command === "enter-dream") {
    root.innerHTML = renderLoading("\u963F\u5E03\u6B63\u5728\u5E26\u4F60\u8D70\u5165\u96FE\u8DEF");
    try {
      let visit = await createDreamVisit(activeCaseId);
      visit = await enterDreamVisit(visit.visit_id);
      location.assign(`/experience/dream/visits/${encodeURIComponent(visit.visit_id)}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      root.innerHTML = renderUnavailable("\u8FD9\u6761\u68A6\u8DEF\u6682\u65F6\u6CA1\u6709\u5F00\u653E", humanizeError(message), "\u56DE\u5230\u751F\u547D\u4E16\u754C");
    }
    return;
  }
  if (command === "grant-dream-consent") {
    const accepted = window.confirm(
      "\u786E\u8BA4\u6388\u6743\u5F53\u524D\u6863\u6848\u4EE5\u533F\u540D\u751F\u547D\u6811\u8FDB\u5165\u672C\u5730\u5C01\u95ED\u68A6\u5883\uFF1F\u4EC5\u5C55\u793A\u786E\u5B9A\u6027\u547D\u76D8\u4E0E\u53EA\u8BFB\u6811\u8C61\uFF0C\u4F60\u53EF\u4EE5\u968F\u65F6\u64A4\u56DE\u3002"
    );
    if (!accepted) return;
    try {
      await grantDreamConsent(activeCaseId);
      await refreshDreamStatus();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      window.alert(`\u6388\u6743\u672A\u5B8C\u6210\uFF1A${humanizeError(message)}`);
    }
    return;
  }
  if (command === "withdraw-dream-consent") {
    const confirmed = window.confirm("\u786E\u8BA4\u64A4\u56DE\u5F53\u524D\u6863\u6848\u7684\u68A6\u5883\u5C55\u793A\u6388\u6743\uFF1F\u64A4\u56DE\u540E\uFF0C\u8FD9\u68F5\u771F\u4EBA\u751F\u547D\u6811\u4F1A\u7ACB\u5373\u5931\u53BB\u8FDB\u5165\u8D44\u683C\u3002");
    if (!confirmed) return;
    try {
      await withdrawDreamConsent(activeCaseId);
      await refreshDreamStatus();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      window.alert(`\u64A4\u56DE\u672A\u5B8C\u6210\uFF1A${humanizeError(message)}`);
    }
    return;
  }
  if (command === "listen") {
    dispatch({ type: "toggle-abu", expanded: true });
    if (!await ensureNarration() || !timeline) {
      dispatch({ type: "narration", status: "error", message: "\u56DB\u67F1\u5DF2\u7ECF\u5C31\u7EEA\uFF0C\u8BED\u97F3\u6682\u65F6\u6CA1\u6709\u8FDE\u63A5\u4E0A\u3002" });
    } else if (ui.narrationStatus === "playing") {
      timeline.pause();
    } else {
      await timeline.play();
    }
    return;
  }
  if (command === "stop") {
    timeline?.stop();
    dispatch({ type: "narration", status: "idle", index: -1, message: "\u5DF2\u505C\u6B62\u3002\u4F60\u53EF\u4EE5\u70B9\u4EFB\u610F\u547D\u7406\u5BF9\u8C61\uFF0C\u8BA9\u6211\u4ECE\u90A3\u91CC\u7EE7\u7EED\u3002" });
    return;
  }
  if (command === "focus-pillars") focusAnchor("four-pillars");
}
async function refreshDreamStatus() {
  try {
    dreamStatus = await loadDreamStatus(activeCaseId);
  } catch {
    dreamStatus = null;
  }
  render();
}
function selectLabLayer() {
  if (!canvas) return;
  const layer = canvas.stages[ui.canvasStage].layers.find((item) => item.layer_id === "five_element" && item.available);
  if (layer) ui = reduceUi(ui, { type: "canvas-layer", layer: layer.layer_id });
  if (canvas.renderer_policy.available_visibility_layers.includes("lab_audit")) {
    ui = reduceUi(ui, { type: "canvas-visibility", visibility: "lab_audit" });
  }
}
function scheduleBackgroundCognition() {
  const epoch = ++cognitionEpoch;
  requestAnimationFrame(() => void continueBackgroundCognition(epoch));
}
async function continueBackgroundCognition(epoch) {
  if (epoch !== cognitionEpoch || !cognition || !activeCaseId) return;
  if (cognition.status === "ready") return;
  if (cognition.status === "preparing" && cognition.background_job_id) {
    await pollCognitiveJob(cognition.background_job_id, epoch);
    return;
  }
  const shouldReconcile = cognition.status === "partial" && !localReconciliationAttempted.has(activeCaseId);
  if (!cognition.background_start_allowed && !shouldReconcile) return;
  if (shouldReconcile) localReconciliationAttempted.add(activeCaseId);
  try {
    const started = await startMissingBaseline(activeCaseId);
    if (epoch !== cognitionEpoch) return;
    if (started.status === "baseline_preparing" && started.job_id) {
      cognition = {
        ...cognition,
        status: "preparing",
        message: "\u56DB\u67F1\u5DF2\u7ECF\u5C31\u7EEA\uFF0C\u963F\u5E03\u6B63\u5728\u68B3\u7406\u6574\u76D8\u4E3B\u7EBF\u3002",
        background_start_allowed: false,
        background_job_id: started.job_id
      };
      render();
      await pollCognitiveJob(started.job_id, epoch);
      return;
    }
    if (started.status === "baseline_reconciled" || started.status === "baseline_cache_reused") {
      await refreshWorkspaceAfterCognition(epoch);
      return;
    }
    cognition = {
      ...cognition,
      status: "partial",
      message: "\u56DB\u67F1\u4E0E\u5DF2\u786E\u8BA4\u5185\u5BB9\u90FD\u53EF\u4EE5\u7EE7\u7EED\u67E5\u770B\uFF0C\u5176\u4ED6\u90E8\u5206\u6682\u65F6\u4FDD\u7559\u3002",
      background_start_allowed: false
    };
    render();
  } catch {
    cognition = {
      ...cognition,
      status: "partial",
      message: "\u56DB\u67F1\u5DF2\u7ECF\u5C31\u7EEA\uFF0C\u6574\u76D8\u4E3B\u7EBF\u7A0D\u540E\u518D\u7EE7\u7EED\u6574\u7406\u3002",
      background_start_allowed: false
    };
    render();
  }
}
async function pollCognitiveJob(jobId, epoch) {
  for (let attempt = 0; attempt < 90 && epoch === cognitionEpoch; attempt += 1) {
    await delay(1500);
    let job;
    try {
      job = await loadCognitiveJob(jobId);
    } catch {
      return;
    }
    if (job.status === "completed" || job.status === "failed") {
      await refreshWorkspaceAfterCognition(epoch);
      return;
    }
  }
}
async function refreshWorkspaceAfterCognition(epoch) {
  if (epoch !== cognitionEpoch) return;
  await openCase({ caseId: activeCaseId, profileId: activeProfileId }, true);
}
function dispatch(action) {
  ui = reduceUi(ui, action);
  render();
}
function focusAnchor(anchor, scroll = true) {
  ui = reduceUi(ui, { type: "select", anchor, message: ui.abuMessage });
  applyActiveAnchor(anchor);
  if (scroll) {
    document.querySelector(`[data-anchor="${CSS.escape(anchor)}"]`)?.scrollIntoView({
      behavior: "smooth",
      block: "center"
    });
  }
}
function delay(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}
function showAuth(error = "") {
  accountError = error;
  root.innerHTML = renderAuthSurface({ mode: authMode, busy: accountBusy, error: accountError });
  bindAccountInteractions(root, accountInteractionHandlers());
  history.replaceState({}, "", "/experience");
}
async function openProfileManager(preferredMode = "none") {
  root.innerHTML = renderLoading("\u6B63\u5728\u6253\u5F00\u547D\u7406\u6863\u6848");
  try {
    accountProfiles = await loadProfiles();
    profileEditorMode = preferredMode === "none" && !accountProfiles.length ? "create" : preferredMode;
    editingProfileId = "";
    accountError = "";
    renderProfileManagement();
    history.replaceState({}, "", "/experience?manage=1");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (message.includes("authentication_required")) showAuth();
    else {
      accountError = humanizeAccountError(message);
      accountProfiles = [];
      profileEditorMode = "create";
      renderProfileManagement();
    }
  }
}
function renderProfileManagement() {
  root.innerHTML = renderProfileManager({
    accountName: account.display_name,
    profiles: accountProfiles,
    activeProfileId,
    editorMode: profileEditorMode,
    editingProfileId,
    busy: accountBusy,
    error: accountError,
    canReturnToWorkspace: Boolean(envelope && cognition && activeCaseId)
  });
  bindAccountInteractions(root, accountInteractionHandlers());
}
function accountInteractionHandlers() {
  return {
    setAuthMode(mode) {
      authMode = mode;
      accountError = "";
      showAuth();
    },
    submitAuth(form) {
      void submitAuthForm(form);
    },
    command(command) {
      void handleAccountCommand(command);
    },
    useProfile(profileId) {
      if (!profileId) return;
      root.innerHTML = renderLoading("\u6B63\u5728\u8FDB\u5165\u547D\u5C40");
      void openCase({ profileId });
    },
    editProfile(profileId) {
      profileEditorMode = "edit";
      editingProfileId = profileId;
      accountError = "";
      renderProfileManagement();
    },
    deleteProfile(profileId) {
      void removeProfile(profileId);
    },
    submitProfile(form) {
      void submitProfileForm(form);
    }
  };
}
async function submitAuthForm(form) {
  const data = new FormData(form);
  accountBusy = true;
  accountError = "";
  showAuth();
  try {
    const result = await authenticate({
      mode: authMode,
      email: String(data.get("email") || ""),
      password: String(data.get("password") || ""),
      displayName: String(data.get("display_name") || ""),
      role: String(data.get("role") || "member")
    });
    account = {
      display_name: result.account.display_name,
      role: result.account.role || result.account.account_role || "member"
    };
    accountBusy = false;
    await openCase({});
  } catch (error) {
    accountBusy = false;
    accountError = humanizeAccountError(error instanceof Error ? error.message : String(error));
    showAuth(accountError);
  }
}
async function handleAccountCommand(command) {
  if (command === "create-profile") {
    profileEditorMode = "create";
    editingProfileId = "";
    accountError = "";
    renderProfileManagement();
    return;
  }
  if (command === "cancel-profile") {
    profileEditorMode = "none";
    editingProfileId = "";
    accountError = "";
    renderProfileManagement();
    return;
  }
  if (command === "return-workspace" && envelope && cognition) {
    updateExperienceLocation(activeCaseId, ui);
    render();
    void loadSelectedProjection();
    return;
  }
  if (command === "logout") {
    accountBusy = true;
    renderProfileManagement();
    try {
      await logout();
    } finally {
      timeline?.stop();
      accountBusy = false;
      account = { display_name: "", role: "member" };
      accountProfiles = [];
      activeCaseId = "";
      activeProfileId = "";
      workspace = null;
      envelope = null;
      cognition = null;
      canvas = null;
      narrationManifest = null;
      showAuth();
    }
  }
}
async function submitProfileForm(form) {
  const data = new FormData(form);
  const profileId = form.dataset.profileId || "";
  const existing = accountProfiles.find((item) => item.profile_id === profileId);
  accountBusy = true;
  accountError = "";
  renderProfileManagement();
  try {
    const profile = await saveProfile(profileInputFromForm(data, existing), profileId);
    accountBusy = false;
    root.innerHTML = renderLoading("\u56DB\u67F1\u5DF2\u786E\u8BA4\uFF0C\u6B63\u5728\u8FDB\u5165\u547D\u5C40");
    await openCase({ profileId: profile.profile_id });
  } catch (error) {
    accountBusy = false;
    accountError = humanizeAccountError(error instanceof Error ? error.message : String(error));
    renderProfileManagement();
  }
}
async function removeProfile(profileId) {
  const profile = accountProfiles.find((item) => item.profile_id === profileId);
  if (!profile || !window.confirm(`\u786E\u5B9A\u5220\u9664\u201C${profile.display_name}\u201D\u5417\uFF1F\u5386\u53F2\u63A2\u7D22\u4E0D\u4F1A\u540C\u65F6\u5220\u9664\u3002`)) return;
  accountBusy = true;
  accountError = "";
  renderProfileManagement();
  try {
    await deleteProfile(profileId);
    accountProfiles = accountProfiles.filter((item) => item.profile_id !== profileId);
    if (profileId === activeProfileId) {
      activeCaseId = "";
      activeProfileId = "";
      workspace = null;
      envelope = null;
      cognition = null;
      canvas = null;
      narrationManifest = null;
    }
    profileEditorMode = accountProfiles.length ? "none" : "create";
    editingProfileId = "";
  } catch (error) {
    accountError = humanizeAccountError(error instanceof Error ? error.message : String(error));
  } finally {
    accountBusy = false;
    renderProfileManagement();
  }
}
function profileInputFromForm(data, existing) {
  const approximate = String(data.get("time_precision") || "exact") === "approximate";
  return {
    birth_input_id: existing?.birth_input_id || `profile-${crypto.randomUUID()}`,
    name: String(data.get("name") || "\u6211\u7684\u547D\u76D8"),
    gender: String(data.get("gender") || "unknown"),
    calendar_type: String(data.get("calendar_type") || "solar"),
    birth_date: String(data.get("birth_date") || ""),
    birth_time: String(data.get("birth_time") || ""),
    birth_location: String(data.get("birth_location") || ""),
    timezone: String(data.get("timezone") || "Asia/Seoul"),
    true_solar_time_policy: existing?.true_solar_time_policy || "not_applied",
    lunar_leap_month: data.get("lunar_leap_month") === "on",
    year_pillar: "",
    month_pillar: "",
    day_pillar: "",
    hour_pillar: "",
    input_quality: approximate ? "user_confirmed_approximate" : "user_confirmed",
    warnings: approximate ? ["birth_time_approximate"] : []
  };
}
function humanizeAccountError(message) {
  const messages2 = {
    invalid_email_or_password: "\u90AE\u7BB1\u6216\u5BC6\u7801\u4E0D\u6B63\u786E\u3002",
    email_already_registered: "\u8FD9\u4E2A\u90AE\u7BB1\u5DF2\u7ECF\u6CE8\u518C\uFF0C\u53EF\u4EE5\u76F4\u63A5\u767B\u5F55\u3002",
    invalid_email: "\u8BF7\u586B\u5199\u6709\u6548\u90AE\u7BB1\u3002",
    password_too_short: "\u5BC6\u7801\u81F3\u5C11\u9700\u8981 8 \u4F4D\u3002",
    profile_not_found: "\u6CA1\u6709\u627E\u5230\u8FD9\u4EFD\u6863\u6848\u3002",
    four_pillars_resolution_failed: "\u8FD9\u7EC4\u51FA\u751F\u8D44\u6599\u6682\u65F6\u65E0\u6CD5\u6392\u51FA\u5B8C\u6574\u56DB\u67F1\uFF0C\u8BF7\u68C0\u67E5\u65E5\u671F\u3001\u65F6\u95F4\u4E0E\u5386\u6CD5\u3002"
  };
  return messages2[message] || humanizeError(message);
}
