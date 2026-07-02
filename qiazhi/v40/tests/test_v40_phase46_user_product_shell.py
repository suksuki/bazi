from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.project import build_project_status


def test_phase46_user_ui_uses_product_shell_template_without_engineering_leakage() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    assert "v40/api/user_ui.html" not in html
    assert "Input Workspace" not in html
    assert "测算入口" in html
    assert "当前命盘" in html
    assert "核心判断" in html
    assert "判断与建议" in html
    assert "继续追问" in html
    assert "校准一问" in html
    assert "查看完整报告" in html
    assert "专业视角" in html
    assert "paintReading" in html
    assert "product_projection" in html
    assert "/api/v40/readings/native-report" in html
    assert "/api/v40/conversation/turn" in html
    assert "/api/v40/calibration/practitioner-lens-action" in html

    forbidden = [
        "execution_mode",
        "Gemma4",
        "Local",
        "Ollama",
        "provider",
        "model",
        "acceptance",
        "policy",
        "debug",
        "telemetry",
        "TrainingLabelEvent",
        "roleKey",
        "表达方式",
        "/admin/v40",
    ]
    for token in forbidden:
        assert token not in html


def test_phase46_docs_and_project_status_track_product_shell_runtime() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE46_USER_PRODUCT_SHELL_RUNTIME.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "User Product Shell Runtime" in doc
    assert "v40/api/user_ui.html" in doc
    assert "POST /api/v40/probes/answer" in doc
    assert "2026-07-01 Phase 46" in spec
    assert "docs/V40_PHASE46_USER_PRODUCT_SHELL_RUNTIME.md" in readme
    assert status["current_phase"] == 70
    assert status["current_phase_name"] == "Direct Training Activation Evidence"
    assert any(row["range"] == "46" and row["status"] == "complete" for row in status["phase_groups"])
