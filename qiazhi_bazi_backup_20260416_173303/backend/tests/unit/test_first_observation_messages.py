"""首轮观察提示：Logic_Master_Arbiter 契约与 user 引导回归。"""

from __future__ import annotations

from app.llm.client import FIRST_OBSERVATION_SYSTEM_PROMPT, build_first_observation_messages


def test_first_observation_system_is_logic_master_arbiter() -> None:
    assert "Logic_Master_Arbiter" in FIRST_OBSERVATION_SYSTEM_PROMPT
    assert "GLOBAL_STRUCTURE" in FIRST_OBSERVATION_SYSTEM_PROMPT or "格局" in FIRST_OBSERVATION_SYSTEM_PROMPT


def test_build_first_observation_messages_zh_includes_node_chain_guard() -> None:
    msgs = build_first_observation_messages("FACT_NODE:寅巳穿害，日支受损", "", "ZH")
    assert msgs[0]["role"] == "system"
    user = msgs[1]["content"]
    assert "Node_Chain_Execution" in user
    assert "NODE_FACT" in user


def test_build_first_observation_messages_strips_float_literals_and_accepts_labels() -> None:
    hint = '[Verified Facts·语义标签-only]\n["VF·十神.比肩.Abs档=中庸可用"]'
    msgs = build_first_observation_messages(
        "FACT_NODE:寅巳穿害，日支受损 x=1.414",
        "",
        "ZH",
        semantic_label_json=hint,
    )
    user = msgs[1]["content"]
    assert "语义标签" in user
    assert "1.414" not in user
