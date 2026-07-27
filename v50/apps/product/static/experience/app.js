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
        ${view.editorMode === "none" ? `<div class="profile-editor-idle"><img src="/assets/abu/v12-actor-pass/dream-standard-cycle/web/abu_dream_standard_cycle_v1.webp" alt="\u963F\u5E03"><p>\u963F\u5E03\u5728\u8FD9\u91CC</p><h2>\u9009\u4E00\u4EFD\u6863\u6848\u7EE7\u7EED\uFF0C\u6216\u5EFA\u7ACB\u65B0\u7684\u547D\u5C40\u3002</h2></div>` : renderProfileForm(view.editorMode, editing, view.busy, view.error)}
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

// apps/product/experience_shell/src/dream_asset_registry.ts
var DREAM_ENCOUNTER_ASSET_ROOT = "/assets/dream/encounter-01-v1";
var DIRECTOR_ROOT = `${DREAM_ENCOUNTER_ASSET_ROOT}/director-v2`;
var ABU_V12 = "/assets/abu/v12-actor-pass";
var DREAM_RUNTIME_ASSETS = {
  homeTree: {
    assetId: "semantic_tree_base_clean_v1",
    intent: "home_tree",
    kind: "image",
    source: "/assets/dream/semantic-tree-visible-v1/assets/tree_base_clean.png",
    sourceMaster: "SEMANTIC_TREE_VISIBLE_V1",
    sourceSha256: "dfd661d7e1b171a77afdf75224c453de2d7984ddfe2531df06f2ae11dd187be9",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY"
  },
  abuSleep: {
    assetId: "abu_sleep_breathe_v6_transitional",
    intent: "abu_sleep_breath",
    kind: "actor",
    source: "/assets/abu/v6-designer-sleep/web/abu_sleep_breathe_v6.webp",
    poster: "/assets/abu/v6-designer-sleep/posters/abu_sleep_breathe_v6.png",
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "TRANSITIONAL_FALLBACK"
  },
  abuSeated: {
    assetId: "ABU_01_SEATED_IDLE_LOOP_V3",
    intent: "ghost_orbit",
    kind: "actor",
    source: `${ABU_V12}/abu-01-seated-idle-loop-v3/web/abu_01_seated_idle_loop_v3.webm`,
    poster: `${ABU_V12}/abu-01-seated-idle-loop-v3/posters/abu_01_seated_idle_loop_v3.png`,
    fallback: `${ABU_V12}/abu-01-seated-idle-loop-v3/web/abu_01_seated_idle_loop_v3.webp`,
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "LIBRARY_READY"
  },
  abuWalk: {
    assetId: "ABU_02_CALM_FOLLOW_WALK_LOOP_V1",
    intent: "abu_tree_leap",
    kind: "actor",
    source: `${ABU_V12}/abu-02-calm-follow-walk-loop-v1/web/abu_02_calm_follow_walk_loop_v1.webm`,
    poster: `${ABU_V12}/abu-02-calm-follow-walk-loop-v1/posters/abu_02_calm_follow_walk_loop_v1.png`,
    fallback: `${ABU_V12}/abu-02-calm-follow-walk-loop-v1/web/abu_02_calm_follow_walk_loop_v1.webp`,
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "TRANSITIONAL_FALLBACK"
  },
  dreamEntry: {
    assetId: "ABU_03_DREAM_ENTRY_TRANSITION_V1",
    intent: "fog_gate",
    kind: "video",
    source: "/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_runtime_1080p.mp4",
    poster: "/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_first_frame.png",
    fallback: "/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_last_frame.png",
    sourceMaster: "Create_an_second_cinematic_d.mp4",
    sourceSha256: "ca42b6e7c7ad1236cb3c35676471302d26401ae07fb2fc3550cf15fa2243e7f7",
    sourceTimeRange: [0, 7.75],
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW"
  },
  porchBlue: {
    assetId: "dream_porch_blue_tree_actor_v5",
    intent: "ghost_orbit",
    kind: "actor",
    source: "/assets/dream/porch-v5/tree-blue-actor-v5-08170159.png",
    sourceSha256: "081701597f2f4dfaf422215204f7a607d27fcb9ec05c473a7edf52180923dd85",
    sourceMaster: "blue single-tree scene + background extraction",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW"
  },
  porchJade: {
    assetId: "dream_porch_jade_tree_actor_v5",
    intent: "ghost_orbit",
    kind: "actor",
    source: "/assets/dream/porch-v5/tree-jade-actor-v5-9541d056.png",
    sourceSha256: "9541d056857df81b6f753e99ee68e4113808c47a060bef77b65d9714f69ec6c2",
    sourceMaster: "jade single-tree scene + background extraction",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW"
  },
  porchAmber: {
    assetId: "dream_porch_amber_tree_actor_v5",
    intent: "ghost_orbit",
    kind: "actor",
    source: "/assets/dream/porch-v5/tree-amber-actor-v5-1f98142a.png",
    sourceSha256: "1f98142ad58c8f9b207c780844ab04bd0733d91a01a8c15465359910e1e7c11e",
    sourceMaster: "amber single-tree scene + background extraction",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW"
  },
  porchCleanBackdrop: {
    assetId: "DREAM_PORCH_CLEAN_BACKGROUND_V5",
    intent: "ghost_orbit",
    kind: "image",
    source: "/assets/dream/porch-v5/grove-clean-approved-v5-e97ec6b5.png",
    sourceMaster: "owner-approved forest object-removal edit",
    sourceSha256: "e97ec6b5f856e15371cad08c91609b4585d55eea112ec9b1176ebfb5bd6eca54",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY"
  },
  fixedTreeBud: {
    assetId: "dream_fixed_tree_bud_preseal_v1",
    intent: "fixed_tree",
    kind: "image",
    source: `${DIRECTOR_ROOT}/tree-question-map-full-preseal.png`,
    fallback: `${DIRECTOR_ROOT}/tree-observe-bud-mobile-preseal.jpg`,
    sourceMaster: "1000056879.mp4",
    sourceSha256: "3d2d7e5beeb6705d79ed48178a0deb89b42525beb172a545d5eefe77440b089d",
    sourceTimeRange: [5, 5],
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY"
  },
  fixedTreeFlower: {
    assetId: "dream_fixed_tree_flower_preseal_v1",
    intent: "question_bud",
    kind: "image",
    source: `${DIRECTOR_ROOT}/tree-flower-open-preseal.png`,
    fallback: `${DIRECTOR_ROOT}/tree-flower-open-mobile-preseal.jpg`,
    sourceMaster: "1000056885.mp4",
    sourceSha256: "feb7faf1f08910894e944ebd8ae288afc5f6526b1cd677d4e4f8ade916fde137",
    sourceTimeRange: [5, 7.5],
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY"
  },
  treeEnter: {
    assetId: "dream_tree_entry_transition_v1",
    intent: "fixed_tree",
    kind: "video",
    source: `${DIRECTOR_ROOT}/tree-enter-clean.mp4`,
    fallback: `${DIRECTOR_ROOT}/tree-observe-bud-preseal.png`,
    sourceMaster: "1000056879.mp4",
    sourceSha256: "3d2d7e5beeb6705d79ed48178a0deb89b42525beb172a545d5eefe77440b089d",
    sourceTimeRange: [2.5, 5],
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "LIBRARY_READY"
  },
  fruitForm: {
    assetId: "dream_fog_white_fruit_form_reference_v1",
    intent: "fruit_form",
    kind: "video",
    source: `${DIRECTOR_ROOT}/fruit-reveal-reference-clean.mp4`,
    sourceMaster: "1000056885.mp4",
    sourceSha256: "feb7faf1f08910894e944ebd8ae288afc5f6526b1cd677d4e4f8ade916fde137",
    sourceTimeRange: [7.5, 10],
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "LIBRARY_READY"
  },
  openingTheme: {
    assetId: "abu_mingli_opening_theme_morning_glints_v1",
    intent: "fog_gate",
    kind: "audio",
    source: "/assets/audio/abu/morning-glints-in-the-grove-v1/morning-glints-in-the-grove-opening-v1.opus",
    fallback: "/assets/audio/abu/morning-glints-in-the-grove-v1/morning-glints-in-the-grove-opening-v1.mp3",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY"
  }
};
async function preloadDreamPorchScenes() {
  const sources = [
    DREAM_RUNTIME_ASSETS.porchCleanBackdrop.source,
    DREAM_RUNTIME_ASSETS.porchBlue.source,
    DREAM_RUNTIME_ASSETS.porchJade.source,
    DREAM_RUNTIME_ASSETS.porchAmber.source
  ];
  await Promise.all(sources.map((source) => preloadImage(source)));
}
function preloadImage(source) {
  return new Promise((resolve) => {
    const image = new Image();
    const complete = () => resolve();
    image.addEventListener("load", complete, { once: true });
    image.addEventListener("error", complete, { once: true });
    image.src = source;
    if (image.complete) {
      void image.decode().catch(() => void 0).finally(complete);
    }
  });
}

