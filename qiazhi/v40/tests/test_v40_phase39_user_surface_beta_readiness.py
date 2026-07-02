from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app


def test_user_surface_beta_readiness_reports_all_required_surface_checks() -> None:
    client = TestClient(create_app())

    response = client.get(f"{API_PREFIX}/surface/beta-readiness")

    assert response.status_code == 200
    body = response.json()
    readiness = body["readiness"]
    keys = {check["key"] for check in readiness["checks"]}
    assert readiness["beta_ready_percent"] == 100
    assert readiness["beta_status"] == "ready"
    assert keys == {
        "report_first",
        "conversation_after_report",
        "feedback_to_training",
        "practitioner_calibration",
        "admin_separated",
        "no_local_fallback_when_llm_required",
    }
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False


def test_user_surface_consumes_beta_readiness_without_exposing_control_plane_language() -> None:
    client = TestClient(create_app())

    response = client.get("/v40/ui")

    assert response.status_code == 200
    assert "/api/v40/surface/beta-readiness" not in response.text
    assert "报告优先 · 自然追问 · 轻量校准" in response.text
    assert "判断与建议" in response.text
    assert "查看完整报告" in response.text
    assert "production weight" not in response.text
    assert "/admin/v40" not in response.text


def test_phase39_project_status_advances_user_beta_track() -> None:
    body = TestClient(create_app()).get(f"{API_PREFIX}/project/status").json()
    status = body["status"]
    user_beta = next(domain for domain in status["domains"] if domain["key"] == "user_beta")

    assert status["current_phase"] >= 39
    assert user_beta["completion_percent"] >= 68
    assert status["overall_completion_percent"] >= 75
