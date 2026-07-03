from __future__ import annotations

from fastapi.testclient import TestClient

from v30.api.admin_frontend_app import create_admin_frontend_app


def test_admin_frontend_serves_standalone_console() -> None:
    client = TestClient(create_admin_frontend_app())

    response = client.get("/admin")
    html = response.text

    assert response.status_code == 200
    assert "掐指一算 · Admin Control Plane" in html
    assert "window.QIAZHI_ADMIN_STANDALONE = true" in html
    assert "/admin/assets/app.js" in html
    assert "/v30/ui/?surface=admin" not in html


def test_admin_frontend_health_declares_proxy_boundary() -> None:
    client = TestClient(create_admin_frontend_app())

    payload = client.get("/health").json()

    assert payload["ok"] is True
    assert payload["service"] == "qiazhi-v30-admin-frontend"
    assert payload["port"] == 9031
    assert payload["runtime_api_base_url"] == "http://127.0.0.1:9030"
    assert payload["runtime_proxy"] == ["/api/v30/*", "/api/admin/v30/*"]


def test_admin_frontend_app_supports_standalone_admin_flag() -> None:
    source = open("admin_frontend/app.js", encoding="utf-8").read()

    assert "window.QIAZHI_ADMIN_STANDALONE === true" in source


def test_main_frontend_has_no_admin_surface_code() -> None:
    app_source = open("frontend/app.js", encoding="utf-8").read()
    index_source = open("frontend/index.html", encoding="utf-8").read()
    style_source = open("frontend/styles.css", encoding="utf-8").read()

    combined = "\n".join([app_source, index_source, style_source])
    forbidden = ["admin", "Admin", "管理台", "后台", "data-admin", "surface=admin", "role=admin"]
    assert not [token for token in forbidden if token in combined]
