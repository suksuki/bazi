from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.project import build_project_status


def test_phase55_user_ui_has_three_line_process_ticker_without_multistep_interaction() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    assert "processTicker" in html
    assert "processLine1" in html
    assert "processLine2" in html
    assert "processLine3" in html
    assert "renderProcessLoading" in html
    assert "renderProcessTicker(runtime)" in html
    assert "renderProcessFailure" in html
    assert "定盘" in html
    assert "取象" in html
    assert "合参" in html
    assert "查看推演过程" in html
    assert "三行" not in html
    assert "V30 多步" not in html
    assert "provider" not in html
    assert "model" not in html
    assert "debug" not in html
    assert "/admin/v40" not in html


def test_phase55_docs_and_project_status_track_compact_process_ticker() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE55_COMPACT_PROCESS_TICKER.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Compact Staged Process Ticker" in doc
    assert "Do not bring back V30 multi-step interaction" in doc
    assert "2026-07-02 Phase 55" in spec
    assert "docs/V40_PHASE55_COMPACT_PROCESS_TICKER.md" in readme
    assert "three-line staged process ticker" in ui_spec
    assert status["current_phase"] == 65
    assert status["current_phase_name"] == "V30 Mingli Asset Migration Gate"
    assert any(row["range"] == "54" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "55" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "56" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "59" and row["status"] == "complete" for row in status["phase_groups"])
    assert "P65-1: V30 Mingli Asset Migration Gate" in status["next_mainline_tasks"]
