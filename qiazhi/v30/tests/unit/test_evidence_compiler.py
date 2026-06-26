from __future__ import annotations

from v30.core.chart_context import build_chart_context_from_displays
from v30.evidence import compile_feature_evidence
from v30.contracts import FeatureEvidence
from tests.fixtures.core_cases import CORE_CASES


def test_compile_feature_evidence_from_chart_context() -> None:
    case = CORE_CASES["useful_god_candidate_gate"]
    context = build_chart_context_from_displays(**{key: case[key] for key in ("reading_id", "year", "month", "day", "hour")})
    rows = compile_feature_evidence(context)
    domains = {row.domain for row in rows}
    assert case["expect"]["domains"] <= domains
    assert all(row.source == context.context_id for row in rows)
    assert all(row.evidence_id.startswith(context.context_id) for row in rows)


def test_compile_feature_evidence_marks_ten_god_and_branch_families() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-family-markers",
        year="甲子",
        month="乙丑",
        day="甲寅",
        hour="丁卯",
    )
    rows = compile_feature_evidence(context)
    visible = next(row for row in rows if row.domain == "ten_god" and row.kind == "visibility")
    hidden = next(row for row in rows if row.domain == "ten_god" and row.kind == "hidden_stem")
    branch = next(row for row in rows if row.domain == "branch_relation")
    assert "ten_god_family:self" in visible.supports
    assert "ten_god_family:output" in visible.supports
    assert any(item.startswith("hidden_ten_god_family:") for item in hidden.supports)
    assert any(item.startswith("branch_relation:") for item in branch.supports)
    assert "branch_conflict_family:punishment" in branch.supports
    assert "branch_alignment_family:harmony" in branch.supports


def test_compile_feature_evidence_marks_strength_pattern_candidates() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-strength-pattern",
        year="甲子",
        month="乙丑",
        day="甲寅",
        hour="丁卯",
    )
    rows = compile_feature_evidence(context)
    strength = next(row for row in rows if row.domain == "structure_pattern")
    assert strength.kind == "strength_pattern_review"
    assert "strength_review_candidate" in strength.supports
    assert "structure_pattern_candidate" in strength.supports
    assert any(item.startswith("season_element:") for item in strength.supports)
    assert any(item.startswith("useful_god_candidate_family:") for item in strength.supports)
    assert "fixed_strength_verdict" in strength.weakens
    assert "fixed_geju_verdict" in strength.weakens


def test_compile_feature_evidence_marks_m3_source_backed_features() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-m3-source-backed",
        year="甲子",
        month="乙丑",
        day="甲寅",
        hour="丁卯",
    )
    rows = compile_feature_evidence(context)
    supports = {support for row in rows for support in row.supports}
    assert "month_command_review" in supports
    assert "wang_xiang_xiu_qiu_si_review" in supports
    assert "climate_regulation_review" in supports
    assert "tiaohou_candidate_path" in supports
    assert "bingyao_blockage_review" in supports
    assert "bingyao_remedy_candidate_path" in supports
    assert "element_flow_transform_review" in supports
    assert "tongguan_candidate_path" in supports
    assert "zhihua_candidate_path" in supports
    assert "ten_god_role_set_review" in supports
    assert "branch_relation_arbitration_review" in supports


def test_compile_feature_evidence_marks_domain_rule_candidates() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-domain-rule",
        year="甲子",
        month="乙丑",
        day="甲寅",
        hour="丁卯",
    )
    rows = compile_feature_evidence(context)
    domain_rule = next(row for row in rows if row.domain == "domain_rule")
    assert domain_rule.kind == "domain_path_review"
    assert "domain_rule_review_candidate" in domain_rule.supports
    assert "domain_rule_family:wealth_pressure" in domain_rule.supports
    assert "domain_rule_family:wealth_output_generation_path" in domain_rule.supports
    assert "domain_rule_family:wealth_authority_bridge_path" in domain_rule.supports
    assert "domain_rule_family:career_authority_path" in domain_rule.supports
    assert "domain_rule_family:career_authority_pressure_path" in domain_rule.supports
    assert "domain_rule_family:career_resource_resolution_path" in domain_rule.supports
    assert "domain_rule_family:relationship_relation_path" in domain_rule.supports
    assert "domain_rule_family:relationship_conflict_path" in domain_rule.supports
    assert "domain_rule_family:relationship_alignment_review_path" in domain_rule.supports
    assert "domain_rule_family:health_element_imbalance_review" in domain_rule.supports
    assert "domain_rule_family:health_element_excess_review" in domain_rule.supports
    assert "domain_rule_family:health_conflict_pressure_review" in domain_rule.supports
    assert "fixed_health_outcome_claim" in domain_rule.weakens


def test_compile_feature_evidence_marks_missing_time_boundary() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-time-missing",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    rows = compile_feature_evidence(context)
    missing = next(row for row in rows if row.domain == "time_context")
    assert missing.kind == "missing_requirement"
    assert "timing_claim" in missing.weakens
    assert missing.boundary == "no_timing_prediction_without_explicit_time_layer"


def test_compile_feature_evidence_marks_explicit_time_layers() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-time-ready",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
        luck_pillar="庚午",
        flow_year_pillar="辛未",
    )
    rows = compile_feature_evidence(context)
    time = next(row for row in rows if row.domain == "time_context")
    assert time.kind == "explicit_layer"
    assert "time_activation_review" in time.supports
    assert "luck" in time.label
    assert "flow_year" in time.label


