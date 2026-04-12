"""首轮观察提示：防弱模型胡编（星座/经纬度对撞等）的约束文案回归。"""

from __future__ import annotations

from app.llm.client import FIRST_OBSERVATION_SYSTEM_PROMPT, build_first_observation_messages


def test_first_observation_system_prompt_forbids_western_astro_and_geo_fiction() -> None:
    assert "十二星座" in FIRST_OBSERVATION_SYSTEM_PROMPT or "西洋" in FIRST_OBSERVATION_SYSTEM_PROMPT
    assert "经纬度" in FIRST_OBSERVATION_SYSTEM_PROMPT
    assert "conflict_matrix" in FIRST_OBSERVATION_SYSTEM_PROMPT


def test_build_first_observation_messages_zh_includes_guard_lines() -> None:
    msgs = build_first_observation_messages({"pillars": {}, "conflict_matrix": {"points": []}}, "", "ZH")
    assert msgs[0]["role"] == "system"
    user = msgs[1]["content"]
    assert "星座" in user or "占星" in user
    assert "BaziMetadata" in user
