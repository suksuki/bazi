from __future__ import annotations

from pathlib import Path

from v40.project import build_project_status


def test_phase59_ui_product_convergence_plan_is_documented() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE59_UI_PRODUCT_CONVERGENCE_PLAN.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")

    assert "engineering workbench to mingli reading product" in doc
    assert "Layer 1: Reading Setup" in doc
    assert "Layer 2: Reading Result" in doc
    assert "Layer 3: Follow-up And Conversation" in doc
    assert "Layer 4: Calibration And Practitioner Lens" in doc
    assert "P0: De-Engineering" in doc
    assert "P1: Reading Setup First Screen" in doc
    assert "P2: Report-First Layout" in doc
    assert "P3: Follow-Up And Conversation Layering" in doc
    assert "Practitioner is a role-based lens" in doc
    assert "same Reading" in doc
    assert "ContextualPractitionerLensDrawer" in ui_spec
    assert "docs/V40_PHASE59_UI_PRODUCT_CONVERGENCE_PLAN.md" in readme
    assert "2026-07-02 Phase 59 UI 收敛 runtime 已启动" in spec
    assert "same Reading + RoleProjection + Contextual Practitioner Lens" in spec
    assert "Reading Setup" in ui_spec
    assert "Account/profile management" in ui_spec


def test_phase59_ui_product_convergence_is_next_mainline_task() -> None:
    status = build_project_status()

    assert status["current_phase"] == 67
    assert status["current_phase_name"] == "Hidden Factor Probe Engine"
    assert any(row["range"] == "59" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "60" and row["status"] == "complete" for row in status["phase_groups"])
    assert "P67-1: Hidden Factor Probe Engine" in status["next_mainline_tasks"]
