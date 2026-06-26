from __future__ import annotations

from v30.knowledge import KRP_LIBRARY_PACK_ID, match_krp_library_units, summarize_krp_library_units
from v30.runtime import create_smoke_runtime


def test_krp_library_units_match_runtime_evidence_supports() -> None:
    runtime = create_smoke_runtime("v30-krp-library-test")
    units = match_krp_library_units(runtime.feature_evidence)
    unit_ids = {str(row["unit_id"]) for row in units}
    assert "v30.krp.ten_god.visibility_context" in unit_ids
    assert "v30.krp.useful_god.candidate_gate" in unit_ids
    assert "v30.krp.chart.bound_context_no_rewrite" in unit_ids
    assert "v30.krp.chart.output_fact_basis_required" in unit_ids
    assert "v30.krp.element.balance_not_strength_verdict" in unit_ids
    assert "v30.krp.element.seasonal_counterforce_review" in unit_ids
    assert "v30.krp.foundation.m1_m2_m3_chain" in unit_ids
    assert "v30.krp.foundation.module_handoff_trace" in unit_ids
    assert "v30.krp.foundation.training_read_only_boundary" in unit_ids
    assert "v30.krp.romance.private_fact_boundary" in unit_ids
    assert "v30.krp.romance.marker_context_review" in unit_ids
    assert "v30.krp.romance.conflict_alignment_review" in unit_ids
    assert "v30.krp.domain_rule.subfamily_gate" in unit_ids
    assert "v30.krp.domain_rule.outcome_language_block" in unit_ids
    assert "v30.krp.domain_rule.cross_domain_bridge_review" in unit_ids
    assert "v30.krp.rule_counterevidence.original_trace_required" in unit_ids
    assert "v30.krp.rule_counterevidence.policy_override_block" in unit_ids
    assert "v30.krp.rule_counterevidence.silent_override_block" in unit_ids
    assert "v30.krp.structure.pattern_success_failure_rescue_review" in unit_ids
    assert "v30.krp.time_context.explicit_time_layer_required" in unit_ids
    assert "v30.krp.structure.dynamic_path" in unit_ids
    assert "v30.krp.time_context.missing_boundary" in unit_ids
    assert "v30.krp.chart.context_bound" in unit_ids
    assert "v30.krp.element.day_master_context" in unit_ids
    assert "v30.krp.element.balance_review" in unit_ids
    assert "v30.krp.branch_relation.dynamic_review" in unit_ids
    assert "v30.krp.ten_god.hidden_stem_context" in unit_ids
    assert "v30.krp.ten_god.output_expression_review" in unit_ids
    assert "v30.krp.ten_god.self_competition_review" in unit_ids
    assert "v30.krp.branch_relation.conflict_family" in unit_ids
    assert "v30.krp.branch_relation.alignment_family" in unit_ids
    assert "v30.krp.strength.seasonal_review" in unit_ids
    assert "v30.krp.structure.pattern_candidate_review" in unit_ids
    assert "v30.krp.useful_god.family_candidate_review" in unit_ids
    assert "v30.krp.structure.path_resolution_review" in unit_ids
    assert "v30.krp.wealth.domain_path_review" in unit_ids
    assert "v30.krp.wealth.competition_path_review" in unit_ids
    assert "v30.krp.wealth.output_generation_path_review" in unit_ids
    assert "v30.krp.wealth.authority_bridge_path_review" in unit_ids
    assert "v30.krp.career.authority_path_review" in unit_ids
    assert "v30.krp.career.authority_pressure_path_review" in unit_ids
    assert "v30.krp.career.resource_resolution_path_review" in unit_ids
    assert "v30.krp.relationship.relation_path_review" in unit_ids
    assert "v30.krp.relationship.conflict_path_review" in unit_ids
    assert "v30.krp.relationship.alignment_path_review" in unit_ids
    assert "v30.krp.relationship.marker_path_review" in unit_ids
    assert "v30.krp.health.element_imbalance_review" in unit_ids
    assert "v30.krp.health.excess_review" in unit_ids
    assert "v30.krp.health.conflict_pressure_review" in unit_ids
    assert "v30.krp.useful_god.domain_path_candidate_review" in unit_ids
    assert "v30.krp.structure.tongguan_resource_mediator_review" in unit_ids
    assert "v30.krp.structure.tongguan_output_wealth_bridge_review" in unit_ids
    assert "v30.krp.structure.zhihua_output_authority_review" in unit_ids
    assert "v30.krp.structure.zhihua_wealth_authority_resource_review" in unit_ids
    assert len(units) >= 68
    assert all(row["matched_supports"] for row in units)
    assert all(row["pack_id"] == KRP_LIBRARY_PACK_ID for row in units)
    assert all(row["pack_version"] for row in units)
    assert any(row["portrait_dimensions"] for row in units)
    assert any(row["training_tags"] for row in units)


def test_krp_library_units_consume_policy_weights() -> None:
    runtime = create_smoke_runtime(
        "v30-krp-library-weight-test",
        policy_payload_overrides={
            "question_policy": {
                "krp_unit_weights": {
                    "hidden_factor": 1.2,
                    "*": 1.0,
                }
            }
        },
    )
    units = runtime.question_plan.policy_effect["krp_library_units"]
    hidden_unit = next(row for row in units if row["domain"] == "hidden_factor")
    assert hidden_unit["score"] > 0.8
    assert "krp_policy_weight:1.2" in hidden_unit["score_reasons"]


