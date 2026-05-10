from __future__ import annotations

import mimetypes
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


class StaticAsset:
    def __init__(self, relative_path: str) -> None:
        self.path = FRONTEND_DIR / relative_path
        self.status_code = 200 if self.path.exists() else 404
        self.text = self.path.read_text(encoding="utf-8") if self.path.suffix in {".html", ".js", ".css"} else ""
        content_type = mimetypes.guess_type(self.path.name)[0] or "application/octet-stream"
        self.headers = {"content-type": content_type}


def read_static_asset(relative_path: str) -> StaticAsset:
    return StaticAsset(relative_path)


def test_v20_ui_static_shell_is_served_from_v20_directory() -> None:
    entry = read_static_asset("index.html")
    entry_script = read_static_asset("entry.js")
    profiles = read_static_asset("profiles.html")
    profiles_script = read_static_asset("profiles.js")
    page = read_static_asset("workbench.html")
    script = read_static_asset("app.js")
    admin = read_static_asset("admin.html")
    admin_script = read_static_asset("admin.js")
    style = read_static_asset("styles.css")
    logo = read_static_asset("qiazhi-logo-mark.png")
    favicon = read_static_asset("favicon.png")

    assert entry.status_code == 200
    assert "进入掐指一算" in entry.text
    assert "styles.css?v=20260505-glass" in entry.text
    assert "entry.js?v=20260509-route-state" in entry.text
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
    assert 'window.location.href = "/v20/ui/workbench.html"' in entry_script.text
    assert 'role: "guest"' not in entry_script.text
    assert 'auto_measure' not in entry_script.text
    assert "document.querySelector(\"#registerRole\").value" in entry_script.text
    assert "document.querySelector(\"#registerName\").value" in entry_script.text
    assert "document.querySelector(\"#registerPassword\").value" in entry_script.text
    assert "document.querySelector(\"#loginRole\")" not in entry_script.text
    assert "/api/v20/auth/logout" in entry_script.text
    assert profiles.status_code == 200
    assert "V20 八字档案管理" in profiles.text
    assert "styles.css?v=20260505-glass" in profiles.text
    assert "profiles.js?v=20260509-route-state" in profiles.text
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
    assert "params.get(\"role\")" not in profiles_script.text
    assert page.status_code == 200
    assert "V20 命理测算台" in page.text
    assert "styles.css?v=20260505-glass" in page.text
    assert "app.js?v=20.3.5" in page.text
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
    assert "chatText" in page.text
    assert "chatButton" in page.text
    assert "chatQuestionList" not in page.text
    assert "chatTranscript" in page.text
    assert "interactionSignals" not in page.text
    assert "practitionerCalibration" in page.text
    assert 'id="practitionerCalibration" class="panel calibration-panel-card collapsed" hidden' in page.text
    assert "calibrationControls" in page.text
    assert "latentCalibration" in page.text
    assert "latentCalibrationControls" in page.text
    assert "observationPage" in page.text
    assert 'id="observationPage" class="observation-page collapsed" hidden' in page.text
    assert "observationToggle" in page.text
    assert 'id="observationToggle" class="observation-toggle" type="button" aria-expanded="false"' in page.text
    assert "observationBody" in page.text
    assert 'id="observationBody" class="observation-grid collapsible-body" hidden' in page.text
    assert "orchestratorTraceSummary" in page.text
    assert "orchestratorTraceSteps" in page.text
    assert 'id="featureStatePanel" class="panel feature-spine-panel" hidden' in page.text
    assert "图谱画像总览" in page.text
    assert "Decision Hits" in page.text
    assert "practitionerToggle" in page.text
    assert "profileImportButton" not in page.text
    assert "反馈校准" not in page.text
    assert "八字特征状态" in page.text
    assert "主题投射画像" in page.text
    assert "智能问题" in page.text
    assert page.text.index('id="chatTranscript"') < page.text.index('class="answer-question-strip"') < page.text.index('class="dialog-row"')
    assert "交互信号" not in page.text
    assert "八字专业回复" in page.text
    assert "/api/v20/measure/view/" in script.text
    assert "/api/v20/system/status" not in script.text
    assert "/api/v20/auth/me" in script.text
    assert "/api/v20/profiles/" in script.text
    assert "/api/v20/profiles/import-v19?apply=true" not in script.text
    assert "scheduleMeasure({ force: true })" in script.text
    assert "document.body.classList.toggle(\"profile-reading\", Boolean(params.get(\"profile_id\")))" in script.text
    assert "questions.slice(0, 8)" in script.text
    assert "const decisionReport = result.decision_report || {}" in script.text
    assert "const featureStateModel = result.feature_state_model || {}" in script.text
    assert "const structureDynamics = result.structure_dynamics || {}" in script.text
    assert "const mainlineArbitration = result.mainline_arbitration || {}" in script.text
    assert "const answerStrategy = result.answer_plan?.dimension_context?.answer_strategy || {}" in script.text
    assert "const questionIntentModel = result.question_intent_model || {}" in script.text
    assert "const interactionSession = result.interaction_session || {}" not in script.text
    assert "交互会话模型" not in script.text
    assert "renderInteractionSignals" not in script.text
    assert "renderFeatures(" in script.text
    assert "renderStructureDynamics(structureDynamics, mainlineArbitration)" in script.text
    assert "renderOrchestratorTrace(result.reasoning_orchestrator || {}, mainlineArbitration, result.redis_cache || {}, answerStrategy)" in script.text
    assert "redisCacheLabel" in script.text
    assert "qualityGateLabel" in script.text
    assert "practitionerReviewLabel" in script.text
    assert "answerStrategyLabel" in script.text
    assert "人工复核" in script.text
    assert "回答策略" in script.text
    assert "质量门复核" in script.text
    assert "确认第一主线" in script.text
    assert "arbitration.quality_gate" in script.text
    assert "orchestrator.primary_outputs" in script.text
    assert "arbitrationSummaryLine" in script.text
    assert "chainNodeLabel" in script.text
    assert "dynamicSummaryLine" in script.text
    assert "dynamicInterpretation" in script.text
    assert "命理解释" in script.text
    assert "日主承载需要复核" in script.text
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
    assert "control.mainline_arbitration" in Path(__file__).resolve().parents[1].joinpath("interaction/practitioner_calibration.py").read_text(encoding="utf-8")
    assert "renderLatentCalibration(result.input_id || \"\", role)" in script.text
    assert "renderObservationAccess(role)" in script.text
    assert "renderFeatureStateAccess(role)" in script.text
    assert "panel.hidden = role === \"user\"" in script.text
    assert "role === \"admin\"" in script.text
    assert "setPractitionerCollapsed" in script.text
    assert "/api/v20/learning/latent-event-calibration" in script.text
    assert "/api/v20/latent-event/calibration/record" in script.text
    assert "/api/v20/practitioner/calibration/record" in script.text
    assert "result.decision_validation || {}" in script.text
    assert "rule-candidate" not in script.text
    assert "规则候选验证" not in script.text
    assert "特征发现验证" not in script.text
    assert "chatButton.textContent = busy ? text.wb.generating : text.wb.send" in script.text
    assert "payload.llm_mode = llmMode" in script.text
    assert "const interactiveLlmMode = () => (params.get(\"llm\") === \"practitioner\" ? \"practitioner\" : \"deterministic\")" in script.text
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
    assert ".structure-dynamics-panel" in style.text
    assert ".dynamic-metric-grid" in style.text
    assert ".dynamic-interpretation" in style.text
    assert "payload.practitioner_selections = state.practitionerSelections" in script.text
    assert "payload.latent_event_answers = state.latentAnswers" in script.text
    assert "已记录 · 刷新问题" in script.text
    assert ".evidence-row.validation" in style.text
    assert ".latent-calibration-card" in style.text
    assert ".observation-page" in style.text
    assert ".observation-grid" in style.text
    assert ".observation-toggle" in style.text
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
    assert "DB / LLM" in admin.text
    assert "styles.css?v=20260505-glass" in admin.text
    assert "admin.js?v=20260509-route-state" in admin.text
    assert "new URLSearchParams(window.location.search)" not in admin_script.text
    assert "/v20/ui/qiazhi-logo-mark.png" in admin.text
    assert "brand-logo" in admin.text
    assert "/v20/ui/profiles.html" in admin.text
    assert "/api/v20/admin/db" in admin_script.text
    assert "/api/v20/admin/llm" in admin_script.text
    assert "/api/v20/auth/logout" in admin_script.text
    assert "Knowledge Evidence Store" not in admin.text
    assert "八字资料来源库" not in admin.text
    assert ".measure-layout" in style.text
    assert "body.profile-reading .control-panel" in style.text
    assert "body.profile-reading .feature-spine-panel" in style.text
    assert ".questions-panel-card" not in style.text
    assert "body.profile-reading .pillar-panel" in style.text
    assert "grid-template-columns: repeat(6, minmax(72px, 1fr))" in style.text
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
    assert style.status_code == 200
    assert entry_script.status_code == 200
    assert profiles_script.status_code == 200
    assert logo.status_code == 200
    assert favicon.status_code == 200
    assert logo.headers["content-type"] == "image/png"
