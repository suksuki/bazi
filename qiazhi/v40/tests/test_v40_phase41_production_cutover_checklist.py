from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.project import build_production_cutover_checklist


def test_production_cutover_checklist_blocks_on_human_signoff_when_automatic_ready() -> None:
    checklist = build_production_cutover_checklist(
        replacement_readiness={"status": "candidate_ready"},
        weights=[
            {
                "weight_version_id": "weight.active",
                "active": True,
                "rollback_version_id": "weight.rollback",
            }
        ],
        llm_ready=True,
        repository_configured=True,
    )

    assert checklist["automatic_status"] == "ready"
    assert checklist["automatic_ready_percent"] == 100
    assert checklist["cutover_status"] == "blocked_by_human_signoff"
    assert "线上切换窗口" in checklist["manual_signoff_required"]
    assert checklist["boundary"] == "production_cutover_checklist_observes_readiness_without_switching_traffic"


def test_production_cutover_checklist_blocks_without_rollback() -> None:
    checklist = build_production_cutover_checklist(
        replacement_readiness={"status": "candidate_ready"},
        weights=[{"weight_version_id": "weight.active", "active": True, "rollback_version_id": ""}],
        llm_ready=True,
        repository_configured=True,
    )

    rollback = next(check for check in checklist["checks"] if check["key"] == "rollback_available")
    assert checklist["automatic_status"] == "blocked"
    assert checklist["cutover_status"] == "blocked_by_automatic_checks"
    assert rollback["ready"] is False


def test_production_cutover_checklist_api_is_readonly() -> None:
    response = TestClient(create_app()).get(f"{API_PREFIX}/project/production-cutover-checklist")

    assert response.status_code == 200
    body = response.json()
    assert body["checklist"]["version"] == "v40.production_cutover_checklist.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "production_cutover_checklist_reads_v40_evidence_without_switching_traffic"


def test_phase41_project_status_advances_cutover_track() -> None:
    status = TestClient(create_app()).get(f"{API_PREFIX}/project/status").json()["status"]

    assert status["current_phase"] >= 41
    assert status["overall_completion_percent"] >= 84
    assert status["next_mainline_tasks"][0].startswith("P66-")