// apps/product/experience_shell/src/dream_abu_motion_director.ts
function abuMotionFor(role, reducedMotion = false) {
  if (role === "home_sleeping_portal") {
    const asset3 = DREAM_RUNTIME_ASSETS.abuSleep;
    return contract(
      role,
      asset3.assetId,
      reducedMotion ? asset3.poster || asset3.source : asset3.source,
      asset3.poster || asset3.source,
      reducedMotion ? "poster" : "loop",
      "ABU_03/04 canonical character-lock assets are not yet available; v6 is a registered non-semantic visual fallback."
    );
  }
  if (role === "tree_commit_guide") {
    const asset3 = DREAM_RUNTIME_ASSETS.abuWalk;
    return contract(
      role,
      asset3.assetId,
      reducedMotion ? asset3.poster || asset3.source : asset3.source,
      asset3.poster || asset3.source,
      reducedMotion ? "poster" : "loop",
      "ABU_05 leap is missing; the approved calm walk is used only inside the masked transition."
    );
  }
  const asset2 = DREAM_RUNTIME_ASSETS.abuSeated;
  return contract(
    role,
    asset2.assetId,
    reducedMotion ? asset2.poster || asset2.source : asset2.source,
    asset2.poster || asset2.source,
    reducedMotion ? "poster" : "loop",
    ""
  );
}
function contract(role, assetId, source, poster, playback, fallbackReason) {
  return {
    role,
    assetId,
    source,
    poster,
    playback,
    interruptible: true,
    semanticOwner: "ABU_MOTION_DIRECTOR",
    changesBusinessState: false,
    fallbackReason
  };
}
function renderAbuActor(motion, alt, className) {
  if (motion.playback === "poster" || !motion.source.endsWith(".webm")) {
    return `<img class="${escapeAttr2(className)}" src="${escapeAttr2(motion.source)}" alt="${escapeAttr2(alt)}" draggable="false" data-abu-asset-id="${escapeAttr2(motion.assetId)}">`;
  }
  return `<video class="${escapeAttr2(className)}" src="${escapeAttr2(motion.source)}" poster="${escapeAttr2(motion.poster)}" ${motion.playback === "loop" ? "loop " : ""}autoplay muted playsinline preload="metadata" aria-label="${escapeAttr2(alt)}" data-abu-asset-id="${escapeAttr2(motion.assetId)}"></video>`;
}
function escapeAttr2(value) {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

// apps/product/experience_shell/src/dream_home_portal.ts
function renderDreamHomeLifeTree(view) {
  const portalReady = Boolean(view.status?.enabled && view.status.available);
  const motion = abuMotionFor("home_sleeping_portal", prefersReducedMotion());
  const callState = view.returnedWithSeed ? "seed-return" : portalReady ? "portal-ready" : "quiet";
  const visual = view.visualProfile;
  const visualClass = visual ? ` is-${visual.form.replaceAll("_", "-")} is-${visual.material.replaceAll("_", "-")}` : "";
  const visualStyle = visual ? [
    `--tree-scale-x:${finiteNumber(visual.render_tokens.scale_x, 1)}`,
    `--tree-scale-y:${finiteNumber(visual.render_tokens.scale_y, 1)}`,
    `--tree-rotation:${finiteNumber(visual.render_tokens.rotation_deg, 0)}deg`,
    `--tree-hue:${finiteNumber(visual.render_tokens.hue_rotate_deg, 0)}deg`,
    `--tree-saturation:${finiteNumber(visual.render_tokens.saturation, 1)}`,
    `--tree-brightness:${finiteNumber(visual.render_tokens.brightness, 1)}`,
    `--tree-canopy-echo:${finiteNumber(visual.render_tokens.canopy_echo_opacity, 0)}`,
    `--tree-ground-sheen:${finiteNumber(visual.render_tokens.ground_sheen_opacity, 0)}`,
    `--tree-density:${finiteNumber(visual.metrics.density, 0.5)}`,
    `--tree-moisture:${finiteNumber(visual.metrics.moisture, 0.2)}`,
    `--tree-light:${finiteNumber(visual.metrics.light, 0.3)}`
  ].join(";") : "";
  const portalLabel = view.status?.resumable ? "\u8F7B\u89E6\u719F\u7761\u7684\u963F\u5E03\uFF0C\u7EE7\u7EED\u4E0A\u6B21\u7684\u68A6" : "\u8F7B\u89E6\u719F\u7761\u7684\u963F\u5E03\uFF0C\u968F\u4ED6\u8FDB\u5165\u68A6\u5883";
  const abu = portalReady ? `<button
        class="dream-home-abu-portal"
        type="button"
        data-command="enter-dream"
        aria-label="${escapeAttr3(portalLabel)}"
      >
        ${renderAbuActor(motion, "\u963F\u5E03\u5728\u751F\u547D\u6811\u6839\u65C1\u5B89\u9759\u7761\u7740", "dream-home-sleeping-abu")}
        <span class="dream-home-root-call" aria-hidden="true"></span>
      </button>` : `<div class="dream-home-abu-resting" aria-hidden="true">
        <img src="${escapeAttr3(DREAM_RUNTIME_ASSETS.abuSeated.poster || DREAM_RUNTIME_ASSETS.abuSeated.source)}" alt="" draggable="false">
      </div>`;
  const questionNodes = view.questionNodes.length ? view.questionNodes.map(renderQuestionNode).join("") : `
      <button
        type="button"
        class="dream-home-tree-mark is-chart"
        data-product-area="workbench"
        aria-label="\u6253\u5F00\u547D\u76D8\u57FA\u7EBF"
      ><small>\u547D</small><strong>${escapeHtml2(view.pillars || "\u56DB\u67F1\u5F85\u786E\u8BA4")}</strong></button>
      <button
        type="button"
        class="dream-home-tree-mark is-path"
        data-select-anchor="baseline-work-path"
        data-message="${escapeAttr3(view.pathSummary)}"
        aria-label="\u67E5\u770B\u5F53\u524D\u8BA4\u77E5"
      ><small>\u4E8B</small><strong>${escapeHtml2(firstSentence(view.pathSummary))}</strong></button>
      <button
        type="button"
        class="dream-home-tree-mark is-person"
        data-command="toggle-abu"
        aria-label="\u67E5\u770B\u5F53\u524D\u884C\u52A8\u6761\u4EF6"
      ><small>\u4EBA</small><strong>${escapeHtml2(firstSentence(view.condition))}</strong></button>
    `;
  return `<div
    class="life-tree dream-home-life-tree${visualClass}"
    data-dream-home-state="${callState}"
    data-tree-visual-profile="${escapeAttr3(visual?.profile_id || "pending")}"
    data-tree-visual-source="${escapeAttr3(visual?.source || "pending")}"
    style="${escapeAttr3(visualStyle)}"
    aria-label="\u4F60\u7684\u751F\u547D\u6811"
  >
    <img
      class="dream-home-tree-art"
      src="${escapeAttr3(DREAM_RUNTIME_ASSETS.homeTree.source)}"
      alt=""
      draggable="false"
    >
    <img
      class="dream-home-tree-canopy-echo"
      src="${escapeAttr3(DREAM_RUNTIME_ASSETS.homeTree.source)}"
      alt=""
      aria-hidden="true"
      draggable="false"
    >
    <span class="dream-home-tree-ground-sheen" aria-hidden="true"></span>
    <span class="dream-home-canopy-light" aria-hidden="true"></span>
    <div class="dream-home-question-organs" aria-label="\u5F53\u524D\u547D\u5C40\u751F\u957F\u51FA\u7684\u547D\u9898">${questionNodes}</div>
    ${view.returnedWithSeed ? `<span class="dream-home-seed-landing" aria-label="\u4E00\u9897\u77E5\u8BC6\u79CD\u5B50\u56DE\u5230\u4E86\u4F60\u7684\u751F\u547D\u6811\u6839"></span>` : ""}
    ${abu}
  </div>`;
}
function finiteNumber(value, fallback) {
  return Number.isFinite(value) ? value : fallback;
}
function renderQuestionNode(node) {
  const asset2 = {
    "leaf-observation": "leaf_basic_01.png",
    "leaf-timing": "leaf_basic_02.png",
    "trunk-framework": "trunk_backbone_01.png",
    "flower-question": node.status === "explored" ? "flower_open.png" : "flower_bud_closed.png"
  }[node.nodeId] || "leaf_basic_01.png";
  const disabled = !node.questionId || node.status === "locked" || node.status === "unavailable";
  const organVisual = node.nodeId === "root-counterfactual" ? `<i class="dream-home-root-ripple" aria-hidden="true"></i>` : `<img src="/assets/dream/semantic-tree-visible-v1/assets/${asset2}" alt="" aria-hidden="true">`;
  return `<button
    type="button"
    class="dream-home-question-organ is-${escapeAttr3(node.nodeId)} is-${escapeAttr3(node.status)}"
    data-life-tree-question="${escapeAttr3(node.questionId)}"
    data-life-tree-category="${escapeAttr3(node.category)}"
    aria-label="${escapeAttr3(`${node.label}\uFF0C\u5DF2\u63A2\u7D22 ${node.answeredCount}/${node.questionCount}`)}"
    ${disabled ? "disabled" : ""}
  >
    ${organVisual}
    <span>${escapeHtml2(node.label)}</span>
    <small>${node.answeredCount}/${node.questionCount}</small>
  </button>`;
}
function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
function firstSentence(value) {
  return value.split(/[。！？!?]/)[0]?.trim() || value.trim();
}
function escapeHtml2(value) {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
function escapeAttr3(value) {
  return escapeHtml2(value);
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
  const thesis = firstSentence2(fullThesis);
  const pathSummary = steps[steps.length - 1]?.conclusion || "\u5148\u4ECE\u786E\u5B9A\u6027\u7684\u56DB\u67F1\u5F00\u59CB\u3002";
  const condition = claim?.conditions[0] || "\u5F53\u524D\u8FD8\u6CA1\u6709\u8DB3\u591F\u4F9D\u636E\u5199\u4E0B\u6210\u7ACB\u6761\u4EF6\u3002";
  const uncertainty = view.envelope.uncertainty.reasons[0] || "\u5F53\u524D\u6CA1\u6709\u989D\u5916\u672A\u51B3\u9879\u3002";
  return `<div class="deepbeing-shell" data-product-area-current="${escapeAttr4(view.ui.productArea)}">
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
  const thesis = firstSentence2(fullThesis);
  return `
    ${renderWorkspaceNavigation(view)}

    <div class="workbench-surface" data-workspace-current-surface="${escapeAttr4(view.ui.workspaceSurface)}">
      ${view.ui.workspaceSurface === "overview" ? `<section class="opening-band" id="baseline-summary" data-anchor="baseline-summary">
        <div class="opening-copy">
          <p class="section-kicker">\u770B\u89C1\u547D\u5C40 \xB7 \u5F53\u524D\u57FA\u7EBF</p>
          <h1>${escapeHtml3(thesis)}</h1>
          <p class="opening-lede">${escapeHtml3(view.cognition.message)}</p>
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
        </div>` : `<div class="cognition-progress" data-cognition-status="${escapeAttr4(view.cognition.status)}"><i></i><span><strong>\u547D\u76D8\u5148\u5230\uFF0C\u8BA4\u77E5\u968F\u540E</strong><small>\u56DB\u67F1\u5DF2\u786E\u8BA4\uFF1B\u963F\u5E03\u53EA\u4F1A\u8865\u5145\u4F9D\u636E\u5145\u5206\u7684\u90E8\u5206\u3002</small></span></div>`}
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
    <div><p>\u547D\u76D8\u5DE5\u4F5C\u53F0 \xB7 ${escapeHtml3(activeCaseName(view))}</p><h1>${labels[view.ui.workspaceSurface]}</h1><span>${detail}</span></div>
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
        <p class="section-kicker">\u6211\u7684\u751F\u547D\u4E16\u754C \xB7 ${escapeHtml3(activeCaseName(view))}</p>
        <h1>${escapeHtml3(thesis)}</h1>
        <p>${escapeHtml3(firstSentence2(pathSummary))}</p>
        <div class="world-actions">
          <button class="primary-command" type="button" data-command="listen">${view.ui.narrationStatus === "playing" ? "\u6682\u505C\u963F\u5E03" : "\u542C\u963F\u5E03\u8BB2"}</button>
          <button class="text-command" type="button" data-product-area="workbench">\u6253\u5F00\u547D\u76D8</button>
        </div>
        ${renderDreamConsent(view)}
      </div>
      ${renderDreamHomeLifeTree({
    status: view.dreamStatus,
    returnedWithSeed: view.dreamReturnedWithSeed,
    pillars,
    pathSummary,
    condition,
    questionNodes: lifeTreeQuestionNodes(view.realLifeTree),
    visualProfile: view.realLifeTree?.tree_visual_profile || null
  })}
      ${renderLifeTreeQuestionPanel(view)}
    </section>
    <section class="world-ledger" aria-label="\u751F\u547D\u8BB0\u5F55">
      <header><p>\u751F\u547D\u8BB0\u5F55</p><h2>\u547D\u662F\u8D77\u70B9\uFF0C\u73B0\u5B9E\u8BA9\u7406\u89E3\u7EE7\u7EED\u751F\u957F</h2></header>
      <div class="world-ledger-flow">
        <button type="button" data-product-area="workbench"><span>\u547D\u76D8\u57FA\u7EBF</span><strong>${escapeHtml3(pillars || "\u7B49\u5F85\u5EFA\u6863")}</strong><small>${escapeHtml3(view.envelope.source.life_case_version || "\u547D\u76D8\u4E8B\u5B9E")}</small></button>
        <button type="button" data-select-anchor="baseline-work-path" data-message="${escapeAttr4(fullThesis)}"><span>\u5F53\u524D\u8BA4\u77E5</span><strong>${escapeHtml3(thesis)}</strong><small>\u6765\u81EA\u6B63\u5F0F LifeCase</small></button>
        <button type="button" data-command="toggle-abu"><span>\u7EE7\u7EED\u89C2\u5BDF</span><strong>${escapeHtml3(firstSentence2(uncertainty))}</strong><small>\u4E0E\u963F\u5E03\u4E00\u8D77\u9A8C\u8BC1</small></button>
      </div>
    </section>
  </div>`;
}
function lifeTreeQuestionNodes(tree) {
  if (!tree) return [];
  const answered = new Set(
    tree.explorations.flatMap((item) => Object.keys(item.responses))
  );
  const questions = new Map(tree.questions.map((item) => [item.instance_id, item]));
  const labels = {
    "leaf-observation": "\u7ED3\u6784\u53F6",
    "leaf-timing": "\u65F6\u5E8F\u53F6",
    "trunk-framework": "\u4E3B\u8109",
    "root-counterfactual": "\u6839\u90E8",
    "flower-question": "\u751F\u547D\u95EE\u9898\u82B1"
  };
  return tree.tree_scene.nodes.flatMap((node) => {
    const available = node.question_refs.flatMap((ref) => {
      const question = questions.get(ref);
      return question ? [question] : [];
    });
    if (!available.length) return [];
    const selected = available.find((item) => !answered.has(item.instance_id)) || available[0];
    return [{
      nodeId: node.node_id,
      questionId: selected.instance_id,
      category: selected.category,
      label: labels[node.node_id] || "\u547D\u9898",
      status: node.status,
      answeredCount: available.filter((item) => answered.has(item.instance_id)).length,
      questionCount: available.length
    }];
  });
}
function renderLifeTreeQuestionPanel(view) {
  if (view.realLifeTreeLoading) {
    return `<section class="life-tree-question-panel is-loading"><i></i><span>\u6B63\u5728\u4ECE\u5F53\u524D LifeCase \u751F\u957F\u547D\u9898</span></section>`;
  }
  if (view.realLifeTreeError) {
    return `<section class="life-tree-question-panel is-empty"><strong>\u547D\u9898\u6682\u672A\u5F00\u653E</strong><span>${escapeHtml3(view.realLifeTreeError)}</span></section>`;
  }
  const tree = view.realLifeTree;
  if (!tree) return "";
  const question = tree.questions.find(
    (item) => item.instance_id === view.selectedLifeTreeQuestionId
  );
  if (!question) {
    return `<section class="life-tree-question-panel is-invitation">
      <p>\u5F53\u524D LifeCase \xB7 ${tree.question_count} \u6735\u73B0\u5B9E\u89C2\u5BDF\u82B1</p>
      <strong>${escapeHtml3(tree.empty_state || "\u89E6\u78B0\u6709\u5FAE\u5149\u7684\u95EE\u9898\u82B1\uFF0C\u9009\u62E9\u4E00\u4EF6\u672A\u6765\u53EF\u4EE5\u88AB\u73B0\u5B9E\u6838\u9A8C\u7684\u4E8B\u3002")}</strong>
      <span>\u547D\u76D8\u53EA\u51B3\u5B9A\u4E3A\u4EC0\u4E48\u503C\u5F97\u89C2\u5BDF\uFF0C\u4E0D\u9884\u544A\u7ED3\u679C\uFF1B\u5C01\u5B58\u524D\u4E8B\u5B9E\u4E0D\u8BA1\u4F5C\u672A\u6765\u8BC1\u636E\u3002</span>
    </section>`;
  }
  const exploration = tree.explorations.find(
    (item) => Object.hasOwn(item.responses, question.instance_id)
  );
  const selectedOption = exploration?.responses[question.instance_id] || view.selectedLifeTreeOptionId;
  const evidence = [
    ...question.work_path_candidate_refs.map((item) => `\u89C2\u5BDF\u7F18\u7531 ${compactRef(item)}`)
  ];
  return `<section class="life-tree-question-panel${exploration ? " is-explored" : ""}" aria-label="\u5F53\u524D\u751F\u547D\u6811\u547D\u9898">
    <header>
      <p>${escapeHtml3(lifeTreeCategoryLabel(question.category))} \xB7 ${escapeHtml3(lifeDomainLabel(question.life_domain))}</p>
      <span>${exploration ? "\u89C2\u5BDF\u5DF2\u5C01\u5B58" : "\u7B49\u5F85\u4F60\u7684\u5224\u65AD"}</span>
    </header>
    <h2>${escapeHtml3(question.prompt)}</h2>
    <p class="life-tree-question-why"><strong>\u4E3A\u4EC0\u4E48\u51FA\u73B0</strong>${escapeHtml3(question.why_this_question)}</p>
    <p class="life-tree-question-window"><strong>\u89C2\u5BDF\u7A97\u53E3</strong>${escapeHtml3(question.observation_window)}</p>
    <div class="life-tree-question-evidence" aria-label="\u547D\u9898\u4F9D\u636E">
      ${(evidence.length ? evidence : ["\u5F53\u524D\u547D\u76D8\u51BB\u7ED3\u6295\u5F71"]).map((item) => `<code>${escapeHtml3(item)}</code>`).join("")}
    </div>
    <div class="life-tree-future-evidence" aria-label="\u672A\u6765\u63ED\u76F2\u9700\u8981\u7684\u8BC1\u636E">
      <strong>\u672A\u6765\u51ED\u4EC0\u4E48\u56DE\u770B</strong>
      ${question.future_evidence_requirements.map((item) => `<span>${escapeHtml3(item)}</span>`).join("")}
    </div>
    <div class="life-tree-question-options" role="radiogroup" aria-label="\u9009\u62E9\u4E00\u79CD\u89C2\u5BDF">
      ${question.options.map((option) => `<button
        type="button"
        data-life-tree-option="${escapeAttr4(option.option_id)}"
        aria-pressed="${selectedOption === option.option_id}"
        class="${selectedOption === option.option_id ? "is-selected" : ""}"
        ${exploration ? "disabled" : ""}
      >${escapeHtml3(option.label_template)}</button>`).join("")}
    </div>
    <footer>
      <span>${exploration ? "\u8FD9\u6B21\u73B0\u5B9E\u89C2\u5BDF\u5DF2\u6301\u4E45\u4FDD\u5B58\uFF1B\u7B49\u5F85\u540E\u7EED\u8BC1\u636E\uFF0CLifeCase \u672A\u88AB\u6539\u5199\u3002" : "\u4E09\u4E2A\u65B9\u5411\u90FD\u5141\u8BB8\u53D1\u751F\uFF1B\u5F53\u524D\u7ED3\u6784\u5019\u9009\u4E0D\u4F1A\u66FF\u4F60\u9009\u62E9\u7B54\u6848\u3002"}</span>
      ${exploration ? `<strong>\u72B6\u6001\uFF1A\u7B49\u5F85\u73B0\u5B9E\u56DE\u770B</strong>` : `<button type="button" data-life-tree-submit ${selectedOption && !view.lifeTreeAnswerSaving ? "" : "disabled"}>${view.lifeTreeAnswerSaving ? "\u6B63\u5728\u5C01\u5B58" : "\u5C01\u5B58\u8FD9\u6B21\u89C2\u5BDF"}</button>`}
    </footer>
  </section>`;
}
function renderRelationWorkControls(view) {
  const lab = view.realMingliLab;
  return `<section class="canonical-relation-work" aria-label="\u771F\u5B9E\u5173\u7CFB\u4E0E\u5019\u9009\u505A\u529F">
    <header class="relation-work-toolbar">
      <nav aria-label="\u5173\u7CFB\u7814\u7A76\u5C42">
        ${relationModeButton("facts", "\u4E8B\u5B9E\u5173\u7CFB", view.relationLabMode)}
        ${relationModeButton("candidates", "\u5019\u9009\u505A\u529F", view.relationLabMode)}
        ${relationModeButton("professional", "\u4E13\u4E1A\u51C6\u5165", view.relationLabMode)}
      </nav>
      <button type="button" data-relation-restore-natal>\u6062\u590D\u539F\u5C40</button>
    </header>
    ${view.realMingliLabLoading ? `<div class="relation-work-loading">\u6B63\u5728\u8BFB\u53D6\u5F53\u524D LifeCase \u7684\u5173\u7CFB\u6295\u5F71</div>` : view.realMingliLabError ? `<div class="relation-work-empty">${escapeHtml3(view.realMingliLabError)}</div>` : lab ? renderRelationWorkBody(view, lab) : `<div class="relation-work-empty">\u5F53\u524D\u5173\u7CFB\u6295\u5F71\u5C1A\u672A\u5C31\u7EEA\u3002</div>`}
  </section>`;
}
function renderRelationWorkBody(view, lab) {
  const projection = lab.relation_work;
  if (view.relationLabMode === "professional") {
    if (!projection.professionally_resolved_view.length) {
      return `<div class="relation-work-professional-empty">
        <strong>\u5F53\u524D\u5C1A\u65E0\u901A\u8FC7\u4E13\u4E1A\u51C6\u5165\u7684\u6709\u6548\u505A\u529F\u8DEF\u5F84\u3002</strong>
        <span>\u4E8B\u5B9E\u5173\u7CFB\u4E0E\u7ED3\u6784\u5019\u9009\u4ECD\u53EF\u5728\u524D\u4E24\u5C42\u67E5\u770B\uFF1B\u8FD9\u91CC\u4E0D\u4F1A\u4ECE\u90BB\u63A5\u3001\u7EBF\u6761\u6216\u5019\u9009\u6570\u91CF\u731C\u6D4B\u4E13\u4E1A\u4E3B\u7EBF\u3002</span>
      </div>`;
    }
    return `<div class="relation-work-professional-list">${projection.professionally_resolved_view.map((item) => `
      <article><strong>${escapeHtml3(item.resolved_effect_atoms.join(" \xB7 "))}</strong><code>${escapeHtml3(compactRef(item.effect_resolution_ref))}</code></article>
    `).join("")}</div>`;
  }
  if (view.relationLabMode === "facts") {
    return `<div class="relation-work-facts">${projection.factual_view.slice(0, 8).map((fact) => `
        <article>
          <strong>${escapeHtml3(fact.participant_coordinates.map(relationCoordinateLabel).join(" \u2192 "))}</strong>
          <span>${escapeHtml3(relationFamilyLabel(fact.relation_family))} \xB7 ${escapeHtml3(relationActivationLabel(fact.activation_state))}</span>
          <small>${fact.effect_status === "professionally_resolved" ? "\u4F5C\u7528\u5DF2\u83B7\u51C6" : "\u5173\u7CFB\u4E8B\u5B9E\u6210\u7ACB\uFF0C\u4F5C\u7528\u5F85\u5B9A"}</small>
        </article>
      `).join("")}</div>
      ${renderLabLearningQuestions(lab.learning_questions)}`;
  }
  const paths = projection.candidate_path_view;
  const selected = paths.find(
    (item) => item.work_path_candidate_ref === view.selectedRelationPathRef
  ) || paths[0];
  return `<div class="relation-work-candidates">
    <nav aria-label="\u5F53\u524D\u76D8\u652F\u6301\u7684\u5019\u9009\u505A\u529F">
      ${paths.map((path) => `<button
        type="button"
        data-relation-path="${escapeAttr4(path.work_path_candidate_ref)}"
        class="${path.work_path_candidate_ref === selected?.work_path_candidate_ref ? "is-selected" : ""}"
      ><strong>${escapeHtml3(path.label)}</strong><span>${path.ordered_fact_revision_refs.length} \u6BB5\u4E8B\u5B9E \xB7 ${path.blocker_types.length} \u9879\u5F85\u5B9A</span></button>`).join("")}
    </nav>
    ${selected ? renderWorkPathDetail(selected) : `<div class="relation-work-empty">\u5F53\u524D LifeCase \u6CA1\u6709\u6EE1\u8DB3\u7ED3\u6784\u8BC1\u636E\u7684\u5019\u9009\u505A\u529F\u3002</div>`}
  </div>`;
}
function renderLabLearningQuestions(questions) {
  if (!questions.length) return "";
  return `<section class="relation-work-learning" aria-label="\u7ED3\u6784\u5C0F\u8BFE">
    <header>
      <p>\u7ED3\u6784\u5C0F\u8BFE</p>
      <strong>\u8FD9\u4E9B\u95EE\u9898\u5C5E\u4E8E Mingli Lab\uFF0C\u4E0D\u8BA1\u5165\u751F\u547D\u6811\u95EE\u9898\u82B1</strong>
    </header>
    <div>
      ${questions.map((question) => `<article>
        <span>${escapeHtml3(lifeTreeCategoryLabel(question.category))}</span>
        <strong>${escapeHtml3(question.prompt)}</strong>
        <small>${escapeHtml3(question.why_this_question)}</small>
      </article>`).join("")}
    </div>
  </section>`;
}
function renderWorkPathDetail(path) {
  return `<article class="relation-work-path-detail">
    <header><p>\u7ED3\u6784\u5019\u9009</p><h2>${escapeHtml3(path.label)}</h2></header>
    <div class="relation-work-statuses">
      <span>\u7ED3\u6784\u5019\u9009</span>
      <span>\u4F5C\u7528\u5F85\u5B9A</span>
      <span>\u5BB9\u91CF\u5F85\u5B9A</span>
      <span>\u53EF\u7528\u6027\u5F85\u5B9A</span>
      <span>\u4E13\u4E1A\u51C6\u5165\u5F85\u5B9A</span>
    </div>
    <dl>
      <dt>\u53C2\u4E0E\u5750\u6807</dt><dd>${escapeHtml3(path.participant_coordinates.map(relationCoordinateLabel).join(" \u2192 "))}</dd>
      <dt>\u7ADE\u4E89\u5171\u4EAB</dt><dd>${escapeHtml3(path.shared_resource_refs.length ? path.shared_resource_refs.map(compactRef).join("\u3001") : "\u5F53\u524D\u672A\u53D1\u73B0\u5171\u4EAB\u53C2\u4E0E\u8005")}</dd>
      <dt>\u74F6\u9888</dt><dd>${escapeHtml3(path.bottleneck_node_refs.length ? path.bottleneck_node_refs.map(compactRef).join("\u3001") : "\u627F\u8F7D\u4E0E\u6548\u679C\u8BC1\u636E\u4ECD\u5F85\u6838\u9A8C")}</dd>
      <dt>\u963B\u65AD</dt><dd>${escapeHtml3(path.blocker_types.length ? path.blocker_types.map(workPathBlockerLabel).join("\uFF1B") : "\u65E0\u7ED3\u6784\u963B\u65AD")}</dd>
    </dl>
    <small>\u5019\u9009\u7EBF\u53EA\u8868\u793A\u5F53\u524D\u8BC1\u636E\u4E0B\u7684\u7ED3\u6784\u8FDE\u7EED\u6027\uFF0C\u4E0D\u8868\u793A\u6709\u6548\u505A\u529F\u3001\u4E3B\u529F\u6216\u4E13\u4E1A\u6392\u540D\u3002</small>
  </article>`;
}
function relationWorkCanvasOverlay(view) {
  const projection = view.realMingliLab?.relation_work;
  if (!projection || view.relationLabMode === "professional") return [];
  let facts = projection.factual_view.slice(0, 8);
  let kind = "fact";
  if (view.relationLabMode === "candidates") {
    const selected = projection.candidate_path_view.find(
      (item) => item.work_path_candidate_ref === view.selectedRelationPathRef
    ) || projection.candidate_path_view[0];
    if (!selected) return [];
    const refs = new Set(selected.ordered_fact_revision_refs);
    facts = projection.factual_view.filter((item) => refs.has(item.fact_revision_ref));
    kind = "candidate";
  }
  return facts.flatMap((fact) => {
    const source = fact.participant_coordinates[0];
    const target = fact.participant_coordinates[1];
    if (!source || !target) return [];
    return [{
      relation_ref: fact.fact_revision_ref,
      label: relationFamilyLabel(fact.relation_family),
      source_node_ref: source.node_ref,
      target_node_ref: target.node_ref,
      formal: false,
      kind,
      directionality: fact.directionality
    }];
  });
}
function relationModeButton(mode, label, current) {
  return `<button type="button" data-relation-lab-mode="${mode}" aria-pressed="${mode === current}" class="${mode === current ? "is-active" : ""}">${label}</button>`;
}
function lifeTreeCategoryLabel(category) {
  return {
    factual_observation: "\u7ED3\u6784\u53F6",
    temporal_change: "\u65F6\u5E8F\u53F6",
    candidate_comparison: "\u4E3B\u8109",
    counterfactual: "\u6839\u90E8\u8FFD\u95EE",
    discriminating: "\u95EE\u9898\u82B1",
    life_observation: "\u73B0\u5B9E\u89C2\u5BDF\u82B1"
  }[category] || "\u751F\u547D\u547D\u9898";
}
function lifeDomainLabel(value) {
  return {
    career: "\u4E8B\u4E1A\u884C\u52A8",
    career_wealth: "\u4E8B\u4E1A\u4E0E\u6536\u5165",
    relationship: "\u5173\u7CFB\u89C2\u5BDF",
    mobility: "\u8FC1\u79FB\u4E0E\u53D8\u5316",
    self_structure: "\u81EA\u6211\u7ED3\u6784"
  }[value] || "\u751F\u547D\u89C2\u5BDF";
}
function relationFamilyLabel(family) {
  return {
    generates: "\u751F",
    controls: "\u514B",
    same_element_support: "\u540C\u6C14\u652F\u6301",
    clashes: "\u51B2",
    combines: "\u5408",
    harmonizes: "\u5408",
    harms: "\u5BB3",
    punishes: "\u5211"
  }[family] || family;
}
function relationActivationLabel(value) {
  return {
    natal_present: "\u539F\u5C40\u5B58\u5728",
    timing_present: "\u65F6\u8FD0\u51FA\u73B0",
    activated: "\u5DF2\u6FC0\u6D3B",
    latent: "\u6F5C\u5728"
  }[value] || value;
}
function workPathBlockerLabel(value) {
  return {
    missing_effect_resolution: "\u7F3A\u5C11\u4F5C\u7528\u5224\u5B9A",
    capacity_unresolved: "\u5BB9\u91CF\u5F85\u5B9A",
    usability_unresolved: "\u53EF\u7528\u6027\u5F85\u5B9A",
    structural_break: "\u7ED3\u6784\u65AD\u88C2",
    competition_unresolved: "\u7ADE\u4E89\u8DEF\u5F84\u5F85\u5206\u8FA8",
    timing_unresolved: "\u65F6\u5E8F\u5F85\u5B9A"
  }[value] || value;
}
function slotLabel(value) {
  return {
    year: "\u5E74\u67F1",
    month: "\u6708\u67F1",
    day: "\u65E5\u67F1",
    hour: "\u65F6\u67F1",
    luck: "\u5927\u8FD0"
  }[value] || `${value}\u6D41\u5E74`;
}
function relationCoordinateLabel(coordinate) {
  const level = {
    stem: "\u5929\u5E72",
    branch: "\u5730\u652F",
    hidden_stem: "\u85CF\u5E72"
  }[coordinate.level] || coordinate.level;
  return `${slotLabel(coordinate.slot)}${level}${coordinate.component}`;
}
function compactRef(value) {
  if (value.length <= 22) return value;
  return `${value.slice(0, 10)}\u2026${value.slice(-8)}`;
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
  const relationWork = view.realMingliLab?.relation_work;
  const factCount = relationWork?.factual_view.length ?? stage.spec.relations.filter((item) => item.relation_state === "potential").length;
  const sourceCount = new Set(
    relationWork?.factual_view.flatMap((item) => item.evidence_refs) ?? stage.spec.relations.flatMap((item) => item.trace.source_refs)
  ).size;
  const hiddenCount = stage.spec.nodes.filter((item) => item.node_type.includes("hidden")).length;
  const candidateCount = relationWork?.candidate_path_view.length ?? 0;
  return `<div class="mingli-lab">
    <header class="lab-header">
      <div><p>Mingli Lab \xB7 ${escapeHtml3(activeCaseName(view))}</p><h1>\u540C\u4E00 LifeCase \u7684\u516D\u67F1\u4E8B\u5B9E\u4E0E\u5019\u9009\u505A\u529F</h1><span>\u4E8B\u5B9E\u3001\u7ED3\u6784\u5019\u9009\u548C\u4E13\u4E1A\u51C6\u5165\u5206\u5C42\u5448\u73B0\uFF1B\u6B63\u5F0F Case \u4E0D\u5728\u8FD9\u91CC\u88AB\u6539\u5199\u3002</span></div>
      <code>${escapeHtml3((relationWork?.foundation_content_hash || view.workspace?.state.scene_source_hash || view.envelope.source.source_hash).slice(0, 18))}</code>
    </header>
    <div class="lab-evidence-rail" aria-label="\u5F53\u524D\u7814\u7A76\u8303\u56F4">
      <span><small>\u5173\u7CFB\u4E8B\u5B9E</small><strong>${factCount}</strong></span>
      <span><small>\u85CF\u5E72\u8282\u70B9</small><strong>${hiddenCount}</strong></span>
      <span><small>\u5019\u9009\u505A\u529F</small><strong>${candidateCount}</strong></span>
      <span><small>\u8BC1\u636E\u5F15\u7528</small><strong>${sourceCount}</strong></span>
    </div>
    ${renderRelationWorkControls(view)}
    <section class="lab-canvas"><p class="lab-lens-label">\u6B63\u5F0F OneCanvas \xB7 \u516D\u67F1\u5341\u4E8C\u8282\u70B9</p>${renderReadOnlyCanvas(
    view.canvas,
    view.ui,
    view.canvasContext,
    view.cognition.status === "preparing",
    relationWorkCanvasOverlay(view)
  )}</section>
  </div>`;
}
function renderProductSidebar(view) {
  return `<aside class="product-sidebar">
    <a class="brand" href="/experience" aria-label="DeepBeing \u9996\u9875"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi Life Intelligence"><span>DeepBeing</span></a>
    ${renderProductNavigation(view, "sidebar")}
    <div class="sidebar-context">${renderProfileSelector(view.cases, view.activeProfileId)}<small>${escapeHtml3(view.envelope.source.life_case_version || "\u547D\u76D8\u4E8B\u5B9E")}</small></div>
    <div class="sidebar-account"><span>${escapeHtml3(view.accountName)}</span><div class="sidebar-account-actions">${renderOpeningMusicControl()}<button type="button" data-command="manage-profiles">\u6863\u6848</button></div></div>
  </aside>`;
}
function renderMobileHeader(view) {
  const labels = { world: "\u6211\u7684\u751F\u547D\u4E16\u754C", workbench: "\u547D\u76D8\u5DE5\u4F5C\u53F0", lab: "Mingli Lab" };
  return `<header class="mobile-header"><a href="/experience"><img src="/assets/deepbazi_symbol.png" alt="DeepBazi"></a><strong>${labels[view.ui.productArea]}</strong><div class="mobile-header-actions">${renderProfileSelector(view.cases, view.activeProfileId)}${renderOpeningMusicControl("mobile")}<button type="button" data-command="manage-profiles" aria-label="\u7BA1\u7406\u6863\u6848" title="\u7BA1\u7406\u6863\u6848">\u6863</button></div></header>`;
}
function renderOpeningMusicControl(placement = "sidebar") {
  return `<button class="opening-music-control is-${placement}" type="button" data-command="toggle-opening-music" data-opening-music-control data-music-state="armed" aria-pressed="false" aria-label="\u64AD\u653E\u5F00\u573A\u97F3\u4E50\uFF1B\u9996\u6B21\u64CD\u4F5C\u540E\u4F1A\u81EA\u52A8\u5F00\u59CB" title="\u64AD\u653E\u5F00\u573A\u97F3\u4E50\uFF1B\u9996\u6B21\u64CD\u4F5C\u540E\u4F1A\u81EA\u52A8\u5F00\u59CB"><i aria-hidden="true">\u266B</i></button>`;
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
    <header><p>\u963F\u5E03\u8BB2\u89E3</p><h1>${escapeHtml3(thesis)}</h1><span>${segments.length ? "\u4ECE\u6574\u76D8\u91CD\u5FC3\u5F00\u59CB\uFF0C\u6CBF\u56DB\u67F1\u3001\u8DEF\u5F84\u3001\u6761\u4EF6\u4E0E\u672A\u51B3\u9010\u6BB5\u5C55\u5F00\u3002" : "\u6587\u5B57\u5DF2\u7ECF\u53EF\u8BFB\uFF1B\u70B9\u64AD\u653E\u540E\u624D\u51C6\u5907\u58F0\u97F3\uFF0C\u4E0D\u963B\u585E\u5F53\u524D\u9875\u9762\u3002"}</span></header>
    <div class="narration-workspace-actions">
      <button class="primary-command" type="button" data-command="listen">${view.ui.narrationStatus === "playing" ? "\u6682\u505C" : "\u4ECE\u5934\u542C"}</button>
      ${view.ui.narrationStatus !== "idle" ? '<button class="text-command" type="button" data-command="stop">\u505C\u6B62</button>' : ""}
    </div>
    ${segments.length ? `<ol>${segments.map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><small>${String(index + 1).padStart(2, "0")}</small><span><strong>${escapeHtml3(item.title)}</strong><em>${escapeHtml3(item.text)}</em></span><b aria-hidden="true">\u25B6</b></button></li>`).join("")}</ol>` : `<div class="narration-pending"><i></i><p>${escapeHtml3(view.cognition.message)}</p></div>`}
  </section>`;
}
function renderDeterministicCanvasSkeleton(envelope2, cognition2) {
  const pillars = envelope2.allowed_chart_facts.filter((item) => item.fact_type === "pillar");
  return `<div class="deterministic-canvas-skeleton">
    <header><span>\u786E\u5B9A\u6027\u547D\u76D8</span><strong>\u56DB\u67F1\u5148\u663E\u793A\uFF0C\u5173\u7CFB\u6309\u6B63\u5F0F\u6765\u6E90\u9010\u6B65\u8FDB\u5165</strong></header>
    <div class="skeleton-pillar-rail">${pillars.map((pillar) => `<article>
      <small>${escapeHtml3(pillar.pillar_label)}</small>
      <b class="element-${escapeAttr4(pillar.stem_element)}" data-polarity="${escapeAttr4(pillar.stem_polarity)}">${escapeHtml3(pillar.stem)}</b>
      <i></i>
      <b class="element-${escapeAttr4(pillar.branch_element)}" data-polarity="${escapeAttr4(pillar.branch_polarity)}">${escapeHtml3(pillar.branch)}</b>
      <em>${escapeHtml3(pillar.visible_ten_god || "\u547D\u76D8\u4E8B\u5B9E")}</em>
    </article>`).join("")}</div>
    <p><i></i>${escapeHtml3(cognition2.message)}</p>
  </div>`;
}
function renderReadOnlyCanvas(canvas2, ui2, context, pathTaskRunning, relationWorkOverlay = []) {
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
  return `<div class="temporal-viewer" data-canvas-stage-root="${escapeAttr4(ui2.canvasStage)}">
    <div class="temporal-toolbar">
      <div class="stage-switch" role="tablist" aria-label="\u67E5\u770B\u65F6\u95F4\u9636\u6BB5">
        ${canvas2.stage_order.map((item, index) => {
    const projection = canvas2.stages[item];
    return `<button type="button" role="tab" data-canvas-stage="${item}" aria-selected="${item === ui2.canvasStage}" class="${item === ui2.canvasStage ? "active" : ""}">
            <small>0${index + 1}</small><span>${escapeHtml3(projection.title)}</span>
          </button>`;
  }).join("")}
      </div>
      <div class="temporal-status">
        <span>${escapeHtml3(ui2.canvasStage === "natal" ? "\u539F\u5C40\u57FA\u7EBF" : ui2.canvasStage === "luck" ? range : `${canvas2.source.analysis_year || "\u5F53\u524D"}\u5E74`)}</span>
        <strong>${escapeHtml3(stage.summary)}</strong>
      </div>
    </div>

    <div class="canvas-lens-controls">
      <div class="layer-switch" role="tablist" aria-label="\u547D\u5C40\u89C2\u5BDF\u955C\u5934">
        ${displayLayers.map((item) => `<button type="button" role="tab" data-canvas-layer="${escapeAttr4(item.layer_id)}" aria-selected="${item.layer_id === layer?.layer_id}" class="${item.layer_id === layer?.layer_id ? "active" : ""}"${item.available || item.layer_id === "overview" || item.layer_id === "work_path" ? "" : " disabled"}>
          <span>${escapeHtml3(item.label)}</span>${item.count > 0 ? `<small>${item.count}</small>` : ""}
        </button>`).join("")}
      </div>
      <div class="visibility-switch" role="tablist" aria-label="\u5173\u7CFB\u62AB\u9732\u5C42">
        ${allowedVisibility.map((item) => `<button type="button" role="tab" data-canvas-visibility="${item}" aria-selected="${item === visibility}" class="${item === visibility ? "active" : ""}">${visibilityLabel(item)}</button>`).join("")}
      </div>
    </div>

    <div class="canvas-board" data-layer="${escapeAttr4(layer?.layer_id || "")}" data-visibility="${escapeAttr4(visibility)}">
      <div class="six-pillar-scroll">
        ${renderCanonicalCanvasScene(
    stage.scene_slots,
    stage.spec.nodes,
    activeRelations,
    activePaths,
    selected,
    visibility === "lab_audit",
    relationWorkOverlay,
    new Set(relationWorkOverlay.flatMap((item) => [
      item.source_node_ref,
      item.target_node_ref
    ]))
  )}
      </div>
      <p class="layer-caption"><strong>${escapeHtml3(layer?.label || "\u5F53\u524D\u56FE\u5C42")}</strong>${escapeHtml3(layer?.description || "\u5F53\u524D\u6CA1\u6709\u53EF\u663E\u793A\u7684\u5173\u7CFB\u3002")}</p>
    </div>

    <div class="canvas-reading-grid">
      ${renderCanvasChanges(stage.change_groups, selected, ui2.canvasStage)}
      ${renderCanvasInspector(stage.spec, selected, context, ui2.canvasContextStatus)}
    </div>

    <div class="canvas-boundary ${canvas2.path_availability.status === "available" ? "is-ready" : "is-limited"}">
      <span>${canvas2.path_availability.status === "available" ? "\u6B63\u5F0F\u8DEF\u5F84\u5DF2\u786E\u8BA4" : pathTaskRunning ? "\u6B63\u5F0F\u4E3B\u8DEF\u5F84\u6B63\u5728\u5F62\u6210" : "\u5F53\u524D\u6682\u65E0\u5DF2\u786E\u8BA4\u4E3B\u8DEF\u5F84"}</span>
      <p>${escapeHtml3(
    canvas2.path_availability.status !== "available" && pathTaskRunning ? "\u540E\u53F0\u6B63\u5728\u5F62\u6210\u6700\u5C0F\u6574\u76D8\u4E3B\u7EBF\uFF0C\u5DF2\u7ECF\u786E\u8BA4\u7684\u7ED3\u6784\u4F1A\u81EA\u52A8\u51FA\u73B0\u3002" : canvas2.path_availability.message
  )}</p>
      ${canvas2.path_availability.disclosure_level === "audit" && canvas2.path_availability.diagnostic ? `<small>${escapeHtml3(pathDiagnosticLabel(canvas2.path_availability.diagnostic.rejection_reason))}</small>` : ""}
      ${visibility === "lab_audit" && canvas2.path_availability.diagnostic ? `<code>${escapeHtml3(canvas2.path_availability.diagnostic.rejection_reason)}</code>` : ""}
    </div>
  </div>`;
}
function renderDreamVerificationCanvas(canvas2, verification) {
  const stageName = verification.binding.target_stage;
  const stage = canvas2.stages[stageName] || canvas2.stages[canvas2.default_stage];
  const focused = verification.state === "focused";
  const selected = focused ? verification.target_object_ref : "";
  const relations = focused && verification.reveal_kind === "relation" ? stage.spec.relations.filter((item) => item.relation_ref === selected) : [];
  const paths = focused && verification.reveal_kind === "path" ? stage.spec.paths.filter((item) => item.path_ref === selected) : [];
  const statement = focused ? verification.authorized_statement : "\u5F53\u524D\u6682\u65E0\u5DF2\u786E\u8BA4\u4E3B\u8DEF\u5F84";
  return `<section class="dream-verification-canvas" data-verification-state="${escapeAttr4(verification.state)}" data-verification-lens="${escapeAttr4(verification.binding.target_lens)}">
    <p class="sr-only">${escapeHtml3(focused ? `${verification.verification_copy}${statement}` : statement)}</p>
    <div class="dream-verification-geometry" inert>
      ${renderCanonicalCanvasScene(
    stage.scene_slots,
    stage.spec.nodes,
    relations,
    paths,
    selected,
    verification.binding.target_lens === "roots_reveal"
  )}
    </div>
    <div class="dream-verification-copy" aria-hidden="true">
      ${focused ? `<span>${escapeHtml3(verification.verification_copy)}</span>` : ""}
      <strong>${escapeHtml3(statement)}</strong>
    </div>
  </section>`;
}
function renderDreamGameCanvas(canvas2, lens, candidateNodeRefs = [], candidateRelations = []) {
  const stage = canvas2.stages.natal || canvas2.stages[canvas2.default_stage];
  const layer = stage.layers.find((item) => item.layer_id === lens) || stage.layers.find((item) => item.layer_id === "overview") || stage.layers[0];
  const formalRelationRefs = new Set(layer?.formal_relation_refs || []);
  const formalPathRefs = new Set(layer?.formal_path_refs || []);
  const relations = stage.spec.relations.filter((item) => formalRelationRefs.has(item.relation_ref));
  const paths = stage.spec.paths.filter((item) => formalPathRefs.has(item.path_ref));
  return `<section class="dream-game-onecanvas" data-dream-game-lens="${escapeAttr4(lens)}">
    <p class="sr-only">\u51BB\u7ED3\u4E8E\u95EE\u9898\u53D1\u751F\u524D\u7684\u540C\u6E90\u547D\u76D8\u3002\u73A9\u5BB6\u5019\u9009\u89C2\u5BDF\u4E0D\u4F1A\u5199\u5165\u6B63\u5F0F\u547D\u7406\u4E8B\u5B9E\u3002</p>
    <div class="six-pillar-scroll">
      ${renderCanonicalCanvasScene(
    stage.scene_slots,
    stage.spec.nodes,
    relations,
    paths,
    candidateNodeRefs[0] || "",
    lens === "roots_reveal",
    candidateRelations.filter((item) => !item.formal),
    new Set(candidateNodeRefs)
  )}
    </div>
    <p class="dream-game-canvas-caption"><strong>${escapeHtml3(layer?.label || "\u603B\u89C8")}</strong>${escapeHtml3(layer?.description || "\u53EA\u663E\u793A\u51BB\u7ED3\u6295\u5F71\u4E2D\u5DF2\u6388\u6743\u7684\u7ED3\u6784\u3002")}</p>
    ${candidateRelations.some((item) => !item.formal) ? `<p class="dream-game-candidate-key"><i aria-hidden="true"></i>\u73A9\u5BB6\u5019\u9009\u5047\u8BF4 \xB7 \u975E\u6B63\u5F0F PathAssertion</p>` : ""}
  </section>`;
}
function renderCanonicalCanvasScene(slots, nodes, relations, paths, selected, showHiddenStems, candidateRelations = [], candidateNodeRefs = /* @__PURE__ */ new Set()) {
  const nodesByRef = new Map(nodes.map((item) => [item.node_ref, item]));
  const anchors = canvasAnchorRegistry(slots, nodes);
  const pathRelationRefs = new Set(paths.flatMap((item) => item.relation_refs));
  const requiredNodeRefs = /* @__PURE__ */ new Set([
    ...relations.flatMap((item) => [
      item.from_node_ref,
      item.to_node_ref,
      ...item.participant_node_refs
    ]),
    ...paths.flatMap((item) => item.node_refs),
    ...candidateNodeRefs,
    ...candidateRelations.flatMap((item) => [item.source_node_ref, item.target_node_ref])
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
      <path d="${route.d}" marker-end="url(#canvas-arrow)" data-canvas-object="${escapeAttr4(relation.relation_ref)}"></path>
      <text x="${route.labelX}" y="${route.labelY}" text-anchor="middle" tabindex="0" role="button" data-canvas-object="${escapeAttr4(relation.relation_ref)}" aria-label="${escapeAttr4(relation.label)}">${escapeHtml3(shortRelationLabel(relation))}</text>
    </g>`];
  }).join("");
  const candidateMarkup = candidateRelations.map((relation, index) => {
    const source = anchors.get(relation.source_node_ref);
    const target = anchors.get(relation.target_node_ref);
    if (!source || !target) return "";
    const route = routeCanvasRelation(source, target, index + relations.length);
    const kind = relation.kind === "fact" ? "fact" : "candidate";
    const marker = relation.directionality === "symmetric" ? "" : ` marker-end="url(#canvas-${kind}-arrow)"`;
    return `<g class="canvas-${kind}-relation" data-${kind}-relation="${escapeAttr4(relation.relation_ref)}">
      <path d="${route.d}"${marker}></path>
      <text x="${route.labelX}" y="${route.labelY}" text-anchor="middle">${escapeHtml3(relation.label)}</text>
    </g>`;
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
      <marker id="canvas-candidate-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker>
      <marker id="canvas-fact-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker>
    </defs>
    <g class="canvas-scene-tracks" aria-hidden="true"><line x1="44" y1="185" x2="1276" y2="185"></line><line x1="44" y1="390" x2="1276" y2="390"></line><text x="46" y="171">\u5929\u5E72</text><text x="46" y="376">\u5730\u652F</text></g>
    <g class="canvas-scene-relations">${relationMarkup}</g>
    <g class="canvas-scene-paths">${pathMarkup}</g>
    <g class="canvas-scene-candidates">${candidateMarkup}</g>
    <g class="canvas-scene-nodes">${nodeMarkup}</g>
    ${!relationMarkup && !pathMarkup && !candidateMarkup ? `<g class="canvas-scene-empty"><text x="660" y="292" text-anchor="middle">\u6B64\u955C\u5934\u6CA1\u6709\u5DF2\u62AB\u9732\u5173\u7CFB</text><text x="660" y="315" text-anchor="middle">\u9875\u9762\u4E0D\u4F1A\u4E3A\u4E86\u586B\u6EE1\u753B\u9762\u800C\u8865\u7EBF</text></g>` : ""}
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
  const slotAction = active ? ` tabindex="0" role="button" data-canvas-object="${escapeAttr4(slot.slot_ref)}"` : "";
  return `<g class="canvas-scene-slot${temporal ? " is-temporal" : ""} state-${slot.state}" transform="translate(${x} 0)">
    <g class="canvas-slot-label${selected === slot.slot_ref ? " is-selected" : ""}"${slotAction}>
      <text x="0" y="70" text-anchor="middle">${escapeHtml3(slot.label)}</text>
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
    return `<g class="canvas-hidden-node element-${escapeAttr4(node.element)}${selected === node.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr4(node.polarity)}" transform="translate(${anchor.x - slotX} 515)" tabindex="0" role="button" data-canvas-object="${escapeAttr4(node.node_ref)}" aria-label="${escapeAttr4(`${slot.label}\u85CF\u5E72${node.label}`)}">
        <circle r="21"></circle>
        <text text-anchor="middle" dominant-baseline="central">${escapeHtml3(node.label)}</text>
      </g>`;
  }).join("")}
  </g>`;
}
function renderCanvasSceneNode(slot, node, anchor, selected, level) {
  const y = level === "stem" ? 185 : 390;
  const value = level === "stem" ? slot.stem : slot.branch;
  if (!node || !anchor) {
    return `<g class="canvas-scene-node is-inactive" transform="translate(0 ${y})"><text class="canvas-node-character" text-anchor="middle" dominant-baseline="central">${escapeHtml3(value || "\xB7")}</text></g>`;
  }
  const label = level === "stem" ? node.ten_god === "day_master" ? "\u65E5\u4E3B" : tenGodLabel(node.ten_god || "\u5929\u5E72") : "\u5730\u652F";
  return `<g class="canvas-scene-node element-${escapeAttr4(node.element)}${selected === node.node_ref ? " is-selected" : ""}" data-polarity="${escapeAttr4(node.polarity)}" transform="translate(0 ${y})" tabindex="0" role="button" data-canvas-object="${escapeAttr4(node.node_ref)}" aria-label="${escapeAttr4(`${slot.label}${label}${value}`)}">
    <rect x="-56" y="-58" width="112" height="116" rx="6"></rect>
    <text class="canvas-node-role" x="0" y="-33" text-anchor="middle">${escapeHtml3(label)}</text>
    <text class="canvas-node-character" x="0" y="11" text-anchor="middle" dominant-baseline="central">${escapeHtml3(value)}</text>
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
  return `<g class="canvas-work-path${candidate ? " is-candidate" : ""}${selected === path.path_ref ? " is-selected" : ""}" tabindex="0" role="button" data-canvas-object="${escapeAttr4(path.path_ref)}" aria-label="${escapeAttr4(path.label)}">
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
    roots: "\u65E7\u7248",
    source_identity_evidence: "\u540C\u5B57\u6765\u6E90",
    source_element_affinity: "\u540C\u4E94\u884C\u6765\u6E90",
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
    ${visible.length ? `<div class="change-list">${visible.map((group) => `<div class="change-group change-${escapeAttr4(group.change_type)}">
      <span><b>${escapeHtml3(group.label)}</b><em>${group.count}</em></span>
      ${group.items.slice(0, 5).map((item) => `<button type="button" data-canvas-object="${escapeAttr4(item.target_ref)}" class="${selected === item.target_ref ? "is-selected" : ""}">${escapeHtml3(item.label)}</button>`).join("")}
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
    <header><span>${escapeHtml3(type)}</span><b class="epistemic-${escapeAttr4(trace.epistemic_status)}">${escapeHtml3(epistemicLabel(trace.epistemic_status))}</b></header>
    <h3>${escapeHtml3(label)}</h3>
    <p>${status === "loading" ? "\u6B63\u5728\u53D6\u56DE\u8FD9\u4E2A\u5BF9\u8C61\u7684\u53D7\u63A7\u4E0A\u4E0B\u6587\u3002" : contextMatches ? objectExplanation(slot, node, relation, path) : "\u9009\u62E9\u5DF2\u5B9A\u4F4D\uFF1B\u53D7\u63A7\u4E0A\u4E0B\u6587\u5C06\u5728\u8FD9\u91CC\u663E\u793A\u3002"}</p>
    <dl><div><dt>\u5F53\u524D\u72B6\u6001</dt><dd>${escapeHtml3(stateLabel(semanticState))}</dd></div><div><dt>\u6765\u6E90</dt><dd>${trace.source_refs.length} \u6761\u53EF\u8FFD\u6EAF\u5F15\u7528</dd></div><div><dt>\u5F53\u524D\u9636\u6BB5</dt><dd>${escapeHtml3(spec.stage)}</dd></div></dl>
    ${trace.uncertainty.length || trace.rejection_or_block_reasons.length ? `<div class="inspector-caution"><span>\u4ECD\u9700\u4FDD\u7559</span><p>${escapeHtml3([...trace.uncertainty, ...trace.rejection_or_block_reasons][0])}</p></div>` : ""}
    <details><summary>\u67E5\u770B\u6765\u6E90</summary><ul>${trace.source_refs.map((ref) => `<li>${escapeHtml3(ref)}</li>`).join("")}</ul></details>
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
  return `<main class="system-state"><div class="state-mark"></div><p>\u770B\u89C1\u547D\u5C40</p><h1>${escapeHtml3(message)}</h1></main>`;
}
function renderUnavailable(title, detail, actionLabel) {
  return `
    <main class="system-state unavailable">
      <img src="/assets/abu/v11-designer-sad-tears/web/abu_sad_tears_v11.webp" alt="\u963F\u5E03\u6B63\u5728\u7B49\u5F85">
      <p>\u963F\u5E03\u5728\u8FD9\u91CC</p>
      <h1>${escapeHtml3(title)}</h1>
      <span>${escapeHtml3(detail)}</span>
      <a class="primary-command" href="/experience?manage=1">${escapeHtml3(actionLabel)}</a>
    </main>`;
}
function renderProfileSelector(cases2, activeProfileId2) {
  if (cases2.length <= 1) {
    const active = cases2.find((item) => item.profile_id === activeProfileId2);
    return `<span class="active-case"><i></i>${escapeHtml3(active?.display_name || "\u5F53\u524D\u547D\u76D8")}</span>`;
  }
  return `<label class="case-select-label"><span>\u5F53\u524D\u547D\u76D8</span><select data-profile-select>${cases2.map((item) => `<option value="${escapeAttr4(item.profile_id)}"${item.profile_id === activeProfileId2 ? " selected" : ""}>${escapeHtml3(item.display_name)}</option>`).join("")}</select></label>`;
}
function summaryItem(label, value, anchor) {
  return `<button type="button" class="scan-item" data-select-anchor="${escapeAttr4(anchor)}" data-message="${escapeAttr4(value)}"><span>${escapeHtml3(label)}</span><strong>${escapeHtml3(value)}</strong></button>`;
}
function renderCollapsibleSection(input) {
  return `
    <section class="experience-section tone-${escapeAttr4(input.tone)}${input.expanded ? " is-expanded" : " is-collapsed"}" id="${escapeAttr4(input.anchor)}" data-anchor="${escapeAttr4(input.anchor)}">
      <button class="section-heading" type="button" data-toggle-section="${escapeAttr4(input.id)}" aria-expanded="${input.expanded}">
        <span><small>${escapeHtml3(input.eyebrow)}</small><strong>${escapeHtml3(input.title)}</strong><em>${escapeHtml3(input.summary)}</em></span>
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
    return `<button type="button" class="pillar${selectedAnchor === pillar.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr4(pillar.visual_anchor)}" data-message="${escapeAttr4(message)}">
      <span class="pillar-label">${escapeHtml3(pillar.pillar_label)}</span>
      <span class="ten-god">${escapeHtml3(pillar.visible_ten_god || "\u5929\u5E72")}</span>
      <strong class="stem element-${escapeAttr4(pillar.stem_element)}" data-polarity="${escapeAttr4(pillar.stem_polarity)}">${escapeHtml3(pillar.stem)}</strong>
      <strong class="branch element-${escapeAttr4(pillar.branch_element)}" data-polarity="${escapeAttr4(pillar.branch_polarity)}">${escapeHtml3(pillar.branch)}</strong>
      <span class="nature">${polarityLabel[pillar.stem_polarity] || ""}${elementLabel[pillar.stem_element] || ""} \xB7 ${polarityLabel[pillar.branch_polarity] || ""}${elementLabel[pillar.branch_element] || ""}</span>
      <span class="hidden-stems">${pillar.hidden_stems.map((item) => `<i class="element-${escapeAttr4(item.element)}"><b>${escapeHtml3(item.stem)}</b><em>${escapeHtml3(item.ten_god)}</em></i>`).join("")}</span>
    </button>`;
  }).join("")}</div>`;
}
function renderPath(fullThesis, steps, selectedAnchor) {
  if (!steps.length) return `<p class="empty-note">\u4E3B\u8DEF\u5F84\u4ECD\u5728\u53EF\u9760\u6027\u95E8\u7981\u5185\uFF0C\u6CA1\u6709\u88AB\u5305\u88C5\u6210\u786E\u5B9A\u7ED3\u8BBA\u3002</p>`;
  return `<button type="button" class="baseline-thesis${selectedAnchor === "baseline-summary" ? " is-selected" : ""}" data-select-anchor="baseline-summary" data-message="${escapeAttr4(fullThesis)}">
    <span>\u6574\u76D8\u603B\u65AD</span><strong>${escapeHtml3(fullThesis)}</strong>
  </button><div class="path-stage">${steps.map((step, index) => {
    const message = `${step.premise}\uFF0C\u56E0\u6B64\u5F53\u524D\u5F97\u5230\u7684\u5224\u65AD\u662F\uFF1A${step.conclusion}`;
    return `<button type="button" class="path-step${selectedAnchor === step.visual_anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr4(step.visual_anchor)}" data-message="${escapeAttr4(message)}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <small>${escapeHtml3(step.premise)}</small>
      <strong>${escapeHtml3(step.conclusion)}</strong>
    </button>`;
  }).join('<span class="path-arrow" aria-hidden="true">\u2192</span>')}</div>`;
}
function firstSentence2(value) {
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
  return `<button type="button" class="boundary-item${selectedAnchor === anchor ? " is-selected" : ""}" data-select-anchor="${escapeAttr4(anchor)}" data-message="${escapeAttr4(text)}"><span>${escapeHtml3(label)}</span><strong>${escapeHtml3(text)}</strong></button>`;
}
function renderAbuDock(view) {
  const segment = view.narrationManifest?.segments[view.ui.narrationIndex];
  const isBusy = view.ui.narrationStatus === "preparing";
  return `<aside class="abu-dock${view.ui.abuExpanded ? " is-open" : ""}${isBusy ? " is-thinking" : ""}" aria-label="\u963F\u5E03\u540C\u6B65\u8BBA\u547D">
    <button class="abu-avatar" type="button" data-command="toggle-abu" aria-label="${view.ui.abuExpanded ? "\u6536\u8D77\u963F\u5E03" : "\u6253\u5F00\u963F\u5E03"}">
      <img class="${isBusy ? "" : "abu-avatar-standard"}" src="${isBusy ? "/assets/abu/v9-designer-taoist-divination/web/abu_taoist_divination_v9.webp" : "/assets/abu/v12-actor-pass/dream-standard-cycle/web/abu_dream_standard_cycle_v1.webp"}" alt="\u963F\u5E03">
    </button>
    <div class="abu-bubble" role="status"><span>${segment ? escapeHtml3(segment.title) : "\u963F\u5E03"}</span><p>${escapeHtml3(view.ui.abuMessage)}</p></div>
    <div class="abu-panel"${view.ui.abuExpanded ? "" : " hidden"}>
      <div class="abu-panel-heading"><span>\u963F\u5E03\u540C\u6B65\u8BBA\u547D</span><button type="button" data-command="toggle-abu" aria-label="\u6536\u8D77">\xD7</button></div>
      <p>${escapeHtml3(view.ui.abuMessage)}</p>
      <div class="narration-controls">
        <button type="button" class="primary-command compact" data-command="listen">${view.ui.narrationStatus === "playing" ? "\u6682\u505C" : "\u7EE7\u7EED\u542C"}</button>
        <button type="button" class="text-command" data-command="stop">\u505C\u6B62</button>
      </div>
      <ol class="chapter-list">${(view.narrationManifest?.segments || []).map((item, index) => `<li><button type="button" data-play-segment="${index}"${view.ui.narrationIndex === index ? ' class="active"' : ""}><span>${escapeHtml3(item.title)}</span><small>${escapeHtml3(item.text)}</small></button></li>`).join("")}</ol>
    </div>
  </aside>`;
}
function escapeHtml3(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character] || character);
}
function escapeAttr4(value) {
  return escapeHtml3(value).replace(/`/g, "&#96;");
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
  root2.querySelectorAll("[data-life-tree-question]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectLifeTreeQuestion(
      button.dataset.lifeTreeQuestion || "",
      button.dataset.lifeTreeCategory || "factual_observation"
    ));
  });
  root2.querySelectorAll("[data-life-tree-option]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectLifeTreeOption(
      button.dataset.lifeTreeOption || ""
    ));
  });
  root2.querySelector("[data-life-tree-submit]")?.addEventListener(
    "click",
    () => handlers.submitLifeTreeAnswer()
  );
  root2.querySelectorAll("[data-relation-lab-mode]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectRelationLabMode(
      button.dataset.relationLabMode || "facts"
    ));
  });
  root2.querySelectorAll("[data-relation-path]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectRelationPath(
      button.dataset.relationPath || ""
    ));
  });
  root2.querySelector("[data-relation-restore-natal]")?.addEventListener(
    "click",
    () => handlers.restoreRelationNatal()
  );
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
    const asset2 = await prepareNarrationSegment(this.caseId, segment.segment_id);
    const opus = asset2.media.playback_variants.find((item) => item.format === "opus");
    return opus?.audio_url || asset2.media.audio_url;
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

// apps/product/experience_shell/src/opening_music.ts
var MP3_SOURCE = "/assets/audio/abu/morning-glints-in-the-grove-v1/morning-glints-in-the-grove-opening-v1.mp3";
var SESSION_ENABLED_KEY = "deepbeing.opening_music.enabled.v1";
var SESSION_PLAYED_KEY = "deepbeing.opening_music.played.v1";
var OpeningMusicController = class {
  constructor(onStateChange) {
    this.onStateChange = onStateChange;
    this.audio = new Audio(MP3_SOURCE);
    this.audio.preload = "metadata";
    this.audio.loop = false;
    this.audio.volume = 0.52;
    const enabled = window.sessionStorage.getItem(SESSION_ENABLED_KEY) !== "off";
    const alreadyPlayed = window.sessionStorage.getItem(SESSION_PLAYED_KEY) === "1";
    this.state = enabled && !alreadyPlayed ? "armed" : alreadyPlayed ? "complete" : "paused";
    this.reflectState();
    this.audio.addEventListener("play", () => this.setState("playing"));
    this.audio.addEventListener("pause", () => {
      if (!this.audio.ended && this.state === "playing") this.setState("paused");
    });
    this.audio.addEventListener("ended", () => {
      window.sessionStorage.setItem(SESSION_PLAYED_KEY, "1");
      this.setState("complete");
    });
    this.audio.addEventListener("error", () => {
      document.documentElement.dataset.openingMusicError = "media_error";
      this.setState("blocked");
    });
  }
  audio;
  state;
  armed = false;
  arm() {
    if (this.armed || this.state !== "armed") return;
    this.armed = true;
    document.addEventListener("pointerdown", this.onFirstGesture, { capture: true });
    document.addEventListener("keydown", this.onFirstKeyGesture, { capture: true });
  }
  async toggle() {
    this.disarm();
    if (this.state === "playing") {
      window.sessionStorage.setItem(SESSION_ENABLED_KEY, "off");
      this.audio.pause();
      return;
    }
    window.sessionStorage.setItem(SESSION_ENABLED_KEY, "on");
    if (this.state === "complete" || this.audio.ended) this.audio.currentTime = 0;
    await this.tryPlay();
  }
  pauseForNarration() {
    this.disarm();
    window.sessionStorage.setItem(SESSION_PLAYED_KEY, "1");
    if (!this.audio.paused) this.audio.pause();
    if (this.state === "armed") this.setState("complete");
  }
  syncControls(root2 = document) {
    root2.querySelectorAll("[data-opening-music-control]").forEach((button) => {
      const label = this.controlLabel();
      button.dataset.musicState = this.state;
      button.setAttribute("aria-pressed", String(this.state === "playing"));
      button.setAttribute("aria-label", label);
      button.title = label;
    });
  }
  onFirstGesture = (event) => {
    if (this.shouldDeferToControl(event.target)) return;
    this.disarm();
    void this.tryPlay();
  };
  onFirstKeyGesture = (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    if (this.shouldDeferToControl(event.target)) return;
    this.disarm();
    void this.tryPlay();
  };
  shouldDeferToControl(target) {
    if (!(target instanceof Element)) return false;
    return Boolean(target.closest("[data-opening-music-control], [data-command='listen'], [data-play-segment]"));
  }
  async tryPlay() {
    try {
      await this.audio.play();
      window.sessionStorage.setItem(SESSION_PLAYED_KEY, "1");
    } catch (error) {
      document.documentElement.dataset.openingMusicError = error instanceof DOMException ? error.name : "playback_rejected";
      this.setState("blocked");
    }
  }
  disarm() {
    if (!this.armed) return;
    this.armed = false;
    document.removeEventListener("pointerdown", this.onFirstGesture, { capture: true });
    document.removeEventListener("keydown", this.onFirstKeyGesture, { capture: true });
  }
  setState(state) {
    this.state = state;
    this.reflectState();
    this.onStateChange();
  }
  reflectState() {
    document.documentElement.dataset.openingMusicState = this.state;
  }
  controlLabel() {
    if (this.state === "playing") return "\u6682\u505C\u5F00\u573A\u97F3\u4E50";
    if (this.state === "armed") return "\u64AD\u653E\u5F00\u573A\u97F3\u4E50\uFF1B\u9996\u6B21\u64CD\u4F5C\u540E\u4F1A\u81EA\u52A8\u5F00\u59CB";
    if (this.state === "complete") return "\u91CD\u64AD\u5F00\u573A\u97F3\u4E50";
    if (this.state === "blocked") return "\u6D4F\u89C8\u5668\u672A\u80FD\u64AD\u653E\uFF1B\u70B9\u51FB\u91CD\u8BD5";
    return "\u64AD\u653E\u5F00\u573A\u97F3\u4E50";
  }
};

// apps/product/experience_shell/src/dream_api.ts
var DREAM_CLIENT_KEY = "deepbazi.dream.client.v1";
var DREAM_CONTROL_KEY = "deepbazi.dream.control.v1";
var DREAM_NAVIGATION_HANDOFF_KEY = "deepbazi.dream.navigation-handoff.v1";
var pageClientInstanceId = "";
var DreamApiError = class extends Error {
  constructor(code, status) {
    super(code);
    this.code = code;
    this.status = status;
    this.name = "DreamApiError";
  }
};
function randomId(prefix) {
  const value = globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${value}`;
}
function dreamClientInstanceId() {
  if (pageClientInstanceId) return pageClientInstanceId;
  const navigation = performance.getEntriesByType("navigation")[0];
  const handoffAt = Number(sessionStorage.getItem(DREAM_NAVIGATION_HANDOFF_KEY));
  const handoffIsCurrent = Number.isFinite(handoffAt) && Date.now() - handoffAt < 15e3;
  const existing = sessionStorage.getItem(DREAM_CLIENT_KEY);
  sessionStorage.removeItem(DREAM_NAVIGATION_HANDOFF_KEY);
  if (existing && existing.length >= 8 && (navigation?.type === "reload" || handoffIsCurrent)) {
    pageClientInstanceId = existing;
    return existing;
  }
  const created = randomId("dream-client");
  sessionStorage.setItem(DREAM_CLIENT_KEY, created);
  pageClientInstanceId = created;
  return created;
}
function markDreamNavigationHandoff() {
  sessionStorage.setItem(DREAM_NAVIGATION_HANDOFF_KEY, String(Date.now()));
}
function readStoredControl(visitId = "") {
  try {
    const raw = sessionStorage.getItem(DREAM_CONTROL_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed.lease?.lease_id || visitId && parsed.visitId !== visitId) return null;
    return parsed;
  } catch {
    sessionStorage.removeItem(DREAM_CONTROL_KEY);
    return null;
  }
}
function rememberDreamControl(visit) {
  if (visit.control_lease) {
    sessionStorage.setItem(DREAM_CONTROL_KEY, JSON.stringify({
      visitId: visit.visit_id,
      worldProjectionRef: visit.world_projection_ref,
      lease: visit.control_lease
    }));
  }
  return visit;
}
function clearDreamControl() {
  sessionStorage.removeItem(DREAM_CONTROL_KEY);
}
function currentDreamWorldProjectionRef(visitId) {
  return readStoredControl(visitId)?.worldProjectionRef || "";
}
function dreamControlHeaders(visitId) {
  const control = readStoredControl(visitId);
  if (!control) throw new DreamApiError("dream_control_lease_required", 409);
  return {
    "x-dream-client-instance": control.lease.client_instance_id,
    "x-dream-lease-id": control.lease.lease_id,
    "x-dream-lease-epoch": String(control.lease.lease_epoch),
    "x-dream-fence-token": String(control.lease.fence_token)
  };
}
async function dreamRequest(url, init, visitId = "") {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...visitId ? dreamControlHeaders(visitId) : {},
      ...init?.headers || {}
    }
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new DreamApiError(
      String(payload.detail || `dream_request_failed_${response.status}`),
      response.status
    );
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
async function createDreamVisit(homeCaseId, takeover = false) {
  const visit = await dreamRequest("/api/v50/dream/visits", {
    method: "POST",
    body: JSON.stringify({
      home_case_id: homeCaseId,
      client_instance_id: dreamClientInstanceId(),
      takeover
    })
  });
  return rememberDreamControl(visit);
}
async function loadDreamVisit(visitId) {
  const visit = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}`,
    void 0,
    visitId
  );
  return rememberDreamControl(visit);
}
async function takeoverDreamVisit(visitId) {
  const visit = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/control/takeover`,
    {
      method: "POST",
      body: JSON.stringify({ client_instance_id: dreamClientInstanceId() })
    }
  );
  return rememberDreamControl(visit);
}
async function enterDreamVisit(visitId) {
  const visit = await dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/enter`, {
    method: "POST",
    body: "{}"
  }, visitId);
  return rememberDreamControl(visit);
}
function loadDreamEncounter(visitId) {
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/encounter`,
    void 0,
    visitId
  );
}
async function selectDreamTree(visitId, sceneRef) {
  const visit = await dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/select-tree`, {
    method: "POST",
    body: JSON.stringify({ scene_ref: sceneRef })
  }, visitId);
  return rememberDreamControl(visit);
}
function loadDreamTree(visitId, sceneRef) {
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}`,
    void 0,
    visitId
  );
}
function prepareDreamReveal(visitId, sceneRef) {
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/reveal`,
    { method: "POST", body: "{}" },
    visitId
  );
}
async function openDreamMirror(visitId, onecanvasViewRef, navigation) {
  const visit = await dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/open`, {
    method: "POST",
    body: JSON.stringify({ onecanvas_view_ref: onecanvasViewRef, navigation })
  }, visitId);
  return rememberDreamControl(visit);
}
async function closeDreamMirror(visitId) {
  const visit = await dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/close`, {
    method: "POST",
    body: "{}"
  }, visitId);
  return rememberDreamControl(visit);
}
function loadDreamMirror(visitId, sceneRef, onecanvasViewRef) {
  const query = new URLSearchParams({ view_ref: onecanvasViewRef });
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/mirror?${query.toString()}`,
    void 0,
    visitId
  );
}
async function heartbeatDreamControl(visitId) {
  const visit = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/control/heartbeat`,
    { method: "POST", body: "{}" },
    visitId
  );
  return rememberDreamControl(visit);
}
async function checkpointDreamVisit(visitId, navigation, recoverySequence) {
  const result = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/recovery/checkpoint`,
    {
      method: "POST",
      body: JSON.stringify({ navigation, recovery_sequence: recoverySequence })
    },
    visitId
  );
  return rememberDreamControl(result.visit);
}
async function suspendDreamVisit(visitId, navigation, recoverySequence, keepalive = false) {
  const visit = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/suspend`,
    {
      method: "POST",
      keepalive,
      body: JSON.stringify({ navigation, recovery_sequence: recoverySequence })
    },
    visitId
  );
  return rememberDreamControl(visit);
}
async function recoverDreamVisit(visitId) {
  const visit = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/recover`,
    { method: "POST", body: "{}" },
    visitId
  );
  return rememberDreamControl(visit);
}
async function setDreamDepartureIntent(visitId, active) {
  const visit = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/departure/intent`,
    { method: "POST", body: JSON.stringify({ active }) },
    visitId
  );
  return rememberDreamControl(visit);
}
async function commitDreamDeparture(visitId, trigger, navigation, commitSequence, boundaryPosition) {
  const result = await dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/departure/commit`,
    {
      method: "POST",
      body: JSON.stringify({
        trigger,
        navigation,
        boundary_position: boundaryPosition || null,
        commit_sequence: commitSequence
      })
    },
    visitId
  );
  clearDreamControl();
  return result;
}
function loadDreamDepartureResult(visitId, commitSequence) {
  const params = new URLSearchParams({ commit_sequence: String(commitSequence) });
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/departure/result?${params.toString()}`
  );
}
function migrateGuestDreamAnchor(caseId, guestAnchorCapability, accepted) {
  return dreamRequest("/api/v50/dream/anchors/migrate-guest", {
    method: "POST",
    body: JSON.stringify({
      case_id: caseId,
      guest_anchor_capability: guestAnchorCapability,
      accepted
    })
  });
}

// apps/product/experience_shell/src/dream_game_api.ts
var DREAM_GAME_BANNER = "V50\u7ED3\u6784\u9A8C\u8BC1\u573A\uFF5C\u6B63\u5F0F\u547D\u76D8\u5FEB\u7167\uFF5C\u4E0D\u8BA1\u5165\u771F\u4EBA\u679C\u5B9E";
function gamePath(visitId, suffix) {
  return `/api/v50/dream/visits/${encodeURIComponent(visitId)}/game/${suffix}`;
}
function loadDreamGameContentGate(visitId) {
  return dreamRequest(gamePath(visitId, "content-gate"), void 0, visitId);
}
function loadDreamGameRounds(visitId) {
  return dreamRequest(gamePath(visitId, "rounds"), void 0, visitId);
}
function startDreamGameRound(visitId, roundId) {
  return dreamRequest(
    gamePath(visitId, `rounds/${encodeURIComponent(roundId)}/start`),
    { method: "POST", body: "{}" },
    visitId
  );
}
function loadDreamGameAttempt(visitId, attemptId) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}`),
    void 0,
    visitId
  );
}
function answerDreamLearningQuestion(visitId, attemptId, questionId, optionId, idempotencyKey) {
  return dreamRequest(
    gamePath(
      visitId,
      `attempts/${encodeURIComponent(attemptId)}/learning/${encodeURIComponent(questionId)}/answer`
    ),
    {
      method: "POST",
      body: JSON.stringify({
        option_id: optionId,
        idempotency_key: idempotencyKey
      })
    },
    visitId
  );
}
function observeDreamGameLens(visitId, attemptId, lens) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/lenses/${lens}`),
    { method: "POST", body: "{}" },
    visitId
  );
}
function openDreamProblemFlower(visitId, attemptId) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/question/open`),
    { method: "POST", body: "{}" },
    visitId
  );
}
function castDreamGameDivination(visitId, attemptId, idempotencyKey) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/divination`),
    {
      method: "POST",
      body: JSON.stringify({ explicit_user_intent: true, idempotency_key: idempotencyKey })
    },
    visitId
  );
}
function beginDreamGameJudgment(visitId, attemptId) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/judgment/start`),
    { method: "POST", body: "{}" },
    visitId
  );
}
function sealDreamGameJudgment(visitId, attemptId, payload) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/judgment/seal`),
    { method: "POST", body: JSON.stringify(payload) },
    visitId
  );
}
function closeDreamProblemFlower(visitId, attemptId, idempotencyKey) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/flower/close`),
    {
      method: "POST",
      body: JSON.stringify({
        idempotency_key: idempotencyKey,
        confirmed: true
      })
    },
    visitId
  );
}
function revealDreamGameOutcome(visitId, attemptId, idempotencyKey) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/reveal`),
    { method: "POST", body: JSON.stringify({ idempotency_key: idempotencyKey }) },
    visitId
  );
}
function loadDreamGameResult(visitId, attemptId) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/result`),
    void 0,
    visitId
  );
}
function completeDreamGameRound(visitId, attemptId) {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/complete`),
    { method: "POST", body: "{}" },
    visitId
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

// apps/product/experience_shell/src/semantic_tree_scene_bundle.ts
var ROOT = "/assets/dream/semantic-tree-visible-v1";
var SEMANTIC_TREE_SCENE_BUNDLE = {
  bundleId: "SEMANTIC_TREE_VISIBLE_V1",
  schemaVersion: "deepbazi.semantic_tree_asset_bundle.v1",
  ownerAcceptedOuterSha256: "2bd3f4d277462eec9200622315e2124ddd8e9ed417f12603500dfc9adf777efc",
  publicRoot: ROOT,
  legacyFallbackAllowed: false,
  characterPolicy: "PRESERVE_EXISTING_RUNTIME_ABU",
  canvas: {
    nativeWidth: 1280,
    nativeHeight: 720,
    fit: "cover",
    cameraMotionAfterEntry: false
  },
  assets: {
    treeBase: asset(
      "assets/tree_base_clean.png",
      "dfd661d7e1b171a77afdf75224c453de2d7984ddfe2531df06f2ae11dd187be9",
      1280,
      720,
      false
    ),
    leafBasic01: asset(
      "assets/leaf_basic_01.png",
      "e13b7640c3cbed3be6a185a550e0f4df39df7dedc37dbc5468d0c1b93a9288b8",
      320,
      249,
      true,
      "masks/leaf_basic_01_hit_mask.png",
      "10f6d4c0dde6aafd99b972592aa2a097f6abfc7785830da1c8f03c827bc6be8d"
    ),
    leafBasic02: asset(
      "assets/leaf_basic_02.png",
      "f13312a1b25fd117208ea0cb67c932ed2af9b68d7f8a53cee7a218690a3837f8",
      208,
      280,
      true,
      "masks/leaf_basic_02_hit_mask.png",
      "542b76f1190afc0c841e1be3e435a3f2789d479cfbc7e0b558deaad99e38ebc4"
    ),
    trunkBackbone01: asset(
      "assets/trunk_backbone_01.png",
      "cc594091d7ae29c91b54813817570d9aac2c49c531447e7d717604f7eb450837",
      107,
      460,
      true,
      "masks/trunk_backbone_01_hit_mask.png",
      "72abef1ed2321e5f10228eb30e9e19fe9f4539188cbe4efae08256a296147b53"
    ),
    energyFlow: asset(
      "assets/energy_flow_mask.png",
      "f8c1a9f8453f29896cbbd170b48308a2a1f1a84df24badd2b7f2948e465b6e4f",
      1280,
      720,
      true
    ),
    flowerBudClosed: asset(
      "assets/flower_bud_closed.png",
      "2e96823d2cb5ed3956db70afcda82800f65e0ba9f6c33a79f3f82c5e00a6b713",
      112,
      280,
      true,
      "masks/flower_bud_closed_hit_mask.png",
      "8516603bde01a8d5fa44bb617e595adefe1615648bcd74d953527cc4228b8f60"
    ),
    flowerOpen: asset(
      "assets/flower_open.png",
      "14a7d4f92b317542dbfb4e2036021b7225c730dafe0ed7aeff8bf3d2270b2f86",
      290,
      320,
      true,
      "masks/flower_open_hit_mask.png",
      "2dbce319ffd6be5686bf10f1f10218de8a505aebd60883124df2a820f96e6451"
    ),
    fruitWhite: asset(
      "assets/fruit_white.png",
      "7619465b06110857dff001edb31b3a00de11326765f8a7fe0d4b7721cac08452",
      240,
      222,
      true,
      "masks/fruit_white_hit_mask.png",
      "fe31f0057077864452b5b982a1e8a7aef9c5dc67eb5fdc97d65a6b7931318c11"
    ),
    foregroundOcclusion: asset(
      "assets/foreground_occlusion.png",
      "8fbce9ff56d7c2a107c3b04df87aa950031a7a8a6547ece9c6addabe6a3b59d2",
      318,
      340,
      true
    )
  },
  layouts: {
    leafBasic01: layout(
      { x: 620, y: 245, displayWidth: 104 },
      { x: 138, y: 210, displayWidth: 76 }
    ),
    leafBasic02: layout(
      { x: 950, y: 340, displayWidth: 78 },
      { x: 260, y: 370, displayWidth: 56 }
    ),
    trunkBackbone01: layout(
      { x: 674, y: 280, displayWidth: 92 },
      { x: 168, y: 280, displayWidth: 52 }
    ),
    flowerBudClosed: layout(
      { x: 1050, y: 240, displayHeight: 110 },
      { x: 286, y: 230, displayHeight: 95 }
    ),
    flowerOpen: layout(
      { x: 1008, y: 200, displayHeight: 145 },
      { x: 250, y: 210, displayHeight: 120 }
    ),
    fruitWhite: layout(
      { x: 1030, y: 250, displayHeight: 95 },
      { x: 270, y: 250, displayHeight: 80 }
    ),
    foregroundOcclusion: layout(
      { x: 1060, y: 270, displayWidth: 105 },
      { x: 280, y: 280, displayWidth: 90 }
    )
  },
  integrityFiles: {
    "ASSET_PROVENANCE.md": "0223c298d8f2fa6d9281221b01247913b49c0aa064dcfe8c6142ca301bd3ed52",
    "LAYOUT_CONTRACT.json": "aae176a9a7ecc6338a1a853c8794a19adc4196451d8801540a5f7866d1c114e2",
    "MANIFEST.json": "904dfe13c7483444aecb4a7d2beac1ee0699c4e7779450bf24f4493efcacb9bb",
    "README.md": "9f18d75eb4a18ae118ff917a22b212bd7da8d63a3590f6252eeb516e8ef80e31",
    "assets/abu_character_v1.webm": "a63cfd680f27eae5f8fcbb317231d1a0e15ec37db52b854d9163777f769d2ec7",
    "assets/abu_character_v1_poster.png": "6aa0b95c6b7f325286087eb665c943f2aa49c2d43a0615b64102a3027b128702",
    "assets/energy_flow_mask.png": "f8c1a9f8453f29896cbbd170b48308a2a1f1a84df24badd2b7f2948e465b6e4f",
    "assets/energy_flow_mask.svg": "88926f9b927feb8a1ab09022d6d3302b6d8123150036db3b69a3b6fb190f7061",
    "assets/flower_bud_closed.png": "2e96823d2cb5ed3956db70afcda82800f65e0ba9f6c33a79f3f82c5e00a6b713",
    "assets/flower_open.png": "14a7d4f92b317542dbfb4e2036021b7225c730dafe0ed7aeff8bf3d2270b2f86",
    "assets/foreground_occlusion.png": "8fbce9ff56d7c2a107c3b04df87aa950031a7a8a6547ece9c6addabe6a3b59d2",
    "assets/fruit_white.png": "7619465b06110857dff001edb31b3a00de11326765f8a7fe0d4b7721cac08452",
    "assets/leaf_basic_01.png": "e13b7640c3cbed3be6a185a550e0f4df39df7dedc37dbc5468d0c1b93a9288b8",
    "assets/leaf_basic_02.png": "f13312a1b25fd117208ea0cb67c932ed2af9b68d7f8a53cee7a218690a3837f8",
    "assets/tree_base_clean.png": "dfd661d7e1b171a77afdf75224c453de2d7984ddfe2531df06f2ae11dd187be9",
    "assets/trunk_backbone_01.png": "cc594091d7ae29c91b54813817570d9aac2c49c531447e7d717604f7eb450837",
    "masks/flower_bud_closed_hit_mask.png": "8516603bde01a8d5fa44bb617e595adefe1615648bcd74d953527cc4228b8f60",
    "masks/flower_open_hit_mask.png": "2dbce319ffd6be5686bf10f1f10218de8a505aebd60883124df2a820f96e6451",
    "masks/fruit_white_hit_mask.png": "fe31f0057077864452b5b982a1e8a7aef9c5dc67eb5fdc97d65a6b7931318c11",
    "masks/leaf_basic_01_hit_mask.png": "10f6d4c0dde6aafd99b972592aa2a097f6abfc7785830da1c8f03c827bc6be8d",
    "masks/leaf_basic_02_hit_mask.png": "542b76f1190afc0c841e1be3e435a3f2789d479cfbc7e0b558deaad99e38ebc4",
    "masks/trunk_backbone_01_hit_mask.png": "72abef1ed2321e5f10228eb30e9e19fe9f4539188cbe4efae08256a296147b53",
    "previews/semantic_tree_desktop_three_states.png": "8bce863a6a11821b5d8f5299b6049132edb5b25fbd8bb24523bf314756d447f7",
    "previews/semantic_tree_mobile_stage2.png": "ecc8a0b40a063e6068b7576957093c6f242efaa9a1ec97ee5bc78bf432beceb8",
    "previews/semantic_tree_organ_contact_sheet.png": "5aabfc5a74ca7cd78aec58111edf8efd4219417d3cdae3779722d4518aaa55c7"
  }
};
function semanticTreeOrganStyle(layoutKey) {
  const selected = SEMANTIC_TREE_SCENE_BUNDLE.layouts[layoutKey];
  return [
    anchorStyle("desktop", selected.desktop, 1440, 900),
    anchorStyle("mobile", selected.mobile, 390, 844)
  ].join(";");
}
function asset(path, sha256, width, height, alpha, hitMaskPath, hitMaskSha256) {
  return {
    source: `${ROOT}/${path}`,
    sha256,
    width,
    height,
    alpha,
    ...hitMaskPath ? { hitMask: `${ROOT}/${hitMaskPath}` } : {},
    ...hitMaskSha256 ? { hitMaskSha256 } : {}
  };
}
function layout(desktop, mobile) {
  return { desktop, mobile };
}
function anchorStyle(profile, anchor, viewportWidth, viewportHeight) {
  const values = [
    `--semantic-${profile}-left:${percentage(anchor.x, viewportWidth)}`,
    `--semantic-${profile}-top:${percentage(anchor.y, viewportHeight)}`
  ];
  if (anchor.displayWidth) {
    values.push(`--semantic-${profile}-width:${percentage(anchor.displayWidth, viewportWidth)}`);
  }
  if (anchor.displayHeight) {
    values.push(`--semantic-${profile}-height:${percentage(anchor.displayHeight, viewportHeight)}`);
  }
  return values.join(";");
}
function percentage(value, total) {
  return `${(value / total * 100).toFixed(5)}%`;
}

// apps/product/experience_shell/src/dream_tree_world.ts
var LENS_META = {
  overview: { label: "\u603B\u89C8", objectLabel: "\u6811\u5E72\u5E74\u8F6E" },
  five_element: { label: "\u4E94\u884C", objectLabel: "\u53F6\u9762\u4E94\u884C" },
  roots_reveal: { label: "\u6765\u6E90", objectLabel: "\u6765\u6E90\u5750\u6807" },
  combination_conflict: { label: "\u5408\u51B2", objectLabel: "\u679D\u8DEF\u5206\u5408" },
  work_path: { label: "\u505A\u529F", objectLabel: "\u4E3B\u679D\u8DEF\u5F84" },
  timing: { label: "\u65F6\u8FD0", objectLabel: "\u53F6\u95F4\u9732\u65F6" }
};
function renderDreamTreePorch(view) {
  const rounds = view.rounds.slice(0, 3);
  const count = Math.max(1, rounds.length);
  const activeIndex = (view.activeIndex % count + count) % count;
  const active = rounds[activeIndex];
  const abu = abuMotionFor("ghost_orbit_observer", prefersReducedMotion2());
  const sceneAssets = [
    DREAM_RUNTIME_ASSETS.porchBlue,
    DREAM_RUNTIME_ASSETS.porchJade,
    DREAM_RUNTIME_ASSETS.porchAmber
  ];
  const treeTargets = rounds.map((round, index) => {
    const activeTree = index === activeIndex;
    const forward = (index - activeIndex + count) % count;
    const orbitSlot = forward === 0 ? 0 : forward === 1 ? 1 : -1;
    const sceneAsset = sceneAssets[index] || sceneAssets[0];
    return `<button
      class="dream-tree-porch-tree is-porch-actor${activeTree ? " is-active is-dream-heart" : " is-ghost"}"
      type="button"
      data-dream-game-command="porch-select"
      data-porch-index="${index}"
      data-orbit-slot="${orbitSlot}"
      aria-current="${activeTree ? "true" : "false"}"
      aria-label="${escapeAttr5(activeTree ? `${round.anonymous_label}\u4F4D\u4E8E\u68A6\u5FC3\uFF0C\u8F7B\u89E6\u8FDB\u5165` : `\u8BA9${round.anonymous_label}\u6765\u5230\u68A6\u5FC3`)}"
    ><img src="${sceneAsset.source}" alt="" draggable="false" aria-hidden="true" decoding="async" fetchpriority="${activeTree ? "high" : "auto"}"><span aria-hidden="true"></span></button>`;
  }).join("");
  const whisper = view.focusedWhisper ? `<p class="dream-ghost-orbit-whisper" aria-live="polite">${escapeHtml4(view.focusedWhisper)}</p>` : `<p class="dream-ghost-orbit-whisper" aria-hidden="true"></p>`;
  const treeEnter = view.mediaCue === "tree_enter" ? `<div class="dream-director-transition is-tree-enter" data-dream-director-transition="tree-enter">
        <video
          data-dream-director-video="tree-enter"
          src="${DREAM_RUNTIME_ASSETS.treeEnter.source}"
          autoplay muted playsinline preload="auto"
        ></video>
      </div>` : "";
  return `<div
      class="dream-tree-world-shell is-porch is-layered-porch-v5${view.entering ? " is-entering" : ""}"
      data-tree-world-mode="porch"
      data-dream-scene-id="${escapeAttr5(view.scene.sceneId)}"
      data-dream-business-state="${escapeAttr5(view.scene.businessState)}"
      data-dream-presentation-state="${escapeAttr5(view.scene.presentationState)}"
      style="--porch-active-index:${activeIndex}"
  >
    <section
      class="dream-tree-porch-camera"
      data-dream-tree-porch
      aria-label="\u4E09\u68F5\u51BB\u7ED3\u6848\u4F8B\u7684\u68A6\u6811\u95E8\u5ECA"
      aria-roledescription="\u53EF\u5DE6\u53F3\u8F6C\u5411\u7684\u8FDE\u7EED\u6797\u5883"
      tabindex="0"
    >
      <div class="dream-tree-porch-panorama" aria-hidden="true">
        <img
          class="dream-tree-porch-backdrop"
          src="${DREAM_RUNTIME_ASSETS.porchCleanBackdrop.source}"
          alt=""
          draggable="false"
          decoding="async"
          fetchpriority="high"
        >
        <span class="dream-tree-porch-mist"></span>
        <span class="dream-ghost-orbit-veil is-left"></span>
        <span class="dream-ghost-orbit-veil is-right"></span>
      </div>
      <button
        class="dream-tree-porch-abu"
        type="button"
        data-dream-game-command="porch-shift"
        data-direction="1"
        aria-label="\u8BF7\u963F\u5E03\u5E26\u4E0B\u4E00\u68F5\u68A6\u6811\u6765\u5230\u773C\u524D"
      >
        ${renderAbuActor(abu, "", "dream-tree-porch-abu-actor")}
      </button>
      <div class="dream-tree-porch-targets">${treeTargets}</div>
      ${whisper}
      <div class="dream-ghost-orbit-a11y sr-only">
        <button type="button" data-dream-game-command="porch-shift" data-direction="-1">\u4E0A\u4E00\u68F5\u68A6\u6811</button>
        <button type="button" data-dream-game-command="porch-shift" data-direction="1">\u4E0B\u4E00\u68F5\u68A6\u6811</button>
        ${active ? `<span data-porch-current-label>\u5F53\u524D\u68A6\u5FC3\u4F4D\uFF1A${escapeHtml4(active.anonymous_label)}</span>` : ""}
      </div>
      <button
        class="dream-tree-porch-departure"
        type="button"
        data-dream-game-command="depart"
        aria-label="\u6CBF\u96FE\u5F84\u79BB\u5F00\u68A6\u5883"
      ><span aria-hidden="true"></span><b>\u6CBF\u96FE\u5F84\u79BB\u5F00</b></button>
    </section>
    ${treeEnter}
  </div>`;
}
function renderDreamTreeQuestionMap(view) {
  const passed = new Set(view.passedNodes);
  const bundle = SEMANTIC_TREE_SCENE_BUNDLE;
  const abu = abuMotionFor("fixed_tree_companion", prefersReducedMotion2());
  const transition = renderTreeMediaTransition(view.mediaCue);
  const nodeMarkup = [
    renderTreeNode({
      id: "leaf_structure",
      label: "\u8BFB\u53D6\u6811\u51A0\u4E2D\u7684\u663E\u73B0\u53F6",
      active: view.activeNode === "leaf_structure",
      passed: passed.has("leaf_structure"),
      locked: false,
      asset: bundle.assets.leafBasic01,
      layout: "leafBasic01",
      disabled: Boolean(view.resultMarkup)
    }),
    renderTreeNode({
      id: "leaf_support",
      label: "\u8BFB\u53D6\u6811\u51A0\u4E2D\u7684\u627F\u8F7D\u53F6",
      active: view.activeNode === "leaf_support",
      passed: passed.has("leaf_support"),
      locked: false,
      asset: bundle.assets.leafBasic02,
      layout: "leafBasic02",
      disabled: Boolean(view.resultMarkup)
    }),
    renderTreeNode({
      id: "branch_path",
      label: "\u8BFB\u53D6\u7279\u6B8A\u679D\u5E72",
      active: view.activeNode === "branch_path",
      passed: passed.has("branch_path"),
      locked: !passed.has("leaf_structure") || !passed.has("leaf_support"),
      asset: bundle.assets.trunkBackbone01,
      layout: "trunkBackbone01",
      disabled: Boolean(view.resultMarkup)
    }),
    renderFlowerOrFruit(view)
  ].join("");
  return `<div
    class="dream-tree-world-shell is-question-map"
    data-tree-world-mode="question-map"
    data-dream-scene-id="${escapeAttr5(view.scene.sceneId)}"
    data-dream-business-state="${escapeAttr5(view.scene.businessState)}"
    data-dream-presentation-state="${escapeAttr5(view.scene.presentationState)}"
    data-active-node="${view.activeNode || "none"}"
    data-semantic-tree-bundle="${bundle.bundleId}"
    data-semantic-tree-bundle-sha256="${bundle.ownerAcceptedOuterSha256}"
    data-semantic-tree-cue="${view.mediaCue}"
    data-flower-state="${view.fruitVisible ? "fruit" : view.flowerUnlocked ? "open" : "bud"}"
    data-fruit-visible="${view.fruitVisible ? "true" : "false"}"
  >
    <header class="dream-tree-world-header">
      <button type="button" data-dream-game-command="return-porch" aria-label="\u8FD4\u56DE\u68A6\u6811\u95E8\u5ECA">\u2039</button>
      <div><small>\u963F\u5E03\u95EE\u679C \xB7 \u4E09\u6811\u5C40</small><strong>${escapeHtml4(view.residentDisplayLabel)}</strong></div>
      <span aria-hidden="true">\u7ED3\u6784\u76F2\u5C40</span>
    </header>
    <p class="dream-tree-world-banner" role="status">${escapeHtml4(view.banner)}</p>
    <section class="dream-question-tree-stage${!view.activeNode && passed.size === 0 ? " is-first-growth" : ""}" aria-label="${escapeAttr5(`${view.residentDisplayLabel}\u7684\u751F\u547D\u6811`)}">
      <picture class="semantic-tree-base-layer"><img
        class="dream-question-tree-master"
        src="${bundle.assets.treeBase.source}"
        data-asset-sha256="${bundle.assets.treeBase.sha256}"
        alt=""
        draggable="false"
      ></picture>
      <img
        class="semantic-tree-energy-flow${view.flowerUnlocked ? " is-active" : ""}${view.mediaCue === "flower_open" ? " is-awakening" : ""}"
        src="${bundle.assets.energyFlow.source}"
        data-asset-sha256="${bundle.assets.energyFlow.sha256}"
        alt=""
        draggable="false"
        aria-hidden="true"
      >
      <div class="dream-question-tree-nodes">${nodeMarkup}</div>
      <img
        class="semantic-tree-foreground-occlusion"
        src="${bundle.assets.foregroundOcclusion.source}"
        data-asset-sha256="${bundle.assets.foregroundOcclusion.sha256}"
        style="${semanticTreeOrganStyle("foregroundOcclusion")}"
        alt=""
        draggable="false"
        aria-hidden="true"
      >
      <div class="dream-question-tree-abu" aria-hidden="true">${renderAbuActor(abu, "", "dream-question-tree-abu-actor")}</div>
      ${view.resultMarkup}
      ${view.questionBandMarkup && !view.resultMarkup ? `<aside class="dream-question-band" aria-live="polite">${view.questionBandMarkup}</aside>` : ""}
    </section>
    ${view.lensOpen ? `<section class="dream-tree-lens-overlay" aria-label="${escapeAttr5(LENS_META[view.activeLens].label)}\u547D\u76D8\u955C">
      <div class="dream-tree-lens-forest-edge" aria-hidden="true"></div>
      <header>
        <div><small>${escapeHtml4(LENS_META[view.activeLens].objectLabel)}</small><strong>${escapeHtml4(LENS_META[view.activeLens].label)}</strong></div>
        <button type="button" data-dream-game-command="close-lens" aria-label="\u56DE\u5230\u751F\u547D\u6811">\u56DE\u5230\u6811\u4E2D</button>
      </header>
      <div class="dream-tree-lens-canvas">${view.canvasMarkup}</div>
    </section>` : ""}
    ${view.statusMessage ? `<p class="dream-game-status" role="status">${escapeHtml4(view.statusMessage)}</p>` : ""}
    ${transition}
  </div>`;
}
function buildDreamTreeQuestions(attempt) {
  return attempt.question_set.questions.map((question) => ({
    nodeId: questionNodeId(question),
    questionId: question.question_id,
    title: question.title,
    prompt: question.prompt,
    lens: question.target_lens,
    available: question.available,
    options: question.options.map((option) => ({
      optionId: option.option_id,
      label: option.label
    }))
  }));
}
function treeQuestionForNode(attempt, nodeId) {
  return buildDreamTreeQuestions(attempt).find((item) => item.nodeId === nodeId);
}
function questionNodeId(question) {
  if (question.kind === "LEAF_BASIC_01") return "leaf_structure";
  if (question.kind === "LEAF_BASIC_02") return "leaf_support";
  return "branch_path";
}
function renderTreeNode(input) {
  return `<button
    class="dream-question-tree-node semantic-tree-organ is-${input.id.replaceAll("_", "-")}${input.active ? " is-active" : ""}${input.passed ? " is-passed" : ""}${input.locked ? " is-locked" : ""}"
    type="button"
    data-dream-game-command="tree-node"
    data-tree-node="${input.id}"
    data-semantic-organ="${semanticOrganId(input.id)}"
    data-semantic-hit-mask="${escapeAttr5(input.asset.hitMask || "")}"
    data-asset-sha256="${input.asset.sha256}"
    style="${semanticTreeOrganStyle(input.layout)}"
    aria-pressed="${input.active}"
    aria-disabled="${input.locked}"
    aria-label="${escapeAttr5(input.label)}"
    ${input.disabled ? "disabled" : ""}
  ><img
    class="semantic-tree-organ-visual"
    src="${input.asset.source}"
    alt=""
    draggable="false"
    aria-hidden="true"
  >${input.asset.hitMask ? `<img
    class="semantic-tree-organ-hit-mask"
    src="${input.asset.hitMask}"
    alt=""
    draggable="false"
    aria-hidden="true"
  >` : ""}<span class="sr-only">${escapeHtml4(input.label)}</span></button>`;
}
function renderFlowerOrFruit(view) {
  const bundle = SEMANTIC_TREE_SCENE_BUNDLE;
  if (view.fruitVisible) {
    const fruit = bundle.assets.fruitWhite;
    return `<div
      class="dream-question-tree-node semantic-tree-organ is-problem-flower is-fruit-white"
      data-tree-node="problem_flower"
      data-semantic-organ="FRUIT_RESULT"
      data-semantic-anchor="FLOWER_BLINDROUND_01"
      data-semantic-hit-mask="${escapeAttr5(fruit.hitMask || "")}"
      data-asset-sha256="${fruit.sha256}"
      style="${semanticTreeOrganStyle("fruitWhite")}"
      aria-label="\u53CC\u91CD\u5C01\u5B58\u540E\u751F\u6210\u7684\u96FE\u767D\u679C\u5B9E"
    ><img class="semantic-tree-organ-visual" src="${fruit.source}" alt="" draggable="false" aria-hidden="true"></div>`;
  }
  const flower = view.flowerUnlocked ? bundle.assets.flowerOpen : bundle.assets.flowerBudClosed;
  const layout2 = view.flowerUnlocked ? "flowerOpen" : "flowerBudClosed";
  const label = view.flowerUnlocked ? "\u67E5\u770B\u5DF2\u7ECF\u89E3\u9501\u7684\u95EE\u9898\u82B1" : "\u5C1A\u672A\u5F00\u653E\u7684\u95EE\u9898\u82B1";
  return `<button
    class="dream-question-tree-node semantic-tree-organ is-problem-flower${view.activeNode === "problem_flower" ? " is-active" : ""}${view.flowerOpened ? " is-passed" : ""}${view.flowerUnlocked ? " is-open" : " is-locked"}"
    type="button"
    data-dream-game-command="tree-node"
    data-tree-node="problem_flower"
    data-semantic-organ="FLOWER_BLINDROUND_01"
    data-semantic-anchor="FLOWER_BLINDROUND_01"
    data-semantic-hit-mask="${escapeAttr5(flower.hitMask || "")}"
    data-asset-sha256="${flower.sha256}"
    style="${semanticTreeOrganStyle(layout2)}"
    aria-pressed="${view.activeNode === "problem_flower"}"
    aria-disabled="${!view.flowerUnlocked}"
    ${view.resultMarkup ? "disabled" : ""}
    aria-label="${escapeAttr5(label)}"
  ><img class="semantic-tree-organ-visual" src="${flower.source}" alt="" draggable="false" aria-hidden="true">${flower.hitMask ? `<img
    class="semantic-tree-organ-hit-mask"
    src="${flower.hitMask}"
    alt=""
    draggable="false"
    aria-hidden="true"
  >` : ""}<span class="sr-only">${escapeHtml4(label)}</span></button>`;
}
function semanticOrganId(nodeId) {
  if (nodeId === "leaf_structure") return "LEAF_BASIC_01";
  if (nodeId === "leaf_support") return "LEAF_BASIC_02";
  if (nodeId === "branch_path") return "TRUNK_BACKBONE_01";
  return "FLOWER_BLINDROUND_01";
}
function renderTreeMediaTransition(cue) {
  return cue === "none" || cue === "tree_enter" ? "" : `<span class="semantic-tree-state-cue is-${cue.replaceAll("_", "-")}" data-dream-director-transition="${cue.replaceAll("_", "-")}" aria-hidden="true"></span>`;
}
function escapeHtml4(value) {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
function escapeAttr5(value) {
  return escapeHtml4(value);
}
function prefersReducedMotion2() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// apps/product/experience_shell/src/dream_scene_director.ts
var STORY_SCENES = {
  HOME_AWAKE: scene("home-awake", "HOME_AWAKE", "HOME_TREE_QUIET", [], ["home_tree"]),
  DREAM_AVAILABLE: scene(
    "home-tree-call",
    "DREAM_AVAILABLE",
    "HOME_TREE_CALLING",
    ["OpenDream"],
    ["home_tree", "abu_sleep_breath"],
    ["opening_theme", "leaf_whisper"]
  ),
  DREAM_PORTAL_READY: scene(
    "home-sleeping-portal",
    "DREAM_PORTAL_READY",
    "ABU_SLEEP_BREATH",
    ["OpenDream", "ResumeDream"],
    ["home_tree", "abu_curl_to_sleep", "abu_sleep_breath"],
    ["sleep_breath", "root_light"]
  ),
  ENTERING_DREAM: scene(
    "fog-gate",
    "ENTERING_DREAM",
    "FOG_GATE_OPENING",
    [],
    ["fog_gate"],
    ["opening_theme", "mist_open"]
  ),
  THREE_TREE_SELECTION: scene(
    "ghost-orbit-three-tree-selection",
    "THREE_TREE_SELECTION",
    "GHOST_ORBIT_FOCUSED",
    ["FocusCandidate", "CommitCandidate", "ReturnHome"],
    ["ghost_orbit"],
    ["leaf_whisper"]
  ),
  ENCOUNTER_COMMITTED: scene(
    "tree-commit-dissolve",
    "ENCOUNTER_COMMITTED",
    "TREE_COMMIT_DISSOLVE",
    [],
    ["ghost_orbit", "abu_tree_leap"],
    ["root_light", "mist_close"]
  ),
  FIXED_TREE_EXPLORATION: scene(
    "fixed-tree-exploration",
    "FIXED_TREE_EXPLORATION",
    "FIXED_TREE_IDLE",
    ["OpenQuestionNode", "SubmitFoundationAnswer", "ReturnHome"],
    ["fixed_tree", "question_leaf", "question_branch", "question_bud"],
    ["leaf_whisper", "branch_wake"]
  ),
  FOUNDATION_COMPLETE: scene(
    "fixed-tree-foundation-complete",
    "FOUNDATION_COMPLETE",
    "FIXED_TREE_IDLE",
    ["OpenQuestionNode", "OpenBlindRound", "ReturnHome"],
    ["fixed_tree", "question_bud"],
    ["flower_open"]
  ),
  BLIND_ROUND_OPEN: scene(
    "problem-flower",
    "BLIND_ROUND_OPEN",
    "QUESTION_NODE_ACTIVE",
    ["SubmitJudgment", "ReturnHome"],
    ["question_bud"],
    ["flower_open"]
  ),
  JUDGMENT_SUBMITTED: scene(
    "judgment-sealed",
    "JUDGMENT_SUBMITTED",
    "FIXED_TREE_IDLE",
    ["RequestReveal", "ReturnHome"],
    ["fixed_tree"]
  ),
  DOUBLE_SEALED: scene(
    "fog-white-fruit",
    "DOUBLE_SEALED",
    "FRUIT_FORMING",
    ["RequestReveal", "ReturnHome"],
    ["fruit_form"],
    ["fruit_form"]
  ),
  REVEALABLE: scene(
    "three-act-reveal",
    "REVEALABLE",
    "REVEAL_ACT_ACTIVE",
    ["CompleteReveal", "ReturnHome"],
    ["fruit_form"]
  ),
  REVEAL_COMPLETE: scene(
    "knowledge-seed",
    "REVEAL_COMPLETE",
    "REVEAL_ACT_ACTIVE",
    ["ReturnHome"],
    ["knowledge_seed"],
    ["seed_land"]
  ),
  RETURNED_WITH_SEED: scene(
    "home-seed-landing",
    "RETURNED_WITH_SEED",
    "SEED_LANDING",
    ["OpenDream"],
    ["home_tree", "knowledge_seed"],
    ["seed_land"]
  )
};
function sceneForStory(snapshot) {
  const base = STORY_SCENES[snapshot.businessState];
  return {
    ...base,
    presentationState: snapshot.presentationState
  };
}
function scene(sceneId, businessState, presentationState, allowedCommands, assetDependencies, audioCues = ["none"]) {
  return {
    sceneId,
    businessState,
    presentationState,
    entryIntent: `${sceneId}:enter`,
    idleIntent: `${sceneId}:idle`,
    exitIntent: `${sceneId}:exit`,
    allowedCommands,
    audioCues,
    subtitleCues: [],
    assetDependencies,
    reducedMotionFallback: `${sceneId}:static-crossfade`,
    resumePolicy: `${sceneId}:restore-from-server-and-local-presentation-checkpoint`,
    errorPolicy: "FAIL_CLOSED",
    telemetry: [
      "scene_entered",
      "scene_command_attempted",
      "scene_command_committed",
      "scene_fail_closed"
    ]
  };
}

// apps/product/experience_shell/src/dream_story_reducer.ts
function initialDreamStorySnapshot() {
  return {
    businessState: "HOME_AWAKE",
    presentationState: "HOME_TREE_QUIET",
    focusedCandidateIndex: 0,
    committedRoundId: "",
    foundationComplete: false,
    revealAct: "user",
    revision: 0,
    lastEvent: "SYNC_SERVER"
  };
}
function reduceDreamStory(current, event) {
  const next = { ...current, revision: current.revision + 1, lastEvent: event.type };
  if (event.type === "SYNC_SERVER") return syncServer(next, event.context);
  if (event.type === "DREAM_BECAME_AVAILABLE") {
    return withState(next, "DREAM_AVAILABLE", "HOME_TREE_CALLING");
  }
  if (event.type === "OPEN_DREAM_REQUESTED") {
    return withState(next, "DREAM_PORTAL_READY", "ABU_CURLING_TO_SLEEP");
  }
  if (event.type === "PORTAL_READY") {
    return withState(next, "DREAM_PORTAL_READY", "ABU_SLEEP_BREATH");
  }
  if (event.type === "FOG_GATE_COMPLETED") {
    return withState(next, "THREE_TREE_SELECTION", "GHOST_ORBIT_SETTLING");
  }
  if (event.type === "FOCUS_CANDIDATE") {
    const count = Math.max(1, event.candidateCount);
    return {
      ...withState(next, "THREE_TREE_SELECTION", "GHOST_ORBIT_FOCUSED"),
      focusedCandidateIndex: (event.index % count + count) % count
    };
  }
  if (event.type === "COMMIT_CANDIDATE") {
    return {
      ...withState(next, "ENCOUNTER_COMMITTED", "TREE_COMMIT_DISSOLVE"),
      committedRoundId: event.roundId
    };
  }
  if (event.type === "TREE_ENTRY_COMPLETED") {
    return withState(next, "FIXED_TREE_EXPLORATION", "FIXED_TREE_IDLE");
  }
  if (event.type === "FOUNDATION_PROGRESS") {
    return {
      ...withState(
        next,
        event.complete ? "FOUNDATION_COMPLETE" : "FIXED_TREE_EXPLORATION",
        event.complete ? "FIXED_TREE_IDLE" : "QUESTION_NODE_ACTIVE"
      ),
      foundationComplete: event.complete
    };
  }
  if (event.type === "QUESTION_NODE_OPENED") {
    return withState(next, next.businessState, "QUESTION_NODE_ACTIVE");
  }
  if (event.type === "FLOWER_OPENED") {
    return withState(next, "BLIND_ROUND_OPEN", "FLOWER_OPENING");
  }
  if (event.type === "JUDGMENT_SEALED") {
    return withState(next, "JUDGMENT_SUBMITTED", "FIXED_TREE_IDLE");
  }
  if (event.type === "DOUBLE_SEAL_CONFIRMED") {
    return withState(next, "DOUBLE_SEALED", "FRUIT_FORMING");
  }
  if (event.type === "REVEAL_STARTED") {
    return withState(next, "REVEALABLE", "REVEAL_ACT_ACTIVE");
  }
  if (event.type === "REVEAL_ACT_CHANGED") {
    return {
      ...withState(next, "REVEALABLE", "REVEAL_ACT_ACTIVE"),
      revealAct: event.act
    };
  }
  if (event.type === "REVEAL_COMPLETED") {
    return withState(next, "REVEAL_COMPLETE", "REVEAL_ACT_ACTIVE");
  }
  if (event.type === "RETURN_STARTED") {
    return withState(next, next.businessState, "RETURN_MIST");
  }
  if (event.type === "RETURNED_WITH_SEED") {
    return withState(next, "RETURNED_WITH_SEED", "SEED_LANDING");
  }
  return withState(next, next.businessState, "FAIL_CLOSED");
}
function syncServer(current, context) {
  if (context.returnedWithSeed) {
    return withState(current, "RETURNED_WITH_SEED", "SEED_LANDING");
  }
  if (!context.visit) {
    return context.dreamAvailable ? withState(current, context.resumable ? "DREAM_PORTAL_READY" : "DREAM_AVAILABLE", "HOME_TREE_CALLING") : withState(current, "HOME_AWAKE", "HOME_TREE_QUIET");
  }
  if (context.visit.state === "COMPLETED") {
    return withState(current, "HOME_AWAKE", "HOME_TREE_QUIET");
  }
  if (["HOME_GROVE", "PATH_OFFERED"].includes(context.visit.state)) {
    return withState(current, "DREAM_PORTAL_READY", "ABU_SLEEP_BREATH");
  }
  if (context.visit.state === "DREAM_ENTERING") {
    return withState(current, "ENTERING_DREAM", "FOG_GATE_OPENING");
  }
  if (!context.hasAttempt) {
    return withState(current, "THREE_TREE_SELECTION", "GHOST_ORBIT_FOCUSED");
  }
  if (context.hasResult) {
    return {
      ...withState(current, "REVEAL_COMPLETE", "REVEAL_ACT_ACTIVE"),
      foundationComplete: true
    };
  }
  if (context.gameState === "OUTCOME_REVEALABLE") {
    return {
      ...withState(current, "DOUBLE_SEALED", "FRUIT_FORMING"),
      foundationComplete: true
    };
  }
  if (context.gameState === "JUDGMENT_DRAFTING") {
    return {
      ...withState(current, "BLIND_ROUND_OPEN", "QUESTION_NODE_ACTIVE"),
      foundationComplete: context.foundationComplete
    };
  }
  if (["QUESTION_FLOWER_OPEN", "OPTIONAL_DIVINATION"].includes(context.gameState)) {
    return {
      ...withState(current, "BLIND_ROUND_OPEN", "FIXED_TREE_IDLE"),
      foundationComplete: true
    };
  }
  return {
    ...withState(
      current,
      context.foundationComplete ? "FOUNDATION_COMPLETE" : "FIXED_TREE_EXPLORATION",
      "FIXED_TREE_IDLE"
    ),
    foundationComplete: context.foundationComplete
  };
}
function withState(snapshot, businessState, presentationState) {
  return { ...snapshot, businessState, presentationState };
}

// apps/product/experience_shell/src/dream_story_runtime.ts
var DREAM_RETURN_PRESENTATION_KEY = "deepbazi.dream.returned-with-seed.v1";
var DreamStoryRuntime = class {
  snapshotValue = initialDreamStorySnapshot();
  get snapshot() {
    return this.snapshotValue;
  }
  get scene() {
    return sceneForStory(this.snapshotValue);
  }
  dispatch(event) {
    this.snapshotValue = reduceDreamStory(this.snapshotValue, event);
    return this.snapshotValue;
  }
  sync(input) {
    return this.dispatch({
      type: "SYNC_SERVER",
      context: {
        dreamAvailable: Boolean(input.dreamAvailable),
        resumable: Boolean(input.resumable),
        visit: input.visit || null,
        gameState: input.gameState || "",
        hasAttempt: Boolean(input.hasAttempt),
        hasResult: Boolean(input.hasResult),
        foundationComplete: Boolean(input.foundationComplete),
        returnedWithSeed: Boolean(input.returnedWithSeed)
      }
    });
  }
  can(command) {
    return this.scene.allowedCommands.includes(command);
  }
};
function markDreamReturnedWithSeed(hasKnowledgeSeed) {
  sessionStorage.setItem(DREAM_RETURN_PRESENTATION_KEY, JSON.stringify({
    hasKnowledgeSeed,
    recordedAt: Date.now()
  }));
}
function consumeDreamReturnedWithSeed() {
  try {
    const raw = sessionStorage.getItem(DREAM_RETURN_PRESENTATION_KEY);
    sessionStorage.removeItem(DREAM_RETURN_PRESENTATION_KEY);
    if (!raw) return false;
    const value = JSON.parse(raw);
    return Boolean(
      value.hasKnowledgeSeed && Number.isFinite(value.recordedAt) && Date.now() - Number(value.recordedAt) < 5 * 60 * 1e3
    );
  } catch {
    sessionStorage.removeItem(DREAM_RETURN_PRESENTATION_KEY);
    return false;
  }
}

// apps/product/experience_shell/src/dream_runtime.ts
var AMBIENT_AUDIO = DREAM_RUNTIME_ASSETS.openingTheme.source;
var ABU_WAIT = DREAM_RUNTIME_ASSETS.abuSeated.fallback || DREAM_RUNTIME_ASSETS.abuSeated.poster || "";
var ABU_WALK = DREAM_RUNTIME_ASSETS.abuWalk.fallback || DREAM_RUNTIME_ASSETS.abuWalk.poster || "";
var ABU_REST = DREAM_RUNTIME_ASSETS.abuSeated.poster || DREAM_RUNTIME_ASSETS.abuSeated.source;
var ENTER_HINT_DELAY_MS = 4200;
var FOLLOW_DELAY_MS = 620;
var TREE_TOUCH_DISTANCE = 13;
var MIRROR_POLL_MS = 5e3;
var FOG_CROSSING_MS = 2300;
var SELF_RECOGNITION_END_MS = 5400;
var LOCAL_MIST_REENTRY_MS = 1500;
var HEARTBEAT_MS = 3e4;
var CHECKPOINT_MS = 12e3;
var PENDING_DEPARTURE_KEY = "deepbazi.dream.pending-departure.v1";
var PENDING_GAME_ACTION_KEY = "deepbazi.dream.pending-game-action.v1";
var TREE_QUESTION_STATE_KEY = "deepbazi.dream.tree-question-map.v1";
async function bootDreamExperience(root2) {
  const runtime = new DreamFirstVisitRuntime(root2);
  await runtime.boot();
}
var DreamFirstVisitRuntime = class {
  constructor(root2) {
    this.root = root2;
    this.root.addEventListener("pointerdown", (event) => this.handlePointerDown(event));
    this.root.addEventListener("pointermove", (event) => this.handlePointerMove(event));
    this.root.addEventListener("pointerup", (event) => void this.handlePointerUp(event));
    this.root.addEventListener("pointercancel", (event) => this.handlePointerCancel(event));
    this.root.addEventListener("click", (event) => void this.handleCommand(event));
    this.root.addEventListener("input", (event) => this.handleGameInput(event));
    this.root.addEventListener("change", (event) => this.handleGameInput(event));
    window.addEventListener("keydown", (event) => void this.handleKeyDown(event));
    window.addEventListener("popstate", () => void this.handleHistoryReturn());
    document.addEventListener("visibilitychange", () => void this.handleVisibilityChange());
    window.addEventListener("online", () => void this.resumePendingDeparture());
    window.addEventListener("online", () => void this.resumePendingGameAction());
    window.addEventListener("pagehide", () => void this.handlePageHide());
  }
  story = new DreamStoryRuntime();
  visit = null;
  encounter = null;
  trees = [];
  reveal = null;
  mirror = null;
  phase = "fog_wait";
  user = { x: 50, y: 88 };
  abu = { x: 47, y: 76 };
  pointer = null;
  masks = /* @__PURE__ */ new Map();
  trail = [];
  movementFrame = 0;
  previousFrameAt = 0;
  tapMotion = null;
  userMoving = false;
  abuFollowing = false;
  abuFacing = "right";
  totalTravel = 0;
  followNotBefore = Number.POSITIVE_INFINITY;
  nearestResidentRef = "";
  hintTimer = 0;
  revealTimer = 0;
  mirrorPollTimer = 0;
  mirrorHistoryActive = false;
  suppressNextPop = false;
  ambient = null;
  sceneStartedAt = Date.now();
  canonicalAbu = false;
  heartbeatTimer = 0;
  checkpointTimer = 0;
  recoverySequence = 0;
  departureCommitSequence = 0;
  departureIntentPending = false;
  departureIntentActive = false;
  departureCommitPending = false;
  lastStableUser = { x: 50, y: 88 };
  visibilityRequestInFlight = false;
  visibilityReconcilePending = false;
  forestHistoryActive = false;
  gameRounds = [];
  gameContentUnavailable = false;
  gameAttempt = null;
  gameResult = null;
  gameLens = "overview";
  gameDraft = this.emptyGameDraft();
  gameSealConfirmation = false;
  gameCastConfirmation = false;
  gameBusy = false;
  gameStatusMessage = "";
  gameHistoryActive = false;
  gamePollTimer = 0;
  gameShellOpen = false;
  porchIndex = 0;
  porchEntering = true;
  porchIntroTimer = 0;
  porchOrbitTimer = 0;
  porchWhisperTimer = 0;
  porchWhisper = "";
  spokenRoundIds = /* @__PURE__ */ new Set();
  porchPointer = null;
  suppressNextPorchSelection = false;
  gameLensOpen = false;
  gameLensHistoryActive = false;
  gameQuestionHistoryActive = false;
  gameMediaCue = "none";
  gameMediaTimer = 0;
  gameTreeState = {
    attemptId: "",
    activeNode: "",
    judgmentStep: "outcome",
    draft: this.emptyGameDraft()
  };
  gameRevealAct = "user";
  async boot() {
    this.renderPreflight();
    try {
      if (await this.resolveCompletedDeparture()) return;
      const route = parseDreamRoute();
      this.visit = await this.acquireVisit(route.visitId);
      if (!this.visit) return;
      this.recoverySequence = this.visit.recovery_sequence;
      this.departureCommitSequence = this.visit.departure_commit_sequence;
      const pendingDeparture = this.readPendingDeparture();
      if (pendingDeparture?.visitId === this.visit.visit_id) {
        await this.resumePendingDeparture();
        if (this.phase === "departed" || this.departureCommitPending) return;
      }
      if (["HOME_GROVE", "PATH_OFFERED", "DREAM_ENTERING"].includes(this.visit.state)) {
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
      }
      if ((this.visit.is_return_visit || this.visit.runtime_state === "LOCAL_MIST_REENTRY") && this.visit.runtime_state !== "FOREST_ACTIVE") {
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
      }
      this.encounter = await loadDreamEncounter(this.visit.visit_id);
      this.trees = placeTrees(this.encounter.trees);
      await this.loadGameRounds();
      if (this.gameRounds.length) await preloadDreamPorchScenes();
      this.sceneStartedAt = readSceneAnchor(this.visit.visit_id);
      this.applyServerNavigationState();
      this.renderGrove();
      this.activateForestHistory();
      this.startControlLoops();
      if (this.gameRounds.length || this.gameContentUnavailable) {
        this.gameShellOpen = true;
        if (!this.gameRounds.length) {
          this.porchEntering = false;
          this.phase = "free_roam";
          this.syncSceneDom();
          this.renderGameLayer();
          return;
        }
        this.porchEntering = !this.visit.is_return_visit;
        this.playAmbient();
        if (this.visit.is_return_visit || this.visit.runtime_state === "LOCAL_MIST_REENTRY") {
          await this.beginReturnVisit();
        } else {
          this.phase = "free_roam";
          this.syncSceneDom();
        }
        await this.resumeGameFromRoute();
        if (!this.gameAttempt) this.renderGameLayer();
        await this.resumePendingGameAction();
        return;
      }
      if (this.visit.is_return_visit || this.visit.runtime_state === "LOCAL_MIST_REENTRY") {
        await this.beginReturnVisit();
        await this.resumeGameFromRoute();
        await this.resumePendingGameAction();
        return;
      }
      const routeMatchesVisit = !route.visitId || route.visitId === this.visit.visit_id;
      const sceneRef = (routeMatchesVisit ? route.sceneRef : "") || this.visit.selected_scene_ref;
      if (sceneRef) {
        await this.resumeSelectedTree(
          sceneRef,
          routeMatchesVisit && route.mirror || this.visit.state === "MIRROR_OPEN"
        );
      } else {
        this.startEntranceHint();
      }
      await this.resumeGameFromRoute();
      await this.resumePendingGameAction();
    } catch (error) {
      this.renderError(error);
    }
  }
  async acquireVisit(routeVisitId) {
    try {
      return routeVisitId ? await loadDreamVisit(routeVisitId) : await createDreamVisit("");
    } catch (error) {
      const code = this.errorCode(error);
      if ([
        "dream_control_takeover_required",
        "dream_control_lease_required",
        "dream_control_lease_superseded",
        "dream_control_lease_stale",
        "dream_control_lease_expired"
      ].includes(code)) {
        this.renderTakeover(routeVisitId);
        return null;
      }
      throw error;
    }
  }
  renderTakeover(routeVisitId) {
    this.root.innerHTML = `<main class="dream-state dream-control-choice" aria-labelledby="dream-control-title">
      <img src="${ABU_REST}" alt="\u963F\u5E03\u5B89\u9759\u5750\u7740">
      <h1 id="dream-control-title">\u68A6\u5883\u6B63\u5728\u53E6\u4E00\u5904\u7EE7\u7EED</h1>
      <p>\u8FD9\u91CC\u4E0D\u4F1A\u540C\u65F6\u63A7\u5236\u540C\u4E00\u7247\u6797\u5883\u3002</p>
      <div class="dream-control-actions">
        <button class="dream-command" type="button" data-dream-takeover>\u4ECE\u8FD9\u91CC\u63A5\u7BA1</button>
        <a class="dream-command is-quiet" href="/experience">\u6682\u4E0D\u8FDB\u5165</a>
      </div>
    </main>`;
    this.root.querySelector("[data-dream-takeover]")?.addEventListener("click", async () => {
      try {
        const visit = routeVisitId ? await takeoverDreamVisit(routeVisitId) : await createDreamVisit("", true);
        location.replace(`/experience/dream/visits/${encodeURIComponent(visit.visit_id || routeVisitId)}`);
      } catch (error) {
        this.renderError(error);
      }
    });
  }
  applyServerNavigationState() {
    if (!this.visit) return;
    const resolved = this.visit.anchor_resolution;
    if (resolved) {
      this.user = { ...resolved.position };
      this.lastStableUser = { ...resolved.position };
    }
    const abu = this.visit.canonical_abu;
    if (abu) {
      this.abu = { ...abu.public_position };
      this.canonicalAbu = true;
    }
  }
  acceptVisit(visit) {
    this.visit = visit;
    this.recoverySequence = Math.max(this.recoverySequence, visit.recovery_sequence);
    this.departureCommitSequence = Math.max(
      this.departureCommitSequence,
      visit.departure_commit_sequence
    );
    return visit;
  }
  async beginReturnVisit() {
    if (!this.visit) return;
    this.reveal = null;
    this.mirror = null;
    this.nearestResidentRef = "";
    this.phase = "local_mist_reentry";
    this.syncSceneDom();
    this.announce("\u96FE\u53EA\u5728\u4F60\u8EAB\u8FB9\u8F7B\u8F7B\u6563\u5F00\u3002\u6797\u4E2D\u7684\u65F6\u95F4\u4E00\u76F4\u5728\u7EE7\u7EED\u3002");
    this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
    await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 180 : LOCAL_MIST_REENTRY_MS);
    if (this.phase !== "local_mist_reentry") return;
    this.phase = "free_roam";
    this.syncSceneDom();
  }
  activateForestHistory() {
    if (this.forestHistoryActive || !this.visit) return;
    history.replaceState(
      { dreamForest: true, visitId: this.visit.visit_id },
      "",
      location.href
    );
    history.pushState(
      { dreamForestGuard: true, visitId: this.visit.visit_id },
      "",
      location.href
    );
    this.forestHistoryActive = true;
  }
  renderPreflight() {
    this.root.innerHTML = `<main class="dream-first-visit dream-preflight" aria-label="\u963F\u5E03\u68A6\u5883">
      <div class="dream-grove-background" aria-hidden="true"></div>
      <div class="dream-fog dream-fog-front" aria-hidden="true"></div>
      <img class="dream-abu dream-abu-preflight" src="${ABU_WAIT}" alt="\u963F\u5E03\u5728\u96FE\u4E2D\u7B49\u5F85">
    </main>`;
  }
  renderGrove() {
    if (!this.visit) return;
    this.root.innerHTML = `<main class="dream-first-visit" data-phase="${this.phase}" aria-label="\u963F\u5E03\u68A6\u5883\u4E2D\u7684\u4E09\u6811\u6797\u5883">
      <audio class="dream-ambient-audio" preload="metadata" loop src="${AMBIENT_AUDIO}"></audio>
      <div class="dream-grove-background" aria-hidden="true"></div>
      <div class="dream-grove-parallax" aria-hidden="true"></div>
      <section class="dream-grove" data-dream-ground tabindex="0" aria-label="\u53EF\u81EA\u7531\u884C\u8D70\u7684\u6797\u5730">
        <div class="dream-canopy-shadow" aria-hidden="true"></div>
        <div class="dream-departure-path" aria-hidden="true">
          <span class="dream-departure-mist"></span>
          <span class="dream-departure-ground"></span>
        </div>
        <span class="dream-user-presence" aria-hidden="true"></span>
        <span class="dream-abu-shadow" aria-hidden="true"></span>
        <img class="dream-abu" src="${ABU_WAIT}" alt="\u963F\u5E03" draggable="false">
        <div class="dream-paw-hint" aria-live="polite"><i aria-hidden="true"></i><span>\u8F7B\u89E6\uFF0C\u8DDF\u4E0A\u963F\u5E03</span></div>
        <p class="dream-abu-line" aria-live="polite">\u6162\u4E00\u70B9\u3002\u5148\u542C\u3002</p>
        <div class="dream-fog dream-fog-back" aria-hidden="true"></div>
        <div class="dream-fog dream-fog-front" aria-hidden="true"></div>
      </section>
      <section class="dream-mirror-layer" aria-label="\u6839\u955C\u4E2D\u7684\u547D\u76D8" aria-hidden="true"></section>
      <section class="dream-game-layer" aria-label="\u963F\u5E03\u95EE\u679C\u4E09\u6811\u5C40" aria-hidden="true"></section>
      <div class="dream-runtime-veil" aria-hidden="true"><span></span></div>
      <nav class="sr-only dream-a11y-actions" aria-label="\u68A6\u5883\u65E0\u969C\u788D\u52A8\u4F5C">
        <button type="button" data-dream-a11y="follow">\u8DDF\u4E0A\u963F\u5E03</button>
        <button type="button" data-dream-a11y="open-mirror">\u89E6\u78B0\u6839\u955C</button>
        <button type="button" data-dream-a11y="leave-mirror">\u8FD4\u56DE\u6797\u5730</button>
        <button type="button" data-dream-a11y="leave-dream">\u79BB\u5F00\u68A6\u5883</button>
      </nav>
      <p class="sr-only" data-dream-announcer aria-live="polite"></p>
    </main>`;
    this.ambient = this.root.querySelector(".dream-ambient-audio");
    this.syncSceneDom();
  }
  async resumeSelectedTree(sceneRef, resumeMirror) {
    if (!this.visit) return;
    await loadDreamTree(this.visit.visit_id, sceneRef);
    this.nearestResidentRef = sceneRef;
    const placement = this.treeByRef(sceneRef);
    if (placement) {
      const point = this.treeWorldPoint(placement);
      this.user = { x: point.x - 5, y: Math.min(88, point.y + 3) };
      this.abu = { x: this.user.x - 5, y: this.user.y + 4 };
    }
    if (resumeMirror && this.visit.active_onecanvas_view_ref) {
      this.phase = "mirror_ready";
      this.syncSceneDom();
      await this.openMirror(this.visit.active_onecanvas_view_ref, false);
      return;
    }
    if (this.visit.state === "MIRROR_OPEN") {
      this.acceptVisit(await closeDreamMirror(this.visit.visit_id));
    }
    this.reveal = await prepareDreamReveal(this.visit.visit_id, sceneRef);
    this.phase = "mirror_ready";
    this.syncSceneDom();
  }
  startEntranceHint() {
    window.clearTimeout(this.hintTimer);
    this.hintTimer = window.setTimeout(() => {
      if (this.phase === "fog_wait") {
        this.root.querySelector(".dream-first-visit")?.classList.add("show-paw-hint");
      }
    }, ENTER_HINT_DELAY_MS);
  }
  beginFogEntrance() {
    if (this.phase !== "fog_wait") return;
    window.clearTimeout(this.hintTimer);
    this.playAmbient();
    this.phase = "fog_crossing";
    this.tapMotion = null;
    this.userMoving = false;
    this.abuFollowing = false;
    this.user = { x: 50, y: 74 };
    this.abu = { x: 48, y: 62 };
    this.syncSceneDom();
    this.announce("\u4F60\u8DDF\u7740\u963F\u5E03\u7A7F\u8FC7\u96FE\u754C\u3002\u6162\u4E00\u70B9\uFF0C\u5148\u542C\u3002");
    window.setTimeout(() => {
      if (this.phase !== "fog_crossing") return;
      this.phase = "self_recognition";
      this.user = { x: 42, y: 68 };
      const own = this.trees.find((tree) => tree.own);
      if (own) {
        const root2 = this.treeWorldPoint(own);
        this.abu = { x: root2.x + 4, y: root2.y };
      }
      this.syncSceneDom();
      this.announce("\u4E00\u6761\u6811\u6839\u63A5\u4F4F\u4E86\u4F60\u811A\u8FB9\u7684\u5FAE\u5149\u3002\u90A3\u68F5\u6811\u5148\u8BA4\u51FA\u4E86\u4F60\u3002");
    }, FOG_CROSSING_MS);
    window.setTimeout(() => {
      if (this.phase !== "self_recognition") return;
      this.phase = "free_roam";
      const own = this.trees.find((tree) => tree.own);
      if (own) {
        const root2 = this.treeWorldPoint(own);
        this.abu = { x: root2.x + 3, y: root2.y };
      }
      this.trail = [{ at: performance.now(), point: { ...this.user } }];
      this.totalTravel = 0;
      this.followNotBefore = Number.POSITIVE_INFINITY;
      this.syncSceneDom();
      this.announce("\u6797\u5730\u5DF2\u7ECF\u8BA9\u5F00\u3002\u4F60\u53EF\u4EE5\u81EA\u5DF1\u51B3\u5B9A\u5F80\u54EA\u91CC\u8D70\u3002");
    }, SELF_RECOGNITION_END_MS);
  }
  handlePointerDown(event) {
    const commandTarget = event.target instanceof Element ? event.target : null;
    const porchCamera = commandTarget?.closest("[data-dream-tree-porch]");
    const porchTree = commandTarget?.closest(".dream-tree-porch-tree");
    const porchControl = commandTarget?.closest(
      "button, a, input, textarea, select"
    );
    if (porchCamera && (!porchControl || porchTree) && !this.porchPointer && !this.gameAttempt) {
      event.preventDefault();
      porchCamera.setPointerCapture(event.pointerId);
      this.porchPointer = {
        id: event.pointerId,
        startClientX: event.clientX,
        currentClientX: event.clientX,
        camera: porchCamera,
        treeIndex: porchTree?.dataset.porchIndex ? Number(porchTree.dataset.porchIndex) : null
      };
      return;
    }
    const scene2 = this.root.querySelector(".dream-grove");
    if (!scene2 || !this.visit || this.pointer) return;
    const target = commandTarget;
    if (target?.closest(
      "button, a, input, textarea, select, [role='button'], [data-dream-game-round], [data-dream-game-command], [data-dream-a11y]"
    )) return;
    if (this.gameAttempt) return;
    if (this.phase === "fog_wait") {
      event.preventDefault();
      this.beginFogEntrance();
      return;
    }
    if (this.phase === "mirror_open") {
      const exitGeometry = this.mirrorExitGeometry(event);
      if (!exitGeometry) return;
      event.preventDefault();
      exitGeometry.layer.setPointerCapture(event.pointerId);
      exitGeometry.layer.classList.add("is-pulling-mirror");
      this.pointer = {
        id: event.pointerId,
        mode: "mirror_exit",
        startedAt: performance.now(),
        startClientX: event.clientX,
        startClientY: event.clientY,
        target: { x: event.clientX, y: event.clientY },
        sceneRef: this.visit.selected_scene_ref,
        moved: false,
        crossedMirrorBoundary: false,
        mirrorBoundaryClientY: exitGeometry.boundaryClientY
      };
      return;
    }
    if (!["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) return;
    let point = this.worldPointFromClient(event.clientX, event.clientY);
    const touchedTree = this.hitTreeAt(event.clientX, event.clientY);
    const mirror = event.target instanceof Element ? event.target.closest(".dream-root-mirror") : null;
    let mode = "ground";
    let sceneRef = "";
    if (mirror && this.phase === "mirror_ready" && mirror.dataset.rootMirror === this.visit.selected_scene_ref) {
      mode = "root_mirror";
      sceneRef = this.visit.selected_scene_ref;
    } else if (touchedTree && this.isWithinTouchDistance(touchedTree)) {
      mode = "tree_touch";
      sceneRef = touchedTree.scene_ref;
    } else if (touchedTree && !touchedTree.own) {
      point = this.treeApproachPoint(touchedTree);
      sceneRef = touchedTree.scene_ref;
    }
    event.preventDefault();
    scene2.setPointerCapture(event.pointerId);
    this.pointer = {
      id: event.pointerId,
      mode,
      startedAt: performance.now(),
      startClientX: event.clientX,
      startClientY: event.clientY,
      target: point,
      sceneRef,
      moved: false,
      crossedMirrorBoundary: false,
      mirrorBoundaryClientY: 0
    };
    if (mode === "ground") this.startMovementLoop();
  }
  handlePointerMove(event) {
    if (this.porchPointer?.id === event.pointerId) {
      this.porchPointer.currentClientX = event.clientX;
      const drag = clamp(
        (event.clientX - this.porchPointer.startClientX) / Math.max(1, this.porchPointer.camera.clientWidth),
        -0.32,
        0.32
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-x",
        `${drag * this.porchPointer.camera.clientWidth}px`
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-sky",
        `${drag * this.porchPointer.camera.clientWidth * 0.18}px`
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-far",
        `${drag * this.porchPointer.camera.clientWidth * 0.42}px`
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-ground",
        `${drag * this.porchPointer.camera.clientWidth * 0.7}px`
      );
      return;
    }
    if (!this.pointer || this.pointer.id !== event.pointerId) return;
    const distance = Math.hypot(
      event.clientX - this.pointer.startClientX,
      event.clientY - this.pointer.startClientY
    );
    if (distance > 8) this.pointer.moved = true;
    if (this.pointer.mode === "ground") {
      this.pointer.target = this.worldPointFromClient(event.clientX, event.clientY);
      return;
    }
    if (this.pointer.mode === "mirror_exit") {
      const pull = Math.max(0, event.clientY - this.pointer.startClientY);
      this.pointer.crossedMirrorBoundary = event.clientY >= this.pointer.mirrorBoundaryClientY && pull >= 28;
      const layer = this.root.querySelector(".dream-mirror-layer");
      const distanceToBoundary = Math.max(
        48,
        this.pointer.mirrorBoundaryClientY - this.pointer.startClientY
      );
      layer?.style.setProperty(
        "--mirror-pull",
        String(Math.min(1, pull / (distanceToBoundary + 42)))
      );
    }
  }
  async handlePointerUp(event) {
    if (this.porchPointer?.id === event.pointerId) {
      const pointer = this.porchPointer;
      this.porchPointer = null;
      this.resetPorchDrag(pointer.camera);
      const travel = pointer.currentClientX - pointer.startClientX;
      if (Math.abs(travel) >= Math.min(72, pointer.camera.clientWidth * 0.16)) {
        this.suppressNextPorchSelection = true;
        window.setTimeout(() => {
          this.suppressNextPorchSelection = false;
        }, 250);
        this.shiftPorch(travel < 0 ? 1 : -1);
      } else if (pointer.treeIndex !== null && Number.isInteger(pointer.treeIndex) && pointer.treeIndex >= 0 && pointer.treeIndex < this.gameRounds.length) {
        this.suppressNextPorchSelection = true;
        window.setTimeout(() => {
          this.suppressNextPorchSelection = false;
        }, 250);
        if (pointer.treeIndex === this.porchIndex) {
          await this.commitFocusedTree();
        } else {
          this.focusPorchIndex(pointer.treeIndex);
        }
      }
      return;
    }
    if (!this.pointer || this.pointer.id !== event.pointerId) return;
    const session = this.pointer;
    this.pointer = null;
    if (session.mode === "ground") {
      if (performance.now() - session.startedAt < 180) {
        this.startTapMotion(session.target, session.sceneRef ? 100 : 5.5);
      } else {
        this.startMovementLoop();
      }
      return;
    }
    this.stopMovementLoopIfIdle();
    if (session.mode === "tree_touch" && !session.moved) {
      await this.touchTree(session.sceneRef);
      return;
    }
    if (session.mode === "root_mirror" && !session.moved && this.reveal) {
      await this.openMirror(this.reveal.onecanvas_view_ref, true);
      return;
    }
    if (session.mode === "mirror_exit") {
      const layer = this.root.querySelector(".dream-mirror-layer");
      layer?.classList.remove("is-pulling-mirror");
      layer?.style.removeProperty("--mirror-pull");
      if (session.crossedMirrorBoundary) await this.closeMirror("gesture");
    }
  }
  handlePointerCancel(event) {
    if (this.porchPointer?.id === event.pointerId) {
      this.resetPorchDrag(this.porchPointer.camera);
      this.porchPointer = null;
      return;
    }
    if (!this.pointer || this.pointer.id !== event.pointerId) return;
    this.pointer = null;
    this.tapMotion = null;
    this.stopMovementLoopIfIdle();
    const layer = this.root.querySelector(".dream-mirror-layer");
    layer?.classList.remove("is-pulling-mirror");
    layer?.style.removeProperty("--mirror-pull");
  }
  mirrorExitGeometry(event) {
    const target = event.target instanceof Element ? event.target : null;
    const layer = this.root.querySelector(".dream-mirror-layer");
    const optics = layer?.querySelector(".dream-mirror-optics");
    const boundary = layer?.querySelector(".dream-mirror-root-boundary");
    if (!target || !layer || !optics || !boundary || !layer.contains(target)) return null;
    if (target.closest(
      ".canvas-scene-node, .canvas-slot-label, .canvas-relation, .canvas-work-path, button, a"
    )) return null;
    const opticsRect = optics.getBoundingClientRect();
    const boundaryRect = boundary.getBoundingClientRect();
    const boundaryClientY = boundaryRect.top + boundaryRect.height / 2;
    if (event.clientX < opticsRect.left || event.clientX > opticsRect.right || event.clientY < opticsRect.top || event.clientY >= boundaryClientY) return null;
    return { layer, boundaryClientY };
  }
  async handleCommand(event) {
    const gameRound = event.target instanceof Element ? event.target.closest("[data-dream-game-round]") : null;
    if (gameRound?.dataset.dreamGameRound) {
      event.preventDefault();
      await this.openProblemRound(gameRound.dataset.dreamGameRound);
      return;
    }
    const gameCommand = event.target instanceof Element ? event.target.closest("[data-dream-game-command]") : null;
    if (gameCommand) {
      event.preventDefault();
      await this.handleGameCommand(gameCommand);
      return;
    }
    const target = event.target instanceof Element ? event.target.closest("[data-dream-a11y]") : null;
    if (!target) return;
    const command = target.dataset.dreamA11y;
    if (command === "follow") {
      this.beginFogEntrance();
      return;
    }
    if (command === "approach") {
      const tree = this.treeByRef(target.dataset.sceneRef || "");
      if (!tree || tree.own) return;
      const point = this.treeWorldPoint(tree);
      this.user = { x: point.x - 5, y: Math.min(88, point.y + 3) };
      this.nearestResidentRef = tree.scene_ref;
      this.syncSceneDom();
      this.announce(`\u4F60\u5DF2\u7ECF\u8D70\u5230${tree.resident_label}\u7684\u751F\u547D\u6811\u524D\u3002`);
      return;
    }
    if (command === "touch" && this.nearestResidentRef) {
      await this.touchTree(this.nearestResidentRef);
      return;
    }
    if (command === "open-mirror" && this.reveal) {
      await this.openMirror(this.reveal.onecanvas_view_ref, true);
      return;
    }
    if (command === "leave-mirror" && this.phase === "mirror_open") {
      await this.closeMirror("accessibility");
      return;
    }
    if (command === "leave-dream" && ["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) {
      await this.departDream("SEMANTIC_EXIT");
      return;
    }
    if (command === "open-problem-flower") {
      await this.openProblemRound(target.dataset.roundId || "");
    }
  }
  async handleKeyDown(event) {
    if (!this.gameAttempt && this.gameShellOpen && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
      event.preventDefault();
      this.shiftPorch(event.key === "ArrowRight" ? 1 : -1);
      return;
    }
    if (event.key !== "Escape" && event.key !== "BrowserBack") return;
    if (this.gameAttempt) {
      event.preventDefault();
      if (this.gameLensOpen) {
        this.closeGameLens("accessibility");
      } else if (this.gameTreeState.activeNode) {
        this.closeTreeQuestion("accessibility");
      } else if (this.gameAttempt.state === "JUDGMENT_DRAFTING" && this.gameTreeState.judgmentStep !== "outcome") {
        this.stepJudgmentBack();
      } else {
        await this.returnToTreePorch("accessibility");
      }
      return;
    }
    if (this.gameShellOpen) {
      event.preventDefault();
      await this.departDream("SEMANTIC_EXIT");
      return;
    }
    if (this.phase === "mirror_open" || this.phase === "mirror_opening") {
      event.preventDefault();
      await this.closeMirror("accessibility");
      return;
    }
    if (!["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) return;
    event.preventDefault();
    await this.departDream("SEMANTIC_EXIT");
  }
  async handleHistoryReturn() {
    if (this.suppressNextPop) {
      this.suppressNextPop = false;
      return;
    }
    if (this.gameAttempt) {
      if (this.gameLensOpen) {
        this.closeGameLens("history");
      } else if (this.gameTreeState.activeNode) {
        this.closeTreeQuestion("history");
      } else if (this.gameAttempt.state === "JUDGMENT_DRAFTING" && this.gameTreeState.judgmentStep !== "outcome") {
        this.stepJudgmentBack();
        this.restoreGameHistoryGuard();
      } else {
        this.gameHistoryActive = false;
        await this.returnToTreePorch("history");
      }
      return;
    }
    if (this.phase === "mirror_open" || this.phase === "mirror_opening") {
      this.mirrorHistoryActive = false;
      await this.closeMirror("history");
      return;
    }
    if (["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) {
      history.pushState(
        { dreamForestGuard: true, visitId: this.visit?.visit_id || "" },
        "",
        location.href
      );
      await this.departDream("SEMANTIC_EXIT");
    }
  }
  async handleVisibilityChange() {
    this.resyncSceneClock();
    if (!this.visit) return;
    if (this.visibilityRequestInFlight) {
      this.visibilityReconcilePending = true;
      return;
    }
    const requestedVisibility = document.visibilityState;
    this.visibilityRequestInFlight = true;
    try {
      if (requestedVisibility === "hidden") {
        this.clearSensitiveProjection();
        this.phase = "visit_suspended";
        this.syncSceneDom();
        this.acceptVisit(await suspendDreamVisit(
          this.visit.visit_id,
          this.navigationSample(this.lastStableUser),
          ++this.recoverySequence,
          true
        ));
        return;
      }
      if (this.phase === "visit_suspended" || this.visit.runtime_state === "VISIT_SUSPENDED") {
        this.acceptVisit(await recoverDreamVisit(this.visit.visit_id));
        this.applyServerNavigationState();
        this.phase = "local_mist_reentry";
        this.syncSceneDom();
        await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 120 : 780);
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
        this.phase = "free_roam";
        this.syncSceneDom();
        if (this.gameAttempt) {
          this.gameAttempt = await loadDreamGameAttempt(
            this.visit.visit_id,
            this.gameAttempt.attempt_id
          );
          if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
            this.gameResult = await loadDreamGameResult(
              this.visit.visit_id,
              this.gameAttempt.attempt_id
            );
          }
          this.renderGameLayer();
          this.startGamePolling();
        } else if (this.gameShellOpen) {
          this.renderGameLayer();
        }
      } else if (this.phase === "mirror_open") {
        await this.validateOpenMirror();
      } else if (this.gameAttempt) {
        await this.validateOpenGame();
        this.renderGameLayer();
        this.startGamePolling();
      }
    } catch (error) {
      this.handleRuntimeFailure(error);
    } finally {
      this.visibilityRequestInFlight = false;
      const shouldReconcile = this.visibilityReconcilePending || document.visibilityState !== requestedVisibility;
      this.visibilityReconcilePending = false;
      if (shouldReconcile && this.visit && !["departure_committing", "departed"].includes(this.phase)) {
        queueMicrotask(() => void this.handleVisibilityChange());
      }
    }
  }
  handlePageHide() {
    if (!this.visit || this.phase === "departed" || this.departureCommitPending || this.visibilityRequestInFlight) return;
    this.clearSensitiveProjection();
    void suspendDreamVisit(
      this.visit.visit_id,
      this.navigationSample(this.lastStableUser),
      ++this.recoverySequence,
      true
    ).catch(() => void 0);
  }
  startMovementLoop() {
    if (this.movementFrame) return;
    this.previousFrameAt = performance.now();
    const tick = (now) => {
      const deltaSeconds = Math.min(0.05, (now - this.previousFrameAt) / 1e3);
      this.previousFrameAt = now;
      const groundPointer = this.pointer?.mode === "ground" ? this.pointer : null;
      let userMoved = false;
      if (groundPointer) {
        const elapsed = now - groundPointer.startedAt;
        if (elapsed > 180) {
          const remaining = pointDistance(this.user, groundPointer.target);
          const acceleration = clamp((elapsed - 180) / 360, 0.18, 1);
          const braking = clamp(remaining / 7, 0.28, 1);
          userMoved = this.moveToward(
            groundPointer.target,
            15 * acceleration * braking * deltaSeconds,
            now
          );
        }
      }
      if (this.tapMotion) userMoved = this.advanceTapMotion(now) || userMoved;
      const abuMoved = this.advanceAbuFollower(now, deltaSeconds);
      const motionStateChanged = this.userMoving !== userMoved || this.abuFollowing !== abuMoved;
      this.userMoving = userMoved;
      this.abuFollowing = abuMoved;
      if (userMoved || abuMoved || motionStateChanged) this.syncSceneDom();
      if (groundPointer || this.tapMotion || this.shouldContinueAbuFollower(now)) {
        this.movementFrame = requestAnimationFrame(tick);
        return;
      }
      this.movementFrame = 0;
      this.userMoving = false;
      this.abuFollowing = false;
      this.followNotBefore = Number.POSITIVE_INFINITY;
      this.syncSceneDom();
    };
    this.movementFrame = requestAnimationFrame(tick);
  }
  stopMovementLoop() {
    if (this.movementFrame) cancelAnimationFrame(this.movementFrame);
    this.movementFrame = 0;
    this.tapMotion = null;
    this.userMoving = false;
    this.abuFollowing = false;
    this.followNotBefore = Number.POSITIVE_INFINITY;
  }
  stopMovementLoopIfIdle() {
    if (this.pointer?.mode === "ground" || this.tapMotion || this.shouldContinueAbuFollower(performance.now())) {
      this.startMovementLoop();
      return;
    }
    this.stopMovementLoop();
    this.syncSceneDom();
  }
  startTapMotion(target, maximumDistance) {
    const dx = target.x - this.user.x;
    const dy = target.y - this.user.y;
    const length = Math.hypot(dx, dy);
    if (length < 0.05) return;
    const distance = Math.min(length, maximumDistance);
    const now = performance.now();
    this.tapMotion = {
      from: { ...this.user },
      to: {
        x: clamp(this.user.x + dx / length * distance, 7, 97),
        y: clamp(this.user.y + dy / length * distance, 24, 91)
      },
      startedAt: now,
      durationMs: clamp(
        500 + distance * (maximumDistance > 20 ? 76 : 54),
        620,
        maximumDistance > 20 ? 4200 : 880
      )
    };
    this.startMovementLoop();
  }
  advanceTapMotion(now) {
    if (!this.tapMotion) return false;
    const motion = this.tapMotion;
    const progress = clamp((now - motion.startedAt) / motion.durationMs, 0, 1);
    const eased = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;
    const previous = { ...this.user };
    this.user = {
      x: motion.from.x + (motion.to.x - motion.from.x) * eased,
      y: motion.from.y + (motion.to.y - motion.from.y) * eased
    };
    this.recordUserMotion(previous, now);
    if (progress >= 1) this.tapMotion = null;
    return pointDistance(previous, this.user) > 0.01;
  }
  moveToward(target, maximumDistance, now) {
    const dx = target.x - this.user.x;
    const dy = target.y - this.user.y;
    const length = Math.hypot(dx, dy);
    if (length < 0.05 || maximumDistance <= 0) return false;
    const distance = Math.min(length, maximumDistance);
    const previous = { ...this.user };
    this.user = {
      x: clamp(this.user.x + dx / length * distance, 7, 97),
      y: clamp(this.user.y + dy / length * distance, 24, 91)
    };
    this.recordUserMotion(previous, now);
    return true;
  }
  recordUserMotion(previous, now) {
    const distance = pointDistance(previous, this.user);
    if (distance <= 1e-3) return;
    if (!Number.isFinite(this.followNotBefore)) {
      this.followNotBefore = now + FOLLOW_DELAY_MS;
    }
    this.totalTravel += distance;
    if (this.user.x <= 93 && this.user.y <= 91 && !(this.user.x >= 88 && this.user.y >= 80)) {
      this.lastStableUser = { ...this.user };
    }
    this.trail.push({ at: now, point: { ...this.user } });
    while (this.trail.length > 2 && this.trail[1].at < now - 2600) this.trail.shift();
    this.updateNearestResident();
    void this.updateDepartureState();
  }
  advanceAbuFollower(now, deltaSeconds) {
    if (this.totalTravel < 2.4) return false;
    if (now < this.followNotBefore) return false;
    const delayed = [...this.trail].reverse().find((item) => item.at <= now - FOLLOW_DELAY_MS);
    if (!delayed) return false;
    const dx = delayed.point.x - this.abu.x;
    const dy = delayed.point.y - this.abu.y;
    const distance = Math.hypot(dx, dy);
    if (distance <= 2.2) return false;
    if (Math.abs(dx) > 0.08) this.abuFacing = dx < 0 ? "left" : "right";
    const speed = clamp(distance * 1.28, 4.4, 10.6);
    const step = Math.min(distance, speed * deltaSeconds);
    this.abu = {
      x: clamp(this.abu.x + dx / distance * step, 7, 93),
      y: clamp(this.abu.y + dy / distance * step, 24, 91)
    };
    return true;
  }
  shouldContinueAbuFollower(now) {
    if (this.totalTravel < 2.4 || this.trail.length === 0) return false;
    if (now < this.followNotBefore) return true;
    const latest = this.trail[this.trail.length - 1];
    if (now - latest.at < FOLLOW_DELAY_MS + 40) return true;
    const delayed = [...this.trail].reverse().find((item) => item.at <= now - FOLLOW_DELAY_MS);
    return Boolean(delayed && pointDistance(this.abu, delayed.point) > 2.2);
  }
  updateNearestResident() {
    const residents = this.trees.filter((tree) => !tree.own);
    const nearest = residents.map((tree) => ({ tree, distance: pointDistance(this.user, this.treeWorldPoint(tree)) })).sort((left, right) => left.distance - right.distance)[0];
    this.nearestResidentRef = nearest && nearest.distance < 22 ? nearest.tree.scene_ref : "";
  }
  async updateDepartureState() {
    if (!this.visit || this.departureIntentPending || this.departureCommitPending || !["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) return;
    if (this.user.x >= 95 && this.user.y >= 86) {
      await this.departDream("SPATIAL_BOUNDARY", { ...this.user });
      return;
    }
    const insideMist = this.user.x >= 88 && this.user.y >= 80;
    if (insideMist === this.departureIntentActive) return;
    this.departureIntentPending = true;
    try {
      this.acceptVisit(await setDreamDepartureIntent(this.visit.visit_id, insideMist));
      this.departureIntentActive = insideMist;
      this.phase = insideMist ? "departure_intent" : this.reveal ? "mirror_ready" : "free_roam";
      if (this.ambient) this.ambient.volume = insideMist ? 0.045 : 0.12;
      this.syncSceneDom();
    } catch (error) {
      this.handleRuntimeFailure(error);
    } finally {
      this.departureIntentPending = false;
    }
  }
  async departDream(trigger, boundaryPosition) {
    if (!this.visit || this.departureCommitPending || this.phase === "departed") return;
    if (this.phase === "mirror_open" || this.phase === "mirror_opening") {
      await this.closeMirror("accessibility");
      return;
    }
    this.departureCommitPending = true;
    this.stopControlLoops();
    this.stopMovementLoop();
    this.stopMirrorPolling();
    this.clearSensitiveProjection();
    this.phase = "departure_committing";
    this.syncSceneDom();
    if (this.ambient) this.ambient.volume = 0.025;
    const commitSequence = ++this.departureCommitSequence;
    const navigation = this.navigationSample(this.lastStableUser);
    const pending = {
      visitId: this.visit.visit_id,
      trigger,
      navigation,
      boundaryPosition: boundaryPosition || null,
      commitSequence,
      hasKnowledgeSeed: Boolean(this.gameResult?.knowledge_seed)
    };
    sessionStorage.setItem(PENDING_DEPARTURE_KEY, JSON.stringify(pending));
    try {
      const result = await commitDreamDeparture(
        pending.visitId,
        trigger,
        navigation,
        commitSequence,
        boundaryPosition
      );
      await this.finishDeparture(result.waking_route, pending.hasKnowledgeSeed);
    } catch (error) {
      this.departureCommitPending = false;
      if (!navigator.onLine || !(error instanceof DreamApiError)) {
        this.announce("\u96FE\u5728\u539F\u5730\u505C\u4F4F\u4E86\u3002\u8FDE\u63A5\u6062\u590D\u540E\uFF0C\u4F1A\u7EE7\u7EED\u5B8C\u6210\u8FD9\u6B21\u79BB\u5F00\u3002");
        return;
      }
      this.handleRuntimeFailure(error);
    }
  }
  async resumePendingDeparture() {
    const pending = this.readPendingDeparture();
    if (!pending || this.departureCommitPending) return;
    try {
      const result = await loadDreamDepartureResult(pending.visitId, pending.commitSequence);
      await this.finishDeparture(result.waking_route, pending.hasKnowledgeSeed);
      return;
    } catch (error) {
      if (!(error instanceof DreamApiError) || error.status !== 404) return;
    }
    if (!this.visit || this.visit.visit_id !== pending.visitId) return;
    this.departureCommitPending = true;
    try {
      const result = await commitDreamDeparture(
        pending.visitId,
        pending.trigger,
        pending.navigation,
        pending.commitSequence,
        pending.boundaryPosition || void 0
      );
      await this.finishDeparture(result.waking_route, pending.hasKnowledgeSeed);
    } catch (error) {
      this.departureCommitPending = false;
      if (navigator.onLine) this.handleRuntimeFailure(error);
    }
  }
  async resolveCompletedDeparture() {
    const pending = this.readPendingDeparture();
    if (!pending) return false;
    try {
      const result = await loadDreamDepartureResult(pending.visitId, pending.commitSequence);
      sessionStorage.removeItem(PENDING_DEPARTURE_KEY);
      clearDreamControl();
      markDreamReturnedWithSeed(pending.hasKnowledgeSeed);
      location.replace(result.waking_route);
      return true;
    } catch {
      return false;
    }
  }
  readPendingDeparture() {
    try {
      const raw = sessionStorage.getItem(PENDING_DEPARTURE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      sessionStorage.removeItem(PENDING_DEPARTURE_KEY);
      return null;
    }
  }
  async finishDeparture(wakingRoute, hasKnowledgeSeed) {
    this.departureCommitPending = false;
    this.departureIntentActive = false;
    this.phase = "departed";
    this.stopControlLoops();
    this.syncSceneDom();
    sessionStorage.removeItem(PENDING_DEPARTURE_KEY);
    clearDreamControl();
    markDreamReturnedWithSeed(hasKnowledgeSeed);
    this.announce("\u4F60\u79BB\u5F00\u4E86\u68A6\u5883\u3002\u6797\u4E2D\u7684\u65F6\u95F4\u4ECD\u4F1A\u7EE7\u7EED\u3002");
    await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 80 : 680);
    location.replace(wakingRoute);
  }
  navigationSample(position) {
    if (!this.visit) throw new DreamApiError("dream_visit_not_ready", 409);
    const ref = this.visit.world_projection_ref || currentDreamWorldProjectionRef(this.visit.visit_id);
    return {
      world_projection_ref: ref,
      world_space_ref: "dream-world:canonical-grove:v1",
      position: { x: position.x, y: position.y },
      camera_heading: 0,
      geometry_version: "dream-grove-geometry.v1"
    };
  }
  startControlLoops() {
    this.stopControlLoops();
    void this.heartbeat();
    this.heartbeatTimer = window.setInterval(() => void this.heartbeat(), HEARTBEAT_MS);
    this.checkpointTimer = window.setInterval(() => void this.checkpoint(), CHECKPOINT_MS);
  }
  stopControlLoops() {
    if (this.heartbeatTimer) window.clearInterval(this.heartbeatTimer);
    if (this.checkpointTimer) window.clearInterval(this.checkpointTimer);
    this.heartbeatTimer = 0;
    this.checkpointTimer = 0;
  }
  async heartbeat() {
    if (!this.visit || document.visibilityState !== "visible" || this.departureCommitPending) return;
    try {
      this.acceptVisit(await heartbeatDreamControl(this.visit.visit_id));
    } catch (error) {
      if (this.departureCommitPending || ["departure_committing", "departed"].includes(this.phase)) return;
      this.handleRuntimeFailure(error);
    }
  }
  async checkpoint() {
    if (!this.visit || document.visibilityState !== "visible" || this.departureCommitPending || !["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) return;
    try {
      this.acceptVisit(await checkpointDreamVisit(
        this.visit.visit_id,
        this.navigationSample(this.lastStableUser),
        ++this.recoverySequence
      ));
    } catch (error) {
      if (this.departureCommitPending || ["departure_committing", "departed"].includes(this.phase)) return;
      this.handleRuntimeFailure(error);
    }
  }
  async touchTree(sceneRef) {
    if (!this.visit || !["free_roam", "mirror_ready"].includes(this.phase)) return;
    const tree = this.treeByRef(sceneRef);
    if (!tree || tree.own || !this.isWithinTouchDistance(tree)) return;
    this.playAmbient();
    this.phase = "tree_contact";
    this.nearestResidentRef = sceneRef;
    this.syncSceneDom();
    try {
      if (this.visit.selected_scene_ref !== sceneRef) {
        this.acceptVisit(await selectDreamTree(this.visit.visit_id, sceneRef));
        history.replaceState(
          {},
          "",
          `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(sceneRef)}`
        );
      }
      await loadDreamTree(this.visit.visit_id, sceneRef);
      this.reveal = await prepareDreamReveal(this.visit.visit_id, sceneRef);
      this.phase = "reveal_settling";
      this.syncSceneDom();
      this.playRevealTone(this.reveal.reveal_kind !== "none");
      this.announce(
        this.reveal.reveal_kind === "none" ? "\u6811\u76AE\u8F7B\u8F7B\u56DE\u5E94\u4E86\u89E6\u78B0\uFF0C\u6CA1\u6709\u751F\u6210\u65B0\u7684\u547D\u7406\u542B\u4E49\u3002" : this.reveal.authorized_statement
      );
      window.clearTimeout(this.revealTimer);
      this.revealTimer = window.setTimeout(() => {
        if (this.phase !== "reveal_settling") return;
        this.phase = "mirror_ready";
        this.syncSceneDom();
        this.announce("\u6811\u6839\u95F4\u7684\u5012\u5F71\u73B0\u5728\u53EF\u4EE5\u88AB\u89E6\u78B0\u3002");
      }, this.reveal.reveal_kind === "none" ? 2100 : 3200);
    } catch (error) {
      this.handleAuthorizationOrError(error);
    }
  }
  async openMirror(viewRef, pushHistory) {
    if (!this.visit || !this.visit.selected_scene_ref) return;
    this.phase = "mirror_opening";
    this.syncSceneDom();
    try {
      this.acceptVisit(await openDreamMirror(
        this.visit.visit_id,
        viewRef,
        this.navigationSample(this.lastStableUser)
      ));
      this.mirror = await loadDreamMirror(
        this.visit.visit_id,
        this.visit.selected_scene_ref,
        viewRef
      );
      this.renderMirrorLayer();
      this.phase = "mirror_open";
      this.syncSceneDom();
      if (pushHistory) {
        history.pushState(
          { dreamMirror: true, visitId: this.visit.visit_id },
          "",
          `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(this.visit.selected_scene_ref)}/mirror`
        );
        this.mirrorHistoryActive = true;
      }
      this.startMirrorPolling();
      this.announce(
        this.mirror.verification.state === "focused" ? `${this.mirror.verification.verification_copy}${this.mirror.verification.authorized_statement}` : "\u5F53\u524D\u6682\u65E0\u5DF2\u786E\u8BA4\u4E3B\u8DEF\u5F84\u3002"
      );
    } catch (error) {
      this.handleAuthorizationOrError(error);
    }
  }
  renderMirrorLayer() {
    if (!this.mirror) return;
    const layer = this.root.querySelector(".dream-mirror-layer");
    if (!layer) return;
    layer.innerHTML = `<div class="dream-mirror-optics" aria-hidden="true"></div>
      <div class="dream-mirror-canvas-shell">
        ${renderDreamVerificationCanvas(this.mirror.canvas, this.mirror.verification)}
      </div>
      <div class="dream-mirror-water" data-mirror-exit-start aria-hidden="true">
        <span class="dream-mirror-root-boundary"></span>
        <span class="dream-mirror-forest-edge"></span>
      </div>`;
    layer.setAttribute("aria-hidden", "false");
    requestAnimationFrame(() => this.focusMirrorTarget());
  }
  async closeMirror(origin) {
    if (!this.visit || !["mirror_open", "mirror_opening", "authorization_closed"].includes(this.phase)) return;
    this.stopMirrorPolling();
    this.phase = origin === "revoked" ? "authorization_closed" : "mirror_closing";
    const layer = this.root.querySelector(".dream-mirror-layer");
    if (origin === "revoked") layer?.classList.add("is-masked");
    this.syncSceneDom();
    try {
      if (this.visit.state === "MIRROR_OPEN") {
        this.acceptVisit(await closeDreamMirror(this.visit.visit_id));
      }
    } catch (error) {
      if (origin !== "revoked") this.handleAuthorizationOrError(error);
    }
    window.setTimeout(() => {
      if (layer) {
        layer.innerHTML = "";
        layer.setAttribute("aria-hidden", "true");
        layer.classList.remove("is-masked");
      }
      this.mirror = null;
      this.reveal = null;
      this.phase = "free_roam";
      this.syncSceneDom();
      this.announce("\u4F60\u628A\u624B\u4ECE\u955C\u4E2D\u5E26\u56DE\u6797\u5730\u3002\u6797\u4E2D\u7684\u65F6\u95F4\u4ECD\u5728\u7EE7\u7EED\u3002");
    }, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 720);
    if (origin !== "history" && this.mirrorHistoryActive) {
      this.mirrorHistoryActive = false;
      this.suppressNextPop = true;
      history.back();
    } else if (this.visit) {
      history.replaceState(
        {},
        "",
        `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(this.visit.selected_scene_ref)}`
      );
    }
  }
  startMirrorPolling() {
    this.stopMirrorPolling();
    this.mirrorPollTimer = window.setInterval(
      () => void this.validateOpenMirror(),
      MIRROR_POLL_MS
    );
  }
  stopMirrorPolling() {
    if (this.mirrorPollTimer) window.clearInterval(this.mirrorPollTimer);
    this.mirrorPollTimer = 0;
  }
  async validateOpenMirror() {
    if (!this.visit || this.phase !== "mirror_open" || !this.visit.active_onecanvas_view_ref) return;
    try {
      const next = await loadDreamMirror(
        this.visit.visit_id,
        this.visit.selected_scene_ref,
        this.visit.active_onecanvas_view_ref
      );
      if (next.verification.state !== this.mirror?.verification.state) {
        this.mirror = next;
        this.renderMirrorLayer();
      }
    } catch (error) {
      await this.closeMirror("revoked");
      this.announce("\u8FD9\u68F5\u6811\u7684\u5C55\u793A\u6388\u6743\u5DF2\u7ECF\u5931\u6548\uFF0C\u547D\u76D8\u5185\u5BB9\u5DF2\u88AB\u6536\u8D77\u3002");
    }
  }
  async loadGameRounds() {
    if (!this.visit) return;
    const load = async () => {
      if (!this.visit) return [];
      const gate = await loadDreamGameContentGate(this.visit.visit_id);
      if (gate.development_content !== "V50_CANONICAL_ONLY" || gate.simulated_round_count !== 0 || gate.v50_canonical_round_count !== 3 || gate.verified_real_content_gate !== "0/3") {
        throw new Error("dream_game_development_gate_invalid");
      }
      return loadDreamGameRounds(this.visit.visit_id);
    };
    try {
      this.gameRounds = await load();
      this.gameContentUnavailable = this.gameRounds.length === 0;
    } catch {
      try {
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
        this.gameRounds = await load();
        this.gameContentUnavailable = this.gameRounds.length === 0;
      } catch {
        this.gameRounds = [];
        this.gameContentUnavailable = true;
      }
    }
  }
  async openProblemRound(roundId) {
    if (!this.visit || this.gameBusy || !roundId) return;
    const round = this.gameRounds.find((item) => item.round_id === roundId);
    if (!round) return;
    this.porchIndex = Math.max(0, this.gameRounds.findIndex((item) => item.round_id === roundId));
    this.gameBusy = true;
    this.gameStatusMessage = "\u6B63\u5728\u51BB\u7ED3\u95EE\u9898\u53D1\u751F\u524D\u7684\u89C2\u5BDF\u9762\u3002";
    try {
      if (this.visit.selected_scene_ref !== round.resident_scene_ref) {
        this.acceptVisit(await selectDreamTree(this.visit.visit_id, round.resident_scene_ref));
      }
      this.nearestResidentRef = round.resident_scene_ref;
      const tree = this.treeByRef(round.resident_scene_ref);
      if (tree) {
        const point = this.treeApproachPoint(tree);
        this.user = point;
      }
      this.gameAttempt = await startDreamGameRound(this.visit.visit_id, roundId);
      this.gameLens = "overview";
      if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
        this.gameResult = await loadDreamGameResult(
          this.visit.visit_id,
          this.gameAttempt.attempt_id
        );
      } else {
        this.gameResult = null;
        if (this.gameAttempt.state === "ROUND_OBSERVING" && !this.gameAttempt.observed_lenses.includes(this.gameLens)) {
          this.gameAttempt = await observeDreamGameLens(
            this.visit.visit_id,
            this.gameAttempt.attempt_id,
            this.gameLens
          );
        }
      }
      this.gameShellOpen = true;
      this.gameLensOpen = false;
      this.gameLensHistoryActive = false;
      this.gameRevealAct = "user";
      this.gameDraft = this.emptyGameDraft();
      this.gameSealConfirmation = false;
      this.gameCastConfirmation = false;
      this.gameStatusMessage = "";
      this.restoreTreeQuestionState();
      this.openGameHistory(this.gameAttempt.attempt_id);
      this.renderGameLayer();
      this.startGamePolling();
      this.announce(
        `${this.gameResidentDisplayLabel(round.resident_scene_ref, round.resident_label)}\u7684\u751F\u547D\u6811\u5DF2\u7ECF\u53EF\u4EE5\u89C2\u5BDF\u3002\u5F53\u524D\u9898\u7EC4\u6765\u81EA\u6B63\u5F0F\u547D\u76D8\u51BB\u7ED3\u5FEB\u7167\u3002`
      );
    } catch (error) {
      this.handleGameError(error);
    } finally {
      this.gameBusy = false;
    }
  }
  async resumeGameFromRoute() {
    if (!this.visit) return;
    const attemptId = new URL(location.href).searchParams.get("dreamGameAttempt") || "";
    if (!attemptId) return;
    try {
      this.gameAttempt = await loadDreamGameAttempt(this.visit.visit_id, attemptId);
      this.gameShellOpen = true;
      this.gameLensOpen = false;
      this.porchIndex = Math.max(
        0,
        this.gameRounds.findIndex((item) => item.round_id === this.gameAttempt?.round_id)
      );
      this.restoreTreeQuestionState();
      if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
        this.gameResult = await loadDreamGameResult(this.visit.visit_id, attemptId);
        this.gameRevealAct = "user";
      }
      this.gameHistoryActive = true;
      this.renderGameLayer();
      this.startGamePolling();
    } catch (error) {
      this.handleGameError(error);
    }
  }
  renderGameLayer() {
    const layer = this.root.querySelector(".dream-game-layer");
    if (!layer) return;
    this.syncStoryRuntime();
    layer.classList.toggle("is-tree-world", this.gameShellOpen);
    if (!this.gameAttempt) {
      if (!this.gameShellOpen) {
        layer.innerHTML = "";
        layer.setAttribute("aria-hidden", "true");
        this.syncSceneDom();
        return;
      }
      if (!this.gameRounds.length) {
        layer.innerHTML = renderDreamTreePorch({
          rounds: [],
          activeIndex: 0,
          banner: "",
          entering: false,
          mediaCue: "none",
          focusedWhisper: "\u8FD9\u68F5\u6811\u6682\u65F6\u6CA1\u6709\u5F00\u653E\u65B0\u7684\u547D\u9898\u3002",
          scene: this.story.scene
        });
        layer.setAttribute("aria-hidden", "false");
        this.syncSceneDom();
        return;
      }
      layer.innerHTML = renderDreamTreePorch({
        rounds: this.displayGameRounds(),
        activeIndex: this.porchIndex,
        banner: DREAM_GAME_BANNER,
        entering: this.porchEntering,
        mediaCue: this.gameMediaCue,
        focusedWhisper: this.porchWhisper,
        scene: this.story.scene
      });
      layer.setAttribute("aria-hidden", "false");
      this.syncSceneDom();
      layer.querySelector("[data-dream-tree-porch]")?.focus({ preventScroll: true });
      this.schedulePorchIntroCompletion();
      return;
    }
    layer.innerHTML = this.renderDeferredQuestionLayer();
    layer.setAttribute("aria-hidden", "false");
    this.syncSceneDom();
  }
  renderDeferredQuestionLayer() {
    if (!this.gameAttempt) return "";
    const attempt = this.gameAttempt;
    const projection = attempt.projection;
    const selectedRelations = projection.allowed_relations.filter(
      (item) => this.gameDraft.relationRefs.includes(item.relation_ref)
    );
    const canvas2 = renderDreamGameCanvas(
      projection.canvas,
      this.gameLens,
      this.gameDraft.nodeRefs,
      selectedRelations
    );
    const passedNodes = this.passedTreeQuestionNodes();
    const flowerUnlocked = attempt.question_progress.flower_unlocked;
    return renderDreamTreeQuestionMap({
      attempt,
      residentDisplayLabel: this.gameResidentDisplayLabel(
        projection.resident_scene_ref,
        projection.resident_label
      ),
      banner: projection.banner,
      activeLens: this.gameLens,
      lensOpen: this.gameLensOpen,
      canvasMarkup: canvas2,
      questionBandMarkup: this.renderGameStage(),
      resultMarkup: this.gameResult ? this.renderGameResult() : "",
      activeNode: this.gameTreeState.activeNode,
      passedNodes,
      flowerUnlocked,
      flowerOpened: flowerUnlocked,
      fruitVisible: Boolean(attempt.flower?.shared_fruit_visible || this.gameResult),
      mediaCue: this.gameMediaCue,
      statusMessage: this.gameStatusMessage,
      scene: this.story.scene
    });
  }
  renderGameStage() {
    if (!this.gameAttempt) return "";
    const attempt = this.gameAttempt;
    if (attempt.state === "ROUND_OBSERVING") {
      if (!this.gameTreeState.activeNode) return "";
      if (this.gameTreeState.activeNode === "problem_flower") {
        return `<section class="dream-tree-node-question is-problem-flower">
          <button type="button" class="dream-question-close" data-dream-game-command="tree-question-close" aria-label="\u6536\u8D77\u95EE\u9898">\xD7</button>
          <small>\u95EE\u9898\u82B1 \xB7 \u5DF2\u89E3\u9501</small>
          <h2>\u8FD9\u6735\u82B1\u627F\u8F7D\u7740\u4E00\u4E2A\u5DF2\u7ECF\u5C01\u5B58\u7ED3\u679C\u7A97\u53E3\u7684\u95EE\u9898\u3002</h2>
          <p>\u6458\u4E0B\u82B1\u6735\u53EA\u4F1A\u6253\u5F00\u6B63\u5F0F\u95EE\u9898\uFF0C\u4E0D\u4F1A\u81EA\u52A8\u8D77\u5366\uFF0C\u4E5F\u4E0D\u4F1A\u63D0\u524D\u751F\u6210\u679C\u5B9E\u3002</p>
          <div class="dream-game-actions">
            <button type="button" data-dream-game-command="open-flower">\u6458\u4E0B\u95EE\u9898\u82B1</button>
          </div>
        </section>`;
      }
      return this.renderTreeQuestion(this.gameTreeState.activeNode);
    }
    if (["QUESTION_FLOWER_OPEN", "OPTIONAL_DIVINATION"].includes(attempt.state)) {
      const question = attempt.flower_question;
      if (!question) {
        return `<section class="dream-game-question-stage" role="alert">
          <h2>\u95EE\u9898\u82B1\u672A\u80FD\u901A\u8FC7\u670D\u52A1\u7AEF\u6838\u9A8C</h2>
          <p>\u672C\u8F6E\u5DF2\u505C\u6B62\u62AB\u9732\uFF0C\u4E0D\u4F1A\u5BFB\u627E\u6216\u66FF\u6362\u53E6\u4E00\u4E2A\u95EE\u9898\u3002</p>
        </section>`;
      }
      return `<section class="dream-game-question-stage">
        <button type="button" class="dream-question-close" data-dream-game-command="tree-question-close" aria-label="\u6536\u8D77\u95EE\u9898">\xD7</button>
        <div class="dream-game-question-copy">
          <small>\u95EE\u9898\u53D1\u751F\u524D\u51BB\u7ED3\u4E8E ${escapeHtml5(formatDreamDate(question.knowledge_cutoff))}</small>
          <h2>${escapeHtml5(question.neutral_question_text)}</h2>
          <p>\u7ED3\u679C\u7A97\u53E3\uFF1A${escapeHtml5(formatDreamDate(question.outcome_window_start))} \u81F3 ${escapeHtml5(formatDreamDate(question.outcome_window_end))}</p>
        </div>
        ${attempt.divination ? this.renderDivination(attempt.divination.line_values_bottom_up, attempt.divination.moving_line_indexes) : ""}
        <div class="dream-game-actions">
          ${question.liuyao_permitted && !attempt.divination ? this.gameCastConfirmation ? `<span class="dream-game-inline-confirm">\u516D\u723B\u5C06\u5728\u4F60\u660E\u786E\u786E\u8BA4\u540E\u624D\u8D77\u5366\uFF0C\u4E0D\u751F\u6210\u89E3\u91CA\u3002
                  <button type="button" data-dream-game-command="cast-confirm">\u786E\u8BA4\u53D1\u8D77</button>
                  <button type="button" data-dream-game-command="cast-cancel">\u53D6\u6D88</button>
                </span>` : `<button type="button" class="secondary" data-dream-game-command="cast-review">\u660E\u786E\u53D1\u8D77\u516D\u723B</button>` : ""}
          <button type="button" data-dream-game-command="start-judgment">${attempt.divination ? "\u5E26\u7740\u5366\u8C61\u4F5C\u51FA\u5224\u65AD" : "\u4E0D\u5360\uFF0C\u76F4\u63A5\u5224\u65AD"}</button>
        </div>
      </section>`;
    }
    if (attempt.state === "JUDGMENT_DRAFTING") {
      return this.renderJudgmentForm();
    }
    if (attempt.flower) {
      const flower = attempt.flower;
      if (flower.state === "OPEN" && attempt.sealed) {
        return `<section class="dream-game-sealed-fruit">
          <small>\u72EC\u7ACB\u5224\u65AD\u5DF2\u5C01\u5B58</small>
          <h2>\u4F60\u7684\u5224\u65AD\u5DF2\u7ECF\u5C01\u5165\u82B1\u5FC3</h2>
          <p>${escapeHtml5(flower.neutral_message)}</p>
          ${flower.answer_count_visible ? `<p>\u5F53\u524D\u5DF2\u6709 ${flower.answer_count ?? 0} \u4EFD\u56DE\u5E94\u3002\u5F00\u653E\u671F\u95F4\u4E0D\u4F1A\u663E\u793A\u7B54\u6848\u6216\u65B9\u5411\u3002</p>
              <button type="button" class="secondary" data-dream-game-command="close-flower">\u7ED3\u675F\u6536\u96C6</button>` : ""}
        </section>`;
      }
      if (flower.state === "OPEN" && flower.answer_count_visible) {
        return `<section class="dream-game-sealed-fruit">
          <small>\u95EE\u9898\u82B1\u4ECD\u5728\u5F00\u653E</small>
          <h2>\u53EA\u663E\u793A\u56DE\u5E94\u6570\u91CF\uFF0C\u4E0D\u663E\u793A\u7B54\u6848\u65B9\u5411</h2>
          <p>\u5F53\u524D\u5DF2\u6709 ${flower.answer_count ?? 0} \u4EFD\u56DE\u5E94\u3002</p>
          <button type="button" class="secondary" data-dream-game-command="close-flower">\u7ED3\u675F\u6536\u96C6</button>
        </section>`;
      }
      if (flower.state === "CLOSED_NO_RESPONSE") {
        return `<section class="dream-game-sealed-fruit">
          <small>\u7B54\u6848\u96C6\u5408\u5DF2\u5173\u95ED</small>
          <h2>\u8FD9\u6735\u82B1\u6CA1\u6709\u5F62\u6210\u5171\u540C\u679C\u5B9E</h2>
          <p>${escapeHtml5(flower.neutral_message)}</p>
        </section>`;
      }
      if (flower.state === "SHARED_FRUIT_FORMED" && !flower.revealable) {
        return `<section class="dream-game-sealed-fruit">
          <small>\u7B54\u6848\u96C6\u5408\u5DF2\u7ECF\u5C01\u5B58</small>
          <h2>\u5171\u540C\u96FE\u767D\u679C\u5B9E\u6B63\u5728\u7B49\u5F85\u73B0\u5B9E\u53CD\u9988</h2>
          <p>${escapeHtml5(flower.neutral_message)}</p>
        </section>`;
      }
      if (flower.revealable && attempt.sealed) {
        return `<section class="dream-game-sealed-fruit">
          <small>\u5171\u540C\u679C\u5B9E\u5DF2\u7ECF\u5230\u8FBE\u63ED\u76F2\u65F6\u523B</small>
          <h2>\u96FE\u767D\u679C\u5B9E\u53EF\u4EE5\u6253\u5F00</h2>
          <p>\u63ED\u76F2\u53EA\u4F1A\u8FFD\u52A0\u4F60\u7684\u79C1\u4EBA\u5BF9\u8D26\u8BB0\u5F55\uFF0C\u4E0D\u4F1A\u4FEE\u6539\u4EFB\u4F55\u4E8B\u524D\u5224\u65AD\u3002</p>
          <button type="button" data-dream-game-command="reveal">\u63ED\u5F00\u679C\u5B9E</button>
        </section>`;
      }
    }
    if (attempt.state === "OUTCOME_REVEALABLE") {
      return `<section class="dream-game-sealed-fruit">
        <small>\u73A9\u5BB6\u5224\u65AD\u4E0E\u72EC\u7ACB\u7CFB\u7EDF\u5224\u65AD\u5DF2\u7ECF\u5206\u522B\u5C01\u5B58</small>
        <h2>\u96FE\u767D\u679C\u5B9E\u7B2C\u4E00\u6B21\u663E\u5F62</h2>
        <p>\u63ED\u76F2\u53EA\u4F1A\u8FFD\u52A0\u7ED3\u679C\u8BB0\u5F55\uFF0C\u4E0D\u4F1A\u4FEE\u6539\u4EFB\u4F55\u4E00\u4EFD\u4E8B\u524D\u5224\u65AD\u3002</p>
        <button type="button" data-dream-game-command="reveal">\u63ED\u5F00\u679C\u5B9E</button>
      </section>`;
    }
    return `<section class="dream-game-sealed-fruit"><p>\u8FD9\u4E00\u5C40\u6B63\u5728\u6062\u590D\u3002</p></section>`;
  }
  renderTreeQuestion(nodeId) {
    if (!this.gameAttempt || nodeId === "problem_flower") return "";
    const definition = treeQuestionForNode(this.gameAttempt, nodeId);
    if (!definition) return "";
    const progress = this.questionProgressForNode(nodeId);
    const answer = progress?.last_selected_option_id || "";
    return `<section class="dream-tree-node-question" data-tree-question="${nodeId}">
      <button type="button" class="dream-question-close" data-dream-game-command="tree-question-close" aria-label="\u6536\u8D77\u95EE\u9898">\xD7</button>
      <small>${escapeHtml5(definition.title)}</small>
      <h2>${escapeHtml5(definition.prompt)}</h2>
      <div class="dream-tree-question-options">
        ${definition.options.map((option) => `<button
          type="button"
          class="${answer === option.optionId ? "is-selected" : ""}"
          data-dream-game-command="tree-answer"
          data-tree-node="${nodeId}"
          data-answer-id="${escapeAttr6(option.optionId)}"
          ${progress?.status === "COMPLETED" ? " disabled" : ""}
        >${escapeHtml5(option.label)}</button>`).join("")}
      </div>
      ${progress?.feedback ? `<p class="dream-tree-question-feedback">${escapeHtml5(progress.feedback)}</p>` : ""}
      <button
        type="button"
        class="dream-tree-observe-lens"
        data-dream-game-command="tree-open-lens"
        data-lens="${definition.lens}"
      >\u56DE\u5230\u540C\u6E90\u547D\u76D8\u955C\u89C2\u5BDF</button>
    </section>`;
  }
  renderJudgmentForm() {
    if (!this.gameAttempt) return "";
    const question = this.gameAttempt.flower_question;
    if (!question) return this.renderMissingFlowerQuestion();
    const options = Object.entries(question.outcome_options);
    if (this.gameTreeState.judgmentStep === "outcome") {
      return `<form class="dream-game-judgment is-outcome" data-dream-game-form>
        <header><small>\u6B63\u5F0F\u5224\u65AD \xB7 1 / 4</small><h2>${escapeHtml5(question.neutral_question_text)}</h2></header>
        <fieldset><legend>\u9009\u62E9\u4F60\u8BA4\u4E3A\u6700\u53EF\u80FD\u53D1\u751F\u7684\u7ED3\u679C</legend>
          ${options.map(([value, label]) => `<label><input type="radio" name="dream-outcome" data-dream-game-field="selectedOutcome" value="${value}"${this.gameDraft.selectedOutcome === value ? " checked" : ""}><span>${escapeHtml5(label)}</span></label>`).join("")}
        </fieldset>
        <div class="dream-game-actions"><button type="button" data-dream-game-command="judgment-next">\u7EE7\u7EED</button></div>
      </form>`;
    }
    if (this.gameTreeState.judgmentStep === "hypothesis") {
      const evidence = [
        ...this.gameDraft.nodeRefs.map((ref) => this.gameEvidenceDisplayLabel(ref)),
        ...this.gameDraft.relationRefs.map((ref) => this.gameEvidenceDisplayLabel(ref))
      ];
      return `<form class="dream-game-judgment is-hypothesis" data-dream-game-form>
        <header><small>\u4E3B\u8981\u4F9D\u636E \xB7 2 / 4</small><h2>\u4F60\u600E\u6837\u628A\u521A\u624D\u8BFB\u8FC7\u7684\u53F6\u4E0E\u679D\u8FDE\u6210\u5224\u65AD\uFF1F</h2></header>
        <div class="dream-game-hypothesis-summary">
          <strong>\u5DF2\u8BFB\u7ED3\u6784</strong>
          ${evidence.length ? evidence.map((item) => `<i>${escapeHtml5(item)}</i>`).join("") : "<span>\u5F53\u524D\u6682\u4E0D\u786E\u8BA4\u4E3B\u8981\u4F5C\u7528\u8DEF\u5F84</span>"}
        </div>
        <label><span>\u4F60\u7684\u5019\u9009\u8DEF\u5F84\u5047\u8BF4</span><textarea data-dream-game-field="interpretation" maxlength="1200" placeholder="\u8FD9\u662F\u73A9\u5BB6\u5047\u8BF4\uFF0C\u4E0D\u4F1A\u5199\u6210\u6B63\u5F0F PathAssertion\u3002">${escapeHtml5(this.gameDraft.interpretation)}</textarea></label>
        <div class="dream-game-actions"><button type="button" class="secondary" data-dream-game-command="judgment-back">\u8FD4\u56DE</button><button type="button" data-dream-game-command="judgment-next">\u7EE7\u7EED</button></div>
      </form>`;
    }
    if (this.gameTreeState.judgmentStep === "counter") {
      return `<form class="dream-game-judgment is-counter" data-dream-game-form>
        <header><small>\u53CD\u8BC1\u4E0E\u4FE1\u5FC3 \xB7 3 / 4</small><h2>\u5982\u679C\u4F60\u7684\u5224\u65AD\u9519\u4E86\uFF0C\u6700\u53EF\u80FD\u662F\u54EA\u6761\u8BC1\u636E\u63A8\u7FFB\u5B83\uFF1F</h2></header>
        <label class="dream-game-confidence"><span>\u4FE1\u5FC3\u7A0B\u5EA6 <b data-confidence-value>${Math.round(this.gameDraft.confidence / 100)}%</b></span><input type="range" min="0" max="10000" step="100" value="${this.gameDraft.confidence}" data-dream-game-field="confidence"></label>
        <label><span>\u6700\u5F3A\u7684\u53E6\u4E00\u79CD\u89E3\u91CA</span><textarea data-dream-game-field="strongestAlternative" maxlength="1000" required>${escapeHtml5(this.gameDraft.strongestAlternative)}</textarea></label>
        <label><span>\u4EC0\u4E48\u4E8B\u5B9E\u4F1A\u8BA9\u4F60\u6539\u53D8\u5224\u65AD\uFF1F</span><textarea data-dream-game-field="disconfirmationCondition" maxlength="1000" required>${escapeHtml5(this.gameDraft.disconfirmationCondition)}</textarea></label>
        <div class="dream-game-actions"><button type="button" class="secondary" data-dream-game-command="judgment-back">\u8FD4\u56DE</button><button type="button" data-dream-game-command="review-seal">\u82B1\u5FC3\u56DE\u987E</button></div>
      </form>`;
    }
    return this.renderSealConfirmation();
  }
  renderSealConfirmation() {
    if (!this.gameAttempt) return "";
    const question = this.gameAttempt.flower_question;
    if (!question) return this.renderMissingFlowerQuestion();
    const relationOptions = this.gameAttempt.projection.allowed_relations.filter(
      (item) => this.gameDraft.relationRefs.includes(item.relation_ref)
    );
    return `<section class="dream-game-seal-confirmation">
      <small>\u82B1\u5FC3\u56DE\u987E \xB7 4 / 4</small>
      <h2>${escapeHtml5(question.outcome_options[this.gameDraft.selectedOutcome])}</h2>
      <p>\u4FE1\u5FC3 ${Math.round(this.gameDraft.confidence / 100)}%</p>
      <div class="dream-game-hypothesis-summary">
        <strong>\u73A9\u5BB6\u5019\u9009\u8DEF\u5F84 \xB7 \u975E\u6B63\u5F0F</strong>
        <span>${escapeHtml5(this.gameDraft.interpretation || "\u672A\u586B\u5199\u8DEF\u5F84\u8BF4\u660E")}</span>
        ${relationOptions.map((item) => `<i>${escapeHtml5(item.label)}</i>`).join("")}
      </div>
      <dl><dt>\u6700\u5F3A\u66FF\u4EE3</dt><dd>${escapeHtml5(this.gameDraft.strongestAlternative)}</dd><dt>\u53CD\u8BC1\u6761\u4EF6</dt><dd>${escapeHtml5(this.gameDraft.disconfirmationCondition)}</dd></dl>
      <div class="dream-game-review-petals">
        <button type="button" data-dream-game-command="edit-step" data-step="outcome">\u6B63\u5F0F\u9009\u62E9</button>
        <button type="button" data-dream-game-command="edit-step" data-step="hypothesis">\u4E3B\u8981\u4F9D\u636E</button>
        <button type="button" data-dream-game-command="edit-step" data-step="counter">\u53CD\u8BC1\u4E0E\u4FE1\u5FC3</button>
      </div>
      <div class="dream-game-actions"><button type="button" class="secondary" data-dream-game-command="judgment-back">\u8FD4\u56DE</button><button type="button" data-dream-game-command="seal">\u5C01\u5B58\u8FD9\u6B21\u5224\u65AD</button></div>
    </section>`;
  }
  renderDivination(lines, moving) {
    return `<section class="dream-game-divination" aria-label="\u672C\u6B21\u660E\u786E\u53D1\u8D77\u7684\u516D\u723B\u539F\u59CB\u8BB0\u5F55">
      <header><strong>\u516D\u723B\u539F\u59CB\u8BB0\u5F55</strong><small>\u6CA1\u6709\u81EA\u52A8\u89E3\u91CA</small></header>
      <ol>${[...lines].reverse().map((value, reverseIndex) => {
      const lineIndex = 6 - reverseIndex;
      const yang = value === 7 || value === 9;
      return `<li class="${yang ? "is-yang" : "is-yin"}${moving.includes(lineIndex) ? " is-moving" : ""}"><span>${yang ? "\u2501\u2501\u2501\u2501\u2501\u2501" : "\u2501\u2501  \u2501\u2501"}</span><small>${lineIndex}${moving.includes(lineIndex) ? " \xB7 \u52A8" : ""}</small></li>`;
    }).join("")}</ol>
    </section>`;
  }
  renderGameResult() {
    if (!this.gameResult || !this.gameAttempt) return "";
    const result = this.gameResult;
    const question = this.gameAttempt.flower_question;
    if (!question) return this.renderMissingFlowerQuestion();
    const labels = question.outcome_options;
    const acts = {
      user: `<article class="dream-tree-reveal-act is-user">
        <small>\u7B2C\u4E00\u5E55 \xB7 \u6211\u7684\u5224\u65AD</small>
        <strong>${escapeHtml5(labels[result.submission.selected_outcome_option_id])}</strong>
        <span>\u5C01\u5B58\u4FE1\u5FC3 ${Math.round(result.submission.confidence_basis_points / 100)}%</span>
        <p>${escapeHtml5(result.submission.user_path_hypothesis.interpretation || "\u672A\u586B\u5199\u8DEF\u5F84\u8BF4\u660E")}</p>
        <dl><dt>\u6700\u5F3A\u66FF\u4EE3</dt><dd>${escapeHtml5(result.submission.strongest_alternative)}</dd><dt>\u63A8\u7FFB\u6761\u4EF6</dt><dd>${escapeHtml5(result.submission.disconfirmation_condition)}</dd></dl>
      </article>`,
      system: `<article class="dream-tree-reveal-act is-system">
        <small>\u7B2C\u4E8C\u5E55 \xB7 \u7CFB\u7EDF\u5224\u65AD</small>
        <strong>${escapeHtml5(labels[result.system_seal.selected_outcome_option_id])}</strong>
        <span>\u5C01\u5B58\u4FE1\u5FC3 ${Math.round(result.system_seal.confidence_basis_points / 100)}%</span>
        <p>${escapeHtml5(result.system_seal.reasoning_summary)}</p>
        <dl><dt>\u6700\u5F3A\u66FF\u4EE3</dt><dd>${escapeHtml5(result.system_seal.strongest_alternative)}</dd><dt>\u63A8\u7FFB\u6761\u4EF6</dt><dd>${escapeHtml5(result.system_seal.disconfirmation_condition)}</dd></dl>
      </article>`,
      evidence: `<article class="dream-tree-reveal-act is-evidence">
        <small>\u7B2C\u4E09\u5E55 \xB7 \u4E8B\u5B9E\u8BC1\u636E</small>
        <strong>${escapeHtml5(labels[result.outcome_evidence.resolved_option_id])}</strong>
        <p>${escapeHtml5(result.outcome_evidence.outcome_summary)}</p>
        <ul>${result.outcome_evidence.evidence_items.map((item) => `<li>${escapeHtml5(item)}</li>`).join("")}</ul>
      </article>`,
      seed: `<article class="dream-tree-reveal-act is-seed">
        <small>\u77E5\u8BC6\u79CD\u5B50 \xB7 \u79C1\u4EBA\u590D\u76D8\u8BB0\u5F55</small>
        <strong>${escapeHtml5(result.knowledge_seed.issued_calibration_summary)}</strong>
        <p>${escapeHtml5(result.knowledge_seed.applicable_boundary)}</p>
        ${result.knowledge_seed.observation_kept.length ? `<div><b>\u4FDD\u7559\u7684\u89C2\u5BDF</b>${result.knowledge_seed.observation_kept.map((item) => `<span>${escapeHtml5(this.gameEvidenceDisplayLabel(item))}</span>`).join("")}</div>` : ""}
        ${result.knowledge_seed.missed_or_overweighted.length ? `<div><b>\u9057\u6F0F\u6216\u8FC7\u5EA6\u5F3A\u8C03</b>${result.knowledge_seed.missed_or_overweighted.map((item) => `<span>${escapeHtml5(this.gameEvidenceDisplayLabel(item))}</span>`).join("")}</div>` : ""}
      </article>`
    };
    const sequence = ["user", "system", "evidence", "seed"];
    const index = sequence.indexOf(this.gameRevealAct);
    const previous = index > 0;
    const next = index < sequence.length - 1;
    return `<section class="dream-tree-reveal" data-reveal-act="${this.gameRevealAct}">
      <header><small>V50 \u7ED3\u6784\u679C\u5B9E\u5DF2\u63ED\u76F2</small><h2>${escapeHtml5(question.neutral_question_text)}</h2></header>
      <div class="dream-tree-reveal-stage">${acts[this.gameRevealAct]}</div>
      <nav class="dream-tree-reveal-progress" aria-label="\u63ED\u76F2\u8FDB\u5EA6">
        ${sequence.map((act, itemIndex) => `<span aria-current="${act === this.gameRevealAct ? "step" : "false"}">${itemIndex + 1}</span>`).join("")}
      </nav>
      <div class="dream-game-actions">
        ${previous ? `<button type="button" class="secondary" data-dream-game-command="reveal-prev">\u4E0A\u4E00\u5E55</button>` : ""}
        ${next ? `<button type="button" data-dream-game-command="reveal-next">\u7EE7\u7EED</button>` : `<button type="button" data-dream-game-command="return-porch">\u56DE\u5230\u68A6\u6811\u95E8\u5ECA</button>
             <button type="button" class="secondary" data-dream-game-command="depart">\u6B63\u5F0F\u79BB\u68A6</button>`}
      </div>
    </section>`;
  }
  renderMissingFlowerQuestion() {
    return `<section class="dream-game-question-stage" role="alert">
      <h2>\u95EE\u9898\u82B1\u672A\u80FD\u901A\u8FC7\u670D\u52A1\u7AEF\u6838\u9A8C</h2>
      <p>\u672C\u8F6E\u5DF2\u505C\u6B62\u62AB\u9732\uFF0C\u4E0D\u4F1A\u5BFB\u627E\u6216\u66FF\u6362\u53E6\u4E00\u4E2A\u95EE\u9898\u3002</p>
    </section>`;
  }
  gameEvidenceDisplayLabel(ref) {
    const projection = this.gameAttempt?.projection;
    const node = projection?.allowed_nodes.find((item) => item.node_ref === ref);
    if (node) return `${node.pillar_label} \xB7 ${node.label}`;
    const relation = projection?.allowed_relations.find((item) => item.relation_ref === ref);
    if (relation) return relation.label;
    if (ref.startsWith("node:")) return "\u672A\u5C55\u793A\u7684\u547D\u76D8\u8282\u70B9";
    return "\u672C\u5C40\u4E2D\u7684\u4E00\u9879\u89C2\u5BDF";
  }
  async handleGameCommand(target) {
    if (!this.visit || this.gameBusy) return;
    const command = target.dataset.dreamGameCommand;
    this.gameStatusMessage = "";
    if (command === "porch-select") {
      if (this.suppressNextPorchSelection) {
        this.suppressNextPorchSelection = false;
        return;
      }
      const next = Number(target.dataset.porchIndex);
      if (Number.isInteger(next) && next >= 0 && next < this.gameRounds.length) {
        if (next === this.porchIndex) await this.commitFocusedTree();
        else this.focusPorchIndex(next);
      }
      return;
    }
    if (command === "porch-shift") {
      this.shiftPorch(Number(target.dataset.direction) || 0);
      return;
    }
    if (command === "depart" && !this.gameAttempt) {
      await this.departDream("SEMANTIC_EXIT");
      return;
    }
    if (!this.gameAttempt) return;
    if (command === "tree-node") {
      const nodeId = target.dataset.treeNode;
      const definition = nodeId === "problem_flower" ? null : treeQuestionForNode(this.gameAttempt, nodeId);
      const locked = nodeId === "problem_flower" ? !this.gameAttempt.question_progress.flower_unlocked : !definition?.available;
      if (locked) {
        this.gameStatusMessage = nodeId === "problem_flower" ? "\u5148\u8BFB\u61C2\u8FD9\u68F5\u6811\u7684\u53F6\u4E0E\u679D\uFF0C\u82B1\u624D\u4F1A\u5F00\u653E\u3002" : "\u5148\u8BFB\u61C2\u4E24\u7247\u7279\u6B8A\u6811\u53F6\uFF0C\u518D\u6CBF\u679D\u8DEF\u7EE7\u7EED\u89C2\u5BDF\u3002";
        this.persistTreeQuestionState();
        this.renderGameLayer();
        return;
      }
      this.gameTreeState.activeNode = nodeId;
      this.pushTreeQuestionHistory(nodeId);
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "tree-question-close") {
      this.closeTreeQuestion("command");
      return;
    }
    if (command === "tree-answer") {
      const nodeId = target.dataset.treeNode;
      const answerId = target.dataset.answerId || "";
      await this.answerTreeQuestion(nodeId, answerId);
      return;
    }
    if (command === "tree-open-lens") {
      const lens = target.dataset.lens;
      await this.openGameLens(lens);
      return;
    }
    if (command === "close-lens") {
      this.closeGameLens("command");
      return;
    }
    if (command === "return-porch" || command === "return-forest") {
      if (this.gameResult && this.gameAttempt.state !== "ROUND_COMPLETE") {
        await this.runGameAction(async () => {
          this.gameAttempt = await completeDreamGameRound(
            this.visit.visit_id,
            this.gameAttempt.attempt_id
          );
        }, false);
      }
      await this.returnToTreePorch("command");
      return;
    }
    if (command === "reveal-next" || command === "reveal-prev") {
      this.shiftRevealAct(command === "reveal-next" ? 1 : -1);
      return;
    }
    if (command === "lens") {
      const lens = target.dataset.lens;
      await this.openGameLens(lens);
      return;
    }
    if (command === "open-flower") {
      if (!this.gameAttempt.question_progress.flower_unlocked) {
        this.gameStatusMessage = "\u5148\u8BFB\u61C2\u8FD9\u68F5\u6811\u7684\u53F6\u4E0E\u679D\uFF0C\u82B1\u624D\u4F1A\u5F00\u653E\u3002";
        this.persistTreeQuestionState();
        this.renderGameLayer();
        return;
      }
      await this.runGameAction(async () => {
        this.gameAttempt = await openDreamProblemFlower(
          this.visit.visit_id,
          this.gameAttempt.attempt_id
        );
        this.gameTreeState.activeNode = "problem_flower";
        this.persistTreeQuestionState();
      });
      this.playGameMediaCue("flower_open", 2250);
      return;
    }
    if (command === "cast-review") {
      this.gameCastConfirmation = true;
      this.renderGameLayer();
      return;
    }
    if (command === "cast-cancel") {
      this.gameCastConfirmation = false;
      this.renderGameLayer();
      return;
    }
    if (command === "cast-confirm") {
      const key = actionId("dream-cast");
      await this.runGameAction(async () => {
        this.gameAttempt = await castDreamGameDivination(
          this.visit.visit_id,
          this.gameAttempt.attempt_id,
          key
        );
        this.gameCastConfirmation = false;
      });
      return;
    }
    if (command === "start-judgment") {
      await this.runGameAction(async () => {
        this.gameAttempt = await beginDreamGameJudgment(
          this.visit.visit_id,
          this.gameAttempt.attempt_id
        );
        this.gameTreeState.judgmentStep = "outcome";
        this.persistTreeQuestionState();
      });
      return;
    }
    if (command === "judgment-next") {
      if (this.gameTreeState.judgmentStep === "outcome") {
        this.gameTreeState.judgmentStep = "hypothesis";
      } else if (this.gameTreeState.judgmentStep === "hypothesis") {
        this.gameTreeState.judgmentStep = "counter";
      }
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "judgment-back") {
      this.stepJudgmentBack();
      return;
    }
    if (command === "edit-step") {
      const step = target.dataset.step;
      if (["outcome", "hypothesis", "counter"].includes(step)) {
        this.gameTreeState.judgmentStep = step;
        this.persistTreeQuestionState();
        this.renderGameLayer();
      }
      return;
    }
    if (command === "review-seal") {
      if (!this.gameDraft.strongestAlternative.trim() || !this.gameDraft.disconfirmationCondition.trim()) {
        this.gameStatusMessage = "\u8BF7\u5148\u5199\u4E0B\u6700\u5F3A\u66FF\u4EE3\u89E3\u91CA\u548C\u53EF\u63A8\u7FFB\u5224\u65AD\u7684\u4E8B\u5B9E\u3002";
        this.renderGameLayer();
        return;
      }
      this.gameTreeState.judgmentStep = "review";
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "edit-judgment") {
      this.gameTreeState.judgmentStep = "outcome";
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "seal") {
      await this.sealCurrentGameJudgment();
      return;
    }
    if (command === "close-flower") {
      await this.closeCurrentProblemFlower();
      return;
    }
    if (command === "reveal") {
      await this.revealCurrentGameOutcome();
      return;
    }
    if (command === "depart") {
      if (this.gameResult && this.gameAttempt.state !== "ROUND_COMPLETE") {
        await this.runGameAction(async () => {
          this.gameAttempt = await completeDreamGameRound(
            this.visit.visit_id,
            this.gameAttempt.attempt_id
          );
        }, false);
      }
      await this.closeGameLayer("command");
      await this.departDream("SEMANTIC_EXIT");
    }
  }
  handleGameInput(event) {
    if (!this.gameAttempt || this.gameAttempt.state !== "JUDGMENT_DRAFTING") return;
    const input = event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement ? event.target : null;
    if (!input) return;
    const field = input.dataset.dreamGameField;
    if (field === "selectedOutcome" && input instanceof HTMLInputElement && input.checked) {
      this.gameDraft.selectedOutcome = input.value;
      this.persistTreeQuestionState();
      return;
    }
    if (field === "confidence" && input instanceof HTMLInputElement) {
      this.gameDraft.confidence = Number(input.value);
      const label = this.root.querySelector("[data-confidence-value]");
      if (label) label.textContent = `${Math.round(this.gameDraft.confidence / 100)}%`;
      this.persistTreeQuestionState();
      return;
    }
    if (field === "interpretation") this.gameDraft.interpretation = input.value;
    if (field === "strongestAlternative") this.gameDraft.strongestAlternative = input.value;
    if (field === "disconfirmationCondition") this.gameDraft.disconfirmationCondition = input.value;
    const kind = input.dataset.dreamGameKind;
    const reference = input.dataset.dreamGameRef || "";
    if (input instanceof HTMLInputElement && reference && kind) {
      const target = kind === "node" ? this.gameDraft.nodeRefs : this.gameDraft.relationRefs;
      const next = input.checked ? [.../* @__PURE__ */ new Set([...target, reference])] : target.filter((item) => item !== reference);
      if (kind === "node") this.gameDraft.nodeRefs = next;
      if (kind === "relation") this.gameDraft.relationRefs = next;
      input.closest("label")?.classList.toggle("is-selected", input.checked);
    }
    this.persistTreeQuestionState();
  }
  async sealCurrentGameJudgment() {
    if (!this.visit || !this.gameAttempt) return;
    const payload = {
      selected_outcome_option_id: this.gameDraft.selectedOutcome,
      confidence_basis_points: this.gameDraft.confidence,
      node_refs: this.gameDraft.nodeRefs,
      relation_refs: this.gameDraft.relationRefs,
      interpretation: this.gameDraft.interpretation,
      evidence_refs: [.../* @__PURE__ */ new Set([...this.gameDraft.nodeRefs, ...this.gameDraft.relationRefs])],
      strongest_alternative: this.gameDraft.strongestAlternative,
      disconfirmation_condition: this.gameDraft.disconfirmationCondition,
      idempotency_key: actionId("dream-seal"),
      confirmed: true
    };
    this.rememberPendingGameAction({
      visitId: this.visit.visit_id,
      attemptId: this.gameAttempt.attempt_id,
      kind: "seal",
      payload
    });
    await this.runGameAction(async () => {
      this.gameAttempt = await sealDreamGameJudgment(
        this.visit.visit_id,
        this.gameAttempt.attempt_id,
        payload
      );
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      this.gameSealConfirmation = false;
    });
    if (this.gameAttempt.flower?.shared_fruit_visible) {
      this.playGameMediaCue("fruit_forming", 1800);
    } else if (this.gameAttempt.flower?.own_answer_sealed) {
      this.gameStatusMessage = this.gameAttempt.flower.neutral_message;
    }
  }
  async closeCurrentProblemFlower() {
    if (!this.visit || !this.gameAttempt || !this.gameAttempt.flower?.answer_count_visible) return;
    const payload = { idempotencyKey: actionId("dream-flower-close") };
    this.rememberPendingGameAction({
      visitId: this.visit.visit_id,
      attemptId: this.gameAttempt.attempt_id,
      kind: "close-flower",
      payload
    });
    await this.runGameAction(async () => {
      this.gameAttempt = await closeDreamProblemFlower(
        this.visit.visit_id,
        this.gameAttempt.attempt_id,
        payload.idempotencyKey
      );
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    });
    if (this.gameAttempt.flower?.shared_fruit_visible) {
      this.playGameMediaCue("fruit_forming", 1800);
    }
  }
  async revealCurrentGameOutcome() {
    if (!this.visit || !this.gameAttempt) return;
    const payload = { idempotencyKey: actionId("dream-reveal") };
    this.rememberPendingGameAction({
      visitId: this.visit.visit_id,
      attemptId: this.gameAttempt.attempt_id,
      kind: "reveal",
      payload
    });
    await this.runGameAction(async () => {
      this.gameResult = await revealDreamGameOutcome(
        this.visit.visit_id,
        this.gameAttempt.attempt_id,
        payload.idempotencyKey
      );
      this.gameAttempt = await loadDreamGameAttempt(
        this.visit.visit_id,
        this.gameAttempt.attempt_id
      );
      this.gameLensOpen = false;
      this.gameRevealAct = "user";
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    });
  }
  async runGameAction(action, render2 = true) {
    if (this.gameBusy) return;
    this.gameBusy = true;
    this.gameStatusMessage = "";
    try {
      await action();
    } catch (error) {
      const networkFailure = !(error instanceof DreamApiError);
      this.gameStatusMessage = networkFailure ? "\u8FDE\u63A5\u6682\u65F6\u4E2D\u65AD\u3002\u6062\u590D\u540E\u4F1A\u4F7F\u7528\u540C\u4E00\u5E42\u7B49\u8BF7\u6C42\u7EE7\u7EED\uFF0C\u4E0D\u4F1A\u91CD\u590D\u5C01\u5B58\u3002" : "\u5F53\u524D\u52A8\u4F5C\u6CA1\u6709\u5199\u5165\uFF0C\u8BF7\u91CD\u65B0\u786E\u8BA4\u68A6\u5883\u72B6\u6001\u3002";
      this.handleGameError(error, false);
    } finally {
      this.gameBusy = false;
      if (render2) this.renderGameLayer();
    }
  }
  async resumePendingGameAction() {
    if (!this.visit || this.gameBusy || !navigator.onLine) return;
    const pending = this.readPendingGameAction();
    if (!pending || pending.visitId !== this.visit.visit_id) return;
    try {
      this.gameAttempt = await loadDreamGameAttempt(this.visit.visit_id, pending.attemptId);
      if (pending.kind === "seal" && !this.gameAttempt.sealed) {
        this.gameAttempt = await sealDreamGameJudgment(
          pending.visitId,
          pending.attemptId,
          pending.payload
        );
      }
      if (pending.kind === "close-flower" && this.gameAttempt.flower?.state === "OPEN") {
        const close = pending.payload;
        this.gameAttempt = await closeDreamProblemFlower(
          pending.visitId,
          pending.attemptId,
          close.idempotencyKey
        );
      }
      if (pending.kind === "reveal" && !["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
        const reveal = pending.payload;
        this.gameResult = await revealDreamGameOutcome(
          pending.visitId,
          pending.attemptId,
          reveal.idempotencyKey
        );
        this.gameAttempt = await loadDreamGameAttempt(this.visit.visit_id, pending.attemptId);
      } else if (pending.kind === "reveal") {
        this.gameResult = await loadDreamGameResult(this.visit.visit_id, pending.attemptId);
      }
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      this.renderGameLayer();
    } catch (error) {
      if (error instanceof DreamApiError) {
        sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
        this.handleGameError(error);
      }
    }
  }
  rememberPendingGameAction(value) {
    sessionStorage.setItem(PENDING_GAME_ACTION_KEY, JSON.stringify(value));
  }
  readPendingGameAction() {
    try {
      const raw = sessionStorage.getItem(PENDING_GAME_ACTION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      return null;
    }
  }
  startGamePolling() {
    this.stopGamePolling();
    this.gamePollTimer = window.setInterval(() => void this.validateOpenGame(), 1e4);
  }
  stopGamePolling() {
    if (this.gamePollTimer) window.clearInterval(this.gamePollTimer);
    this.gamePollTimer = 0;
  }
  async validateOpenGame() {
    if (!this.visit || !this.gameAttempt || document.visibilityState !== "visible") return;
    try {
      const next = await loadDreamGameAttempt(this.visit.visit_id, this.gameAttempt.attempt_id);
      const flowerChanged = flowerLifecycleKey(next) !== flowerLifecycleKey(this.gameAttempt);
      if (next.state !== this.gameAttempt.state || next.updated_at !== this.gameAttempt.updated_at || flowerChanged) {
        this.gameAttempt = next;
        if (flowerChanged) {
          this.gameStatusMessage = next.flower?.neutral_message || "";
        }
        if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(next.state)) {
          this.gameResult = await loadDreamGameResult(this.visit.visit_id, next.attempt_id);
        }
        this.renderGameLayer();
      }
    } catch (error) {
      this.handleGameError(error);
    }
  }
  shiftPorch(delta) {
    if (!this.gameRounds.length || this.gameAttempt || this.porchOrbitTimer) return;
    const next = ((this.porchIndex + delta) % this.gameRounds.length + this.gameRounds.length) % this.gameRounds.length;
    this.focusPorchIndex(next);
  }
  focusPorchIndex(index) {
    if (!Number.isInteger(index) || index < 0 || index >= this.gameRounds.length) return;
    const porchCamera = this.root.querySelector("[data-dream-tree-porch]");
    if (porchCamera?.dataset.orbitLocked === "true") return;
    const previousIndex = this.porchIndex;
    if (index === previousIndex || this.porchOrbitTimer) return;
    if (porchCamera) porchCamera.dataset.orbitLocked = "true";
    this.porchIndex = index;
    this.porchEntering = false;
    this.porchWhisper = "";
    this.story.dispatch({
      type: "FOCUS_CANDIDATE",
      index: this.porchIndex,
      candidateCount: this.gameRounds.length
    });
    if (!this.updatePorchFocus(previousIndex)) {
      if (porchCamera) delete porchCamera.dataset.orbitLocked;
      this.renderGameLayer();
    }
    this.scheduleFocusedTreeWhisper(780);
  }
  updatePorchFocus(previousIndex) {
    const layer = this.root.querySelector(".dream-game-layer");
    const camera = layer?.querySelector("[data-dream-tree-porch]");
    if (!layer || !camera || this.gameAttempt) return false;
    const count = this.gameRounds.length;
    const forward = (this.porchIndex - previousIndex + count) % count;
    const direction = forward === 1 ? "next" : "previous";
    camera.classList.remove("is-orbiting-next", "is-orbiting-previous");
    camera.classList.add(`is-orbiting-${direction}`);
    window.clearTimeout(this.porchOrbitTimer);
    this.porchOrbitTimer = window.setTimeout(() => {
      this.porchOrbitTimer = 0;
      camera.classList.remove("is-orbiting-next", "is-orbiting-previous");
      delete camera.dataset.orbitLocked;
      for (const tree of camera.querySelectorAll("[data-orbit-from-slot]")) {
        delete tree.dataset.orbitFromSlot;
      }
    }, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 220 : 1260);
    const rounds = this.displayGameRounds();
    for (const tree of layer.querySelectorAll(
      ".dream-tree-porch-tree.is-porch-actor[data-porch-index]"
    )) {
      const itemIndex = Number(tree.dataset.porchIndex);
      if (!Number.isInteger(itemIndex) || itemIndex < 0 || itemIndex >= count) continue;
      const active = itemIndex === this.porchIndex;
      const itemForward = (itemIndex - this.porchIndex + count) % count;
      tree.dataset.orbitFromSlot = tree.dataset.orbitSlot || "0";
      tree.dataset.orbitSlot = String(itemForward === 0 ? 0 : itemForward === 1 ? 1 : -1);
      tree.classList.toggle("is-active", active);
      tree.classList.toggle("is-dream-heart", active);
      tree.classList.toggle("is-ghost", !active);
      tree.setAttribute("aria-current", active ? "true" : "false");
      tree.setAttribute(
        "aria-label",
        active ? `${rounds[itemIndex].anonymous_label}\u4F4D\u4E8E\u68A6\u5FC3\uFF0C\u8F7B\u89E6\u8FDB\u5165` : `\u8BA9${rounds[itemIndex].anonymous_label}\u6765\u5230\u68A6\u5FC3`
      );
    }
    const currentLabel = layer.querySelector("[data-porch-current-label]");
    if (currentLabel) {
      currentLabel.textContent = `\u5F53\u524D\u68A6\u5FC3\u4F4D\uFF1A${rounds[this.porchIndex].anonymous_label}`;
    }
    this.updatePorchWhisper();
    return true;
  }
  async commitFocusedTree() {
    const round = this.gameRounds[this.porchIndex];
    if (!round || this.gameAttempt || this.gameBusy) return;
    this.gameBusy = true;
    this.story.dispatch({ type: "COMMIT_CANDIDATE", roundId: round.round_id });
    this.gameMediaCue = "tree_enter";
    this.renderGameLayer();
    await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 180 : 2300);
    this.story.dispatch({ type: "TREE_ENTRY_COMPLETED" });
    this.gameMediaCue = "none";
    this.gameBusy = false;
    await this.openProblemRound(round.round_id);
  }
  scheduleFocusedTreeWhisper(delayMs) {
    if (this.porchWhisperTimer) window.clearTimeout(this.porchWhisperTimer);
    const round = this.gameRounds[this.porchIndex];
    if (!round || this.spokenRoundIds.has(round.round_id)) return;
    this.porchWhisperTimer = window.setTimeout(() => {
      this.porchWhisperTimer = 0;
      const focused = this.gameRounds[this.porchIndex];
      if (!focused || focused.round_id !== round.round_id || this.gameAttempt) return;
      this.spokenRoundIds.add(round.round_id);
      this.porchWhisper = round.selection_whisper;
      this.updatePorchWhisper();
      this.announce(round.selection_whisper);
      this.porchWhisperTimer = window.setTimeout(() => {
        this.porchWhisperTimer = 0;
        if (this.porchWhisper !== round.selection_whisper) return;
        this.porchWhisper = "";
        this.updatePorchWhisper();
      }, 3e3);
    }, delayMs);
  }
  updatePorchWhisper() {
    const whisper = this.root.querySelector(".dream-ghost-orbit-whisper");
    if (!whisper) return;
    whisper.textContent = this.porchWhisper;
    if (this.porchWhisper) {
      whisper.removeAttribute("aria-hidden");
      whisper.setAttribute("aria-live", "polite");
    } else {
      whisper.setAttribute("aria-hidden", "true");
      whisper.removeAttribute("aria-live");
    }
  }
  displayGameRounds() {
    return this.gameRounds.map((round) => ({
      ...round,
      resident_label: this.gameResidentDisplayLabel(
        round.resident_scene_ref,
        round.resident_label
      )
    }));
  }
  syncStoryRuntime() {
    const foundationComplete = Boolean(
      this.gameAttempt?.question_progress.flower_unlocked
    );
    this.story.sync({
      visit: this.visit,
      gameState: this.gameAttempt?.state || "",
      hasAttempt: Boolean(this.gameAttempt),
      hasResult: Boolean(this.gameResult),
      foundationComplete
    });
    const main = this.root.querySelector(".dream-first-visit");
    if (!main) return;
    main.dataset.dreamStoryState = this.story.snapshot.businessState;
    main.dataset.dreamStoryPresentation = this.story.snapshot.presentationState;
    main.dataset.dreamSceneId = this.story.scene.sceneId;
  }
  gameResidentDisplayLabel(sceneRef, fallback) {
    const source = this.trees.find((tree) => tree.scene_ref === sceneRef);
    if (source?.source_kind !== "authorized_human") return fallback;
    const index = Math.max(
      0,
      this.gameRounds.findIndex((round) => round.resident_scene_ref === sceneRef)
    );
    return `\u533F\u540D\u68A6\u5883\u5C45\u6C11${["\u4E00", "\u4E8C", "\u4E09"][index] || ""}`;
  }
  resetPorchDrag(camera) {
    camera.style.setProperty("--porch-drag-x", "0px");
    camera.style.setProperty("--porch-drag-sky", "0px");
    camera.style.setProperty("--porch-drag-far", "0px");
    camera.style.setProperty("--porch-drag-ground", "0px");
  }
  schedulePorchIntroCompletion() {
    if (!this.porchEntering || this.porchIntroTimer) return;
    const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 220 : 5200;
    this.porchIntroTimer = window.setTimeout(() => {
      this.porchIntroTimer = 0;
      if (!this.porchEntering || this.gameAttempt) return;
      this.porchEntering = false;
      this.renderGameLayer();
      this.scheduleFocusedTreeWhisper(620);
    }, duration);
  }
  playGameMediaCue(cue, durationMs) {
    if (this.gameMediaTimer) window.clearTimeout(this.gameMediaTimer);
    this.gameMediaCue = cue;
    this.renderGameLayer();
    this.gameMediaTimer = window.setTimeout(() => {
      this.gameMediaTimer = 0;
      if (this.gameMediaCue !== cue) return;
      this.gameMediaCue = "none";
      this.renderGameLayer();
    }, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 180 : durationMs);
  }
  treeQuestionStorageKey(attemptId) {
    return `${TREE_QUESTION_STATE_KEY}:${attemptId}`;
  }
  resetTreeQuestionState(attemptId) {
    this.gameDraft = this.emptyGameDraft();
    this.gameTreeState = {
      attemptId,
      activeNode: "",
      judgmentStep: "outcome",
      draft: { ...this.gameDraft }
    };
    this.persistTreeQuestionState();
  }
  restoreTreeQuestionState() {
    if (!this.gameAttempt) return;
    const attemptId = this.gameAttempt.attempt_id;
    let restored = null;
    try {
      const raw = sessionStorage.getItem(this.treeQuestionStorageKey(attemptId));
      restored = raw ? JSON.parse(raw) : null;
    } catch {
      sessionStorage.removeItem(this.treeQuestionStorageKey(attemptId));
    }
    const allowedNodes = [
      "leaf_structure",
      "leaf_support",
      "branch_path",
      "problem_flower"
    ];
    if (restored?.attemptId === attemptId) {
      const activeNode = restored.activeNode && allowedNodes.includes(restored.activeNode) ? restored.activeNode : "";
      const judgmentStep = restored.judgmentStep && ["outcome", "hypothesis", "counter", "review"].includes(restored.judgmentStep) ? restored.judgmentStep : "outcome";
      this.gameDraft = {
        ...this.emptyGameDraft(),
        ...restored.draft
      };
      this.gameTreeState = {
        attemptId,
        activeNode,
        judgmentStep,
        draft: { ...this.gameDraft }
      };
    } else {
      this.resetTreeQuestionState(attemptId);
    }
    if (this.gameAttempt.state !== "ROUND_OBSERVING") {
      this.gameTreeState.activeNode = "problem_flower";
    }
    const routeNode = new URLSearchParams(location.hash.replace(/^#/, "")).get(
      "tree-question"
    );
    if (routeNode) {
      const routeNodeUnlocked = this.treeQuestionNodeAvailable(routeNode);
      if (allowedNodes.includes(routeNode) && routeNodeUnlocked) {
        this.gameTreeState.activeNode = routeNode;
        this.gameQuestionHistoryActive = true;
      }
    }
    this.persistTreeQuestionState();
  }
  persistTreeQuestionState() {
    const attemptId = this.gameAttempt?.attempt_id || this.gameTreeState.attemptId;
    if (!attemptId) return;
    this.gameTreeState.attemptId = attemptId;
    this.gameTreeState.draft = {
      ...this.gameDraft,
      nodeRefs: [...this.gameDraft.nodeRefs],
      relationRefs: [...this.gameDraft.relationRefs]
    };
    try {
      sessionStorage.setItem(
        this.treeQuestionStorageKey(attemptId),
        JSON.stringify(this.gameTreeState)
      );
    } catch {
    }
  }
  async answerTreeQuestion(nodeId, answerId) {
    if (!this.visit || !this.gameAttempt || nodeId === "problem_flower") return;
    const definition = treeQuestionForNode(this.gameAttempt, nodeId);
    const answer = definition?.options.find((item) => item.optionId === answerId);
    if (!definition || !answer || !definition.available) return;
    const wasUnlocked = this.gameAttempt.question_progress.flower_unlocked;
    await this.runGameAction(async () => {
      this.gameAttempt = await answerDreamLearningQuestion(
        this.visit.visit_id,
        this.gameAttempt.attempt_id,
        definition.questionId,
        answer.optionId,
        actionId("dream-learning-answer")
      );
      const progress = this.questionProgressForNode(nodeId);
      this.gameStatusMessage = progress?.feedback || "";
      if (progress?.status === "COMPLETED") {
        this.gameTreeState.activeNode = "";
        this.closeTreeQuestion("answer");
      }
      this.persistTreeQuestionState();
    });
    if (!wasUnlocked && this.gameAttempt.question_progress.flower_unlocked) {
      this.gameStatusMessage = "\u53F6\u4E0E\u679D\u5DF2\u7ECF\u8BFB\u61C2\uFF0C\u80FD\u91CF\u6CBF\u6811\u4F53\u62B5\u8FBE\u82B1\u9AA8\u6735\u3002";
      this.playGameMediaCue("flower_open", 2250);
    }
  }
  passedTreeQuestionNodes() {
    if (!this.gameAttempt) return [];
    return this.gameAttempt.question_progress.items.filter((item) => item.status === "COMPLETED").map((item) => {
      if (item.kind === "LEAF_BASIC_01") return "leaf_structure";
      if (item.kind === "LEAF_BASIC_02") return "leaf_support";
      return "branch_path";
    });
  }
  questionProgressForNode(nodeId) {
    if (!this.gameAttempt || nodeId === "problem_flower") return void 0;
    const definition = treeQuestionForNode(this.gameAttempt, nodeId);
    if (!definition) return void 0;
    return this.gameAttempt.question_progress.items.find(
      (item) => item.question_id === definition.questionId
    );
  }
  treeQuestionNodeAvailable(nodeId) {
    if (!this.gameAttempt) return false;
    if (nodeId === "problem_flower") {
      return this.gameAttempt.question_progress.flower_unlocked;
    }
    return Boolean(treeQuestionForNode(this.gameAttempt, nodeId)?.available);
  }
  async openGameLens(lens) {
    if (!this.visit || !this.gameAttempt || this.gameBusy || !this.gameAttempt.projection.available_lenses.includes(lens)) return;
    this.gameBusy = true;
    try {
      this.gameAttempt = await observeDreamGameLens(
        this.visit.visit_id,
        this.gameAttempt.attempt_id,
        lens
      );
      this.gameLens = lens;
      this.gameLensOpen = true;
      this.openGameLensHistory(lens);
      this.renderGameLayer();
    } catch (error) {
      this.handleGameError(error);
    } finally {
      this.gameBusy = false;
    }
  }
  pushTreeQuestionHistory(nodeId) {
    if (this.gameQuestionHistoryActive) return;
    const url = new URL(location.href);
    url.hash = `tree-question=${nodeId}`;
    history.pushState(
      {
        dreamTreeQuestion: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt?.attempt_id || "",
        nodeId
      },
      "",
      url
    );
    this.gameQuestionHistoryActive = true;
  }
  closeTreeQuestion(origin) {
    this.gameTreeState.activeNode = "";
    this.persistTreeQuestionState();
    if (origin !== "history" && this.gameQuestionHistoryActive) {
      this.gameQuestionHistoryActive = false;
      if (origin !== "answer") this.renderGameLayer();
      this.suppressNextPop = true;
      history.back();
      return;
    }
    this.gameQuestionHistoryActive = false;
    if (origin === "history") {
      const url = new URL(location.href);
      if (url.hash.startsWith("#tree-question=")) {
        url.hash = "";
        history.replaceState(
          {
            dreamGame: true,
            visitId: this.visit?.visit_id || "",
            attemptId: this.gameAttempt?.attempt_id || ""
          },
          "",
          url
        );
      }
    }
    if (origin !== "answer") this.renderGameLayer();
  }
  stepJudgmentBack() {
    if (this.gameTreeState.judgmentStep === "review") {
      this.gameTreeState.judgmentStep = "counter";
    } else if (this.gameTreeState.judgmentStep === "counter") {
      this.gameTreeState.judgmentStep = "hypothesis";
    } else if (this.gameTreeState.judgmentStep === "hypothesis") {
      this.gameTreeState.judgmentStep = "outcome";
    }
    this.persistTreeQuestionState();
    this.renderGameLayer();
  }
  restoreGameHistoryGuard() {
    if (!this.gameAttempt) return;
    const url = new URL(location.href);
    url.searchParams.set("dreamGameAttempt", this.gameAttempt.attempt_id);
    history.pushState(
      {
        dreamGame: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt.attempt_id
      },
      "",
      url
    );
    this.gameHistoryActive = true;
  }
  openGameLensHistory(lens) {
    if (this.gameLensHistoryActive) return;
    const url = new URL(location.href);
    url.hash = `lens=${lens}`;
    history.pushState(
      {
        dreamTreeLens: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt?.attempt_id || "",
        lens
      },
      "",
      url
    );
    this.gameLensHistoryActive = true;
  }
  closeGameLens(origin) {
    if (!this.gameLensOpen) return;
    this.gameLensOpen = false;
    this.renderGameLayer();
    this.announce("\u4F60\u56DE\u5230\u521A\u624D\u7684\u6811\u4E2D\u4F4D\u7F6E\u3002");
    if (origin !== "history" && this.gameLensHistoryActive) {
      this.gameLensHistoryActive = false;
      this.suppressNextPop = true;
      history.back();
      return;
    }
    this.gameLensHistoryActive = false;
    const url = new URL(location.href);
    url.hash = "";
    history.replaceState(
      {
        dreamGame: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt?.attempt_id || ""
      },
      "",
      url
    );
  }
  shiftRevealAct(delta) {
    const sequence = ["user", "system", "evidence", "seed"];
    const current = sequence.indexOf(this.gameRevealAct);
    const next = clamp(current + delta, 0, sequence.length - 1);
    if (next === current) return;
    this.gameRevealAct = sequence[next];
    this.renderGameLayer();
  }
  async returnToTreePorch(origin) {
    this.stopGamePolling();
    this.gameAttempt = null;
    this.gameResult = null;
    this.gameLensOpen = false;
    this.gameLensHistoryActive = false;
    this.gameQuestionHistoryActive = false;
    this.gameTreeState.activeNode = "";
    this.gameMediaCue = "none";
    if (this.gameMediaTimer) window.clearTimeout(this.gameMediaTimer);
    this.gameMediaTimer = 0;
    this.gameRevealAct = "user";
    this.gameSealConfirmation = false;
    this.gameCastConfirmation = false;
    this.gameStatusMessage = "";
    sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    this.renderGameLayer();
    this.gameHistoryActive = false;
    const url = new URL(location.href);
    url.searchParams.delete("dreamGameAttempt");
    url.hash = "";
    history.replaceState(
      { dreamForest: true, visitId: this.visit?.visit_id || "", origin },
      "",
      url
    );
    this.announce("\u4F60\u56DE\u5230\u4E09\u68F5\u68A6\u6811\u4E4B\u95F4\u3002");
  }
  async closeGameLayer(origin) {
    this.stopGamePolling();
    this.gameShellOpen = false;
    this.gameAttempt = null;
    this.gameResult = null;
    this.gameLensOpen = false;
    this.gameLensHistoryActive = false;
    this.gameQuestionHistoryActive = false;
    this.gameTreeState.activeNode = "";
    this.gameMediaCue = "none";
    if (this.gameMediaTimer) window.clearTimeout(this.gameMediaTimer);
    this.gameMediaTimer = 0;
    this.gameSealConfirmation = false;
    this.gameCastConfirmation = false;
    this.gameStatusMessage = "";
    sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    const layer = this.root.querySelector(".dream-game-layer");
    if (layer) {
      layer.innerHTML = "";
      layer.setAttribute("aria-hidden", "true");
    }
    this.gameHistoryActive = false;
    const url = new URL(location.href);
    url.searchParams.delete("dreamGameAttempt");
    url.hash = "";
    history.replaceState(
      { dreamForest: true, visitId: this.visit?.visit_id || "", origin },
      "",
      url
    );
    this.announce("\u4F60\u56DE\u5230\u4E86\u6301\u7EED\u8FD0\u884C\u7684\u4E09\u6811\u6797\u5883\u3002");
  }
  openGameHistory(attemptId) {
    const url = new URL(location.href);
    url.searchParams.set("dreamGameAttempt", attemptId);
    history.pushState(
      { dreamGame: true, visitId: this.visit?.visit_id || "", attemptId },
      "",
      url
    );
    this.gameHistoryActive = true;
  }
  handleGameError(error, closeOnAuthorityFailure = true) {
    const code = this.errorCode(error);
    if (code.includes("control_lease") || code.includes("content_revoked") || code.includes("authorization") || code.includes("source_changed") || code.includes("projection_invalid")) {
      this.stopGamePolling();
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      if (closeOnAuthorityFailure) {
        const layer = this.root.querySelector(".dream-game-layer");
        if (layer) {
          layer.innerHTML = `<div class="dream-game-fail-closed" role="alert">\u5F53\u524D\u5185\u5BB9\u6388\u6743\u6216\u68A6\u5883\u63A7\u5236\u5DF2\u5931\u6548\uFF0C\u76F2\u5C40\u5185\u5BB9\u5DF2\u7ECF\u6536\u8D77\u3002</div>`;
        }
        this.gameAttempt = null;
        this.gameResult = null;
      }
      if (code.includes("control_lease")) this.handleRuntimeFailure(error);
      return;
    }
    if (closeOnAuthorityFailure) this.gameStatusMessage = "\u6682\u65F6\u65E0\u6CD5\u786E\u8BA4\u76F2\u5C40\u72B6\u6001\u3002\u6CA1\u6709\u7ED3\u679C\u88AB\u63A8\u65AD\u6216\u5199\u5165\u3002";
    this.renderGameLayer();
  }
  emptyGameDraft() {
    return {
      selectedOutcome: "partial_or_unclear",
      confidence: 5e3,
      nodeRefs: [],
      relationRefs: [],
      interpretation: "",
      strongestAlternative: "",
      disconfirmationCondition: ""
    };
  }
  syncSceneDom() {
    const main = this.root.querySelector(".dream-first-visit");
    if (!main) return;
    main.dataset.phase = this.phase;
    main.style.setProperty("--user-x", String(this.user.x));
    main.style.setProperty("--user-y", String(this.user.y));
    main.style.setProperty("--abu-x", String(this.abu.x));
    main.style.setProperty("--abu-y", String(this.abu.y));
    main.style.setProperty("--abu-facing", this.abuFacing === "left" ? "-1" : "1");
    main.style.setProperty("--camera-x", String((50 - this.user.x) * 0.12));
    main.style.setProperty("--camera-y", String((66 - this.user.y) * 0.08));
    main.dataset.nearScene = this.nearestResidentRef;
    main.dataset.selectedScene = this.visit?.selected_scene_ref || "";
    main.dataset.revealMode = this.reveal?.visual_mode || "none";
    main.dataset.runtimeState = this.visit?.runtime_state || "";
    main.dataset.abuMotion = this.abuFollowing ? "walking" : "resting";
    main.classList.toggle("is-canonical-abu", this.canonicalAbu);
    main.classList.toggle("is-departure-intent", this.departureIntentActive);
    main.classList.toggle("is-moving", this.userMoving || this.abuFollowing);
    main.classList.toggle("is-user-moving", this.userMoving);
    main.classList.toggle("is-abu-following", this.abuFollowing);
    main.classList.toggle("is-tree-world-active", this.gameShellOpen);
    main.classList.remove("show-paw-hint");
    if (this.gameShellOpen && main.scrollTop) main.scrollTop = 0;
    const grove = main.querySelector(".dream-grove");
    const legacyA11y = main.querySelector(".dream-a11y-actions");
    if (grove) {
      grove.toggleAttribute("inert", this.gameShellOpen);
      grove.setAttribute("aria-hidden", this.gameShellOpen ? "true" : "false");
    }
    if (legacyA11y) {
      legacyA11y.toggleAttribute("inert", this.gameShellOpen);
      legacyA11y.setAttribute("aria-hidden", this.gameShellOpen ? "true" : "false");
    }
    const abu = main.querySelector(".dream-abu");
    if (abu) {
      const abuElsewhere = this.visit?.canonical_abu?.public_action === "elsewhere";
      abu.hidden = Boolean(abuElsewhere);
      main.querySelector(".dream-abu-shadow")?.toggleAttribute("hidden", Boolean(abuElsewhere));
      const next = this.gameShellOpen ? ABU_REST : this.phase === "fog_wait" || this.phase === "fog_crossing" ? ABU_WALK : this.abuFollowing ? ABU_WALK : this.phase === "free_roam" || this.phase === "mirror_ready" ? ABU_REST : ABU_WAIT;
      if (!abu.src.endsWith(next)) abu.src = next;
    }
    for (const tree of this.trees) {
      const element = main.querySelector(`[data-dream-tree="${cssEscape(tree.scene_ref)}"]`);
      element?.classList.toggle("is-near", tree.scene_ref === this.nearestResidentRef);
      element?.classList.toggle("is-selected", tree.scene_ref === this.visit?.selected_scene_ref);
    }
    this.resyncSceneClock();
  }
  resyncSceneClock() {
    const elapsed = Math.max(0, Date.now() - this.sceneStartedAt);
    for (const tree of this.trees) {
      const element = this.root.querySelector(`[data-dream-tree="${cssEscape(tree.scene_ref)}"]`);
      element?.style.setProperty("--life-delay", `${-((elapsed + tree.autonomous_phase_ms) % 6e4)}ms`);
    }
  }
  async preloadTreeMasks() {
    const entries = this.trees.map(async (tree) => {
      const image = this.root.querySelector(`[data-dream-tree-image="${cssEscape(tree.scene_ref)}"]`);
      if (!image) return;
      try {
        await image.decode();
      } catch {
        await new Promise((resolve) => image.addEventListener("load", () => resolve(), { once: true }));
      }
      const canvas2 = document.createElement("canvas");
      canvas2.width = image.naturalWidth;
      canvas2.height = image.naturalHeight;
      const context = canvas2.getContext("2d", { willReadFrequently: true });
      if (!context) return;
      context.drawImage(image, 0, 0);
      this.masks.set(tree.scene_ref, { image, canvas: canvas2, context });
    });
    await Promise.all(entries);
  }
  hitTreeAt(clientX, clientY) {
    const ordered = [...this.trees].sort((left, right) => right.depth - left.depth);
    for (const tree of ordered) {
      const mask = this.masks.get(tree.scene_ref);
      if (!mask) continue;
      const rect = mask.image.getBoundingClientRect();
      if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) continue;
      const x = Math.floor((clientX - rect.left) / rect.width * mask.canvas.width);
      const y = Math.floor((clientY - rect.top) / rect.height * mask.canvas.height);
      const alpha = mask.context.getImageData(
        clamp(x, 0, mask.canvas.width - 1),
        clamp(y, 0, mask.canvas.height - 1),
        1,
        1
      ).data[3];
      if (alpha > 28) return tree;
    }
    return null;
  }
  isWithinTouchDistance(tree) {
    return pointDistance(this.user, this.treeWorldPoint(tree)) <= TREE_TOUCH_DISTANCE;
  }
  treeWorldPoint(tree) {
    const scene2 = this.root.querySelector(".dream-grove");
    const image = this.root.querySelector(
      `[data-dream-tree-image="${cssEscape(tree.scene_ref)}"]`
    );
    if (!scene2 || !image) return { x: tree.x, y: tree.y + 24 };
    const sceneRect = scene2.getBoundingClientRect();
    const imageRect = image.getBoundingClientRect();
    return {
      x: clamp(
        (imageRect.left + imageRect.width * 0.5 - sceneRect.left) / sceneRect.width * 100,
        7,
        93
      ),
      y: clamp(
        (imageRect.top + imageRect.height * 0.86 - sceneRect.top) / sceneRect.height * 100,
        24,
        91
      )
    };
  }
  treeApproachPoint(tree) {
    const root2 = this.treeWorldPoint(tree);
    return {
      x: clamp(root2.x - 6, 7, 93),
      y: clamp(root2.y + 4, 24, 91)
    };
  }
  focusMirrorTarget() {
    if (!this.mirror?.verification.target_object_ref) return;
    const container = this.root.querySelector(".dream-verification-geometry");
    const target = this.root.querySelector(
      `[data-canvas-object="${cssEscape(this.mirror.verification.target_object_ref)}"]`
    );
    if (!container || !target) return;
    const containerRect = container.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    container.scrollLeft += targetRect.left + targetRect.width / 2 - containerRect.left - containerRect.width / 2;
  }
  worldPointFromClient(clientX, clientY) {
    const scene2 = this.root.querySelector(".dream-grove");
    if (!scene2) return { ...this.user };
    const rect = scene2.getBoundingClientRect();
    return {
      x: clamp((clientX - rect.left) / rect.width * 100, 7, 97),
      y: clamp((clientY - rect.top) / rect.height * 100, 24, 91)
    };
  }
  treeByRef(sceneRef) {
    return this.trees.find((tree) => tree.scene_ref === sceneRef) || null;
  }
  playAmbient() {
    if (!this.ambient) return;
    this.ambient.volume = 0.12;
    void this.ambient.play().catch(() => void 0);
  }
  playRevealTone(hasFact) {
    if (!hasFact) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const context = new AudioContextClass();
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(196, context.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(247, context.currentTime + 0.45);
      gain.gain.setValueAtTime(1e-4, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.055, context.currentTime + 0.08);
      gain.gain.exponentialRampToValueAtTime(1e-4, context.currentTime + 0.7);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.75);
    } catch {
    }
  }
  handleAuthorizationOrError(error) {
    const detail = this.errorCode(error);
    if (detail.includes("control_lease") || detail.includes("world_projection")) {
      this.handleRuntimeFailure(error);
      return;
    }
    if (detail.includes("authorization") || detail.includes("source_version_changed") || detail.includes("reference_invalid")) {
      this.phase = "authorization_closed";
      this.syncSceneDom();
      this.announce("\u8FD9\u68F5\u6811\u5F53\u524D\u4E0D\u80FD\u7EE7\u7EED\u62AB\u9732\u5185\u5BB9\u3002");
      if (this.mirror || this.visit?.state === "MIRROR_OPEN") void this.closeMirror("revoked");
      return;
    }
    this.renderError(error);
  }
  handleRuntimeFailure(error) {
    const code = this.errorCode(error);
    if (code === "dream_control_lease_superseded" || code === "dream_control_lease_stale" || code === "dream_control_lease_expired" || code === "dream_control_lease_required") {
      this.stopControlLoops();
      this.clearSensitiveProjection();
      this.gameAttempt = null;
      this.gameResult = null;
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      clearDreamControl();
      this.phase = "visit_suspended";
      this.syncSceneDom();
      this.setRuntimeVeil("\u68A6\u5883\u5DF2\u5728\u53E6\u4E00\u5904\u7EE7\u7EED\u3002", false);
      this.announce("\u8FD9\u4E2A\u9875\u9762\u5DF2\u7ECF\u5931\u53BB\u68A6\u5883\u63A7\u5236\u6743\uFF0C\u79C1\u4EBA\u5185\u5BB9\u5DF2\u6536\u8D77\u3002");
      return;
    }
    if (code.includes("authorization") || code.includes("source_version_changed") || code.includes("world_projection_invalid")) {
      this.clearSensitiveProjection();
      this.gameAttempt = null;
      this.gameResult = null;
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      this.phase = "authorization_closed";
      this.syncSceneDom();
      this.setRuntimeVeil("\u5F53\u524D\u6388\u6743\u5DF2\u53D8\u5316\uFF0C\u5185\u5BB9\u5DF2\u7ECF\u6536\u8D77\u3002", true);
      return;
    }
    this.stopControlLoops();
    this.clearSensitiveProjection();
    this.gameAttempt = null;
    this.gameResult = null;
    this.phase = "fail_closed";
    this.syncSceneDom();
    this.setRuntimeVeil("\u6682\u65F6\u65E0\u6CD5\u786E\u8BA4\u68A6\u5883\u72B6\u6001\u3002\u8FDE\u63A5\u6062\u590D\u540E\u518D\u7EE7\u7EED\u3002", true);
  }
  clearSensitiveProjection() {
    this.stopMirrorPolling();
    this.stopGamePolling();
    this.mirror = null;
    this.reveal = null;
    const layer = this.root.querySelector(".dream-mirror-layer");
    if (layer) {
      layer.classList.add("is-masked");
      layer.innerHTML = "";
      layer.setAttribute("aria-hidden", "true");
    }
    const gameLayer = this.root.querySelector(".dream-game-layer");
    if (gameLayer) {
      gameLayer.innerHTML = "";
      gameLayer.setAttribute("aria-hidden", "true");
    }
  }
  setRuntimeVeil(message, recoverable) {
    const veil = this.root.querySelector(".dream-runtime-veil");
    if (!veil) return;
    veil.setAttribute("aria-hidden", "false");
    veil.innerHTML = `<span role="status">${escapeHtml5(message)}</span>${recoverable ? `<button type="button" data-dream-retry>\u91CD\u65B0\u786E\u8BA4</button>` : ""}`;
    veil.querySelector("[data-dream-retry]")?.addEventListener("click", () => {
      location.reload();
    });
  }
  errorCode(error) {
    return error instanceof DreamApiError ? error.code : error instanceof Error ? error.message : String(error);
  }
  announce(message) {
    const announcer = this.root.querySelector("[data-dream-announcer]");
    if (announcer) announcer.textContent = message;
  }
  renderError(error) {
    this.stopMovementLoop();
    this.stopMirrorPolling();
    this.stopControlLoops();
    const detail = error instanceof Error ? error.message : String(error);
    const unavailable = detail.includes("DREAM_ENCOUNTER_UNAVAILABLE") || detail.includes("dream_feature_disabled");
    this.root.innerHTML = `<main class="dream-state dream-error">
      <img src="${ABU_WAIT}" alt="\u963F\u5E03">
      <h1>${escapeHtml5(dreamText(unavailable ? "dream.unavailable.title" : "dream.error.title"))}</h1>
      <span>${escapeHtml5(unavailable ? dreamText("dream.unavailable.detail") : detail)}</span>
      <a class="dream-command" href="/experience">${escapeHtml5(dreamText("dream.workspace.back"))}</a>
    </main>`;
  }
};
function placeTrees(trees) {
  const human = trees.find((tree) => tree.source_kind === "authorized_human");
  const residents = trees.filter((tree) => tree.source_kind === "canonical_npc").sort((left, right) => left.resident_label.localeCompare(right.resident_label, "zh-CN"));
  const placements = [
    human ? { tree: human, x: 3, y: 58, scale: 1.48, depth: 3, own: true } : null,
    residents[0] ? { tree: residents[0], x: 56, y: 48, scale: 0.88, depth: 2, own: false } : null,
    residents[1] ? { tree: residents[1], x: 81, y: 27, scale: 0.78, depth: 1, own: false } : null
  ].filter((item) => Boolean(item));
  return placements.map((item) => ({ ...item.tree, ...item }));
}
function pointDistance(left, right) {
  return Math.hypot(left.x - right.x, (left.y - right.y) * 0.82);
}
function readSceneAnchor(visitId) {
  const key = `deepbazi:dream:first-visit:clock:${visitId}`;
  const stored = Number(sessionStorage.getItem(key));
  if (Number.isFinite(stored) && stored > 0) return stored;
  const value = Date.now();
  sessionStorage.setItem(key, String(value));
  return value;
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
function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}
function delay(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}
function actionId(prefix) {
  const value = globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${value}`;
}
function flowerLifecycleKey(attempt) {
  const flower = attempt.flower;
  if (!flower) return "";
  return [
    flower.state,
    flower.answer_count_visible ? flower.answer_count ?? 0 : "private",
    flower.own_answer_sealed,
    flower.shared_fruit_visible,
    flower.revealable,
    flower.close_reason || ""
  ].join("|");
}
function formatDreamDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "UTC"
  }).format(date);
}
function cssEscape(value) {
  return CSS.escape(value);
}
function escapeHtml5(value) {
  return value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character] || character);
}
function escapeAttr6(value) {
  return escapeHtml5(value);
}

