from __future__ import annotations

import mimetypes

from v20.tests.support_paths import FRONTEND_DIR, read_v20_text


class StaticAsset:
    def __init__(self, relative_path: str) -> None:
        self.path = FRONTEND_DIR / relative_path
        self.status_code = 200 if self.path.exists() else 404
        self.text = self.path.read_text(encoding="utf-8") if self.path.suffix in {".html", ".js", ".css"} else ""
        content_type = mimetypes.guess_type(self.path.name)[0] or "application/octet-stream"
        self.headers = {"content-type": content_type}


def read_static_asset(relative_path: str) -> StaticAsset:
    return StaticAsset(relative_path)



def _all_ui_assets() -> tuple[StaticAsset, ...]:
    entry = read_static_asset("index.html")
    entry_script = read_static_asset("entry.js")
    profiles = read_static_asset("profiles.html")
    profiles_script = read_static_asset("profiles.js")
    legacy_page = read_static_asset("workbench.html")
    guest_page = read_static_asset("workbench-guest.html")
    page = read_static_asset("workbench-user.html")
    user_page = page
    practitioner_page = read_static_asset("workbench-practitioner.html")
    observe_page = read_static_asset("workbench-observe.html")
    route_script = read_static_asset("workbench_routes.js")
    page_controller_script = read_static_asset("workbench_page_controller.js")
    script = read_static_asset("app.js")
    admin = read_static_asset("admin.html")
    admin_script = read_static_asset("admin.js")
    style = read_static_asset("styles.css")
    logo = read_static_asset("qiazhi-logo-mark.png")
    favicon = read_static_asset("favicon.png")
    return (
        entry, entry_script, profiles, profiles_script, legacy_page, guest_page, page, user_page, practitioner_page,
        observe_page, route_script, page_controller_script, script, admin, admin_script, style, logo, favicon,
    )

def test_v20_entry_and_route_assets_are_wired() -> None:
    entry, entry_script, profiles, profiles_script, legacy_page, guest_page, page, user_page, practitioner_page, observe_page, route_script, page_controller_script, script, admin, admin_script, style, logo, favicon = _all_ui_assets()

    assert entry.status_code == 200
    assert "进入掐指一算" in entry.text
    assert "styles.css?v=20260510-ui-clean" in entry.text
    assert "workbench_routes.js?v=20260510-mvc-routes" in entry.text
    assert "entry.js?v=20260510-role-pages" in entry.text
    assert "/v20/ui/qiazhi-logo-mark.png" in entry.text
    assert "/v20/ui/favicon.png" in entry.text
    assert "brand-logo" in entry.text
    assert "brand-mark large" not in entry.text
    assert "Admin 入口" not in entry.text
    assert "DB / LLM" not in entry.text
    assert "id=\"loginRole\"" not in entry.text
    assert "id=\"registerRole\"" in entry.text
    assert "id=\"registerName\"" in entry.text
    assert "id=\"registerPassword\"" in entry.text
    assert '<option value="user" data-entry-option="role_user">普通用户</option>' in entry.text
    assert "data-entry-option=\"role_guest\"" not in entry.text
    assert '<option value="admin">Admin</option>' not in entry.text
    assert "guestStart" in entry.text
    assert "loginButton" in entry.text
    assert "registerButton" in entry.text
    assert "/api/v20/auth/guest" in entry_script.text
    assert "/api/v20/auth/login" in entry_script.text
    assert "/api/v20/auth/register" in entry_script.text
    assert "/v20/ui/profiles.html" not in entry.text
    assert "goProfiles" in entry_script.text
    assert 'window.location.href = "/v20/ui/profiles.html"' in entry_script.text
    assert "QiazhiWorkbenchRoutes.pageForRole" in entry_script.text
    assert "/v20/ui/workbench-user.html" in route_script.text
    assert "/v20/ui/workbench-guest.html" in route_script.text
    assert "/v20/ui/workbench-practitioner.html" in route_script.text
    assert "/v20/ui/workbench-observe.html" in route_script.text
    assert 'if (role === "guest") return "guest";' in route_script.text
    assert 'if (role === "lab") return "lab";' in route_script.text
    assert 'if (normalized === "lab") return OBSERVE_PAGE;' in route_script.text
    assert 'if (normalized === "lab") return ["reading", "observe"];' in route_script.text
    assert 'if (normalized === "guest") return ["reading"];' in route_script.text
    assert 'role: "guest"' not in entry_script.text
    assert 'auto_measure' not in entry_script.text
    assert "document.querySelector(\"#registerRole\").value" in entry_script.text
    assert "document.querySelector(\"#registerName\").value" in entry_script.text
    assert "document.querySelector(\"#registerPassword\").value" in entry_script.text
    assert "document.querySelector(\"#loginRole\")" not in entry_script.text
    assert "/api/v20/auth/logout" in entry_script.text

