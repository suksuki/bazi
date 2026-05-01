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
    assert "guestStart" in entry.text
    assert "loginButton" in entry.text
    assert "registerButton" in entry.text
    assert "/api/v20/auth/guest" in entry_script.text
    assert "/api/v20/auth/login" in entry_script.text
    assert "/api/v20/auth/register" in entry_script.text
    assert "/v20/ui/profiles.html" in entry.text
    assert "goProfiles" in entry_script.text
    assert profiles.status_code == 200
    assert "V20 八字档案管理" in profiles.text
    assert "profileList" in profiles.text
    assert "importProfilesButton" in profiles.text
    assert "/api/v20/profiles?owner_id=admin" in profiles_script.text
    assert "/api/v20/profiles/import-v19?apply=true&owner_id=admin" in profiles_script.text
    assert "appendProfileDefaults(query, profile)" in profiles_script.text
    assert "flow_year_pillar" in profiles_script.text
    assert page.status_code == 200
    assert "V20 命理测算台" in page.text
    assert "flow_year_pillar" in page.text
    assert "role_key" in page.text
    assert '<option value="analyst" selected>命理师</option>' in page.text
    assert '<option value="user">游客</option>' in page.text
    assert '<option value="admin">' not in page.text
    assert '<option value="full">' not in page.text
    assert "selectedProfileCard" in page.text
    assert "chatText" in page.text
    assert "chatButton" in page.text
    assert "chatQuestionList" in page.text
    assert "chatTranscript" in page.text
    assert "portrait-summary" in page.text
    assert "profileImportButton" not in page.text
    assert "反馈校准" in page.text
    assert "命理特征主线" in page.text
    assert "画像投影" in page.text
    assert "八字专业回复" in page.text
    assert "/api/v20/measure/view/" in script.text
    assert "/api/v20/system/status" in script.text
    assert "/api/v20/runtime/dependencies" in script.text
    assert "/api/v20/profiles/" in script.text
    assert "/api/v20/profiles/import-v19?apply=true" not in script.text
    assert "scheduleMeasure({ force: true })" in script.text
    assert "document.body.classList.toggle(\"profile-reading\", Boolean(params.get(\"profile_id\")))" in script.text
    assert "questions.slice(0, 5)" in script.text
    assert "renderChatQuestions(result.questions || [], selected.question_key || \"\")" in script.text
    assert "const discovery = result.feature_discovery || {}" in script.text
    assert "renderFeatures(discovery.ranked_features || featureLayer.macro_features || featureLayer.features || [])" in script.text
    assert "result.feature_discovery_validation || {}" in script.text
    assert "rule-candidate" in script.text
    assert "规则候选验证" in script.text
    assert "特征发现验证" in script.text
    assert "chatButton.textContent = busy ? (llmMode === \"rewrite\" ? \"生成中\" : \"测算中\") : \"发送\"" in script.text
    assert "payload.llm_mode = llmMode" in script.text
    assert "llmMode: \"rewrite\"" in script.text
    assert "appendChatTurn(interactionText" in script.text
    assert ".chat-transcript" in style.text
    assert ".evidence-row.rule-candidate" in style.text
    assert ".evidence-row.validation" in style.text
    assert "applyProfileDefaults(profile)" in script.text
    assert "role: measurementRole(params.get(\"role\") || document.body.dataset.role)" in profiles_script.text
    assert "const endpoint = `/api/v20/measure/view/${role}`" in script.text
    assert "确认四柱后会生成建议问题" in script.text
    assert "명리사" in script.text
    assert "full_runtime" not in script.text
    assert "/api/v20/feedback/record" in script.text
    assert "DB / LLM" in admin.text
    assert "/v20/ui/profiles.html" in admin.text
    assert "/api/v20/admin/db" in admin_script.text
    assert "/api/v20/admin/llm" in admin_script.text
    assert "Knowledge Evidence Store" not in admin.text
    assert "八字资料来源库" not in admin.text
    assert ".measure-layout" in style.text
    assert "body.profile-reading .control-panel" in style.text
    assert "body.profile-reading .feature-spine-panel" in style.text
    assert "body.profile-reading .questions-panel-card" in style.text
    assert "body.profile-reading .chat-question-list" in style.text
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
