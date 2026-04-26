from __future__ import annotations

from v17_rebirth.backend.logic.L0_physics_fields.bazi_image import PLUGIN
from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import (
    build_bazi_image_contract,
    normalize_bazi_image_meta,
    resolve_bazi_image,
)
from v17_rebirth.backend.services.evidence_bundle import build_evidence_bundle
from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService


def _tensor() -> dict:
    return {
        "day_master_stem": "庚",
        "four_pillars": {
            "year": "甲子",
            "month": "戊辰",
            "day": "庚申",
            "hour": "壬午",
        },
        "luck_pillar": "乙亥",
        "flow_pillar": "丙午",
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["year", "hour"]}],
            }
        },
    }


def test_bazi_image_contract_declares_l0_symbolic_boundary() -> None:
    contract = build_bazi_image_contract()

    assert contract["contract"] == "v17.symbolic.bazi_image.v1"
    assert contract["is_l0_symbolic_layer"] is True
    assert "four_pillars" in contract["read_only_sources"]
    assert any("不得" in item for item in contract["constraints"])


def test_resolve_bazi_image_maps_stem_material_and_vault_symbol() -> None:
    image = resolve_bazi_image(_tensor())["bazi_image"]

    assert image["contract"] == "v17.symbolic.bazi_image.v1"
    assert image["day_master_stem"] == "庚"
    assert image["stems"][0]["stem"] == "甲"
    assert image["stems"][0]["ten_god"] == "偏财"
    assert image["stems"][0]["domain_projection"]["wealth"][0] == "长期项目"
    assert any(row["branch"] == "辰" and row["storage_context"]["has_vault_signal"] for row in image["branches"])
    assert any(row["fact_type"] == "vault_material" and "资金流" in row["plain_meaning"] for row in image["symbolic_facts"])
    assert any("偏财见甲木" in row["plain_meaning"] for row in image["symbolic_facts"])
    assert image["guardrails"]


def test_normalize_bazi_image_meta_accepts_plain_dict() -> None:
    image = normalize_bazi_image_meta(
        {
            "day_master_stem": "庚",
            "stems": [{"stem": "甲"}],
            "symbolic_facts": [{"plain_meaning": "偏财见甲木"}],
        }
    )

    assert image["contract"] == "v17.symbolic.bazi_image.v1"
    assert image["is_l0_symbolic_layer"] is True
    assert image["stems"][0]["stem"] == "甲"


def test_bazi_image_plugin_emits_read_only_symbolic_fact() -> None:
    facts = PLUGIN.collect_v17_facts(_tensor())

    assert len(facts) == 1
    fact = facts[0]
    assert fact.plugin_id == "v17.symbolic.bazi_image.v1"
    assert fact.causal_tier == 5
    assert fact.meta["claim_type"] == "symbolic_image_observation"
    assert fact.meta["observe_only"] is True
    assert fact.meta["bazi_image"]["contract"] == "v17.symbolic.bazi_image.v1"

    bundle = build_evidence_bundle(facts, physics_tensor=_tensor())
    assert bundle["items"][0]["evidence_type"] == "symbolic"
    assert bundle["items"][0]["details"]["bazi_image"]["contract"] == "v17.symbolic.bazi_image.v1"


def test_physics_canonical_materializes_bazi_image_lines() -> None:
    pt = _tensor()
    pt["meta"]["bazi_image"] = resolve_bazi_image(pt)["bazi_image"]

    lines = PhysicsCanonicalService.materialize_prompt_lines(pt)

    assert any("八字象义合同" in line for line in lines)
    assert any("象义事实" in line and "偏财见甲木" in line for line in lines)
