from __future__ import annotations

import ast
from pathlib import Path

from v40.project import build_project_status


def test_phase50_visual_qa_doc_and_script_are_mainline_artifacts() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE50_USER_UI_VISUAL_QA.md").read_text(encoding="utf-8")
    script_path = Path("qiazhi/v40/scripts/run_user_ui_visual_qa.py")
    script = script_path.read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")

    ast.parse(script)
    assert "User UI Visual QA" in doc
    assert "desktop_user" in doc
    assert "desktop_practitioner" in doc
    assert "mobile_user" in doc
    assert "visual_qa_report.json" in doc
    assert "FORBIDDEN_VISIBLE_TERMS" in script
    assert "page.screenshot" in script
    assert "desktop_practitioner" in script
    assert "mobile horizontal overflow" in script
    assert "2026-07-01 Phase 50" in spec
    assert "scripts/run_user_ui_visual_qa.py" in spec
    assert "docs/V40_PHASE50_USER_UI_VISUAL_QA.md" in readme


def test_phase50_project_status_tracks_visual_qa_as_completed_mainline() -> None:
    status = build_project_status()

    assert status["current_phase"] == 59
    assert status["current_phase_name"] == "UI Product Convergence Runtime"
    assert any(row["range"] == "49" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "50" and row["status"] == "complete" for row in status["phase_groups"])
    assert "UI-15: live LLM user acceptance with admin profiles" in status["next_mainline_tasks"]