def test_v20_profiles_assets_are_wired() -> None:
    entry, entry_script, profiles, profiles_script, legacy_page, guest_page, page, user_page, practitioner_page, observe_page, route_script, page_controller_script, script, admin, admin_script, style, logo, favicon = _all_ui_assets()

    assert profiles.status_code == 200
    assert "V20 八字档案管理" in profiles.text
    assert "styles.css?v=20260510-ui-clean" in profiles.text
    assert "workbench_routes.js?v=20260510-mvc-routes" in profiles.text
    assert "profiles.js?v=20260510-role-pages" in profiles.text
    assert "/v20/ui/qiazhi-logo-mark.png" in profiles.text
    assert "brand-logo" in profiles.text
    assert "profileList" in profiles.text
    assert "newProfileButton" in profiles.text
    assert "profileEditor" in profiles.text
    assert "saveProfileButton" in profiles.text
    assert "importProfilesButton" not in profiles.text
    assert "instantMeasureLink" not in profiles.text
    assert "profileLocale" in profiles.text
    assert "data-profile-ui=\"language\"" not in profiles.text
    assert "class=\"admin-nav-link\" hidden" in profiles.text
    assert "logoutButton" in profiles.text
    assert 'id="profileGender"' in profiles.text
    assert '<option value="male" data-profile-option="gender_male">男</option>' in profiles.text
    assert '<option value="female" data-profile-option="gender_female">女</option>' in profiles.text
    assert 'id="profileLunarLeapMonth"' in profiles.text
    assert '<select id="profileBirthYear">' in profiles.text
    assert '<select id="profileBirthMonth">' in profiles.text
    assert '<select id="profileBirthDay">' in profiles.text
    assert '<select id="profileBirthHour">' in profiles.text
    assert '<select id="profileBirthMinute">' in profiles.text
    assert "/api/v20/profiles?limit=120" in profiles_script.text
    assert "/api/v20/profiles/import-v19?apply=true" not in profiles_script.text
    assert "method: profileId ? \"PATCH\" : \"POST\"" in profiles_script.text
    assert "method: \"DELETE\"" in profiles_script.text
    assert "appendProfileDefaults" not in profiles_script.text
    assert "flow_year_pillar" not in profiles_script.text
    assert "text.owner" not in profiles_script.text
    assert "profile.owner_id" not in profiles_script.text
    assert "profile.metadata?.source_system" not in profiles_script.text
    assert "populateBirthSelects" in profiles_script.text
    assert "for (let next = start; next <= end; next += 1)" in profiles_script.text
    assert "fillNumberSelect(\"#profileBirthYear\", 1900" in profiles_script.text
    assert "gender: value(\"#profileGender\") === \"female\" ? \"female\" : \"male\"" in profiles_script.text
    assert "lunar_is_leap_month" in profiles_script.text
    assert "toggleLunarLeapMonth" in profiles_script.text
    assert "new URLSearchParams({ profile_id: profile.profile_id || \"\" })" in profiles_script.text
    assert "workbenchPageForRole(state.sessionRole)" in profiles_script.text
    assert "QiazhiWorkbenchRoutes.pageForRole" in profiles_script.text
    assert "params.get(\"role\")" not in profiles_script.text

def test_v20_workbench_shells_are_role_scoped() -> None:
    entry, entry_script, profiles, profiles_script, legacy_page, guest_page, page, user_page, practitioner_page, observe_page, route_script, page_controller_script, script, admin, admin_script, style, logo, favicon = _all_ui_assets()

    assert legacy_page.status_code == 200
    assert "V20 测算入口" in legacy_page.text
    assert "routeLegacyWorkbench" in legacy_page.text
    assert "QiazhiWorkbenchRoutes" in legacy_page.text
    assert "measureForm" not in legacy_page.text
    assert page.status_code == 200
    assert guest_page.status_code == 200
    assert user_page.status_code == 200
    assert practitioner_page.status_code == 200
    assert observe_page.status_code == 200
    assert "V20 用户测算阅读" in page.text
    assert "workbench_routes.js?v=20260510-mvc-routes" in page.text
    assert "workbench_page_controller.js?v=20260510-mvc-page-controller" in page.text
    assert "app.js?v=20.3.19-runtime-flow" in page.text
    assert "styles.css?v=20260516-question-narrative" in page.text
    assert 'data-workbench-page="auto"' in legacy_page.text
    assert 'data-workbench-page="guest" data-workbench-default-mode="reading" data-workbench-lock-mode="true" data-role="guest"' in guest_page.text
    assert 'data-workbench-page="user" data-workbench-default-mode="reading" data-workbench-lock-mode="true"' in user_page.text
    assert 'data-workbench-page="practitioner" data-workbench-default-mode="practitioner" data-workbench-lock-mode="true"' in practitioner_page.text
    assert 'data-workbench-page="observe" data-workbench-default-mode="observe" data-workbench-lock-mode="true"' in observe_page.text
    assert "用户测算阅读" in user_page.text
    assert "游客测算阅读" in guest_page.text
    assert '<a href="/v20/ui/" data-ui="nav_profiles">入口</a>' in guest_page.text
    assert '<a href="/v20/ui/profiles.html" data-ui="nav_profiles">档案</a>' in user_page.text
    assert 'data-session-role="guest"' in guest_page.text
    assert 'class="control-panel"' not in guest_page.text
    assert "data-workbench-section=\"input\"" not in guest_page.text
    assert "workbench-mode-bar" not in guest_page.text
    assert "data-ui=\"pillars_form_title\"" not in guest_page.text
    assert "data-ui=\"user_focus\"" not in guest_page.text
    assert "data-ui=\"recommended_question\"" not in guest_page.text
    assert "data-ui=\"flow_year\"" not in guest_page.text
    assert "name=\"luck_pillar\"" not in guest_page.text
    assert "name=\"flow_month_pillar\"" not in guest_page.text
    assert "class=\"primary-action\"" not in guest_page.text
    for page in (guest_page, user_page, practitioner_page, observe_page):
        assert "Evidence" not in page.text
        assert "证据锚点" not in page.text
        assert "evidenceList" not in page.text
        assert "side-panel" not in page.text
    assert "practitionerCalibration" not in guest_page.text
    assert "observationPage" not in guest_page.text
    assert "featureStatePanel" not in guest_page.text
    assert "latentCalibration" not in guest_page.text
    assert "decisionHits" not in guest_page.text
    assert "portraitAxes" not in guest_page.text
    assert "admin-nav-link" not in guest_page.text
    assert "selectedProfileCard" not in guest_page.text
    assert "backToProfiles" not in guest_page.text
    assert "我想看事业和财运" not in guest_page.text
    assert "measureForm" in guest_page.text
    assert "命理师校准台" in practitioner_page.text
    assert "管理员观测台" in observe_page.text
    assert "/v20/ui/qiazhi-logo-mark.png" in page.text
    assert "brand-logo" in page.text
    assert "flow_year_pillar" in page.text
    assert "role_key" in page.text
    assert "<p class=\"section-kicker\">View</p>" not in page.text
    assert "name=\"locale\" id=\"localeSelect\"" in page.text
    assert "<option value=\"zh\">中文</option>" not in page.text
    assert '<option value="analyst" selected>命理师</option>' not in page.text
    assert '<option value="user">普通用户</option>' not in page.text
    assert '<option value="admin">管理员</option>' not in page.text
    assert '<option value="full">' not in page.text
    assert "selectedProfileCard" in page.text
    assert "structureDynamicsPanel" in page.text
    assert "structureDynamicsState" in page.text
    assert "structureDynamicsInterpretation" in page.text
    assert "brainStatePanel" in page.text
    assert "brainStateHeadline" in page.text
    assert "brainStateMeta" in page.text
    assert "brainStateBasis" in page.text
    assert "roleViewPanel" in page.text
    assert "readingProgressPanel" in page.text
    assert "readingProgressHeadline" in page.text
    assert "readingProgressGrid" in page.text
    assert "readingProgressNarrative" in page.text
    assert "roleViewPortrait" in page.text
    assert "chatText" in page.text
    assert "chatButton" in page.text
    assert "chatQuestionList" not in page.text
    assert "chatTranscript" in page.text
    for role_page in (guest_page, user_page, practitioner_page, observe_page):
        assert 'id="answerFeedbackPanel" class="answer-feedback-panel" hidden' in role_page.text
        assert "readingProgressPanel" in role_page.text
        assert "readingProgressNarrative" in role_page.text
    assert "interactionSignals" not in page.text
    assert "practitionerCalibration" in page.text
    assert 'id="practitionerCalibration" class="panel calibration-panel-card collapsed" data-workbench-section="practitioner" hidden' in page.text
    assert "calibrationControls" in page.text
    assert "latentCalibration" in page.text
    assert "latentCalibrationControls" in page.text
    assert "observationPage" in page.text
    assert 'id="observationPage" class="observation-page collapsed" data-workbench-section="observe" hidden' in page.text
    assert "observationToggle" in page.text
    assert 'id="observationToggle" class="observation-toggle" type="button" aria-expanded="false"' in page.text
    assert "observationBody" in page.text
    assert 'id="observationBody" class="observation-grid collapsible-body" hidden' in page.text
    assert "orchestratorTraceSummary" in page.text
    assert "orchestratorTraceSteps" in page.text
    assert "policyObservabilitySummary" in page.text
    assert "policyObservabilityConsumers" in page.text
    assert "policyTrainingTrend" in page.text
    assert "policyTrainingTimeline" in page.text
    assert "roleViewLearningSummary" in page.text
    assert "roleViewLearningDetails" in page.text
    assert "角色策略学习" in page.text
    assert 'id="featureStatePanel" class="panel feature-spine-panel" hidden' in page.text
    assert "图谱画像总览" in page.text
    assert "规则命中" in page.text
    assert "practitionerToggle" in page.text
    assert "profileImportButton" not in page.text
    assert "反馈校准" not in page.text
    assert "八字特征状态" in page.text
    assert "主题投射画像" in page.text
    assert "智能问题" in page.text
    assert page.text.index('id="brainStatePanel"') < page.text.index('id="answerText"') < page.text.index('id="answerFeedbackPanel"')
    assert page.text.index('id="answerFeedbackPanel"') < page.text.index('id="chatTranscript"')
    assert page.text.index('id="chatTranscript"') < page.text.index('class="answer-question-strip"') < page.text.index('class="dialog-row"')
    assert "交互信号" not in page.text
    assert "八字专业回复" in page.text

