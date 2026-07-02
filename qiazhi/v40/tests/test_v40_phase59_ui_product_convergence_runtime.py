from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.project import build_project_status


def test_phase59_user_ui_converges_to_reading_product_flow() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    for text in [
        "我的命盘",
        "测算入口",
        "你想先看什么？",
        "当前命盘",
        "currentChartCard",
        "命盘输入：编辑四柱与高级设置",
        "开始测算",
        "查看推演过程",
        "核心判断",
        "判断与建议",
        "继续追问",
        "校准一问",
        "查看完整报告",
        "question-chip",
        "conversation-mode",
        "专业视角",
        "lensToggleButton",
        "data-lens-topic",
        "查看专业视角",
        "当前聚焦",
        "断项池、影响预览和校准动作",
        "采为主断",
        "作为辅助",
        "需要追问",
        "safeJsonList",
        "data-probe-options",
        "添加备注",
        "more_like_this",
        "supporting_context",
        "do_not_use_now",
        "ask_to_confirm",
        "user_mismatch",
        "报告已放到左侧历史报告",
    ]:
        assert text in html

    assert "Practitioner Lens" not in html
    assert "Input Workspace" not in html
    assert "/admin/v40" not in html
    assert "local_expression_adapter" not in html
    assert "execution_mode" not in html
    assert "downweight" not in html
    assert "policy_key" not in html
    assert "trainable_refs" not in html


def test_phase59_project_status_marks_ui_convergence_runtime_active() -> None:
    status = build_project_status()

    assert status["current_phase"] == 65
    assert status["current_phase_name"] == "V30 Mingli Asset Migration Gate"
    assert any(row["range"] == "58" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "59" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "60" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "P65-1: V30 Mingli Asset Migration Gate"