// apps/product/experience_shell/src/dream_entry_transition.ts
var STORAGE_KEY = "deepbazi.dream.entry-transition.v1";
var HANDOFF_START_MS = 7100;
var RUNTIME_END_MS = 7750;
var STALE_AFTER_MS = 3e4;
var DreamEntryTransition = class {
  constructor(state) {
    this.state = state;
    document.querySelector("[data-dream-entry-cinematic]")?.remove();
    document.documentElement.classList.add("is-dream-entry-active");
    this.shell = document.createElement("div");
    this.shell.className = `dream-entry-cinematic${this.reducedMotion ? " is-reduced-motion" : ""}`;
    this.shell.dataset.dreamEntryCinematic = "active";
    this.shell.setAttribute("aria-hidden", "true");
    this.shell.innerHTML = this.reducedMotion ? `<img src="${DREAM_RUNTIME_ASSETS.dreamEntry.fallback}" alt="" draggable="false">` : `<video
          src="${DREAM_RUNTIME_ASSETS.dreamEntry.source}"
          poster="${DREAM_RUNTIME_ASSETS.dreamEntry.poster}"
          autoplay muted playsinline preload="auto"
        ></video>`;
    this.shell.insertAdjacentHTML(
      "beforeend",
      `<span class="dream-entry-cinematic-mist" aria-hidden="true"></span>
       <span class="dream-entry-cinematic-local-fog" aria-hidden="true"></span>`
    );
    document.body.append(this.shell);
    this.video = this.shell.querySelector("video");
    this.resumeAtElapsedTime();
  }
  shell;
  video;
  reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  destinationReady = false;
  handoffTimer = 0;
  maskTimer = 0;
  removeTimer = 0;
  bindVisit(visitId) {
    this.state = { ...this.state, visitId };
    writeStoredEntry(this.state);
  }
  markDestinationReady() {
    this.destinationReady = true;
    this.scheduleHandoff();
  }
  async waitUntilVisible() {
    if (this.reducedMotion || !this.video) {
      await nextPaint();
      return;
    }
    if (this.video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      await nextPaint();
      return;
    }
    await Promise.race([
      new Promise((resolve) => {
        this.video?.addEventListener("loadeddata", () => resolve(), { once: true });
      }),
      new Promise((resolve) => window.setTimeout(resolve, 480))
    ]);
    await nextPaint();
  }
  cancel() {
    this.clearTimers();
    this.shell.remove();
    document.documentElement.classList.remove("is-dream-entry-active");
    clearStoredEntry();
  }
  resumeAtElapsedTime() {
    const elapsedMs = Math.max(0, Date.now() - this.state.startedAt);
    if (this.reducedMotion || !this.video) return;
    const seek = () => {
      this.video.currentTime = Math.min(elapsedMs / 1e3, (RUNTIME_END_MS - 40) / 1e3);
      void this.video.play().catch(() => void 0);
    };
    if (this.video.readyState >= HTMLMediaElement.HAVE_METADATA) seek();
    else this.video.addEventListener("loadedmetadata", seek, { once: true });
  }
  scheduleHandoff() {
    if (!this.destinationReady) return;
    const elapsedMs = Math.max(0, Date.now() - this.state.startedAt);
    const waitMs = this.reducedMotion ? 180 : Math.max(0, HANDOFF_START_MS - elapsedMs);
    window.clearTimeout(this.handoffTimer);
    this.handoffTimer = window.setTimeout(() => {
      this.handoffTimer = 0;
      if (!this.destinationReady) return;
      this.shell.classList.add("is-masking-abu");
      window.clearTimeout(this.maskTimer);
      this.maskTimer = window.setTimeout(() => {
        this.maskTimer = 0;
        this.shell.classList.add("is-handing-off");
        window.clearTimeout(this.removeTimer);
        this.removeTimer = window.setTimeout(
          () => this.cancel(),
          this.reducedMotion ? 240 : 760
        );
      }, this.reducedMotion ? 40 : 220);
    }, waitMs);
  }
  clearTimers() {
    window.clearTimeout(this.handoffTimer);
    window.clearTimeout(this.maskTimer);
    window.clearTimeout(this.removeTimer);
    this.handoffTimer = 0;
    this.maskTimer = 0;
    this.removeTimer = 0;
  }
};
function beginDreamEntryTransition() {
  const state = { startedAt: Date.now(), visitId: "" };
  writeStoredEntry(state);
  return new DreamEntryTransition(state);
}
function resumeDreamEntryTransition() {
  const state = readStoredEntry();
  if (!state || !state.visitId || Date.now() - state.startedAt > STALE_AFTER_MS) {
    clearStoredEntry();
    return null;
  }
  const routeVisitId = decodeURIComponent(
    location.pathname.match(/\/experience\/dream\/visits\/([^/]+)/)?.[1] || ""
  );
  if (!routeVisitId || routeVisitId !== state.visitId) {
    clearStoredEntry();
    return null;
  }
  return new DreamEntryTransition(state);
}
function readStoredEntry() {
  try {
    const value = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
    if (!value || !Number.isFinite(value.startedAt) || typeof value.visitId !== "string") return null;
    return value;
  } catch {
    return null;
  }
}
function writeStoredEntry(value) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(value));
}
function clearStoredEntry() {
  sessionStorage.removeItem(STORAGE_KEY);
}
function nextPaint() {
  return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
}

