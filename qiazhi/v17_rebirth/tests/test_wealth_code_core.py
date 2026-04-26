from __future__ import annotations

from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import resolve_bazi_image
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code import PLUGIN
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import (
    build_wealth_code_contract,
    normalize_wealth_code_meta,
    resolve_wealth_code,
)
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import resolve_wealth_profile
from v17_rebirth.backend.services.evidence_bundle import build_evidence_bundle
from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService


def _pressure_tensor() -> dict:
    return {
        "day_master_stem": "庚",
        "four_pillars": {
            "year": "甲子",
            "month": "丙寅",
            "day": "庚申",
            "hour": "壬午",
        },
        "luck_pillar": "壬午",
        "flow_pillar": "甲辰",
        "ten_gods_runtime": {
            "食神": 40.0,
            "伤官": 10.0,
            "七杀": 58.0,
            "正官": 8.0,
            "偏财": 24.0,
            "正财": 6.0,
            "正印": 8.0,
            "偏印": 4.0,
            "比肩": 8.0,
            "劫财": 5.0,
        },
        "facts": [
            {"fact": "格局候选：食神制杀，靠输出能力处理压力与复杂任务。", "plugin": "classical.pattern.shishen_zhisha.v1"},
        ],
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "偏财"],
                "taboo_gods": ["七杀"],
                "confidence": 0.8,
            }
        },
    }


def test_wealth_code_contract_declares_path_decoder_boundary() -> None:
    contract = build_wealth_code_contract()

    assert contract["contract"] == "v17.topic.wealth_code.v1"
    assert contract["knowledge_base"] == "v17.knowledge.wealth_path_templates.v1"
    assert "output_controls_pressure" in contract["path_templates"]
    assert any("不得" in item for item in contract["constraints"])


def test_resolve_wealth_code_identifies_food_controls_kill_path() -> None:
    pt = _pressure_tensor()
    pt["meta"]["bazi_image"] = resolve_bazi_image(pt)["bazi_image"]
    pt["meta"]["wealth_profile"] = resolve_wealth_profile(pt)["wealth_profile"]

    code = resolve_wealth_code(pt)["wealth_code"]

    assert code["contract"] == "v17.topic.wealth_code.v1"
    assert code["primary_wealth_path"]["id"] == "output_controls_pressure"
    assert code["primary_wealth_path"]["plain_name"] == "靠解决难题赚钱"
    assert "长期项目" in code["wealth_source"]["plain_source"]
    assert code["monetization_engine"]["driver"] == "output_authority"
    assert code["carrier"]["type"] == "method_and_contract"
    assert code["score"] >= 0.6
    assert code["evidence_graph"]["nodes"]


def test_resolve_wealth_code_models_vault_and_leakage_points() -> None:
    pt = _pressure_tensor()
    pt["four_pillars"] = {
        "year": "甲子",
        "month": "戊辰",
        "day": "庚申",
        "hour": "乙酉",
    }
    pt["ten_gods_runtime"] = {
        "偏财": 36.0,
        "正财": 32.0,
        "比肩": 30.0,
        "劫财": 28.0,
        "食神": 12.0,
        "伤官": 8.0,
        "正官": 6.0,
        "七杀": 5.0,
        "正印": 5.0,
        "偏印": 4.0,
    }
    pt["facts"] = [
        {"fact": "格局候选：比劫夺财，合作分账与竞争明显。", "plugin": "l1.physics.op_robber_wealth"},
        {"fact": "墓库门态：辰为库，资金结构等待引动。", "plugin": "l1.physics.op_branch_muku"},
    ]
    pt["meta"]["bazi_image"] = resolve_bazi_image(pt)["bazi_image"]
    pt["meta"]["wealth_profile"] = resolve_wealth_profile(pt)["wealth_profile"]

    code = resolve_wealth_code(pt)["wealth_code"]

    assert code["wealth_vault"]["has_vault_signal"] is True
    assert code["wealth_vault"]["vault_state"] in {"static", "activated"}
    assert any(row["id"] == "peer_split" for row in code["leakage_points"])
    assert any(row["id"] == "leakage_risk" for row in code["secondary_paths"])


def test_normalize_wealth_code_meta_accepts_plain_dict() -> None:
    code = normalize_wealth_code_meta(
        {
            "score": 0.72,
            "confidence": 0.66,
            "risk": 0.31,
            "primary_wealth_path": {"id": "output_to_wealth"},
            "wealth_source": {"plain_source": "技能变现"},
        }
    )

    assert code["contract"] == "v17.topic.wealth_code.v1"
    assert code["score"] == 0.72
    assert code["primary_wealth_path"]["id"] == "output_to_wealth"


def test_wealth_code_plugin_emits_read_only_fact() -> None:
    facts = PLUGIN.collect_v17_facts(_pressure_tensor())

    assert len(facts) == 1
    fact = facts[0]
    assert fact.plugin_id == "modern.topic.wealth_code.v1"
    assert fact.causal_tier == 2
    assert fact.meta["claim_type"] == "topic_code_observation"
    assert fact.meta["observe_only"] is True
    assert fact.meta["wealth_code"]["contract"] == "v17.topic.wealth_code.v1"

    bundle = build_evidence_bundle(facts, physics_tensor=_pressure_tensor())
    assert bundle["items"][0]["evidence_type"] == "topic"
    assert bundle["items"][0]["details"]["wealth_code"]["contract"] == "v17.topic.wealth_code.v1"


def test_physics_canonical_materializes_wealth_code_lines() -> None:
    pt = _pressure_tensor()
    pt["meta"]["bazi_image"] = resolve_bazi_image(pt)["bazi_image"]
    pt["meta"]["wealth_profile"] = resolve_wealth_profile(pt)["wealth_profile"]
    pt["meta"]["wealth_code"] = resolve_wealth_code(pt)["wealth_code"]

    lines = PhysicsCanonicalService.materialize_prompt_lines(pt)

    assert any("财富密码合同" in line for line in lines)
    assert any("财富主路径" in line and "靠解决难题赚钱" in line for line in lines)
