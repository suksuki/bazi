from __future__ import annotations

from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile import PLUGIN
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import (
    build_wealth_profile_contract,
    normalize_wealth_profile_meta,
    resolve_wealth_profile,
)
from v17_rebirth.backend.services.evidence_bundle import build_evidence_bundle
from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService


def _base_tensor() -> dict:
    return {
        "gender": "male",
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_runtime": {
            "食神": 36.0,
            "伤官": 22.0,
            "正财": 30.0,
            "偏财": 20.0,
            "正官": 16.0,
            "七杀": 8.0,
            "正印": 10.0,
            "偏印": 6.0,
            "比肩": 10.0,
            "劫财": 8.0,
        },
        "facts": [
            {"fact": "格局候选：食伤生财，输出换财通道显性。", "plugin": "classical.pattern.shishen_shengcai.v1"},
            {"fact": "格局候选：正财格月令入口。", "plugin": "classical.pattern.wealth_star.v1"},
        ],
        "energy_meta": {
            "relation_dynamics_summary": [
                {
                    "label": "子午冲",
                    "energy_axis": "激发",
                    "stability_delta_ratio": -0.08,
                    "energy_effect_ratio": 0.28,
                }
            ]
        },
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "正财"],
                "taboo_gods": ["七杀"],
                "tongguan_gods": ["正官"],
                "confidence": 0.82,
            },
            "blind_theme": {
                "contract": "v17.blind.theme.v1",
                "confidence": 0.76,
                "primary_route": "食伤生财",
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


def test_wealth_profile_contract_declares_topic_decoder_boundary() -> None:
    contract = build_wealth_profile_contract()

    assert contract["contract"] == "v17.topic.wealth_profile.v1"
    assert contract["is_l3_topic_decoder"] is True
    assert "ten_gods_runtime" in contract["read_only_sources"]
    assert any("不得" in item for item in contract["constraints"])


def test_resolve_wealth_profile_decodes_output_to_wealth_sample() -> None:
    profile = resolve_wealth_profile(_base_tensor())["wealth_profile"]

    assert profile["contract"] == "v17.topic.wealth_profile.v1"
    assert profile["topic"] == "wealth"
    assert profile["score"] >= 0.6
    assert profile["usable_state"] == "wealth_as_use"
    assert profile["visibility"] == "explicit_wealth"
    assert profile["primary_channels"][0]["id"] in {"output_to_wealth", "stable_income"}
    assert any(row["id"] == "output_to_wealth" for row in profile["primary_channels"])
    assert any("十神财富簇" in item for item in profile["evidence"])
    assert any("食伤" in item or "输出" in item for item in profile["bridge_requirements"])
    assert "必发财" in profile["assertion_style"]["must_avoid"]


def test_resolve_wealth_profile_marks_taboo_and_competition_risks() -> None:
    pt = _base_tensor()
    pt["ten_gods_runtime"] = {
        "正财": 44.0,
        "偏财": 32.0,
        "比肩": 35.0,
        "劫财": 34.0,
        "食神": 10.0,
        "伤官": 8.0,
        "正官": 6.0,
        "七杀": 5.0,
        "正印": 4.0,
        "偏印": 3.0,
    }
    pt["meta"]["god_ring_authority"] = {
        "use_gods": ["正印"],
        "taboo_gods": ["正财", "偏财"],
        "confidence": 0.8,
    }
    pt["facts"] = [
        {"fact": "格局候选：比劫夺财，合伙分利与竞争明显。", "plugin": "l1.physics.op_robber_wealth"},
    ]

    profile = resolve_wealth_profile(pt)["wealth_profile"]

    assert profile["usable_state"] == "wealth_as_taboo"
    assert profile["risk"] >= 0.38
    assert profile["stance"] == "volatile"
    assert any("比劫" in item for item in profile["risks"])
    assert any("体用忌侧" in item for item in profile["contradictions"])
    assert profile["assertion_style"]["tone"] in {"cautious", "risk_first"}


def test_resolve_wealth_profile_identifies_hidden_wealth_path() -> None:
    pt = _base_tensor()
    pt["ten_gods_runtime"] = {
        "食神": 50.0,
        "伤官": 36.0,
        "正财": 7.0,
        "偏财": 5.0,
        "正官": 7.0,
        "七杀": 4.0,
        "正印": 6.0,
        "偏印": 5.0,
        "比肩": 12.0,
        "劫财": 8.0,
    }
    pt["meta"]["god_ring_authority"] = {
        "use_gods": ["食神", "伤官"],
        "taboo_gods": ["正官"],
        "confidence": 0.78,
    }
    pt["facts"] = [
        {"fact": "格局候选：伤官生财，输出换财但财星未透。", "plugin": "classical.pattern.shangguan_shengcai.v1"},
    ]

    profile = resolve_wealth_profile(pt)["wealth_profile"]

    assert profile["visibility"] == "hidden_wealth"
    assert profile["usable_state"] == "wealth_needs_bridge"
    assert profile["primary_channels"][0]["id"] == "output_to_wealth"
    assert any("不是现成财库" in item for item in profile["contradictions"])


def test_normalize_wealth_profile_meta_accepts_plain_dict() -> None:
    profile = normalize_wealth_profile_meta(
        {
            "score": 0.72,
            "confidence": 0.68,
            "risk": 0.24,
            "stance": "active",
            "visibility": "explicit_wealth",
            "usable_state": "wealth_as_use",
            "primary_channels": [{"id": "stable_income", "score": 0.7, "evidence": ["正财"]}],
        }
    )

    assert profile["contract"] == "v17.topic.wealth_profile.v1"
    assert profile["primary_channels"][0]["label"] == "稳定现金流"


def test_wealth_profile_plugin_emits_read_only_fact() -> None:
    facts = PLUGIN.collect_v17_facts(_base_tensor())

    assert len(facts) == 1
    fact = facts[0]
    assert fact.plugin_id == "modern.topic.wealth_profile.v1"
    assert fact.causal_tier == 2
    assert fact.meta["claim_type"] == "topic_profile_observation"
    assert fact.meta["wealth_profile"]["contract"] == "v17.topic.wealth_profile.v1"
    assert fact.meta["observe_only"] is True

    bundle = build_evidence_bundle(facts, physics_tensor=_base_tensor())
    assert bundle["items"][0]["evidence_type"] == "topic"
    assert bundle["items"][0]["details"]["wealth_profile"]["contract"] == "v17.topic.wealth_profile.v1"


def test_physics_canonical_materializes_wealth_profile_lines() -> None:
    pt = _base_tensor()
    pt["meta"]["wealth_profile"] = resolve_wealth_profile(pt)["wealth_profile"]

    lines = PhysicsCanonicalService.materialize_prompt_lines(pt)

    assert any("财富画像合同" in line for line in lines)
    assert any("财富主通道" in line for line in lines)