def test_useful_god_evidence_is_candidate_gate_only() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-useful-god",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    rows = compile_feature_evidence(context)
    gate = next(row for row in rows if row.domain == "useful_god")
    assert gate.kind == "evidence_gate"
    assert "fixed_useful_god_verdict" in gate.weakens
    assert "candidate_paths_only" in gate.boundary


def test_rule_evidence_is_compiled_from_feature_evidence() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-rule-runtime",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    rows = compile_feature_evidence(context)
    rule_rows = [row for row in rows if row.domain == "rule"]
    assert {row.kind for row in rule_rows} >= {"time_context", "useful_god", "hidden_factor", "branch_relation"}
    assert any("rule_time_boundary" in row.supports for row in rule_rows)
    assert any("rule_hidden_factor_dialogue_boundary" in row.supports for row in rule_rows)
    assert any("rule_month_command_pattern_gate" in row.supports for row in rule_rows)
    assert any("rule_tiaohou_candidate_gate" in row.supports for row in rule_rows)
    assert any("rule_bingyao_review_gate" in row.supports for row in rule_rows)
    assert any("rule_domain_outcome_boundary" in row.supports for row in rule_rows)
    assert any("rule_branch_arbitration_gate" in row.supports for row in rule_rows)
    assert all(row.boundary and row.boundary.startswith("rule_boundary_") for row in rule_rows)


def test_rule_policy_weights_rule_evidence_confidence_without_changing_chart_facts() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-rule-policy",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    baseline = compile_feature_evidence(context)
    weighted = compile_feature_evidence(
        context,
        {
            "weights": {
                "rule_weights": {"v30.rule.hidden_factor.requires_dialogue": 1.25},
            }
        },
    )
    baseline_hidden = next(row for row in baseline if row.domain == "rule" and row.kind == "hidden_factor")
    weighted_hidden = next(row for row in weighted if row.domain == "rule" and row.kind == "hidden_factor")
    assert weighted_hidden.confidence > baseline_hidden.confidence
    assert "rule_policy_weight:1.25" in weighted_hidden.supports
    assert [row.label for row in baseline if row.domain == "chart"] == [
        row.label for row in weighted if row.domain == "chart"
    ]


def test_rule_evidence_marks_counterevidence_for_explicit_time_layer() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-rule-counter-time",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
        luck_pillar="庚午",
    )
    rows = compile_feature_evidence(context)
    time_rule = next(row for row in rows if row.domain == "rule" and row.kind == "time_context")
    assert "rule_decision_state:countered" in time_rule.supports
    assert any(item.startswith("counter_evidence:") for item in time_rule.supports)
    assert any(item.startswith("countered_by:") for item in time_rule.weakens)


def test_rule_evidence_marks_hidden_factor_feedback_counterevidence() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-hidden-feedback",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    feedback = FeatureEvidence(
        evidence_id=f"{context.context_id}:feedback:hidden_factor_user_calibrated",
        domain="feedback",
        kind="hidden_factor_calibration",
        label="hidden_factor_user_calibrated:true",
        source=context.context_id,
        confidence=0.92,
        supports=["hidden_factor_user_calibrated", "special_event_confirmed"],
        boundary="feedback_evidence_counters_dialogue_boundary_not_chart_fact",
    )
    rows = compile_feature_evidence(context, supplemental_evidence=[feedback])
    hidden_rule = next(row for row in rows if row.domain == "rule" and row.kind == "hidden_factor")
    assert "rule_decision_state:countered" in hidden_rule.supports
    assert f"counter_evidence:{feedback.evidence_id}" in hidden_rule.supports
    assert "deterministic_hidden_factor_claim" in hidden_rule.weakens


def test_rule_evidence_marks_useful_god_feedback_counterevidence() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-useful-feedback",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    feedback = FeatureEvidence(
        evidence_id=f"{context.context_id}:feedback:useful_god_path_resolved",
        domain="feedback",
        kind="useful_god_resolution",
        label="useful_god_path_resolved:true",
        source=context.context_id,
        confidence=0.9,
        supports=["fixed_useful_god_verdict", "useful_god_path_resolved"],
        boundary="feedback_evidence_counters_candidate_gate_not_chart_fact",
    )
    rows = compile_feature_evidence(context, supplemental_evidence=[feedback])
    useful_rule = next(row for row in rows if row.domain == "rule" and row.kind == "useful_god")
    assert "rule_decision_state:countered" in useful_rule.supports
    assert f"counter_evidence:{feedback.evidence_id}" in useful_rule.supports


def test_rule_evidence_marks_branch_relation_feedback_counterevidence() -> None:
    context = build_chart_context_from_displays(
        reading_id="evidence-branch-feedback",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    feedback = FeatureEvidence(
        evidence_id=f"{context.context_id}:feedback:branch_single_factor_confirmed",
        domain="feedback",
        kind="branch_relation_single_factor",
        label="branch_single_factor_confirmed:true",
        source=context.context_id,
        confidence=0.86,
        supports=["single_factor_reading"],
        boundary="feedback_evidence_counters_dynamic_review_gate_not_chart_fact",
    )
    rows = compile_feature_evidence(context, supplemental_evidence=[feedback])
    branch_rule = next(row for row in rows if row.domain == "rule" and row.kind == "branch_relation")
    assert "rule_decision_state:countered" in branch_rule.supports
    assert f"counter_evidence:{feedback.evidence_id}" in branch_rule.supports
