from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.project import build_release_candidate_audit


def test_release_candidate_audit_passes_automatic_checks_but_requires_human_signoff() -> None:
    audit = build_release_candidate_audit(
        project_status={"overall_completion_percent": 90},
        surface_readiness={"beta_status": "ready"},
        replacement_readiness={"status": "candidate_ready"},
        cutover_checklist={"automatic_status": "ready", "cutover_status": "blocked_by_human_signoff"},
    )

    assert audit["automated_audit_percent"] == 100
    assert audit["audit_status"] == "automatic_audit_passed_human_signoff_required"
    assert "真实命例质量判断" in audit["human_signoff_required"]
    assert audit["boundary"] == "release_candidate_audit_observes_all_readiness_without_releasing_traffic"


def test_release_candidate_audit_blocks_when_cutover_checks_are_not_ready() -> None:
    audit = build_release_candidate_audit(
        project_status={"overall_completion_percent": 90},
        surface_readiness={"beta_status": "ready"},
        replacement_readiness={"status": "candidate_ready"},
        cutover_checklist={"automatic_status": "blocked", "cutover_status": "blocked_by_automatic_checks"},
    )

    cutover = next(check for check in audit["checks"] if check["key"] == "cutover_automatic_checks_ready")
    assert audit["audit_status"] == "needs_automatic_fix"
    assert cutover["passed"] is False


def test_release_candidate_audit_api_is_readonly() -> None:
    response = TestClient(create_app()).get(f"{API_PREFIX}/project/release-candidate-audit")

    assert response.status_code == 200
    body = response.json()
    assert body["audit"]["version"] == "v40.release_candidate_audit.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "release_candidate_audit_reads_v40_readiness_without_releasing_traffic"


def test_phase42_project_status_advances_rc_audit_track() -> None:
    status = TestClient(create_app()).get(f"{API_PREFIX}/project/status").json()["status"]

    assert status["current_phase"] >= 42
    assert status["overall_completion_percent"] >= 90
    assert status["next_mainline_tasks"][0].startswith("QA-19")