def test_v20_workbench_script_runtime_chain_is_wired() -> None:
    entry, entry_script, profiles, profiles_script, legacy_page, guest_page, page, user_page, practitioner_page, observe_page, route_script, page_controller_script, script, admin, admin_script, style, logo, favicon = _all_ui_assets()

    assert "/api/v20/measure/view/" in script.text
    assert "/api/v20/system/status" not in script.text
    assert "/api/v20/auth/me" in script.text
    assert "/api/v20/profiles/" in script.text
    assert "/api/v20/profiles/import-v19?apply=true" not in script.text
    assert "scheduleMeasure({ force: true })" in script.text
    assert "if (submit) submit.textContent = text.run;" in script.text
    assert "if (button) {" in script.text
    assert "document.body.classList.toggle(\"profile-reading\", Boolean(params.get(\"profile_id\")))" in script.text
    assert "renderRoleQuestionProfile(questionProfile, role, questions.length, nextQuestionPlan)" in script.text
    assert "const renderNextQuestionPlanSummary = (root, nextQuestionPlan = {}, role = \"user\") =>" in script.text
    assert "next-question-plan-summary" in script.text
    assert "next-question-chain" in script.text
    assert "followup_edges" in script.text
    assert "nextQuestionPlan.role_journey || {}" in script.text
    assert "nextQuestionPlan.session_memory || {}" in script.text
    assert "nextQuestionPlan.policy_trace || {}" in script.text
    assert "`策略 ${policySource}`" in script.text
    assert "`pointer ${policyTrace.active_policy_version}`" in script.text
    assert "if ([\"admin\", \"lab\", \"analyst\"].includes(role)) {" in script.text
    assert "renderQuestionGroups(root, visibleQuestions, activeId, role)" in script.text
    assert "const groupedRoleQuestions = (questions, role) =>" in script.text
    assert "/api/v20/role-view/question-click/record" in script.text
    assert "const recordRoleQuestionClick = (question, questionGroup = \"\") =>" in script.text
    assert "const recordQuestionFeedback = (question, questionGroup, role, action, reason, activeButton) =>" in script.text
    assert "const canReviewQuestions = (role) =>" in script.text
    assert "const canFeedbackQuestions = (role) =>" in script.text
    assert "const selectedQuestionForFeedback = (selected = {}, questions = []) =>" in script.text
    assert "const renderAnswerFeedback = (question = {}, role = \"user\") =>" in script.text
    assert "const questionFeedbackActions = (question, questionGroup, role) =>" in script.text
    assert "const recordQuestionRewardFeedback = (question, questionGroup, role, actionType, activeButton) =>" in script.text
    assert "[\"answer_helpful\", \"\", \"有帮助\"]" in script.text
    assert "[\"followup\", \"\", \"继续追问\"]" in script.text
    assert "[\"skip\", \"\", \"不感兴趣\"]" in script.text
    assert "action_type: actionType || \"answer_helpful\"" in script.text
    assert "/api/v20/question-review/record" in script.text
    assert "renderAnswerFeedback(selectedQuestionForFeedback(selected, result.questions || []), role)" in script.text
    assert "container.append(questionFeedbackActions(question, questionGroup, role))" not in script.text
    assert "QUESTION_REVIEW" not in script.text
    assert "question_group: questionGroup || roleQuestionGroupKey(question, role)" in script.text
    assert "seed_source_key: question.seed_source_key || \"\"" in script.text
    assert "questions.slice(0, Number.isFinite(limit) && limit > 0 ? limit : 8)" in script.text
    assert "const roleQuestionHint = (style) =>" in script.text
    assert "const roleVoiceProfileLabel = (profile) =>" in script.text
    assert "question.question_narrative || {}" in script.text
    assert "question.display_title" in script.text
    assert "questionAnchorLine(question.question_anchor || {})" in script.text
    assert "question.display_title || question.title" in script.text
    assert "recommended_questions" in script.text
    assert "template_zh" not in script.text
    assert "question-narrative" in script.text
    assert "question.next_question_atom_id" in script.text
    assert "next_question_atom_id: question.next_question_atom_id || \"\"" in script.text
    assert "next_question_topic: question.next_question_topic || \"\"" in script.text
    assert "next_question_stage: question.next_question_stage || \"\"" in script.text
    assert "payload.answered_question_keys = state.answeredQuestionKeys" in script.text
    assert "if (questionKey) state.answeredQuestionKeys = unique([...state.answeredQuestionKeys, questionKey]).slice(-32)" in script.text
    assert "next-question-reason" in script.text
    assert "roleVoiceProfileLabel(questionProfile.voice_profile)" in script.text
    assert "const decisionReport = result.decision_report || {}" in script.text
    assert "const featureStateModel = result.feature_state_model || {}" in script.text
    assert "const structureDynamics = result.structure_dynamics || {}" in script.text
    assert "const mainlineArbitration = result.mainline_arbitration || {}" in script.text
    assert "const brainState = result.brain_state || {}" in script.text
    assert "renderBrainState(brainState)" in script.text
    assert "renderRoleViewModel(result.role_view_model || {}, role)" in script.text
    assert "renderReadingProgress(result, role)" in script.text
    assert "renderContextBinding(result, role)" in script.text
    assert "result.role_view_model?.question_profile || {}" in script.text
    assert "const renderBrainState = (brainState = {}) =>" in script.text
    assert "const renderRoleViewModel = (roleView = {}, role = \"user\") =>" in script.text
    assert "const renderReadingProgress = (result = {}, role = \"user\") =>" in script.text
    assert "const renderContextBinding = (result = {}, role = \"user\") =>" in script.text
    assert "context_alignment_report" in script.text
    assert "当前链路已锁定这一个八字" in script.text
    assert "画像、结构动态和智能问题都按当前命盘展开" in script.text
    assert "const readingProgressModel = (result = {}, role = \"user\") =>" in script.text
    assert "const readingProgressTone = (role = \"user\") =>" in script.text
    assert "先给你抓住重点" in script.text
    assert "命理师链路已收束到" in script.text
    assert "本次阅读主线" in script.text
    assert "summary.selection_reasons" in script.text
    assert "summary.coordination_status" in script.text
    assert "summary.coordination_note" in script.text
    assert "统筹提示" in script.text
    assert "const answerStrategy = result.answer_plan?.dimension_context?.answer_strategy || {}" in script.text
    assert "const questionIntentModel = result.question_intent_model || {}" in script.text
    assert "const interactionSession = result.interaction_session || {}" not in script.text
    assert "交互会话模型" not in script.text
    assert "renderInteractionSignals" not in script.text
    assert 'const displayRole = (role = roleSelect.value) => WorkbenchPage.config.page === "guest" ? "guest" : measurementRole(role);' in script.text
    assert 'const runtimeRole = (role = roleSelect.value) => displayRole(role) === "guest" ? "guest" : measurementRole(role);' in script.text
    assert 'const role = displayRole(result.role?.role_key || roleSelect.value);' in script.text
    assert 'renderGuestNavigation(WorkbenchPage.config.page === "guest" || document.body.dataset.role === "guest")' in script.text
    assert "profilesLink.textContent = currentText().nav_profiles" in script.text
    assert "renderFeatures(" in script.text
    assert "renderStructureDynamics(structureDynamics, mainlineArbitration)" in script.text
    assert "renderOrchestratorTrace(result.reasoning_orchestrator || {}, mainlineArbitration, result.redis_cache || {}, answerStrategy)" in script.text
    assert "renderPolicyObservability(result.orchestrator_policy_observability || {})" in script.text
    assert "renderPolicyTrainingObservability(role)" in script.text
    assert "/api/v20/policy-observability" in script.text
    assert "const renderPolicyObservability = (policy = {}) =>" in script.text
    assert "const renderRoleViewLearningObservability = async (role) =>" in script.text
    assert "renderRoleViewLearningObservability(role)" in script.text
    assert "/api/v20/learning/role-question-click" in script.text
    assert "/api/v20/learning/role-view-policy-candidates" in script.text
    assert "/api/v20/learning/role-view-policy-replay" in script.text
    assert "/api/v20/role-view/runtime-pointer" in script.text
    assert "const roleViewLearningRows = (clicks = {}, candidates = {}, replay = {}, pointer = {}) =>" in script.text
    assert "candidates.policy_payload?.seed_fit_policy || []" in script.text
    assert "row.policy_key === \"seed_fit_policy\"" in script.text
    assert "[\"seed-fit\", String((candidates.policy_payload?.seed_fit_policy || []).length)]" in script.text
    assert "[\"pointer\", pointer.status || \"-\"]" in script.text
    assert "pointer.runtime_applied ? \"applied\" : (replayResult.eligible_for_runtime ? \"eligible\" : \"baseline\")" in script.text
    assert "[\"active role policy\", pointer.active_policy_version || \"-\"]" in script.text
    assert "[\"pointer gate\", pointer.blocking_gate || \"-\"]" in script.text
    assert "replayResult.blocking_gate" in script.text
    assert "const renderPolicyTrainingObservability = async (role) =>" in script.text
    assert "role === \"lab\"" in script.text
    assert "onDone: (payload) =>" in script.text
    assert "setText(\"#answerText\", payload.answer_text || \"\")" in script.text
    assert "doneSeen" in script.text
    assert "status: \"stream_eof\"" in script.text
    assert "redisCacheLabel" in script.text
    assert "qualityGateLabel" in script.text
    assert "practitionerReviewLabel" in script.text
    assert "answerStrategyLabel" in script.text
    assert "命理师校准" in script.text
    assert "回答策略" in script.text
    assert "质量门校准" in script.text
    assert "确认第一主线" in script.text
    assert "arbitration.quality_gate" in script.text
    assert "orchestrator.primary_outputs" in script.text
    assert "arbitrationSummaryLine" in script.text
    assert "chainNodeLabel" in script.text
    assert "dynamicSummaryLine" in script.text
    assert "dynamicInterpretation" in script.text
    assert "const runtimeChainNodes = Array.isArray(chain.nodes) ? chain.nodes : []" in script.text
    assert "const rawChainNodes = runtimeChainNodes.length ? runtimeChainNodes : arbitrationNodes" in script.text
    assert "focusedChainNodes(rawChainNodes, chain.pattern_key || \"\")" in script.text
    assert "food_controls_killing" in script.text
    assert "output_to_wealth" in script.text
    assert "const workPath = dynamics.primary_dynamic_chain || {}" in script.text
    assert "核心做功链" in script.text
    assert "dynamic-work-path" in script.text
    assert "dynamicPathStateLabel" in script.text
    assert "命理解释" in script.text
    assert "[\"output\", \"authority\"]" in script.text
    assert "食神制杀时" in script.text
    assert "不能自动归到食伤生财" in script.text
    assert "日主承载需要继续校准" in script.text
    assert "稳定受冲" in script.text
    assert "output → wealth" not in script.text
    assert "STEM_META" in script.text
    assert "BRANCH_META" in script.text
    assert "pillarGlyph(pillar)" in script.text
    assert "dataset.element" in script.text
    assert "dataset.polarity" in script.text
    assert "featureStateModel.priority_features" in script.text
    assert "renderPortrait(portraitProjection.axes || [])" in script.text
    assert "renderPractitionerCalibration(decisionReport.practitioner_controls || []" in script.text
    assert 'left.control_key === "control.mainline_arbitration"' in script.text
    assert "visibleControls.slice(0, 6)" in script.text
    assert "control.mainline_arbitration" in read_v20_text("interaction/practitioner_calibration.py")
    assert "renderLatentCalibration(result.input_id || \"\", role)" in script.text
    assert "renderObservationAccess(role)" in script.text
    assert "renderFeatureStateAccess(role)" in script.text
    assert "panel.hidden = role === \"user\"" in script.text
    assert "role === \"admin\"" in script.text
    assert "setPractitionerCollapsed" in script.text
    assert "/api/v20/learning/latent-event-calibration" in script.text
    assert "/api/v20/latent-event/calibration/record" in script.text
    assert "/api/v20/practitioner/calibration/record" in script.text
    assert "rule-candidate" not in script.text
    assert "规则候选验证" not in script.text
    assert "特征发现验证" not in script.text
    assert "chatButton.textContent = busy ? text.wb.generating : text.wb.send" in script.text
    assert "payload.llm_mode = llmMode" in script.text
    assert "const interactiveLlmMode = () => (params.get(\"llm\") === \"deterministic\" ? \"deterministic\" : \"practitioner\")" in script.text
    assert "/stream" in script.text
    assert "requestMeasureStream" in script.text
    assert "startAnswerTypewriter" in script.text
    assert "queueAnswerText" in script.text
    assert "questionBindingByKey" not in script.text
    assert "sourceLine" not in script.text
    assert "plainAnswerText" in script.text
    assert "JSON.parse(text)" in script.text
    assert "assist.practitioner_answer" in script.text
    assert "appendChatTurn(interactionText" in script.text
    assert ".chat-transcript" in style.text
    assert ".calibration-panel-card" in style.text
    assert ".axis-temp" in style.text
    assert ".signal-row" not in style.text
    assert ".answer-question-strip" in style.text
    assert ".grouped-question-list" in style.text
    assert ".role-question-group" in style.text
    assert ".question-narrative" in style.text
    assert ".question-review-row" not in style.text
    assert ".answer-feedback-panel" in style.text
    assert ".answer-feedback-meta" in style.text
    assert ".question-feedback-actions" in style.text
    assert ".feedback-action" in style.text
    assert ".structure-dynamics-panel" in style.text
    assert ".brain-state-panel" in style.text
    assert ".brain-state-basis-row" in style.text
    assert ".reading-progress-panel" in style.text
    assert ".reading-progress-grid" in style.text
    assert ".reading-progress-meter-bar" in style.text
    assert ".context-binding-panel" in style.text
    assert ".context-binding-modules" in style.text
    assert 'body[data-workbench-page="guest"] .dashboard-grid' in style.text
    assert 'body[data-workbench-page="user"] .structure-dynamics-panel' in style.text
    assert 'body[data-workbench-page="guest"] .measure-layout' in style.text
    assert ".answer-grid" in style.text
    assert "grid-template-columns: minmax(0, 1.36fr) minmax(300px, 0.64fr)" not in style.text
    assert ".dynamic-metric-grid" in style.text
    assert ".dynamic-interpretation" in style.text
    assert ".dynamic-work-path" in style.text
    assert "payload.practitioner_selections = state.practitionerSelections" in script.text
    assert "payload.latent_event_answers = state.latentAnswers" in script.text
    assert "已记录 · 刷新问题" in script.text
    assert ".evidence-row" not in style.text
    assert ".latent-calibration-card" in style.text
    assert ".observation-page" in style.text
    assert ".observation-grid" in style.text
    assert ".observation-toggle" in style.text
    assert ".policy-observability-summary" in style.text
    assert ".workbench-mode-bar" in style.text
    assert ".workbench-mode-bar::-webkit-scrollbar" in style.text
    assert ".role-question-group-head strong" in style.text
    assert 'body[data-workbench-mode="practitioner"] [data-workbench-section="answer"]' not in style.text
    assert 'body[data-workbench-mode="observe"] [data-workbench-section="answer"]' not in style.text
    assert 'data-workbench-mode-target="reading"' in page.text
    assert 'data-workbench-mode-target="practitioner"' in page.text
    assert 'data-workbench-mode-target="observe"' in page.text
    assert 'data-workbench-section="answer"' in page.text
    assert 'data-workbench-section="practitioner"' in page.text
    assert 'data-workbench-section="observe"' in page.text
    assert "const allowedWorkbenchModes" in script.text
    assert "QiazhiWorkbenchPageController" in script.text
    assert "WorkbenchPage.allowedModes" in script.text
    assert "WorkbenchPage.routeToRolePageIfNeeded" in script.text
    assert "WorkbenchPage.renderNavigation" in script.text
    assert "if (!root) return" in script.text
    assert "const selectedProfileCard = document.querySelector(\"#selectedProfileCard\")" in script.text
    assert "routeToRolePageIfNeeded" in script.text
    assert "renderWorkbenchNavigation" in script.text
    assert "applyWorkbenchMode" in script.text
    assert "params.get(\"role\")" not in script.text
    assert ".orchestrator-trace-card" in style.text
    assert ".orchestrator-step-row" in style.text
    assert ".collapse-toggle" in style.text
    assert "applyProfileDefaults(profile)" in script.text
    assert "params.get(\"role\")" not in script.text
    assert "params.get(\"locale\")" not in script.text
    assert "auto_measure" not in script.text
    assert "const endpoint = `/api/v20/measure/view/${role}`" in script.text
    assert "确认四柱后会生成建议问题" in script.text
    assert "명리사" in script.text
    assert "full_runtime" not in script.text
    assert "/api/v20/feedback/record" not in script.text

