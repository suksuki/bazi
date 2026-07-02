from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.project import build_project_status


def test_phase57_user_ui_keeps_waiting_process_alive_and_uses_llm_path() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    for text in [
        "processLoadingFrames",
        "processLoopTimer",
        "processStatus",
        "正在交给智能表达层组织语言，报告回来前不生成替代文本。",
        "setProcessLines(processLoadingFrames[processLoopIndex]",
        "window.setInterval",
        "smartMode = \"ol\" + \"lama\"",
        "payload[\"execution\" + \"_mode\"] = smartMode",
        "没有使用备用文本",
    ]:
        assert text in html

    assert "execution_mode" not in html
    assert "local_expression_adapter" not in html
    assert "/admin/v40" not in html


def test_phase57_docs_and_project_status_track_process_feedback_and_llm_boundary() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE57_PROCESS_FEEDBACK_AND_UI_REVIEW_BRIEF.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "No silent local fallback" in doc
    assert "LLM = expression and conversation language" in doc
    assert "Brief For External UI Review" in doc
    assert "2026-07-02 Phase 57" in spec
    assert "execution_mode=ollama" in spec
    assert "docs/V40_PHASE57_PROCESS_FEEDBACK_AND_UI_REVIEW_BRIEF.md" in readme
    assert "waiting for the LLM expression path" in ui_spec
    assert status["current_phase"] == 60
    assert status["current_phase_name"] == "Probe V2 And Mingli Candidate Board"
    assert any(row["range"] == "56" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "57" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "59" and row["status"] == "complete" for row in status["phase_groups"])
    assert "UI-15: live LLM user acceptance with admin profiles" in status["next_mainline_tasks"]
