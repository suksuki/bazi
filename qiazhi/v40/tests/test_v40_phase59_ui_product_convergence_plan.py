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
    assert "docs/V40_PHASE59_UI_PRODUCT_CONVERGENCE_PLAN.md" in readme
    assert "2026-07-02 Phase 59 UI 收敛计划已纳入主线" in spec
    assert "Reading Setup" in ui_spec
    assert "Account/profile management" in ui_spec


def test_phase59_ui_product_convergence_is_next_mainline_task() -> None:
    status = build_project_status()

    assert status["current_phase"] == 58
    assert status["current_phase_name"] == "Hard LLM And Direct Training Principles"
    assert "UI-18: Phase 59 productized reading setup and report-first convergence" in status["next_mainline_tasks"]

