from __future__ import annotations

from v30.validation import extract_training_signals, run_synthetic_tier


def test_extract_training_signals_from_synthetic_all() -> None:
    result = run_synthetic_tier("all")
    signals = extract_training_signals(result)
    signal_ids = {signal.signal_id for signal in signals}
    assert "v30.training_signal.krp_unit_coverage" in signal_ids
    assert "v30.training_signal.m3_core_spine_coverage" in signal_ids
    assert "v30.training_signal.per_unit_parameter_tuning" in signal_ids
    assert "v30.training_signal.macro_dimension_coverage" in signal_ids
    assert "v30.training_signal.portrait_projection_coverage" in signal_ids
    assert "v30.training_signal.portrait_projection_view_coverage" in signal_ids
    assert "v30.training_signal.role_locale_client_projection_coverage" in signal_ids
    assert "v30.training_signal.question_graph_edge_coverage" in signal_ids
    assert "v30.training_signal.question_dialogue_outcome" in signal_ids
    assert "v30.training_signal.interaction_state_machine" in signal_ids
    assert "v30.training_signal.interaction_loop_quality" in signal_ids
    assert "v30.training_signal.adaptive_question_replay" in signal_ids
    assert "v30.training_signal.central_brain_route_coverage" in signal_ids
    assert "v30.training_signal.central_brain_judge_quality" in signal_ids
    assert "v30.training_signal.central_brain_synthesis_blueprint_quality" in signal_ids
    assert "v30.training_signal.expression_quality" in signal_ids
    assert "v30.training_signal.llm_output_contract_quality" in signal_ids
    assert "v30.training_signal.structure_dynamic_competition" in signal_ids
    assert "v30.training_signal.hidden_factor_event_alignment" in signal_ids
    assert "v30.training_signal.birth_chart_conversion_boundary" in signal_ids
    assert "v30.training_signal.m1_m2_base_fact_contract" in signal_ids
    assert "v30.training_signal.luck_cycle_alignment" in signal_ids
    assert "v30.training_signal.flow_timing_activation" in signal_ids
    assert "v30.training_signal.six_pillar_context_coverage" in signal_ids
    assert "v30.training_signal.ten_god_energy_fusion" in signal_ids
    assert "v30.training_signal.strength_structure_decision" in signal_ids
    assert "v30.training_signal.ranked_decision_fusion" in signal_ids
    assert "v30.training_signal.m5_weight_replay" in signal_ids
    assert "v30.training_signal.practical_reading_quality" in signal_ids
    assert "v30.training_signal.agent_question_flow_quality" in signal_ids
    assert "v30.training_signal.high_value_question_quality" in signal_ids
    assert "v30.training_signal.question_model_signal_personalization" in signal_ids
    assert "v30.training_signal.real_case_feedback_alignment" in signal_ids
    assert "v30.training_signal.real_case_calibration_pack" in signal_ids
    krp_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.krp_unit_coverage")
    structure_signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.structure_dynamic_competition"
    )
    assert krp_signal.payload["unit_count"] >= 35
    assert krp_signal.strength > 0.8
    m3_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.m3_core_spine_coverage")
    assert m3_signal.domain == "m3_core_spine"
    assert m3_signal.payload["source_family_count"] >= 6
    assert "v30.source.qiong_tong_bao_jian_climate_review" in m3_signal.payload["source_family_ids"]
    assert "v30.source.shen_feng_tong_kao_disease_medicine" in m3_signal.payload["source_family_ids"]
    assert "v30.m3.reference.v20_expanded_knowledge_units" in m3_signal.payload["reference_asset_ids"]
    assert m3_signal.payload["dynamic_case_count"] > 0
    assert m3_signal.payload["completion_summary_version"] == "v30.m3_completion_summary.v1"
    assert m3_signal.payload["completion_summary_count"] > 0
    assert m3_signal.payload["completion_ready_count"] >= 80
    assert m3_signal.payload["average_completion_coverage"] >= 0.95
    assert m3_signal.payload["m4_support_ready_count"] >= 80
    assert m3_signal.payload["m5_support_ready_count"] >= 80
    assert m3_signal.payload["m6_support_ready_count"] >= 80
    assert m3_signal.payload["conclusion_engine_count"] == 0
    assert m3_signal.payload["chart_fact_mutation_allowed_count"] == 0
    assert m3_signal.payload["boundary"] == "m3_core_spine_trains_source_rule_path_weights_not_chart_facts"
    per_unit_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.per_unit_parameter_tuning")
    assert per_unit_signal.domain == "policy_tuning"
    assert per_unit_signal.payload["unit_count"] >= 42
    assert per_unit_signal.payload["rule_weights"]["v30.rule.hidden_factor.requires_dialogue"] > 1.0
    assert per_unit_signal.payload["domain_weights"]["structure_dynamic"] > 1.0
    assert per_unit_signal.payload["mechanism_weights"]["mechanism.useful_god_candidate_gate"] > 1.0
    macro_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.macro_dimension_coverage")
    assert macro_signal.payload["domain_count"] >= 7
    assert set(macro_signal.payload["domains"]) >= {"wealth", "career", "relationship", "romance", "health"}
    assert macro_signal.strength == 1.0
    portrait_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.portrait_projection_coverage")
    assert portrait_signal.payload["domain_count"] >= 6
    assert set(portrait_signal.payload["domains"]) >= {"wealth", "career", "relationship", "romance", "health"}
    assert portrait_signal.strength == 1.0
    portrait_view_signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.portrait_projection_view_coverage"
    )
    assert portrait_view_signal.payload["domain_count"] >= 6
    assert set(portrait_view_signal.payload["roles"]) >= {"user", "guest", "admin"}
    assert portrait_view_signal.payload["guest_hidden_factor_view_count"] == 0
    assert portrait_view_signal.payload["admin_hidden_factor_view_count"] > 0
    projection_signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.role_locale_client_projection_coverage"
    )
    assert projection_signal.domain == "presentation"
    assert set(projection_signal.payload["roles"]) >= {"guest", "user", "practitioner", "analyst", "admin", "lab"}
    assert set(projection_signal.payload["locales"]) == {"zh", "en", "ko"}
    assert set(projection_signal.payload["clients"]) >= {"web", "mobile", "admin", "lab"}
    assert projection_signal.payload["combination_count"] >= 72
    assert "mobile" in projection_signal.payload["compact_clients"]
    assert "admin" in projection_signal.payload["diagnostic_roles"]
    assert projection_signal.payload["boundary"] == "role_locale_client_projection_trains_presentation_policy_not_chart_facts"
    api_projection_signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.api_projection_contract"
    )
    assert api_projection_signal.domain == "presentation"
    assert api_projection_signal.payload["contract_observation_count"] >= 30
    assert api_projection_signal.payload["user_leak_pass_count"] >= 30
    assert api_projection_signal.payload["admin_diagnostic_ready_count"] >= 30
    assert api_projection_signal.payload["core_first_count"] >= 30
    assert api_projection_signal.payload["core_first_policy_count"] >= 30
    assert api_projection_signal.payload["customer_surface_contract_ready_count"] >= 30
    assert api_projection_signal.payload["additive_policy_count"] >= 30
    assert api_projection_signal.payload["forbidden_field_policy_count"] >= 30
    assert {"core_bazi_reading", "domain_cards", "internal_next_question_id", "actor_context", "llm_runtime_status"} <= set(
        api_projection_signal.payload["required_additive_fields"]
    )
    assert api_projection_signal.payload["boundary"] == "api_projection_contract_trains_visibility_policy_not_chart_facts"
    brain_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.central_brain_route_coverage")
    assert set(brain_signal.payload["route_domains"]) >= {"question_intelligence", "expression", "hidden_factor"}
    assert brain_signal.strength == 1.0
    brain_judge_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.central_brain_judge_quality")
    assert brain_judge_signal.domain == "central_brain"
    assert brain_judge_signal.payload["observed_count"] >= 1
    assert brain_judge_signal.payload["accepted_count"] >= 1
    assert brain_judge_signal.payload["average_quality_score"] >= 0.58
    assert brain_judge_signal.payload["can_tune_final_synthesis_quality"] is True
    assert brain_judge_signal.payload["can_tune_template_risk_penalty"] is True
    assert brain_judge_signal.payload["can_tune_chart_facts"] is False
    assert brain_judge_signal.payload["boundary"] == "central_brain_judge_quality_trains_synthesis_policy_not_chart_facts"
    blueprint_signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.central_brain_synthesis_blueprint_quality"
    )
    assert blueprint_signal.domain == "central_brain"
    assert blueprint_signal.payload["observed_count"] >= 1
    assert blueprint_signal.payload["decision_focus_coverage"] >= 0.9
    assert blueprint_signal.payload["action_step_coverage"] >= 0.9
    assert blueprint_signal.payload["risk_boundary_coverage"] >= 0.9
    assert blueprint_signal.payload["chart_fact_mutation_allowed_count"] == 0
    assert blueprint_signal.payload["can_tune_synthesis_blueprint"] is True
    assert blueprint_signal.payload["can_tune_chart_facts"] is False
    assert blueprint_signal.payload["boundary"] == "central_brain_synthesis_blueprint_quality_trains_synthesis_policy_not_chart_facts"
    expression_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.expression_quality")
    assert expression_signal.domain == "expression"
    assert expression_signal.payload["min_bazi_term_count"] >= 2
    assert expression_signal.payload["forbidden_token_hits"] == []
    assert expression_signal.payload["missing_boundary_cases"] == []
    assert "calm_bazi_consultation" in expression_signal.payload["voices"]
    assert expression_signal.strength > 0.5
    llm_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.llm_output_contract_quality")
    assert llm_signal.domain == "llm"
    assert "answer_draft" in llm_signal.payload["task_types"]
    assert "question_explanation" in llm_signal.payload["task_types"]
    assert "synthetic_case_draft" in llm_signal.payload["task_types"]
    assert "failure_cluster_summary" in llm_signal.payload["task_types"]
    assert llm_signal.payload["task_coverage"] == 1.0
    assert llm_signal.payload["drift_failures"] == []
    bazi_llm_result = run_synthetic_tier("bazi_llm_acceptance")
    bazi_llm_signals = extract_training_signals(bazi_llm_result)
    bazi_llm_signal = next(
        signal for signal in bazi_llm_signals
        if signal.signal_id == "v30.training_signal.bazi_llm_output_acceptance_quality"
    )
    assert bazi_llm_signal.domain == "llm"
    assert bazi_llm_signal.strength == 1.0
    assert bazi_llm_signal.payload["accepted_count"] >= 2
    assert bazi_llm_signal.payload["rejected_count"] >= 3
    assert bazi_llm_signal.payload["schema_rejected_count"] >= 1
    assert bazi_llm_signal.payload["role_failure_count"] >= 1
    assert bazi_llm_signal.payload["drift_rejected_count"] >= 1
    assert bazi_llm_signal.payload["can_tune_expression"] is True
    assert bazi_llm_signal.payload["can_tune_question_strategy"] is True
    assert bazi_llm_signal.payload["can_tune_chart_facts"] is False
    assert bazi_llm_signal.payload["chart_fact_mutation_allowed_count"] == 0
    outcome_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.question_dialogue_outcome")
    assert outcome_signal.domain == "question_intelligence"
    assert outcome_signal.payload["outcome_count"] >= 1
    assert "hidden_factor" in outcome_signal.payload["topics"]
    assert outcome_signal.payload["average_confidence"] > 0
    interaction_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.interaction_state_machine")
    assert interaction_signal.domain == "question_intelligence"
    assert "initial_question_selection" in interaction_signal.payload["stages"]
    assert interaction_signal.payload["visible_next_question_count"] > 0
    assert interaction_signal.payload["internal_next_question_count"] > 0
    assert interaction_signal.payload["visible_internal_split_count"] > 0
    assert interaction_signal.payload["boundary"] == "interaction_state_machine_trains_followup_policy_not_chart_facts"
    loop_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.interaction_loop_quality")
    assert loop_signal.domain == "question_intelligence"
    assert loop_signal.payload["visible_surface_next_question_count"] > 0
    assert loop_signal.payload["internal_next_question_surface_leak_count"] == 0
    assert loop_signal.payload["boundary"] == "interaction_loop_quality_trains_presentation_and_question_strategy_not_chart_facts"
    adaptive_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.adaptive_question_replay")
    assert adaptive_signal.domain == "question_intelligence"
    assert adaptive_signal.signal_type == "trace_replay_policy_candidate_source"
    assert adaptive_signal.payload["decision_count"] >= result.case_count
    assert adaptive_signal.payload["alignment_coverage"] > 0
    assert "time_context" in adaptive_signal.payload["topics"]
    assert "context_first_question_strategy" in adaptive_signal.payload["question_strategies"]
    assert adaptive_signal.payload["boundary"] == "adaptive_question_replay_trains_policy_candidates_not_chart_facts"
    birth_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.birth_chart_conversion_boundary")
    assert birth_signal.domain == "core_calculation"
    assert birth_signal.payload["ready_count"] >= 1
    assert birth_signal.payload["blocked_count"] >= 2
    assert birth_signal.payload["no_fake_fact_count"] >= 2
    assert "late_zi_hour_boundary_recorded" in birth_signal.payload["boundary_flags"]
    assert birth_signal.payload["boundary"] == "birth_chart_conversion_signal_validates_deterministic_conversion_not_chart_fact"
    base_fact_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.m1_m2_base_fact_contract")
    assert base_fact_signal.domain == "core_calculation"
    assert base_fact_signal.payload["ready_count"] >= 10
    assert base_fact_signal.payload["deterministic_count"] >= 10
    assert base_fact_signal.payload["non_deterministic_source_count"] == 0
    assert base_fact_signal.payload["required_key_coverage"] == 1.0
    assert base_fact_signal.payload["hidden_ready_count"] >= 10
    assert base_fact_signal.payload["explanation_ready_count"] >= 10
    assert base_fact_signal.payload["root_fact_ready_count"] >= 10
    assert base_fact_signal.payload["completion_summary_version"] == "v30.m1_m2_completion_summary.v1"
    assert base_fact_signal.payload["completion_ready_count"] >= 10
    assert base_fact_signal.payload["downstream_consumption_ready_count"] >= 10
    assert base_fact_signal.payload["categories"]["solar"] is True
    assert base_fact_signal.payload["categories"]["lunar"] is True
    assert base_fact_signal.payload["categories"]["leap_month_lunar"] is True
    assert base_fact_signal.payload["categories"]["true_solar"] is True
    assert base_fact_signal.payload["categories"]["unknown_gender"] is True
    assert base_fact_signal.payload["boundary"] == "m1_m2_base_fact_contract_trains_validation_coverage_not_chart_facts"
    luck_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.luck_cycle_alignment")
    assert luck_signal.payload["ready_count"] >= 1
    six_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.six_pillar_context_coverage")
    assert six_signal.payload["average_pillar_count"] >= 6
    fusion_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.ten_god_energy_fusion")
    assert fusion_signal.domain == "model_signal"
    assert fusion_signal.payload["ready_count"] >= 1
    assert fusion_signal.payload["raw_score_hidden_count"] >= fusion_signal.payload["ready_count"]
    assert set(fusion_signal.payload["ranked_decision_domains"]) >= {"strength", "structure_pattern", "useful_god"}
    assert set(fusion_signal.payload["calibration_family_coverage"]) >= {
        "self",
        "resource",
        "output",
        "wealth",
        "authority",
    }
    assert fusion_signal.payload["calibration_case_count"] >= 5
    assert fusion_signal.payload["real_case_replay_count"] >= 5
    assert fusion_signal.payload["real_case_replay_interface_ready_count"] >= 5
    assert set(fusion_signal.payload["real_case_replay_family_coverage"]) >= {
        "self",
        "resource",
        "output",
        "wealth",
        "authority",
    }
    assert fusion_signal.payload["energy_band_counts"]["high"] >= 1
    assert fusion_signal.payload["stability_band_counts"]["low"] >= 1
    assert fusion_signal.payload["volatility_band_counts"]["high"] >= 1
    assert fusion_signal.payload["boundary"] == "ten_god_energy_fusion_trains_model_weights_not_chart_facts"
    ranked_fusion_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.ranked_decision_fusion")
    assert ranked_fusion_signal.domain == "ranked_decision"
    assert set(ranked_fusion_signal.payload["fused_domains"]) >= {"strength", "structure_pattern", "useful_god"}
    assert ranked_fusion_signal.payload["supporting_model_signal_count"] >= result.case_count
    assert ranked_fusion_signal.payload["candidate_score_domain_count"] >= result.case_count
    assert ranked_fusion_signal.payload["non_unique_candidate_count"] >= 1
    assert ranked_fusion_signal.payload["boundary"] == "ranked_decision_fusion_trains_candidate_scoring_not_fixed_verdicts"
    m5_replay_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.m5_weight_replay")
    assert m5_replay_signal.domain == "ranked_decision"
    assert m5_replay_signal.payload["basis_signal_counts"]["follow_structure_boundary"] >= 1
    assert m5_replay_signal.payload["basis_signal_counts"]["disputed_structure"] >= 1
    assert m5_replay_signal.payload["useful_god_evidence_coverage"] > 0
    assert m5_replay_signal.payload["useful_god_fixed_verdict_guard_count"] >= 1
    assert m5_replay_signal.payload["structure_candidate_weights"]["follow_structure_boundary_review"] > 1.0
    assert m5_replay_signal.payload["useful_god_candidate_weights"]["balance_review"] > 1.0
    assert m5_replay_signal.payload["boundary"] == "m5_weight_replay_trains_candidate_weights_not_chart_facts"
    reading_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.practical_reading_quality")
    assert set(reading_signal.payload["reading_domains"]) >= {"career", "wealth", "relationship", "health", "timing"}
    assert reading_signal.payload["readable_summary_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["customer_takeaway_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["action_prompt_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["quality_contract_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["calculation_basis_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["ranked_decision_link_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["model_signal_context_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["evidence_bound_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["blocked_claim_count"] >= reading_signal.payload["reading_domain_count"]
    assert reading_signal.payload["explanation_unit_count"] >= reading_signal.payload["reading_domain_count"] * 3
    assert reading_signal.payload["average_priority_score"] > 0
    flow_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.agent_question_flow_quality")
    assert "event_year_discovery" in flow_signal.payload["stages"]
    question_quality_signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.high_value_question_quality"
    )
    assert question_quality_signal.domain == "question_intelligence"
    assert question_quality_signal.payload["quality_contract_coverage"] == 1.0
    assert question_quality_signal.payload["average_expected_information_gain"] > 0
    assert "answer_career_direction" in question_quality_signal.payload["primary_gains"]
    assert question_quality_signal.payload["boundary"] == "high_value_question_quality_trains_question_strategy_not_chart_facts"
    model_signal_question_signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.question_model_signal_personalization"
    )
    assert model_signal_question_signal.domain == "question_intelligence"
    assert model_signal_question_signal.payload["model_signal_focused_count"] >= 5
    assert model_signal_question_signal.payload["model_signal_focus_reason_count"] >= 10
    assert model_signal_question_signal.payload["top_question_model_signal_focused_count"] >= 5
    assert model_signal_question_signal.payload["coverage"] >= 0.8
    assert model_signal_question_signal.payload["top_question_coverage"] >= 0.7
    assert model_signal_question_signal.payload["can_tune_question_strategy"] is True
    assert model_signal_question_signal.payload["can_tune_chart_facts"] is False
    assert model_signal_question_signal.payload["chart_fact_mutation_allowed_count"] == 0
    assert (
        model_signal_question_signal.payload["boundary"]
        == "question_model_signal_personalization_trains_question_strategy_not_chart_facts"
    )
    real_case_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.real_case_feedback_alignment")
    assert real_case_signal.domain == "real_case_validation"
    assert real_case_signal.payload["case_count"] >= 4
    assert real_case_signal.payload["ready_count"] >= 3
    assert real_case_signal.payload["blocked_count"] >= 1
    assert real_case_signal.payload["no_fake_fact_count"] >= 1
    assert real_case_signal.payload["six_ready_count"] >= 2
    assert real_case_signal.payload["practical_ready_count"] >= 3
    assert real_case_signal.payload["projection_matrix_count"] >= 3
    assert real_case_signal.payload["boundary"] == "real_case_feedback_alignment_trains_quality_policy_not_chart_facts"
    calibration_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.real_case_calibration_pack")
    assert calibration_signal.domain == "real_case_validation"
    assert calibration_signal.payload["case_count"] >= 30
    assert calibration_signal.payload["categories"]["solar"] is True
    assert calibration_signal.payload["categories"]["lunar"] is True
    assert calibration_signal.payload["categories"]["leap_month_lunar"] is True
    assert calibration_signal.payload["categories"]["true_solar"] is True
    assert calibration_signal.payload["categories"]["unknown_hour"] is True
    assert calibration_signal.payload["categories"]["unknown_gender"] is True
    assert calibration_signal.payload["model_signal_ready_count"] >= 5
    assert calibration_signal.payload["ranked_decision_ready_count"] >= 5
    assert calibration_signal.payload["ranked_score_floor_ready_count"] >= 3
    assert calibration_signal.payload["ranked_basis_signal_counts"]["follow_structure_boundary"] >= 1
    assert calibration_signal.payload["ranked_basis_signal_counts"]["disputed_structure"] >= 1
    assert calibration_signal.payload["ranked_basis_signal_counts"]["non_unique_candidate"] >= 1
    assert calibration_signal.payload["no_fake_fact_count"] >= 1
    assert calibration_signal.payload["m6_practical_contract_ready_count"] >= 20
    assert calibration_signal.payload["m6_practical_domain_contract_count"] >= 100
    assert calibration_signal.payload["m6_practical_raw_score_leak_count"] == 0
    assert calibration_signal.payload["m7_calibration_drift_summary_version"] == "v30.real_case_calibration_drift_summary.v1"
    assert calibration_signal.payload["m7_calibration_drift_summary_count"] >= 30
    assert calibration_signal.payload["m7_calibration_stable_count"] == calibration_signal.payload["m7_calibration_drift_summary_count"]
    assert calibration_signal.payload["m7_calibration_needs_module_review_count"] == 0
    assert calibration_signal.payload["m7_drift_flag_counts"] == {}
    assert calibration_signal.payload["m7_module_adjustment_counts"] == {}
    assert calibration_signal.payload["m7_module_readiness_counts"]["M7_real_case_calibration"] >= 30
    assert calibration_signal.payload["production_replay_metadata_version"] == "v30.production_replay_metadata_summary.v1"
    assert calibration_signal.payload["production_replay_metadata_count"] >= 30
    assert calibration_signal.payload["production_replay_metadata_privacy_guard_pass_count"] == calibration_signal.payload["production_replay_metadata_count"]
    assert calibration_signal.payload["production_replay_metadata_ready_count"] >= 20
    assert calibration_signal.payload["production_replay_metadata_pending_count"] >= 1
    assert calibration_signal.payload["production_replay_metadata_blocked_count"] >= 1
    assert set(calibration_signal.payload["production_replay_metadata_calendar_types"]) >= {"solar", "lunar"}
    assert calibration_signal.payload["production_replay_metadata_true_solar_count"] >= 1
    assert calibration_signal.payload["production_replay_metadata_unknown_hour_count"] >= 1
    assert calibration_signal.payload["production_replay_metadata_unknown_gender_count"] >= 1
    assert calibration_signal.payload["production_replay_metadata_projection_leak_pass_count"] == calibration_signal.payload["production_replay_metadata_count"]
    assert calibration_signal.payload["production_replay_metadata_boundary"] == "production_replay_metadata_summary_trains_replay_selection_policy_not_chart_facts"
    assert calibration_signal.payload["boundary"] == "real_case_calibration_pack_trains_validation_policy_not_chart_facts"
    assert structure_signal.payload["average_competing_path_count"] > 0
    assert structure_signal.payload["average_suppressed_path_count"] > 0
    assert structure_signal.payload["average_conflict_family_count"] > 0
    assert structure_signal.payload["average_path_resolution_family_count"] > 0
    assert structure_signal.payload["average_domain_path_count"] > 0
    assert structure_signal.payload["average_domain_rule_depth_path_count"] > 0
    assert structure_signal.payload["average_tongguan_path_count"] > 0
    assert structure_signal.payload["average_tongguan_resource_mediator_path_count"] > 0
    assert structure_signal.payload["average_tongguan_output_wealth_bridge_path_count"] > 0
    assert structure_signal.payload["average_zhihua_path_count"] > 0
    assert structure_signal.payload["average_model_signal_ready"] > 0
    assert structure_signal.payload["average_model_signal_energy_band_count"] > 0
    assert structure_signal.payload["average_zhihua_output_authority_path_count"] > 0
    assert structure_signal.payload["average_zhihua_wealth_authority_resource_path_count"] > 0
    assert structure_signal.payload["average_wealth_competition_path_count"] > 0
    assert structure_signal.payload["average_career_authority_pressure_path_count"] > 0
    assert structure_signal.payload["average_relationship_conflict_path_count"] > 0
    assert structure_signal.payload["average_health_conflict_pressure_review_count"] > 0
    assert structure_signal.payload["average_useful_god_candidate_path_count"] > 0
    assert structure_signal.payload["average_branch_conflict_edge_count"] > 0
    assert structure_signal.payload["average_branch_alignment_edge_count"] > 0
    hidden_signal = next(signal for signal in signals if signal.signal_id == "v30.training_signal.hidden_factor_event_alignment")
    assert hidden_signal.domain == "hidden_factor"
    assert hidden_signal.payload["candidate_count"] >= 2
    assert hidden_signal.payload["conflict_count"] >= 1
    assert hidden_signal.payload["denial_count"] >= 1
    assert hidden_signal.payload["event_year_coverage"] > 0
    assert hidden_signal.payload["repeated_state_coverage"] > 0
    assert hidden_signal.payload["average_time_layer_alignment_score"] > 0
    assert hidden_signal.payload["time_layer_alignment_coverage"] > 0
