from __future__ import annotations

from fastapi.testclient import TestClient

from v20.server import app


def test_v20_ui_static_shell_is_served_from_v20_directory() -> None:
    client = TestClient(app)

    page = client.get("/v20/ui/")
    script = client.get("/v20/ui/app.js")
    style = client.get("/v20/ui/styles.css")

    assert page.status_code == 200
    assert "V20 命理测算台" in page.text
    assert "flow_year_pillar" in page.text
    assert "role_key" in page.text
    assert '<option value="user">用户</option>' in page.text
    assert "反馈学习" in page.text
    assert "同步边界" in page.text
    assert "知识库" in page.text
    assert "measurement_report" in script.text
    assert "/api/v20/measure/view/" in script.text
    assert "/api/v20/ops/sync-readiness" in script.text
    assert "/api/v20/knowledge/catalog" in script.text
    assert "/api/v20/knowledge/coverage-report" in script.text
    assert "/api/v20/knowledge/release-manifest" in script.text
    assert "/api/v20/knowledge/v19-migration-audit" in script.text
    assert "/api/v20/knowledge/draft-import-preview" in script.text
    assert "/api/v20/knowledge/review-queue" in script.text
    assert "/api/v20/knowledge/first-wave-review-packets" in script.text
    assert "/api/v20/learning/run-plan" in script.text
    assert "full_runtime" not in script.text
    assert "/api/v20/feedback/record" in script.text
    assert "/api/v20/learning/policy-review" in script.text
    assert ".workspace" in style.text
    assert script.status_code == 200
    assert style.status_code == 200
