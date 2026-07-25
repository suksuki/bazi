from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from product.app import create_product_app
from product.product_store import MemoryProductStore
from tests.test_v50_mingli_agent_refoundation import _birth_payload


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "apps/product/experience_shell/src"
LEGACY_STATIC = ROOT / "apps/product/static/l5"


def _registered_client() -> TestClient:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    response = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "Flow Slim User",
            "email": "flow-slim-02@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert response.status_code == 200, response.text
    return client


def test_experience_owns_auth_and_profile_management_without_l5_bundle() -> None:
    account = (SHELL / "account_components.ts").read_text(encoding="utf-8")
    api = (SHELL / "api.ts").read_text(encoding="utf-8")
    main = (SHELL / "main.ts").read_text(encoding="utf-8")

    assert not (LEGACY_STATIC / "index.html").exists()
    assert not (LEGACY_STATIC / "app.js").exists()
    assert not (LEGACY_STATIC / "styles.css").exists()
    assert "/api/v50/product/auth/${input.mode}" in api
    assert "/api/v50/product/profiles" in api
    assert "renderProfileManager" in main
    assert "选择档案，就是进入命局" in account
    assert "/app" not in account + main


def test_app_is_compatibility_redirect_and_old_bundle_routes_are_gone() -> None:
    client = TestClient(create_product_app(product_store=MemoryProductStore()))

    plain = client.get("/app", follow_redirects=False)
    managed = client.get("/app?manage=1", follow_redirects=False)
    selected = client.get("/app?profile=profile-42", follow_redirects=False)

    assert plain.status_code == managed.status_code == selected.status_code == 308
    assert plain.headers["location"] == "/experience"
    assert managed.headers["location"] == "/experience?manage=1"
    assert selected.headers["location"] == "/experience?profile=profile-42"
    assert client.get("/app.js").status_code == 404
    assert client.get("/styles.css").status_code == 404


def test_profile_save_flows_directly_into_one_deterministic_workspace_bootstrap() -> None:
    client = _registered_client()
    before = client.post(
        "/api/v50/experience/workspace/bootstrap",
        json={"profile_id": "", "case_id": ""},
    )
    assert before.status_code == 200, before.text
    assert before.json()["status"] == "workspace_profile_required"

    created = client.post(
        "/api/v50/product/profiles",
        json={"birth_input": _birth_payload()},
    )
    assert created.status_code == 200, created.text
    profile_id = created.json()["profile"]["profile_id"]

    entered = client.post(
        "/api/v50/experience/workspace/bootstrap",
        json={"profile_id": profile_id, "case_id": ""},
    )
    assert entered.status_code == 200, entered.text
    payload = entered.json()
    assert payload["status"] == "workspace_bootstrap_ready"
    assert payload["selected_profile_id"] == profile_id
    assert payload["request_budget"] == {
        "api_requests": 1,
        "llm_calls": 0,
        "tts_calls": 0,
        "domain_generations": 0,
    }
    assert payload["legacy_report_used"] is False
    assert len(payload["envelope"]["allowed_chart_facts"]) == 4


def test_profile_edit_and_delete_use_the_existing_product_owner() -> None:
    client = _registered_client()
    created = client.post(
        "/api/v50/product/profiles",
        json={"birth_input": _birth_payload()},
    ).json()["profile"]
    updated_birth = {**_birth_payload(), "name": "Updated Profile", "birth_time": "19:00"}

    updated = client.put(
        f"/api/v50/product/profiles/{created['profile_id']}",
        json={"birth_input": updated_birth},
    )
    deleted = client.delete(f"/api/v50/product/profiles/{created['profile_id']}")
    remaining = client.get("/api/v50/product/profiles")

    assert updated.status_code == 200, updated.text
    assert updated.json()["profile"]["display_name"] == "Updated Profile"
    assert deleted.status_code == 200, deleted.text
    assert remaining.json()["profiles"] == []
