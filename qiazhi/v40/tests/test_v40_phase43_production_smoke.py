from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.project import build_production_smoke


def test_production_smoke_passes_when_all_readiness_layers_pass() -> None:
    smoke = build_production_smoke(
        project_status={"current_phase": 43},
        surface_readiness={"beta_status": "ready"},
        replacement_readiness={"status": "candidate_ready"},
        cutover_checklist={"automatic_status": "ready"},
        release_candidate_audit={"audit_status": "automatic_audit_passed_human_signoff_required"},
    )

    assert smoke["smoke_percent"] == 100
    assert smoke["smoke_status"] == "passed_handoff_ready"
    assert "自动烟测不等于上线。" in smoke["handoff_notes"]
    assert smoke["boundary"] == "production_smoke_observes_v40_readiness_without_switching_traffic"


def test_production_smoke_api_is_readonly() -> None:
    response = TestClient(create_app()).get(f"{API_PREFIX}/project/production-smoke")

    assert response.status_code == 200
    body = response.json()
    assert body["smoke"]["version"] == "v40.production_smoke.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "production_smoke_reads_v40_readiness_without_switching_traffic"


def test_phase43_project_status_advances_smoke_track() -> None:
    status = TestClient(create_app()).get(f"{API_PREFIX}/project/status").json()["status"]

    assert status["current_phase"] >= 43
    assert status["overall_completion_percent"] >= 95
    assert status["next_mainline_tasks"][0].startswith("UI-17")
