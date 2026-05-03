from __future__ import annotations

from fastapi.testclient import TestClient

from v20.server import app


def test_v20_ui_static_shell_is_served_from_v20_directory() -> None:
    client = TestClient(app)

    entry = client.get("/v20/ui/")
    entry_script = client.get("/v20/ui/entry.js")
    profiles = client.get("/v20/ui/profiles.html")
    profiles_script = client.get("/v20/ui/profiles.js")
    page = client.get("/v20/ui/workbench.html")
    script = client.get("/v20/ui/app.js")
    admin = client.get("/v20/ui/admin.html")
    admin_script = client.get("/v20/ui/admin.js")
    style = client.get("/v20/ui/styles.css")

    assert entry.status_code == 200
    assert "进入掐指一算" in entry.text
    assert "Admin 入口" not in entry.text
    assert "DB / LLM" not in entry.text
    assert "id=\"loginRole\"" not in entry.text
    assert "id=\"registerRole\"" in entry.text
    assert "id=\"registerName\"" in entry.text
    assert "id=\"registerPassword\"" in entry.text
    assert '<option value="user" data-entry-option="role_user">普通用户</option>' in entry.text
    assert "data-entry-option=\"role_guest\"" not in entry.text
    assert '<option value="admin">Admin</option>' not in entry.text
    assert "logoutButton" in entry.text
    assert "guestStart" in entry.text
    assert "loginButton" in entry.text
    assert "registerButton" in entry.text
    assert "/api/v20/auth/guest" in entry_script.text
    assert "/api/v20/auth/login" in entry_script.text
    assert "/api/v20/auth/register" in entry_script.text
    assert "/v20/ui/profiles.html" not in entry.text
    assert "goProfiles" in entry_script.text
    assert "document.querySelector(\"#registerRole\").value" in entry_script.text
    assert "document.querySelector(\"#registerName\").value" in entry_script.text
    assert "document.querySelector(\"#registerPassword\").value" in entry_script.text
    assert "document.querySelector(\"#loginRole\")" not in entry_script.text
    assert "/api/v20/auth/logout" in entry_script.text
    assert profiles.status_code == 200
    assert "V20 八字档案管理" in profiles.text
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
    assert "/api/v20/profiles?limit=120" in profiles_script.text
    assert "/api/v20/profiles/import-v19?apply=true" not in profiles_script.text
    assert "method: profileId ? \"PATCH\" : \"POST\"" in profiles_script.text
    assert "method: \"DELETE\"" in profiles_script.text
    assert "appendProfileDefaults(query, profile)" in profiles_script.text
    assert "flow_year_pillar" in profiles_script.text
    assert page.status_code == 200
    assert "V20 命理测算台" in page.text
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
    assert "chatText" in page.text
    assert "chatButton" in page.text
    assert "chatQuestionList" not in page.text
    assert "chatTranscript" in page.text
    assert "interactionSignals" not in page.text
    assert "practitionerCalibration" in page.text
    assert "calibrationControls" in page.text
    assert "latentCalibration" in page.text
    assert "latentCalibrationControls" in page.text
    assert "observationPage" in page.text
    assert "observationToggle" in page.text
    assert "observationBody" in page.text
    assert 'id="featureStatePanel" class="panel feature-spine-panel" hidden' in page.text
    assert "图谱画像总览" in page.text
    assert "Decision Hits" in page.text
    assert "practitionerToggle" in page.text
    assert "profileImportButton" not in page.text
    assert "反馈校准" not in page.text
    assert "八字特征状态" in page.text
    assert "主题投射画像" in page.text
    assert "智能问题" in page.text
    assert "交互信号" not in page.text
    assert "八字专业回复" in page.text
    assert "/api/v20/measure/view/" in script.text
    assert "/api/v20/system/status" not in script.text
    assert "/api/v20/runtime/dependencies" in script.text
    assert "/api/v20/profiles/" in script.text
    assert "/api/v20/profiles/import-v19?apply=true" not in script.text
    assert "scheduleMeasure({ force: true })" in script.text
    assert "document.body.classList.toggle(\"profile-reading\", Boolean(params.get(\"profile_id\")))" in script.text
    assert "questions.slice(0, 8)" in script.text
    assert "const decisionReport = result.decision_report || {}" in script.text
    assert "const featureStateModel = result.feature_state_model || {}" in script.text
    assert "const questionIntentModel = result.question_intent_model || {}" in script.text
    assert "const interactionSession = result.interaction_session || {}" not in script.text
    assert "交互会话模型" not in script.text
    assert "renderInteractionSignals" not in script.text
    assert "renderFeatures(" in script.text
    assert "featureStateModel.priority_features" in script.text
    assert "renderPortrait(portraitProjection.axes || [])" in script.text
    assert "renderPractitionerCalibration(decisionReport.practitioner_controls || []" in script.text
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
    assert "interactiveLlmMode" in script.text
    assert "assist.practitioner_answer" in script.text
    assert "appendChatTurn(interactionText" in script.text
    assert ".chat-transcript" in style.text
    assert ".calibration-panel-card" in style.text
    assert ".axis-temp" in style.text
    assert ".signal-row" not in style.text
    assert ".answer-question-strip" in style.text
    assert "payload.practitioner_selections = state.practitionerSelections" in script.text
    assert "payload.latent_event_answers = state.latentAnswers" in script.text
    assert "已记录 · 刷新问题" in script.text
    assert ".evidence-row.validation" in style.text
    assert ".latent-calibration-card" in style.text
    assert ".observation-page" in style.text
    assert ".observation-grid" in style.text
    assert ".observation-toggle" in style.text
    assert ".collapse-toggle" in style.text
    assert "applyProfileDefaults(profile)" in script.text
    assert "role: measurementRole(params.get(\"role\") || document.body.dataset.role)" in profiles_script.text
    assert "const endpoint = `/api/v20/measure/view/${role}`" in script.text
    assert "确认四柱后会生成建议问题" in script.text
    assert "명리사" in script.text
    assert "full_runtime" not in script.text
    assert "/api/v20/feedback/record" not in script.text
    assert "DB / LLM" in admin.text
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
    assert ".profiles-layout" in style.text
    assert ".entry-page" in style.text
    assert ".admin-layout" in style.text
    assert "@media (max-width: 1120px)" in style.text
    assert "@media (max-width: 760px)" in style.text
    assert script.status_code == 200
    assert admin.status_code == 200
    assert admin_script.status_code == 200
    assert style.status_code == 200
    assert entry_script.status_code == 200
    assert profiles_script.status_code == 200
