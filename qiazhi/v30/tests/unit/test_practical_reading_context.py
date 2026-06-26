from __future__ import annotations

from v30.contracts import BirthInput
from v30.core.chart_context import build_chart_context_from_birth_input
from v30.runtime import create_runtime_from_context


def test_runtime_exposes_ranked_decisions_practical_reading_and_agent_flow() -> None:
    build = build_chart_context_from_birth_input(
        reading_id="practical-reading-ready",
        birth_input=BirthInput(
            input_id="practical-reading-input",
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Asia/Shanghai",
            gender="male",
        ),
    )
    assert build.chart_context is not None
    runtime = create_runtime_from_context(build.chart_context, trace_suffix="test")
    effect = runtime.question_plan.policy_effect

    assert set(effect["ranked_decisions"]) >= {"strength", "structure_pattern", "useful_god"}
    for domain in ("strength", "structure_pattern", "useful_god"):
        decision = effect["ranked_decisions"][domain]
        assert decision["status"] == "ranked_candidate"
        assert decision["primary_candidate"]
        assert decision["alternatives"]
        assert decision["candidate_scores"]
        assert decision["primary_candidate"] in decision["candidate_scores"]
        assert decision["scoring_basis"]["version"] == "v30.ranked_decision_scoring_basis.v1"
        assert decision["scoring_basis"]["day_master"] == "庚"
        assert decision["scoring_basis"]["boundary"] == (
            "ranked_decision_scoring_basis_uses_chart_facts_and_model_signals_not_fixed_verdict"
        )
        assert decision["scoring_basis"]["model_signal_interface_version"] == "v30.model_signal_interface_contract.v1"
        assert decision["scoring_basis"]["model_signal_calibration_profile_version"] == "v30.model_signal_calibration_profile.v1"
        assert decision["scoring_basis"]["model_signal_calibration_flags"]
        assert decision["scoring_basis"]["model_signal_ranked_adjustment_version"] == "v30.model_signal_ranked_decision_adjustments.v1"
        assert decision["scoring_basis"]["model_signal_ranked_adjustment_flags"]
        assert isinstance(decision["scoring_basis"]["model_signal_score_bias"], dict)
        assert "ranked_decisions" in decision["scoring_basis"]["model_signal_allowed_consumers"]
        assert "raw_weight" in decision["scoring_basis"]["model_signal_forbidden_fields"]
        assert decision["scoring_basis"]["root_fact_summary_version"] == "v30.root_vault_fact_summary.v1"
        assert decision["scoring_basis"]["root_vault_boundary"] == "root_vault_summary_records_presence_without_strength_or_useful_god_verdict"
        assert decision["model_signal_summary"]["interface_contract_version"] == "v30.model_signal_interface_contract.v1"
        assert decision["model_signal_summary"]["calibration_profile_version"] == "v30.model_signal_calibration_profile.v1"
        for band in decision["model_signal_summary"]["energy_bands"]:
            assert "raw_weight" not in band
            assert "raw_score" not in band
            assert "energy" not in band
            assert "stability" not in band
            assert "volatility" not in band
    assert set(effect["ranked_decisions"]["strength"]["candidate_scores"]) >= {
        "strong",
        "slightly_strong",
        "balanced",
        "slightly_weak",
        "weak",
    }
    assert set(effect["ranked_decisions"]["structure_pattern"]["candidate_scores"]) >= {
        "ordinary_structure_review",
        "dynamic_structure_review",
        "follow_structure_boundary_review",
        "special_structure_boundary_review",
        "regulation_climate_boundary_review",
        "disputed_structure_review",
    }
    assert set(effect["ranked_decisions"]["useful_god"]["candidate_scores"]) >= {
        "balance_review",
        "resource_or_self_support_review",
        "output_or_wealth_release_review",
        "authority_regulation_review",
        "climate_regulation_review",
    }
    assert effect["practical_reading_context"]["status"] == "ready"
    assert set(effect["practical_reading_context"]["domain_readings"]) >= {
        "career",
        "wealth",
        "relationship",
        "health",
        "timing",
    }
    career = effect["practical_reading_context"]["domain_readings"]["career"]
    assert career["label"] == "事业"
    assert career["version"] == "v30.practical_domain_reading.v2"
    assert career["calculation_basis"]["version"] == "v30.practical_domain_calculation_basis.v1"
    assert career["calculation_basis"]["root_fact_summary_version"] == "v30.root_vault_fact_summary.v1"
    assert career["model_signal_context"]["version"] == "v30.practical_model_signal_context.v1"
    assert career["model_signal_context"]["boundary"] == "practical_reading_consumes_model_signal_bands_not_raw_scores"
    for band in career["model_signal_context"]["top_energy_bands"]:
        assert "energy" not in band
        assert "stability" not in band
        assert "volatility" not in band
        assert "raw_weight" not in band
        assert "energy_band" in band
    assert set(career["ranked_decision_links"]) >= {"strength", "structure_pattern", "useful_god"}
    assert len(career["domain_insights"]) == 3
    assert {row["insight_type"] for row in career["domain_insights"]} == {
        "opportunity_path",
        "pressure_or_risk_path",
        "calibration_path",
    }
    assert len(career["action_steps"]) >= 3
    assert len(career["calibration_prompts"]) >= 2
    assert career["module_trace"]["version"] == "v30.m6_practical_module_trace.v1"
    assert career["module_trace"]["uses_m1_m2_facts"] is True
    assert career["module_trace"]["uses_m3_structure_evidence"] is True
    assert career["module_trace"]["uses_m4_model_signal"] is True
    assert career["module_trace"]["uses_m5_ranked_decisions"] is True
    assert career["module_trace"]["raw_model_score_visible"] is False
    assert career["module_trace"]["chart_fact_mutation_allowed"] is False
    assert career["evidence_ids"]
    assert len(career["explanation_units"]) >= 3
    assert "M5_ranked_decisions" in career["depends_on_modules"]
    assert "must_not_expose_raw_model_scores" in career["boundary_conditions"]
    assert "certain_promotion_or_job_loss_year" in career["blocked_claims"]
    assert career["customer_takeaway"]
    assert career["action_prompt"]
    assert career["priority_score"] > 0
    assert career["quality_contract"]["boundary"] == "practical_reading_quality_trains_expression_not_chart_facts"
    timing = effect["practical_reading_context"]["domain_readings"]["timing"]
    assert timing["version"] == "v30.practical_domain_reading.v2"
    assert timing["reading_boundary"] == "timing_reading_is_stage_review_not_fixed_event_prediction"
    assert len(timing["domain_insights"]) == 3
    assert timing["module_trace"]["uses_m5_ranked_decisions"] is True
    assert "fixed_event_prediction" in timing["blocked_claims"]
    assert all("priority_score" in row for row in effect["practical_reading_context"]["question_gaps"])
    assert effect["agent_question_flow"]["next_stage"] in {
        "event_year_discovery",
        "domain_gap_followup",
        "final_reading_clarification",
    }
    assert any(row.question_id == "q_v30_practical_domain_focus" for row in runtime.question_anchors)
