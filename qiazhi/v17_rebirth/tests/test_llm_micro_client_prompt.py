from __future__ import annotations

import asyncio

from v17_rebirth.backend.services.physics_service import PhysicsService
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE
from v17_rebirth.infrastructure.llm_micro_client import build_llm_audit_payload, build_v17_system_prompt


def _tensor() -> dict:
    return {
        "four_pillars": {"year": "丙午", "month": "壬辰", "day": "壬戌", "hour": "甲辰"},
        "luck_pillar": "辛卯",
        "flow_pillar": "丙午",
        "flow_year": 2026,
        "ten_gods_absolute_intensity": {"七杀": 72.4, "偏印": 31.2},
        "total_energy_index": 143.6,
        "energy_meta": {
            "relation_formation_summary": [
                {
                    "formation_label": "寅午戌三合火局",
                    "formation_percent": 78.6,
                    "family_factor": 3.5,
                    "status": "受扰成局",
                    "projection_preview": ["劫财65%", "比肩35%"],
                    "conflict_damping": 0.77,
                }
            ],
            "relation_dynamics_summary": [
                {
                    "label": "子午六冲",
                    "energy_axis": "激发",
                    "energy_effect_ratio": 0.58,
                    "stability_delta_ratio": -0.74,
                    "free_energy_lock_ratio": 0.0,
                    "note": "冲不等于没能量，而是把静态资源推成动态事件。",
                }
            ],
        },
        "meta": {
            "v17_physics_stable": True,
            "plugin_claims": [
                {
                    "plugin_id": "classical.pattern.officer.v1",
                    "pattern_candidate": "正官格",
                    "pattern_confidence_percent": 65.0,
                    "target_god": "正官",
                    "pattern_scope_label": "原局",
                }
            ],
            "god_ring_authority": {
                "effect_scores": {
                    "正官": {
                        "authority_profile": "高能躁动",
                        "authority_energy": 1.10,
                        "authority_stability": 0.20,
                        "authority_volatility": 0.62,
                        "authority_use_score": 0.44,
                        "authority_taboo_score": 0.86,
                    },
                    "偏印": {
                        "authority_profile": "低能稳态",
                        "authority_energy": 0.68,
                        "authority_stability": 0.41,
                        "authority_volatility": 0.11,
                        "authority_use_score": 0.78,
                        "authority_taboo_score": 0.08,
                    },
                },
                "judgement_bias_protocol": {
                    "summary": {
                        "entry_count": 3,
                        "total_use_bias": 0.42,
                        "total_taboo_bias": 0.28,
                    }
                },
                "stage_bias_protocol": {
                    "summary": {
                        "entry_count": 2,
                        "total_use_boost": 0.18,
                        "total_taboo_boost": 0.06,
                        "total_stability_boost": 0.09,
                        "total_volatility_boost": 0.12,
                    }
                },
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
    assert "合化摘要：寅午戌三合火局 78.6%" in user_prompt
    assert "关系动力学：子午六冲 激发58%" in user_prompt
    assert "体用双轴摘要：正官 高能躁动" in user_prompt
    assert "判定偏置摘要：条目3；用侧0.42；忌侧0.28" in user_prompt
    assert "阶段偏置摘要：条目2；推用0.18；推忌0.06；稳0.09；波动0.12" in user_prompt
    assert "格局摘要：正官格 65.0%" in user_prompt
    assert "运流解释合同" in user_prompt


def test_build_llm_audit_payload_respects_output_language_lock() -> None:
    en_tensor = {**_tensor(), "ui_lang": "en"}
    en_payload = build_llm_audit_payload(
        [],
        will_proxy="stable",
        decision_anchor="",
        action_signal=False,
        physics_tensor=en_tensor,
    )
    en_system_prompt = str(en_payload.get("llm_system_prompt") or "")
    en_user_prompt = str(en_payload.get("llm_user_prompt") or "")
    assert "STRICT ENGLISH ONLY" in en_system_prompt
    assert "The final answer must be English." in en_system_prompt
    assert "The final response must be written in English only." in en_user_prompt
    for forbidden in ("中文篇章", "不得输出英文", "短指令式中文", "最终正文必须使用简体中文"):
        assert forbidden not in en_system_prompt
        assert forbidden not in en_user_prompt

    ko_tensor = {**_tensor(), "ui_lang": "ko"}
    ko_payload = build_llm_audit_payload(
        [],
        will_proxy="stable",
        decision_anchor="",
        action_signal=False,
        physics_tensor=ko_tensor,
    )
    ko_system_prompt = str(ko_payload.get("llm_system_prompt") or "")
    ko_user_prompt = str(ko_payload.get("llm_user_prompt") or "")
    assert "STRICT KOREAN ONLY" in ko_system_prompt
    assert "최종 답변은 반드시 한국어입니다" in ko_system_prompt
    assert "최종 응답은 반드시 한국어로만 작성하십시오." in ko_user_prompt
    for forbidden in ("中文篇章", "不得输出英文", "短指令式中文", "最终正文必须使用简体中文"):
        assert forbidden not in ko_system_prompt
        assert forbidden not in ko_user_prompt

    ko_judge_payload = build_llm_audit_payload(
        [],
        will_proxy="stable",
        decision_anchor="",
        action_signal=False,
        role_style=V17_ROLE_JUDGE,
        physics_tensor=ko_tensor,
    )
    ko_judge_system_prompt = str(ko_judge_payload.get("llm_system_prompt") or "")
    ko_judge_user_prompt = str(ko_judge_payload.get("llm_user_prompt") or "")
    assert "STRICT KOREAN ONLY" in ko_judge_system_prompt
    assert "최종 답변은 반드시 한국어입니다" in ko_judge_system_prompt
    for forbidden in ("中文篇章", "不得输出英文", "短指令式中文", "最终正文必须使用简体中文"):
        assert forbidden not in ko_judge_system_prompt
        assert forbidden not in ko_judge_user_prompt
