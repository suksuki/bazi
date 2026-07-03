from __future__ import annotations

from pathlib import Path

from v40.project import build_project_status


def test_phase74_mainline_plan_is_registered_as_current_phase() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE74_MAINLINE_COMPLETION_AND_NEXT_PLAN.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Mainline Completion Audit And Next Plan" in doc
    assert "QA-19: live LLM report/conversation acceptance on selected real cases" in doc
    assert "OPS-20: rollback rehearsal and beta traffic smoke" in doc
    assert "USER-21: owner approval for beta cutover window" in doc
    assert "DATA-22: V40 persistent runtime evidence" in doc
    assert "DEPTH-23: mingli depth regression" in doc
    assert "docs/V40_PHASE74_MAINLINE_COMPLETION_AND_NEXT_PLAN.md" in readme
    assert "Phase 74 Mainline Completion Audit And Next Plan" in spec
    assert status["current_phase"] == 74
    assert status["current_phase_name"] == "Mainline Completion Audit And Next Plan"
    assert status["overall_completion_percent"] == 99
    assert any(row["range"] == "73" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "74" and row["status"] == "active" for row in status["phase_groups"])
    assert status["next_mainline_tasks"] == [
        "QA-19: live LLM report/conversation acceptance on selected real cases",
        "OPS-20: rollback rehearsal and beta traffic smoke",
        "USER-21: owner approval for beta cutover window",
    ]
    assert "真实命例质量判断" in status["requires_user_for"]
