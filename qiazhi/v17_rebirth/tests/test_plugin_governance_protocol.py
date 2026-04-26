from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import registry_rows_for_admin
from v17_rebirth.backend.services.plugin_governance import classify_plugin_governance


def test_plugin_governance_classifies_core_authority_boundaries() -> None:
    ziping = classify_plugin_governance(
        plugin_id="classical.ziping.god_ring_resolver.v1",
        layer="L2",
        causal_tier=3,
    )
    blind = classify_plugin_governance(
        plugin_id="classical.blind.work_axis.v1",
        layer="L2",
        causal_tier=3,
    )
    xiangfa = classify_plugin_governance(
        plugin_id="classical.xiangfa.semantic_mapping.v1",
        layer="L2",
        causal_tier=3,
    )
    sanhe = classify_plugin_governance(
        plugin_id="l1.physics.op_branch_sanhe",
        layer="L1",
        causal_tier=4,
    )
    narrative = classify_plugin_governance(
        plugin_id="narrative_clip",
        causal_tier=2,
    )
    topic = classify_plugin_governance(
        plugin_id="modern.topic.wealth_profile.v1",
        layer="L3",
        causal_tier=2,
    )
    wealth_code = classify_plugin_governance(
        plugin_id="modern.topic.wealth_code.v1",
        layer="L3",
        causal_tier=2,
    )
    symbolic = classify_plugin_governance(
        plugin_id="v17.symbolic.bazi_image.v1",
        layer="L0",
        causal_tier=5,
    )

    assert ziping["authority_level"] == "level_1_hard"
    assert ziping["can_enter_authority"] is True
    assert ziping["override_forbidden"] is True

    assert blind["governance_class"] == "soft_bias_topic"
    assert blind["can_enter_authority"] is True
    assert 0 < float(blind["max_bias_ratio"]) < float(ziping["max_bias_ratio"])

    assert xiangfa["governance_class"] == "semantic_only_topic"
    assert xiangfa["can_enter_authority"] is False
    assert xiangfa["max_bias_ratio"] == 0.0

    assert sanhe["governance_class"] == "physical_relation_operator"
    assert sanhe["can_emit_physical_proposal"] is True
    assert sanhe["can_enter_authority"] is False

    assert narrative["governance_class"] == "narrative_or_strategy"
    assert narrative["can_enter_authority"] is False
    assert narrative["learning_family"] == "narrative"

    assert topic["governance_class"] == "topic_decoder"
    assert topic["can_enter_authority"] is False
    assert topic["output_contract"] == "topic_profile"

    assert wealth_code["governance_class"] == "topic_decoder"
    assert wealth_code["can_enter_authority"] is False
    assert wealth_code["learning_family"] == "topic_decoder"

    assert symbolic["governance_class"] == "symbolic_foundation"
    assert symbolic["can_enter_authority"] is False
    assert symbolic["output_contract"] == "symbolic_fact_contract"


def test_admin_registry_exposes_governance_profile() -> None:
    rows = registry_rows_for_admin()
    by_id = {
        str(row.get("plugin_id") or "").strip(): row
        for row in rows
        if str(row.get("plugin_id") or "").strip()
    }

    ziping = by_id["classical.ziping.god_ring_resolver.v1"]
    blind = by_id["classical.blind.work_axis.v1"]
    xiangfa = by_id["classical.xiangfa.semantic_mapping.v1"]
    symbolic = by_id["v17.symbolic.bazi_image.v1"]
    wealth_profile = by_id["modern.topic.wealth_profile.v1"]
    wealth_code = by_id["modern.topic.wealth_code.v1"]

    assert ziping["governance_profile"]["protocol"] == "v17.plugin_governance.v1"
    assert ziping["governance_class"] == "ziping_umbrella"
    assert ziping["authority_level"] == "level_1_hard"

    assert blind["governance_profile"]["governance_class"] == "soft_bias_topic"
    assert blind["learning_family"] == "blind_theme"

    assert xiangfa["governance_profile"]["can_enter_authority"] is False
    assert xiangfa["output_contract"] == "semantic_mapping"

    assert wealth_profile["governance_profile"]["governance_class"] == "topic_decoder"
    assert wealth_profile["learning_family"] == "topic_decoder"

    assert wealth_code["display_name"] == "财富密码解码器"
    assert wealth_code["governance_profile"]["governance_class"] == "topic_decoder"
    assert wealth_code["learning_family"] == "topic_decoder"

    assert symbolic["display_name"] == "八字象义底座"
    assert symbolic["governance_profile"]["governance_class"] == "symbolic_foundation"
    assert symbolic["learning_family"] == "l0_symbolic_basis"
