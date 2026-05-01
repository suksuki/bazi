from __future__ import annotations

from fastapi.testclient import TestClient

from v20.server import app


def test_v20_ui_static_shell_is_served_from_v20_directory() -> None:
    client = TestClient(app)

    entry = client.get("/v20/ui/")
    entry_script = client.get("/v20/ui/entry.js")
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
    assert page.status_code == 200
    assert "V20 命理测算台" in page.text
    assert "flow_year_pillar" in page.text
    assert "role_key" in page.text
    assert '<option value="analyst" selected>命理师</option>' in page.text
    assert '<option value="user">游客</option>' in page.text
    assert "用户档案" in page.text
    assert "profileImportButton" in page.text
    assert "反馈校准" in page.text
    assert "命理特征主线" in page.text
    assert "画像投影" in page.text
    assert "八字专业回复" in page.text
    assert "/api/v20/measure/view/" in script.text
    assert "/api/v20/system/status" in script.text
    assert "/api/v20/runtime/dependencies" in script.text
    assert "/api/v20/profiles/v19-migration-preview" in script.text
    assert "/api/v20/profiles/import-v19?apply=true" in script.text
    assert "명리사" in script.text
    assert "full_runtime" not in script.text
    assert "/api/v20/feedback/record" in script.text
    assert "DB / LLM" in admin.text
    assert "/api/v20/admin/db" in admin_script.text
    assert "/api/v20/admin/llm" in admin_script.text
    assert "Knowledge Evidence Store" not in admin.text
    assert "八字资料来源库" not in admin.text
    assert ".measure-layout" in style.text
    assert ".entry-page" in style.text
    assert ".admin-layout" in style.text
    assert "@media (max-width: 1120px)" in style.text
    assert "@media (max-width: 760px)" in style.text
    assert script.status_code == 200
    assert admin.status_code == 200
    assert admin_script.status_code == 200
    assert style.status_code == 200
    assert entry_script.status_code == 200