// apps/product/experience_shell/src/relation_work_api.ts
async function requestJson2(url, init) {
  const response = await fetch(url, {
    credentials: "same-origin",
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...init?.headers || {} },
    ...init
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(String(payload.detail || `request_failed_${response.status}`));
  }
  return response.json();
}
function loadRealLifeTree(caseId) {
  return requestJson2(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/life-tree/questions`
  );
}
async function answerRealLifeTreeQuestion(caseId, questionId, optionId) {
  const payload = await requestJson2(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/life-tree/questions/${encodeURIComponent(questionId)}/answer`,
    {
      method: "POST",
      body: JSON.stringify({ selected_option_id: optionId })
    }
  );
  return payload.exploration;
}
function loadRealMingliLab(caseId) {
  return requestJson2(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/mingli-lab/relation-work`
  );
}

// apps/product/experience_shell/src/main.ts
var rootElement = document.querySelector("#experienceRoot");
if (!rootElement) throw new Error("experience_root_missing");
var root = rootElement;
var openingMusic = new OpeningMusicController(syncOpeningMusicControls);
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
var dreamReturnedWithSeed = consumeDreamReturnedWithSeed();
var realLifeTree = null;
var realLifeTreeLoading = false;
var realLifeTreeError = "";
var selectedLifeTreeQuestionId = "";
var selectedLifeTreeCategory = "factual_observation";
var selectedLifeTreeOptionId = "";
var lifeTreeAnswerSaving = false;
var realMingliLab = null;
var realMingliLabLoading = false;
var realMingliLabError = "";
var relationLabMode = "facts";
var selectedRelationPathRef = "";
if (location.pathname.startsWith("/experience/dream")) {
  const entryTransition = resumeDreamEntryTransition();
  void bootDreamExperience(root).finally(() => entryTransition?.markDestinationReady());
} else {
  void boot();
}
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
    realLifeTree = null;
    realLifeTreeError = "";
    selectedLifeTreeQuestionId = "";
    selectedLifeTreeOptionId = "";
    realMingliLab = null;
    realMingliLabError = "";
    selectedRelationPathRef = "";
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
  void ensureRealLifeTree();
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
    dreamStatus,
    dreamReturnedWithSeed,
    realLifeTree,
    realLifeTreeLoading,
    realLifeTreeError,
    selectedLifeTreeQuestionId,
    selectedLifeTreeCategory,
    selectedLifeTreeOptionId,
    lifeTreeAnswerSaving,
    realMingliLab,
    realMingliLabLoading,
    realMingliLabError,
    relationLabMode,
    selectedRelationPathRef
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
    },
    selectLifeTreeQuestion(questionId, category) {
      selectedLifeTreeQuestionId = questionId;
      selectedLifeTreeCategory = category;
      selectedLifeTreeOptionId = "";
      realLifeTreeError = "";
      render();
    },
    selectLifeTreeOption(optionId) {
      selectedLifeTreeOptionId = optionId;
      render();
    },
    submitLifeTreeAnswer() {
      void submitRealLifeTreeAnswer();
    },
    selectRelationLabMode(mode) {
      relationLabMode = mode;
      render();
    },
    selectRelationPath(pathRef) {
      selectedRelationPathRef = pathRef;
      relationLabMode = "candidates";
      render();
    },
    restoreRelationNatal() {
      selectCanvasStage("natal");
    }
  });
  syncOpeningMusicControls();
  openingMusic.arm();
  requestAnimationFrame(() => applyActiveAnchor(ui.selectedAnchor));
}
function syncOpeningMusicControls() {
  openingMusic.syncControls(root);
}
function selectArea(area) {
  if (!availableAreas.includes(area)) return;
  ui = reduceUi(ui, { type: "product-area", area });
  if (area === "lab") {
    selectLabLayer();
    void ensureCanvas();
    void ensureRealMingliLab();
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
  if (ui.productArea === "lab" || ui.workspaceSurface === "onecanvas") {
    await ensureCanvas();
  }
  if (ui.productArea === "lab") await ensureRealMingliLab();
  if (ui.workspaceSurface === "theater") await ensureNarration();
}
async function ensureRealLifeTree() {
  if (realLifeTree || realLifeTreeLoading || !activeCaseId) return;
  realLifeTreeLoading = true;
  realLifeTreeError = "";
  render();
  try {
    realLifeTree = await loadRealLifeTree(activeCaseId);
  } catch (error) {
    realLifeTree = null;
    realLifeTreeError = humanizeError(
      error instanceof Error ? error.message : String(error)
    );
  } finally {
    realLifeTreeLoading = false;
    render();
  }
}
async function submitRealLifeTreeAnswer() {
  if (lifeTreeAnswerSaving || !activeCaseId || !selectedLifeTreeQuestionId || !selectedLifeTreeOptionId) return;
  lifeTreeAnswerSaving = true;
  realLifeTreeError = "";
  render();
  try {
    await answerRealLifeTreeQuestion(
      activeCaseId,
      selectedLifeTreeQuestionId,
      selectedLifeTreeOptionId
    );
    realLifeTree = await loadRealLifeTree(activeCaseId);
    selectedLifeTreeOptionId = "";
  } catch (error) {
    realLifeTreeError = humanizeError(
      error instanceof Error ? error.message : String(error)
    );
  } finally {
    lifeTreeAnswerSaving = false;
    render();
  }
}
async function ensureRealMingliLab() {
  if (realMingliLab || realMingliLabLoading || !activeCaseId) return;
  realMingliLabLoading = true;
  realMingliLabError = "";
  render();
  try {
    realMingliLab = await loadRealMingliLab(activeCaseId);
    selectedRelationPathRef = realMingliLab.relation_work.candidate_path_view[0]?.work_path_candidate_ref || "";
  } catch (error) {
    realMingliLab = null;
    realMingliLabError = humanizeError(
      error instanceof Error ? error.message : String(error)
    );
  } finally {
    realMingliLabLoading = false;
    render();
  }
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
  openingMusic.pauseForNarration();
  if (await ensureNarration()) await timeline?.playSegment(index);
}
async function handleCommand(command) {
  if (command === "toggle-opening-music") {
    await openingMusic.toggle();
    return;
  }
  if (command === "manage-profiles") {
    await openProfileManager();
    return;
  }
  if (command === "toggle-abu") {
    dispatch({ type: "toggle-abu" });
    return;
  }
  if (command === "enter-dream") {
    let entryTransition = null;
    try {
      const guestCapability = sessionStorage.getItem("deepbazi.dream.guest-anchor-capability.v1");
      if (guestCapability && await confirmDreamAction(
        "\u53EA\u6062\u590D\u8FD9\u53F0\u8BBE\u5907\u4E0A\u672A\u767B\u5F55\u65F6\u7684\u68A6\u5883\u79BB\u5F00\u4F4D\u7F6E\uFF1F\u4E0D\u4F1A\u8FC1\u79FB\u547D\u7406\u4E8B\u5B9E\u3001\u6388\u6743\u6216\u8BBF\u95EE\u5386\u53F2\u3002",
        "\u6062\u590D\u4F4D\u7F6E"
      )) {
        await migrateGuestDreamAnchor(activeCaseId, guestCapability, true);
        sessionStorage.removeItem("deepbazi.dream.guest-anchor-capability.v1");
      }
      entryTransition = beginDreamEntryTransition();
      let visit = await createDreamVisit(activeCaseId);
      visit = await enterDreamVisit(visit.visit_id);
      entryTransition?.bindVisit(visit.visit_id);
      await entryTransition?.waitUntilVisible();
      markDreamNavigationHandoff();
      location.assign(`/experience/dream/visits/${encodeURIComponent(visit.visit_id)}`);
    } catch (error) {
      entryTransition?.cancel();
      const message = error instanceof Error ? error.message : String(error);
      root.innerHTML = renderUnavailable("\u8FD9\u6761\u68A6\u8DEF\u6682\u65F6\u6CA1\u6709\u5F00\u653E", humanizeError(message), "\u56DE\u5230\u751F\u547D\u4E16\u754C");
    }
    return;
  }
  if (command === "grant-dream-consent") {
    const accepted = await confirmDreamAction(
      "\u6388\u6743\u5F53\u524D\u6863\u6848\u4EE5\u533F\u540D\u751F\u547D\u6811\u8FDB\u5165\u672C\u5730\u5C01\u95ED\u68A6\u5883\uFF1F\u4EC5\u5C55\u793A\u786E\u5B9A\u6027\u547D\u76D8\u4E0E\u53EA\u8BFB\u6811\u8C61\uFF0C\u4F60\u53EF\u4EE5\u968F\u65F6\u64A4\u56DE\u3002",
      "\u786E\u8BA4\u6388\u6743"
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
    const confirmed = await confirmDreamAction(
      "\u64A4\u56DE\u5F53\u524D\u6863\u6848\u7684\u68A6\u5883\u5C55\u793A\u6388\u6743\uFF1F\u64A4\u56DE\u540E\uFF0C\u8FD9\u68F5\u771F\u4EBA\u751F\u547D\u6811\u4F1A\u7ACB\u5373\u5931\u53BB\u8FDB\u5165\u8D44\u683C\u3002",
      "\u786E\u8BA4\u64A4\u56DE"
    );
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
    openingMusic.pauseForNarration();
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
function confirmDreamAction(message, confirmLabel) {
  const dialog = document.createElement("dialog");
  dialog.className = "dream-consent-dialog";
  dialog.setAttribute("aria-labelledby", "dream-consent-dialog-title");
  dialog.innerHTML = `<form method="dialog">
    <p id="dream-consent-dialog-title"></p>
    <div>
      <button type="submit" value="cancel">\u6682\u4E0D</button>
      <button class="is-primary" type="submit" value="confirm"></button>
    </div>
  </form>`;
  const copy = dialog.querySelector("p");
  const confirm = dialog.querySelector('button[value="confirm"]');
  if (copy) copy.textContent = message;
  if (confirm) confirm.textContent = confirmLabel;
  document.body.append(dialog);
  return new Promise((resolve) => {
    const settle = () => {
      const accepted = dialog.returnValue === "confirm";
      dialog.remove();
      resolve(accepted);
    };
    dialog.addEventListener("close", settle, { once: true });
    dialog.showModal();
  });
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
  const layer = canvas.stages[ui.canvasStage].layers.find((item) => item.layer_id === "overview" && item.available);
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
    await delay2(1500);
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
function delay2(milliseconds) {
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
