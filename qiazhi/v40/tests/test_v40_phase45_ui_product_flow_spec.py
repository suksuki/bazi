from __future__ import annotations

from pathlib import Path

from v40.project import build_project_status


def test_phase45_ui_product_flow_spec_is_mainline_document() -> None:
    doc = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")

    assert "Report-first reading" in doc
    assert "user-side product runtime contract" in doc
    assert "用户侧 UI" in doc
    assert "Probe Calibration Surface" in doc
    assert "ConsentGrant" in doc
    assert "Practitioner Lens" in doc
    assert "表达方式" in doc
    assert "Local / Gemma4" in doc
    assert "哪里不太像" in doc
    assert "Phase 1: Hide Engineering Status" in doc
    assert "Core judgment is visible within 5 seconds" in doc
    assert "训练闭环在后台安静发生" in doc
    assert "UI-1 Product Shell" in doc
    assert "docs/V40_UI_PRODUCT_FLOW_SPEC.md" in readme
    assert "2026-07-01 Phase 45" in spec
    assert "普通用户不暴露 provider/model/prompt/acceptance/policy/debug" in spec
    assert "产品运行合同" in spec


def test_phase45_project_status_points_to_ui_mainline() -> None:
    status = build_project_status()

    assert status["current_phase"] == 69
    assert status["current_phase_name"] == "Real Case Expansion And Cutover Evidence"
    assert any("UI product flow" in row["label"] for row in status["phase_groups"])
    assert any(row["range"] == "45" and row["status"] == "complete" for row in status["phase_groups"])
    assert "P69-1: real case expansion and online cutover evidence" in status["next_mainline_tasks"]
    user_beta = next(domain for domain in status["domains"] if domain["key"] == "user_beta")
    assert "真实命例" in user_beta["next_step"]
