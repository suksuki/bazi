from __future__ import annotations

from pathlib import Path

from v40.project import build_project_status


def test_phase45_ui_product_flow_spec_is_mainline_document() -> None:
    doc = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")

    assert "Report-first reading" in doc
    assert "Probe Calibration Surface" in doc
    assert "ConsentGrant" in doc
    assert "Practitioner Lens" in doc
    assert "UI-1 Product Shell" in doc
    assert "docs/V40_UI_PRODUCT_FLOW_SPEC.md" in readme
    assert "2026-07-01 Phase 45" in spec
    assert "普通用户不暴露 provider/model/prompt/acceptance/policy/debug" in spec


def test_phase45_project_status_points_to_ui_mainline() -> None:
    status = build_project_status()

    assert status["current_phase"] == 45
    assert status["current_phase_name"] == "UI Product Flow And Human-Machine Training IA"
    assert any("UI product flow" in row["label"] for row in status["phase_groups"])
    assert "UI-1: final warm-light product shell" in status["next_mainline_tasks"]
    assert "UI-5: Practitioner Lens drawer" in status["next_mainline_tasks"]
    user_beta = next(domain for domain in status["domains"] if domain["key"] == "user_beta")
    assert "V40_UI_PRODUCT_FLOW_SPEC" in user_beta["next_step"]
