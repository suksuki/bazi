from __future__ import annotations

import asyncio

from v17_rebirth.backend.services.physics_service import PhysicsService
from v17_rebirth.infrastructure.llm_micro_client import build_v17_system_prompt


def _tensor() -> dict:
    return {
        "four_pillars": {"year": "丙午", "month": "壬辰", "day": "壬戌", "hour": "甲辰"},
        "luck_pillar": "辛卯",
        "flow_pillar": "丙午",
        "flow_year": 2026,
        "ten_gods_absolute_intensity": {"七杀": 72.4, "偏印": 31.2},
        "total_energy_index": 143.6,
        "meta": {"v17_physics_stable": True},
    }


def test_build_v17_system_prompt_prefers_current_physics_tensor() -> None:
    prompt = build_v17_system_prompt(
        will_proxy="stable",
        decision_anchor="",
        action_signal=False,
        session_id="prompt-tensor-case",
        physics_tensor=_tensor(),
    )

    assert "四柱：丙午 / 壬辰 / 壬戌 / 甲辰" in prompt
    assert "大运：辛卯；流年：丙午；流年锚年：2026" in prompt
    assert "十神能量为绝对物理强度" in prompt
    assert "Total Energy Index" in prompt


def test_get_metadata_returns_local_mirror_inside_running_loop() -> None:
    sid = "prompt-local-mirror"
    PhysicsService.prime_local_tensor(sid, _tensor())

    async def _read() -> dict:
        return PhysicsService.get_metadata(sid)

    try:
        md = asyncio.run(_read())
    finally:
        PhysicsService.release_session(sid)

    assert md.get("four_pillars", {}).get("year") == "丙午"
    assert md.get("flow_year") == 2026
