from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.project import build_project_status


def test_phase61_ui_flow_clean_rebuild_is_documented() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE61_UI_FLOW_CLEAN_REBUILD.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")
    notes = Path("qiazhi/v40/docs/V40_PHASE60_LENS_DISCUSSION_NOTES.md").read_text(encoding="utf-8")

    assert "UI Flow Clean Rebuild" in doc
    assert "setup / running / report / conversation / practitioner" in doc
    assert "docs/V40_PHASE61_UI_FLOW_CLEAN_REBUILD.md" in readme
    assert "setup / running / report / conversation / practitioner" in spec
    assert "Phase 61 clean shell rule" in ui_spec
    assert "UI Flow Clean-Up Before More Functionality" in notes


def test_phase61_user_ui_has_state_machine_shell_and_lightweight_surfaces() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    for text in [
        'data-state="setup"',
        'body[data-state="setup"] .reading',
        'id="editChartButton"',
        'id="rerunButton"',
        'data-review-open="true"',
        "一个问题，让判断更准",
        "setReadingMode(\"running\")",
        "setup",
        "conversation",
        "practitioner",
    ]:
        assert text in html

    assert "登录 / 我的命盘" not in html
    assert 'id="emptyState"' not in html
    assert "provider" not in html
    assert "SignalRegistry" not in html


def test_phase61_project_status_marks_ui_clean_rebuild_complete() -> None:
    status = build_project_status()

    assert status["current_phase"] == 62
    assert status["current_phase_name"] == "Reading History And Conversation Layering"
    assert any(row["range"] == "60" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "61" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "62" and row["status"] == "active" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "UI-23: report history sidebar and folded conversation chain QA"
