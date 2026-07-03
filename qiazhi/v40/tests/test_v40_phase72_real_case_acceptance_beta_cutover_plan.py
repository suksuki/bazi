from __future__ import annotations

from pathlib import Path

from v40.project import build_project_status


def test_phase72_docs_and_project_status_track_real_case_acceptance_cutover_plan() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE72_REAL_CASE_ACCEPTANCE_AND_BETA_CUTOVER_PLAN.md").read_text(
        encoding="utf-8"
    )
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Real Case Acceptance And Beta Cutover Plan" in doc
    assert "USER-18: real case quality signoff and beta cutover window" in doc
    assert "QA-19: live LLM report/conversation acceptance on selected real cases" in doc
    assert "OPS-20: rollback rehearsal and beta traffic smoke" in doc
    assert "docs/V40_PHASE72_REAL_CASE_ACCEPTANCE_AND_BETA_CUTOVER_PLAN.md" in readme
    assert "Phase 72 Real Case Acceptance And Beta Cutover Plan" in spec
    assert status["current_phase"] == 72
    assert status["current_phase_name"] == "Real Case Acceptance And Beta Cutover Plan"
    assert status["overall_completion_percent"] == 99
    assert any(row["range"] == "71" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "72" and row["status"] == "active" for row in status["phase_groups"])
    assert status["next_mainline_tasks"] == [
        "USER-18: real case quality signoff and beta cutover window",
        "QA-19: live LLM report/conversation acceptance on selected real cases",
        "OPS-20: rollback rehearsal and beta traffic smoke",
    ]
    assert "真实命例质量判断" in status["requires_user_for"]
