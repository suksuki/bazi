from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.project import build_online_cutover_decision_pack, build_project_status


def _ready_payload() -> dict[str, object]:
    return {
        "project_status": {"overall_completion_percent": 99},
        "cutover_checklist": {"automatic_status": "ready"},
        "real_case_evidence": {"automatic_status": "ready"},
        "training_activation_evidence": {"automatic_status": "ready", "rollback_ready": True},
        "release_candidate_audit": {"audit_status": "automatic_audit_passed_human_signoff_required"},
    }


def test_phase71_online_cutover_decision_ready_still_requires_human_signoff() -> None:
    decision = build_online_cutover_decision_pack(**_ready_payload())

    assert decision["decision_status"] == "ready_for_human_signoff"
    assert decision["decision_percent"] == 100
    assert decision["passed_check_count"] == decision["check_count"]
    assert decision["traffic_switch_allowed_by_system"] is False
    assert decision["user_acceptance_required"] is True
    assert decision["writes_v30_state"] is False
    assert decision["writes_v40_production"] is False
    assert "线上切换窗口" in decision["manual_signoff_required"]


def test_phase71_online_cutover_decision_surfaces_blockers_without_cutover() -> None:
    payload = _ready_payload()
    payload["real_case_evidence"] = {"automatic_status": "blocked"}

    decision = build_online_cutover_decision_pack(**payload)

    assert decision["decision_status"] == "near_ready_with_blockers"
    assert decision["decision_percent"] == 80
    assert decision["traffic_switch_allowed_by_system"] is False
    assert decision["user_acceptance_required"] is False
    assert decision["blockers"][0]["key"] == "real_case_evidence_ready"
    assert decision["next_actions"] == ["补齐真实命例数量、主题覆盖和 Acceptance Window。"]


def test_phase71_online_cutover_decision_api_is_readonly() -> None:
    response = TestClient(create_app()).post(
        f"{API_PREFIX}/project/online-cutover-decision",
        json=_ready_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v40.online_cutover_decision_response.v1"
    assert body["decision"]["decision_status"] == "ready_for_human_signoff"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "online_cutover_decision_reads_evidence_without_switching_traffic"


def test_phase71_docs_and_project_status_track_online_cutover_decision() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE71_ONLINE_CUTOVER_DECISION_PACK.md").read_text(
        encoding="utf-8"
    )
    review_doc = Path("qiazhi/v40/docs/V40_PHASE71_SYSTEM_REVIEW_AND_MAINLINE_SYNC.md").read_text(
        encoding="utf-8"
    )
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Online Cutover Decision Pack" in doc
    assert "System Review And Mainline Sync" in review_doc
    assert "POST /api/v40/project/online-cutover-decision" in doc
    assert "build_online_cutover_decision_pack" in spec
    assert "docs/V40_PHASE71_ONLINE_CUTOVER_DECISION_PACK.md" in readme
    assert "docs/V40_PHASE71_SYSTEM_REVIEW_AND_MAINLINE_SYNC.md" in readme
    assert status["current_phase"] == 73
    assert status["current_phase_name"] == "Real Case Acceptance Pack"
    assert any(row["range"] == "70" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "71" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "72" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "73" and row["status"] == "active" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "QA-19: live LLM report/conversation acceptance on selected real cases"
