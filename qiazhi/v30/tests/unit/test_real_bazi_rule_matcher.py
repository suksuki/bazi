from __future__ import annotations

from v30.diagnosis import RULE_MATCHER_VERSION, match_real_bazi_rules, summarize_rule_matches
from v30.runtime import create_smoke_runtime


def test_real_bazi_rule_matcher_matches_runtime_m3_rules() -> None:
    runtime = create_smoke_runtime(
        "rbd-rule-matcher-runtime",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    matches = match_real_bazi_rules(
        feature_evidence=runtime.feature_evidence,
        structure_state=runtime.structure_state,
        model_signal_summary=runtime.question_plan.policy_effect["model_signal_summary"],
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )
    rule_ids = {row.rule_id for row in matches}
    summary = summarize_rule_matches(matches)

    assert len(matches) >= 35
    assert "v30.krp.wealth.domain_path_review" in rule_ids
    assert "v30.krp.career.authority_path_review" in rule_ids
    assert "v30.krp.structure.zhihua_wealth_authority_resource_review" in rule_ids
    assert "v30.krp.useful_god.domain_path_candidate_review" in rule_ids
    assert any(row.domain_targets and "career" in row.domain_targets for row in matches)
    assert any(row.domain_targets and "wealth" in row.domain_targets for row in matches)
    assert any(row.path_ids for row in matches)
    assert all(row.evidence_ids for row in matches)
    assert summary["version"] == RULE_MATCHER_VERSION
    assert summary["match_count"] == len(matches)
    assert summary["claim_ready_count"] > 0


def test_rule_matcher_scores_paths_and_counters() -> None:
    runtime = create_smoke_runtime("rbd-rule-matcher-counter", hidden_factor_user_calibrated=True)
    matches = match_real_bazi_rules(
        feature_evidence=runtime.feature_evidence,
        structure_state=runtime.structure_state,
        model_signal_summary=runtime.question_plan.policy_effect["model_signal_summary"],
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )

    countered = [row for row in matches if row.counter_context_hit]
    path_supported = [row for row in matches if row.path_ids]

    assert countered
    assert path_supported
    assert max(row.match_strength for row in path_supported) >= 0.75
    assert all(0.0 < row.match_strength <= 1.0 for row in matches)


def test_rule_matcher_blocks_fact_mutation_and_overclaim_paths() -> None:
    runtime = create_smoke_runtime("rbd-rule-matcher-blockers")
    matches = match_real_bazi_rules(
        feature_evidence=runtime.feature_evidence,
        structure_state=runtime.structure_state,
        model_signal_summary=runtime.question_plan.policy_effect["model_signal_summary"],
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )

    chart_boundary = next(row for row in matches if row.rule_id == "v30.krp.chart.bound_context_no_rewrite")
    domain_boundary = next(row for row in matches if row.rule_id == "v30.krp.domain_rule.outcome_language_block")

    assert "chart_fact_mutation" in chart_boundary.blocked_claims
    assert "llm_chart_fact_generation" in chart_boundary.blocked_claims
    assert domain_boundary.blocked_claims
    assert all(not row.chart_fact_mutation_requested for row in matches)


def test_rule_matcher_can_limit_sorted_results() -> None:
    runtime = create_smoke_runtime("rbd-rule-matcher-limit")
    matches = match_real_bazi_rules(
        feature_evidence=runtime.feature_evidence,
        structure_state=runtime.structure_state,
        model_signal_summary=runtime.question_plan.policy_effect["model_signal_summary"],
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
        limit=5,
    )

    assert len(matches) == 5
    assert matches == sorted(matches, key=lambda row: (-row.match_strength, row.rule_id))