def test_krp_library_summary_exposes_pack_and_portrait_metadata() -> None:
    runtime = create_smoke_runtime("v30-krp-library-summary-test")
    summary = runtime.question_plan.policy_effect["krp_library_summary"]
    assert summary == summarize_krp_library_units(runtime.question_plan.policy_effect["krp_library_units"])
    assert summary["unit_count"] >= 68
    assert KRP_LIBRARY_PACK_ID in summary["pack_ids"]
    assert summary["boundary_count"] == summary["unit_count"]
    assert "hidden_factor_dialogue_required" in summary["portrait_tags"]
    assert "branch_conflict_family" in summary["portrait_tags"]
    assert "output_expression_context" in summary["portrait_tags"]
    assert "seasonal_strength_review" in summary["portrait_tags"]
    assert "path_resolution_candidate" in summary["portrait_tags"]
    assert "wealth_rule_candidate" in summary["portrait_tags"]
    assert "career_rule_candidate" in summary["portrait_tags"]
    assert "relationship_rule_candidate" in summary["portrait_tags"]
    assert "health_rule_candidate" in summary["portrait_tags"]
    assert "wealth_output_generation_candidate" in summary["portrait_tags"]
    assert "career_authority_pressure_candidate" in summary["portrait_tags"]
    assert "relationship_conflict_candidate" in summary["portrait_tags"]
    assert "health_conflict_pressure_candidate" in summary["portrait_tags"]
    assert "chart_read_only_boundary" in summary["portrait_tags"]
    assert "domain_subfamily_evidence_required" in summary["portrait_tags"]
    assert "romance_not_private_fact" in summary["portrait_tags"]
    assert "silent_override_blocked" in summary["portrait_tags"]
    assert "pattern_rescue_counterforce_review" in summary["portrait_tags"]
    assert "explicit_time_layer_required" in summary["portrait_tags"]
    assert "tongguan_resource_candidate" in summary["portrait_tags"]
    assert "zhihua_output_authority_candidate" in summary["portrait_tags"]
    assert "latent_pattern" in summary["portrait_dimensions"]
    assert "branch_conflict" in summary["portrait_dimensions"]
    assert "strength_review" in summary["portrait_dimensions"]
    assert "path_resolution" in summary["portrait_dimensions"]
    assert "tongguan_resource_mediator" in summary["portrait_dimensions"]
    assert "zhihua_wealth_authority_resource" in summary["portrait_dimensions"]
    assert "core_calculation_chain" in summary["portrait_dimensions"]
    assert "domain_rule_subfamily_gate" in summary["portrait_dimensions"]
    assert "romance_marker_context" in summary["portrait_dimensions"]
    assert "silent_override_boundary" in summary["portrait_dimensions"]
    assert "pattern_success_failure_rescue" in summary["portrait_dimensions"]
    assert "time_layer_boundary" in summary["portrait_dimensions"]
    assert "discover_hidden_factor_amplifier" in summary["question_hooks"]
    assert "mechanism.hidden_factor_dialogue_probe" in summary["mechanism_hooks"]
    assert summary["source_family_count"] >= 6
    assert set(summary["source_family_ids"]) >= {
        "v30.source.zi_ping_pattern_month_command",
        "v30.source.san_ming_tong_hui_system_catalog",
        "v30.source.yuan_hai_zi_ping_pattern_catalog",
        "v30.source.di_tian_sui_flow_mechanism",
        "v30.source.qiong_tong_bao_jian_climate_review",
        "v30.source.shen_feng_tong_kao_disease_medicine",
    }
    assert "v30.m3.reference.v20_expanded_knowledge_units" in summary["reference_asset_ids"]
    assert "v30.m3.reference.v20_structure_dynamics_graph_v2" in summary["reference_asset_ids"]


def test_krp_library_units_expose_m3_source_backed_v20_migrations() -> None:
    runtime = create_smoke_runtime("v30-krp-source-migration-test")
    units = runtime.question_plan.policy_effect["krp_library_units"]
    unit_by_id = {str(row["unit_id"]): row for row in units}
    for unit_id in (
        "v30.krp.source.month_command.pattern_gate",
        "v30.krp.source.wang_xiang_strength_review",
        "v30.krp.source.tiaohou.climate_review",
        "v30.krp.source.bingyao.blockage_review",
        "v30.krp.source.element.flow_transform",
        "v30.krp.source.branch.arbitration",
        "v30.krp.source.ten_god.role_set",
        "v30.krp.source.palace.position_boundary",
    ):
        assert unit_id in unit_by_id
        assert unit_by_id[unit_id]["source_family_ids"]
    assert all(row["source_family_ids"] for row in units)


def test_krp_library_units_preserve_counterevidence_trace() -> None:
    runtime = create_smoke_runtime(
        "v30-krp-library-counter-test",
        hidden_factor_user_calibrated=True,
    )
    units = runtime.question_plan.policy_effect["krp_library_units"]
    unit_ids = {str(row["unit_id"]) for row in units}
    assert "v30.krp.rule.counterevidence.trace" in unit_ids
    assert "v30.krp.hidden_factor.user_calibrated_counter" in unit_ids
