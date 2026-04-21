from __future__ import annotations

import asyncio

from v17_rebirth.backend.services.physics_service import PhysicsService
from v17_rebirth.infrastructure.llm_micro_client import build_llm_audit_payload, build_v17_system_prompt


def _tensor() -> dict:
    return {
        "four_pillars": {"year": "丙午", "month": "壬辰", "day": "壬戌", "hour": "甲辰"},
        "luck_pillar": "辛卯",
        "flow_pillar": "丙午",
        "flow_year": 2026,
        "ten_gods_absolute_intensity": {"七杀": 72.4, "偏印": 31.2},
        "total_energy_index": 143.6,
        "meta": {
            "v17_physics_stable": True,
            "god_ring_authority": {
                "core_flux_meta": {
                    "interaction_matrix": [
                        {
                            "source": "食神",
                            "target": "偏财",
                            "net": 0.421,
                            "support_ratio": 0.8,
                            "resist_ratio": 0.2,
                        },
                        {
                            "source": "伤官",
                            "target": "正官",
                            "net": -0.388,
                            "support_ratio": 0.22,
                            "resist_ratio": 0.78,
                        },
                    ],
                    "tension_pairs": [
                        {
                            "left": "伤官",
                            "right": "正官",
                            "mode": "tension",
                            "score": 0.294,
                        }
                    ],
                }
            },
        },
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
        return await PhysicsService.aget_metadata(sid)

    try:
        md = asyncio.run(_read())
    finally:
        PhysicsService.release_session(sid)

    assert md.get("four_pillars", {}).get("year") == "丙午"
    assert md.get("flow_year") == 2026


def test_build_llm_audit_payload_frontloads_flux_summary_into_user_prompt() -> None:
    payload = build_llm_audit_payload(
        [],
        will_proxy="stable",
        decision_anchor="",
        action_signal=False,
        physics_tensor=_tensor(),
    )

    user_prompt = str(payload.get("llm_user_prompt") or "")
    assert "做功方向矩阵" in user_prompt
    assert "做功回路" in user_prompt
    assert "食神->偏财" in user_prompt
