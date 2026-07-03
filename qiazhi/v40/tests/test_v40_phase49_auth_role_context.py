from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_session_context_defaults_to_user_and_maps_admin_to_practitioner() -> None:
    client = TestClient(create_app())

    default_response = client.get(f"{API_PREFIX}/session/context")
    practitioner_response = client.get(f"{API_PREFIX}/session/context", headers={"x-v40-user-role": "practitioner"})
    admin_response = client.get(f"{API_PREFIX}/session/context", headers={"x-v40-user-role": "admin"})

    assert default_response.status_code == 200
    assert default_response.json()["session"]["role_key"] == "user"
    assert default_response.json()["session"]["admin_control_plane_separated"] is True

    assert practitioner_response.status_code == 200
    assert practitioner_response.json()["session"]["role_key"] == "practitioner"
    assert practitioner_response.json()["session"]["role_context"]["can_submit_calibration"] is True

    assert admin_response.status_code == 200
    admin_session = admin_response.json()["session"]
    assert admin_session["role_key"] == "practitioner"
    assert admin_session["admin_mapped_to_practitioner"] is True
    assert admin_session["role_context"]["can_view_debug"] is False


def test_native_report_uses_session_role_context_for_practitioner_surface() -> None:
    client = TestClient(create_app())
    seed = load_synthetic_seeds(SEED_PATH)[0]

    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        headers={"x-v40-user-role": "practitioner"},
        json={
            "request_id": "request.phase49.role.001",
            "reading_id": "reading.phase49.role.001",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "execution_mode": "local",
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session"]["role_key"] == "practitioner"
    assert body["runtime"]["request"]["role_key"] == "practitioner"
    assert body["runtime"]["request"]["runtime_context"]["role_context"]["can_submit_calibration"] is True
    lens = body["runtime"]["surface_bundle"]["surfaces"]["calibration"]["practitioner_lens"]
    assert lens["available"] is True


def test_user_app_runtime_maps_payload_admin_to_practitioner_not_admin_control() -> None:
    client = TestClient(create_app())
    seed = load_synthetic_seeds(SEED_PATH)[0]

    response = client.post(
        f"{API_PREFIX}/runtime/native-bazi",
        json={
            "request_id": "request.phase49.admin.payload",
            "reading_id": "reading.phase49.admin.payload",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "role_key": "admin",
            "persist": False,
        },
    )

    assert response.status_code == 200
    runtime = response.json()["runtime"]
    assert runtime["request"]["role_key"] == "practitioner"
    role_context = runtime["request"]["runtime_context"]["role_context"]
    assert role_context["can_submit_calibration"] is True
    assert role_context["can_view_debug"] is False


def test_user_ui_uses_session_context_instead_of_url_role_hook() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    assert "/api/v40/session/context" in html
    assert "applySessionContext" in html
    assert "URLSearchParams" not in html
    assert "window.location.search" not in html
    assert "role=practitioner" not in html
    assert "role_key" not in html
    assert "role_context" not in html
    assert "/admin/v40" not in html


def test_phase49_docs_and_project_status_track_auth_role_context() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE49_AUTH_DERIVED_ROLE_CONTEXT.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Auth-Derived User Role Context" in doc
    assert "UserAppSessionContext" in doc
    assert "GET /api/v40/session/context" in doc
    assert "2026-07-01 Phase 49" in spec
    assert "docs/V40_PHASE49_AUTH_DERIVED_ROLE_CONTEXT.md" in readme
    assert status["current_phase"] == 73
    assert status["current_phase_name"] == "Real Case Acceptance Pack"
    assert any(row["range"] == "48" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "49" and row["status"] == "complete" for row in status["phase_groups"])
