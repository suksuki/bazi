from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.project import build_project_status


def test_phase62_history_and_conversation_layering_is_documented() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE62_HISTORY_AND_CONVERSATION_LAYERING.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")

    assert "Reading History And Conversation Layering" in doc
    assert "历史报告放到左边栏" in doc
    assert "latest question" in doc
    assert "docs/V40_PHASE62_HISTORY_AND_CONVERSATION_LAYERING.md" in readme
    assert "Phase 62 历史报告与问答层级" in spec
    assert "UI-3A Reading History Sidebar" in ui_spec
    assert "Do not expose global backend runtime records as user history" in ui_spec


def test_phase62_user_ui_has_left_history_and_folded_reverse_conversation_items() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    for text in [
        'id="historyPanel"',
        'id="historyList"',
        "历史报告",
        "rememberReading(currentRuntime, seeds)",
        "openHistoryReading",
        "historyStorageKey",
        "conversation-toggle",
        "data-turn-toggle",
        "foldConversationTurns",
        "$(\"conversationTurns\").prepend(node)",
        'body[data-state="conversation"] #verdictHero',
        'body[data-state="conversation"] #reviewSurface',
        'body[data-state="conversation"] #followupHub',
        'id="conversationSeedCards"',
        'id="conversationQuestion"',
        'id="conversationAskButton"',
        "Gemma 返回前不会生成替代结论",
        "报告在左侧历史报告里查阅",
    ]:
        assert text in html

    assert "global runtime" not in html
    assert "provider" not in html
    assert "policy_key" not in html


def test_phase62_project_status_marks_history_conversation_layering_active() -> None:
    status = build_project_status()

    assert status["current_phase"] == 70
    assert status["current_phase_name"] == "Direct Training Activation Evidence"
    assert any(row["range"] == "61" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "62" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "TRAIN-16: direct training activation before/after acceptance and rollback UX"
