from __future__ import annotations

from v17_rebirth.backend.logic.L3_modern_narrative.macro_theme import PLUGINS
from v17_rebirth.backend.logic.L3_modern_narrative.macro_theme_core import (
    build_macro_theme_contract,
    normalize_macro_theme_meta,
    resolve_macro_theme,
)
from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService


def _tensor() -> dict:
    return {
        "gender": "male",
        "ten_gods_runtime": {
            "食神": 36.0,
            "伤官": 28.0,
            "正财": 30.0,
            "偏财": 24.0,
            "正官": 18.0,
            "七杀": 12.0,
            "正印": 11.0,
            "偏印": 8.0,
            "比肩": 10.0,
            "劫财": 9.0,
        },
        "energy_meta": {
            "relation_dynamics_summary": [
                {
                    "label": "子午冲",
                    "energy_axis": "激发",
                    "stability_delta_ratio": -0.12,
                    "energy_effect_ratio": 0.32,
                }
            ]
        },
        "facts": [
            {"fact": "格局候选：食伤生财，输出换财通道显性。", "plugin": "classical.pattern.shishen_shengcai.v1"},
            {"fact": "关系动力学：子午冲 激发。", "plugin": "l1.physics.op_branch_liuchong"},
        ],
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "正财"],
                "taboo_gods": ["七杀"],
                "confidence": 0.82,
            },
            "blind_theme": {
                "contract": "v17.blind.theme.v1",
                "confidence": 0.76,
                "primary_route": "食伤生财",
                "body_mode": "output_body",
                "house_roles": {"食神": "outside", "正财": "inside"},
            },
            "climate_theme": {
                "contract": "v17.climate.theme.v1",
                "confidence": 0.7,
                "state": "燥热偏盛",
                "climate_tension": 0.72,
            },
            "xiangfa_theme": {
                "contract": "v17.xiangfa.theme.v1",
                "confidence": 0.68,
                "event_framing": ["输出换财，机会伴随成本"],
            },
        },
    }


def test_macro_theme_contract_declares_l3_read_only_boundary() -> None:
    contract = build_macro_theme_contract()
    assert contract["contract"] == "v17.macro.theme.v1"
    assert contract["is_l3_macro_topic"] is True
    assert "财富" not in contract["topics"]
    assert any("不得" in item for item in contract["constraints"])


def test_resolve_macro_theme_builds_four_life_topics() -> None:
    analysis = resolve_macro_theme(_tensor())
    theme = analysis["macro_theme"]

    assert theme["contract"] == "v17.macro.theme.v1"
    assert theme["confidence"] > 0.5
    assert {row["id"] for row in theme["topics"]} == {"wealth", "career", "relationship", "personality"}
    wealth = next(row for row in theme["topics"] if row["id"] == "wealth")
    assert wealth["score"] > 0.6
    assert "食神" in wealth["source_gods"]
    assert wealth["evidence"]
    assert wealth["opportunities"]
    assert theme["llm_guidance"]


def test_resolve_macro_theme_ignores_macro_generated_facts() -> None:
    pt = _tensor()
    pt["facts"] = list(pt["facts"]) + [
        {
            "fact": "宏观象：事业 官印 财官 组织明显。",
            "plugin": "modern.macro.career.v1",
            "meta": {"claim_type": "macro_theme_observation"},
        }
    ]
    pt["meta"]["god_ring_authority"] = {
        "god_of_use": "食神",
        "god_of_taboo": "七杀",
        "confidence": 0.82,
    }

    theme = resolve_macro_theme(pt)["macro_theme"]
    career = next(row for row in theme["topics"] if row["id"] == "career")
    wealth = next(row for row in theme["topics"] if row["id"] == "wealth")

    assert not any("插件碰撞" in item for item in career["evidence"])
    assert "体用顺侧：食神" in wealth["opportunities"]


def test_normalize_macro_theme_meta_accepts_plain_dict() -> None:
    theme = normalize_macro_theme_meta(
        {
            "confidence": 0.66,
            "topics": [
                {
                    "id": "wealth",
                    "label": "财富",
                    "score": 0.72,
                    "confidence": 0.67,
                    "risk": 0.24,
                    "stance": "active",
                    "summary": "财富主题活跃。",
                }
            ],
        }
    )

    assert theme["contract"] == "v17.macro.theme.v1"
    assert theme["topics"][0]["id"] == "wealth"
    assert theme["top_topics"] == ["wealth"]


def test_macro_theme_plugins_emit_topic_facts() -> None:
    facts = []
    for plugin in PLUGINS:
        facts.extend(plugin.collect_v17_facts(_tensor()))

    assert {fact.plugin_id for fact in facts} == {
        "modern.macro.wealth.v1",
        "modern.macro.career.v1",
        "modern.macro.relationship.v1",
        "modern.macro.personality.v1",
    }
    for fact in facts:
        assert fact.causal_tier == 2
        assert fact.meta["source_event"] == "macro_theme"
        assert fact.meta["macro_theme"]["contract"] == "v17.macro.theme.v1"
        assert fact.meta["claim_type"] == "macro_theme_observation"


def test_physics_canonical_materializes_macro_theme_lines() -> None:
    pt = _tensor()
    pt["meta"]["macro_theme"] = resolve_macro_theme(pt)["macro_theme"]

    lines = PhysicsCanonicalService.materialize_prompt_lines(pt)

    assert any("宏观象合同" in line for line in lines)
    assert any("宏观象摘要" in line and "财富" in line for line in lines)
