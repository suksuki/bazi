"""首轮观察提示：Structural Observer 契约与 user 引导回归。"""

from __future__ import annotations

from app.llm.client import FIRST_OBSERVATION_SYSTEM_PROMPT, build_first_observation_messages


def test_first_observation_system_is_structural_observer_template() -> None:
    assert "Structural Observer" in FIRST_OBSERVATION_SYSTEM_PROMPT
    assert "conflict_matrix.points" in FIRST_OBSERVATION_SYSTEM_PROMPT
    assert "[位置]" in FIRST_OBSERVATION_SYSTEM_PROMPT


def test_build_first_observation_messages_zh_includes_metadata_and_positive_guard() -> None:
    msgs = build_first_observation_messages({"pillars": {}, "conflict_matrix": {"points": []}}, "", "ZH")
    assert msgs[0]["role"] == "system"
    user = msgs[1]["content"]
    assert "BaziMetadata" in user
    assert "干支" in user or "JSON" in user


def test_build_first_observation_messages_strips_float_literals_and_accepts_labels() -> None:
    hint = '[Verified Facts·语义标签-only]\n["VF·十神.比肩.Abs档=中庸可用"]'
    msgs = build_first_observation_messages(
        {"pillars": {}, "conflict_matrix": {"points": []}, "x": 1.414},
        "",
        "ZH",
        semantic_label_json=hint,
    )
    user = msgs[1]["content"]
    assert "语义标签" in user
    assert "1.414" not in user
