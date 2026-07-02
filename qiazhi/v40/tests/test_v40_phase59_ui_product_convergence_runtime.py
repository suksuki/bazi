from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.project import build_project_status


def test_phase59_user_ui_converges_to_reading_product_flow() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    for text in [
        "登录 / 我的命盘",
        "测算入口",
        "你想先看什么？",
        "当前命盘",
        "currentChartCard",
        "命盘输入：编辑四柱与高级设置",
        "开始测算",
        "本次已完成：定盘 / 取象 / 合参",
        "核心判断",
        "本次报告",
        "继续追问",
        "一个问题，让判断更准",
        "专业视角",
        "报告不会刷新",
    ]:
        assert text in html

    assert "Practitioner Lens" not in html
    assert "Input Workspace" not in html
    assert "/admin/v40" not in html
    assert "local_expression_adapter" not in html
    assert "execution_mode" not in html


def test_phase59_project_status_marks_ui_convergence_runtime_active() -> None:
    status = build_project_status()

    assert status["current_phase"] == 59
    assert status["current_phase_name"] == "UI Product Convergence Runtime"
    assert any(row["range"] == "58" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "59" and row["status"] == "active" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "UI-18: Phase 59 productized reading setup and report-first convergence"