def test_v20_admin_training_ui_is_wired() -> None:
    entry, entry_script, profiles, profiles_script, legacy_page, guest_page, page, user_page, practitioner_page, observe_page, route_script, page_controller_script, script, admin, admin_script, style, logo, favicon = _all_ui_assets()

    assert "系统与训练" in admin.text
    assert "styles.css?v=20260515-admin-polish" in admin.text
    assert "admin.js?v=20260517-llm-quality-loop" in admin.text
    assert "new URLSearchParams(window.location.search)" not in admin_script.text
    assert "/v20/ui/qiazhi-logo-mark.png" in admin.text
    assert "brand-logo" in admin.text
    assert "/v20/ui/profiles.html" in admin.text
    assert "/api/v20/admin/db" in admin_script.text
    assert "/api/v20/admin/llm" in admin_script.text
    assert "/api/v20/admin/config" in admin_script.text
    assert "/api/v20/admin/db/config" in admin_script.text
    assert "/api/v20/admin/llm/config" in admin_script.text
    assert "/api/v20/admin/llm/test" in admin_script.text
    assert "dbConfigForm" in admin.text
    assert "llmConfigForm" in admin.text
    assert "llmModelSelect" in admin.text
    assert "llmTestPrompt" in admin.text
    assert "llmTestResult" in admin.text
    assert "saveDbConfig" in admin_script.text
    assert "saveLlmConfig" in admin_script.text
    assert "renderModelOptions" in admin_script.text
    assert "testLlm" in admin_script.text
    assert "scrubSecrets" in admin_script.text
    assert "renderTrainingWriterResults" in admin_script.text
    assert "自动调参写入结果" in admin_script.text
    assert "writerLabel" in admin_script.text
    assert ".training-writer-results" in style.text
    assert ".admin-config-form" in style.text
    assert ".admin-test-box" in style.text
    assert "/api/v20/redis/cache-status" in admin_script.text
    assert "/api/v20/redis/cache-clear" in admin_script.text
    assert "clearRedisCache" in admin_script.text
    assert "运行缓存" in admin.text
    assert "/api/v20/auth/logout" in admin_script.text
    assert "Knowledge Evidence Store" not in admin.text
    assert "八字资料来源库" not in admin.text
    assert ".measure-layout" in style.text
    assert "body.profile-reading .control-panel" in style.text
    assert "body.profile-reading .feature-spine-panel" in style.text
    assert ".questions-panel-card" not in style.text
    assert "body.profile-reading .pillar-panel" in style.text
    assert "grid-template-columns: repeat(6, minmax(86px, 1fr))" in style.text
    assert ".pillar-symbol[data-element=\"wood\"]" in style.text
    assert ".pillar-symbol[data-element=\"fire\"]" in style.text
    assert ".pillar-symbol[data-element=\"earth\"]" in style.text
    assert ".pillar-symbol[data-element=\"metal\"]" in style.text
    assert ".pillar-symbol[data-element=\"water\"]" in style.text
    assert "flex-wrap: nowrap" in style.text
    assert "overscroll-behavior-x: contain" in style.text
    assert "-webkit-line-clamp: 2" in style.text
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in style.text
    assert ".profiles-layout" in style.text
    assert ".profile-card .tag" in style.text
    assert ".profile-card-actions" in style.text
    assert ".check-row" in style.text
    assert ".brand-logo" in style.text
    assert "V20 visual polish" in style.text
    assert "Terminal responsive polish" in style.text
    assert "@media (min-width: 1280px)" in style.text
    assert "@media (min-width: 761px) and (max-width: 1120px)" in style.text
    assert "@media (max-width: 420px)" in style.text
    assert "min-height: calc(100dvh - 20px)" in style.text
    assert ".input-grid-time" in style.text
    assert "min-height: 100dvh" in style.text
    assert "grid-template-columns: repeat(6, minmax(62px, 74px))" in style.text
    assert "backdrop-filter" in style.text
    assert "env(safe-area-inset-bottom)" in style.text
    assert "@media (max-width: 480px)" in style.text
    assert "@media (hover: none)" in style.text
    assert ".dialog-row textarea" in style.text
    assert ".entry-page" in style.text
    assert ".admin-layout" in style.text
    assert "@media (max-width: 1120px)" in style.text
    assert "@media (max-width: 760px)" in style.text
    assert "Mobile Chrome final sync guard" in style.text
    assert "-webkit-overflow-scrolling: touch" in style.text
    assert "grid-auto-flow: column" in style.text
    assert script.status_code == 200
    assert admin.status_code == 200
    assert admin_script.status_code == 200
    assert "Policy Observe" not in admin.text
    assert "policySummary" not in admin.text
    assert "Question Policy" not in admin.text
    assert "roleViewPolicySummary" not in admin.text
    assert "Review Training" not in admin.text
    assert "questionReviewTrainingSummary" not in admin.text
    assert "训练任务" in admin.text
    assert "自我训练" in admin.text
    assert "trainingTaskRegistry" in admin.text
    assert "trainingProgressBar" in admin.text
    assert "trainingResultSummary" in admin.text
    assert "trainingTaskLog" in admin.text
    assert "trainingActivationHistory" in admin.text
    assert "admin-tabbar" in admin.text
    assert 'data-admin-tab-section="config"' in admin.text
    assert 'data-admin-tab-section="training"' in admin.text
    assert "admin.js?v=20260517-llm-quality-loop" in admin.text
    assert "/api/v20/admin/policy-observability" not in admin_script.text
    assert "/api/v20/role-view/runtime-pointer" not in admin_script.text
    assert "/api/v20/learning/question-review" not in admin_script.text
    assert "/api/v20/learning/question-dag" not in admin_script.text
    assert "/api/v20/admin/training/tasks/registry" in admin_script.text
    assert "/api/v20/admin/central-brain-architecture" in admin_script.text
    assert "/api/v20/admin/mainline-status" in admin_script.text
    assert "/api/v20/admin/runtime-consumption-audit" in admin_script.text
    assert "/api/v20/admin/training/tasks/start" in admin_script.text
    assert "/api/v20/admin/training/activations" in admin_script.text
    assert "mainline_completion" in admin_script.text
    assert "parameter_impact" in admin_script.text
    assert "\"完成度\"" in admin_script.text
    assert "\"待补齐\"" in admin_script.text
    assert "\"参数优化\"" in admin_script.text
    assert "\"自动调参\"" in admin_script.text
    assert "\"合成缺口\"" in admin_script.text
    assert "training_plan" in admin_script.text
    assert "optimization_topics" in admin_script.text
    assert "training-topic-grid" in admin_script.text
    assert "training_groups" in admin_script.text
    assert "原子训练：" in admin_script.text
    assert "中枢训练控制台" in admin_script.text
    assert "const renderCentralBrainArchitecture = (root, architecture = {}) =>" in admin_script.text
    assert "const renderMainlineStatus = (root, status = {}) =>" in admin_script.text
    assert "主线完成度与最新设计" in admin_script.text
    assert "流式质量样本" in admin_script.text
    assert "上下文预算权重" in admin_script.text
    assert "Prompt 方式" in admin_script.text
    assert "renderLlmConfigDesignSummary" in admin_script.text
    assert "遗留上下文" in admin_script.text
    assert "const renderLlmPromptContextDesign = (design = {}) =>" in admin_script.text
    assert "LLM 提示词与上下文" in admin_script.text
    assert "短提示词负责任务和边界" in admin_script.text
    assert "上下文预算" in admin_script.text
    assert "防止提示词膨胀" in admin_script.text
    assert "流式输入" in admin_script.text
    assert "practitioner_stream_payload_max_chars" in admin_script.text
    assert "zhContextLayer" in admin_script.text
    assert "zhLlmConsumer" in admin_script.text
    assert "answer_plan_rewrite.context.v2" in admin_script.text
    assert "const renderBrainGraphTaskMap = (root, centralBrain = {}) =>" in admin_script.text
    assert "中枢任务编排" in admin_script.text
    assert "brain_graph_task_sections" in admin_script.text
    assert "primary_brain_node" in admin_script.text
    assert "training-brain-targets" in admin_script.text
    assert "brain_graph" in admin_script.text
    assert "runtime_pointer_targets" in admin_script.text
    assert "训练结果接入系统检查" in admin_script.text
    assert "const renderRuntimeConsumptionAudit = (root, audit = {}) =>" in admin_script.text
    assert "调参影响总览" in admin_script.text
    assert "pointer_effect_summary" in admin_script.text
    assert "before_after_effect" in admin_script.text
    assert "const pointerEffectLabel = (status) =>" in admin_script.text
    assert "runtime_consumer_status" in admin_script.text
    assert "parameter_targets" in admin_script.text
    assert "optimizer_writer_status" in admin_script.text
    assert "dedupe_summary" in admin_script.text
    assert "synthetic_rule_plan" in admin_script.text
    assert "candidate_quality_signal" in admin_script.text
    assert "central_brain_tuning_package" in admin_script.text
    assert "structure_dynamics_path_distribution" in admin_script.text
    assert "structure_dynamics_knowledge_coverage" in admin_script.text
    assert "structure_dynamics_corpus_distribution" in admin_script.text
    assert "结构动态覆盖" in admin_script.text
    assert "结构知识覆盖" in admin_script.text
    assert "结构语料回放" in admin_script.text
    assert "结构动态切换报告" in admin_script.text
    assert "当前做功链名称必须能回到知识机制、完整知识单元" in admin_script.text
    assert "full_knowledge_unit_count" in admin_script.text
    assert "不把语料当单盘结论" in admin_script.text
    assert "反例边界" in admin_script.text
    assert "岁运阻断" in admin_script.text
    assert "const zhRelationType = (type) =>" in admin_script.text
    assert "const structureSwitchStatusLabel = (status) =>" in admin_script.text
    assert "const structureKnowledgeCoverageLabel = (status) =>" in admin_script.text
    assert "中枢调参决策包" in admin_script.text
    assert "合成验证、518K 回放和八字上下文偏离" in admin_script.text
    assert "const centralTuningDecisionLabel = (decision) =>" in admin_script.text
    assert "const centralApplyStatusLabel = (status) =>" in admin_script.text
    assert "ready_pointer_count" in admin_script.text
    assert "候选质量信号" in admin_script.text
    assert "candidate_promotion_score" in admin_script.text
    assert "quality_scores" in admin_script.text
    assert "bazi_context_drift_score" in admin_script.text
    assert "八字上下文偏离" in admin_script.text
    assert "const zhQualityScore = (key) =>" in admin_script.text
    assert "const zhGateBlocker = (gate) =>" in admin_script.text
    assert "const renderTrainingPlan = (root, plan = {}) =>" in admin_script.text
    assert "训练计划与去重" in admin_script.text
    assert "结构动态做功链验证脚本" in admin_script.text
    assert "结构动态语料回放脚本" in admin_script.text
    assert "冷却期内避免重复训练" in admin_script.text
    assert "后台训练已启动" in admin_script.text
    assert "后台独立运行" in admin_script.text
    assert "const renderTrainingTasks = async () =>" in admin_script.text
    assert "const startTrainingTask = async (taskKey) =>" in admin_script.text
    assert "const renderTrainingActivationHistory = (rows) =>" in admin_script.text
    assert "const renderTrainingResultSummary = (task = {}) =>" in admin_script.text
    assert "result_summary" in admin_script.text
    assert "machine_gate" in admin_script.text
    assert "机器调参" in admin_script.text
    assert "runtimeFieldLabel" in admin_script.text
    assert "context_quality_signal" in admin_script.text
    assert "八字上下文：" in admin_script.text
    assert "const trainingContextQualityLabel = (status) =>" in admin_script.text
    assert "publish_preview" in admin_script.text
    assert "自动调参" in admin_script.text
    assert "优化方向" in admin_script.text
    assert "const activationFamilyLabel = (family) =>" in admin_script.text
    assert "激活准备" not in admin_script.text
    assert "采纳调参" not in admin_script.text
    assert "重新尝试生效" in admin_script.text
    assert "自动调参" in admin_script.text
    assert "训练完成后直接写入" in admin_script.text
    assert "还缺调参器" in admin_script.text
    assert "const canApplyTrainingParameters = (preview = {}) =>" in admin_script.text
    assert "const recordTrainingParameterApply = async (taskId) =>" in admin_script.text
    assert "ACTIVATE_TRAINING_RESULT" in admin_script.text
    assert "/api/v20/admin/training/tasks/${encodeURIComponent(taskId)}/activate" in admin_script.text
    assert "/api/v20/admin/training/tasks/${encodeURIComponent(taskId)}/review" not in admin_script.text
    assert "const trainingReviewActions = (taskId, gate = {}) =>" not in admin_script.text
    assert "const recordTrainingReview = async (taskId, action) =>" not in admin_script.text
    assert "const recordTrainingActivationPreflight = async (taskId) =>" not in admin_script.text
    assert "scheduleTrainingTaskPoll" in admin_script.text
    assert "trainingTaskPollTimer" in admin_script.text
    assert "const setAdminTab = (tab) =>" in admin_script.text
    assert "Promise.allSettled" in admin_script.text
    assert "renderQuestionReviewTraining" not in admin_script.text
    assert "renderPolicyObservability" not in admin_script.text
    assert "renderRoleViewPolicyPointer" not in admin_script.text
    assert ".admin-training-card" in style.text
    assert ".admin-tabbar" in style.text
    assert 'body[data-admin-tab="config"] [data-admin-tab-section="training"]' in style.text
    assert ".training-task-grid" in style.text
    assert ".training-plan-card" in style.text
    assert ".training-plan-rows" in style.text
    assert ".training-plan-gaps" in style.text
    assert ".training-topic-grid" in style.text
    assert ".central-brain-card" in style.text
    assert ".brain-graph-strip" in style.text
    assert ".brain-graph-node" in style.text
    assert ".brain-task-map" in style.text
    assert ".training-brain-targets" in style.text
    assert ".training-quality-signal" in style.text
    assert ".training-topic-card" in style.text
    assert ".training-progress-bar" in style.text
    assert ".training-result-summary" in style.text
    assert ".training-optimization-gate" in style.text
    assert ".training-activation-actions" in style.text
    assert ".training-publish-preview" in style.text

def test_v20_styles_controller_and_binary_assets_are_wired() -> None:
    entry, entry_script, profiles, profiles_script, legacy_page, guest_page, page, user_page, practitioner_page, observe_page, route_script, page_controller_script, script, admin, admin_script, style, logo, favicon = _all_ui_assets()

    assert style.status_code == 200
    assert entry_script.status_code == 200
    assert profiles_script.status_code == 200
    assert logo.status_code == 200
    assert favicon.status_code == 200
    assert route_script.status_code == 200
    assert page_controller_script.status_code == 200
    assert "QiazhiWorkbenchPageController" in page_controller_script.text
    assert "allowedModes" in page_controller_script.text
    assert "const pageRole" in page_controller_script.text
    assert 'practitioner: "analyst"' in page_controller_script.text
    assert 'observe: "admin"' in page_controller_script.text
    assert "routeAnonymousIfNeeded" in page_controller_script.text
    assert 'window.location.replace("/v20/ui/")' in page_controller_script.text
    assert logo.headers["content-type"] == "image/png"
