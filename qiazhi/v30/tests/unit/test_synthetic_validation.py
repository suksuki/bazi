from __future__ import annotations

from v30.validation import (
    SYNTHETIC_CORE_CALCULATION_CASES,
    SYNTHETIC_CENTRAL_BRAIN_CASES,
    SYNTHETIC_BAZI_LLM_ACCEPTANCE_CASES,
    SYNTHETIC_GRADIENT_CASES,
    SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES,
    SYNTHETIC_INTERACTION_LOOP_CASES,
    SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES,
    SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES,
    SYNTHETIC_REAL_BAZI_DIAGNOSIS_CASES,
    SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES,
    SYNTHETIC_SMOKE_CASES,
    SYNTHETIC_TRAINING_PIPELINE_CASES,
    SyntheticBaziCase,
    extract_training_signals,
    run_synthetic_case,
    run_synthetic_suite,
    run_synthetic_tier,
)


def test_synthetic_case_smoke_passes_current_spine() -> None:
    case = SyntheticBaziCase(
        case_id="synthetic-smoke",
        case_type="positive_prototype",
        domain="core_spine",
        chart_input={"day_master": "甲"},
        expected_domains={"chart", "element", "ten_god", "time_context", "useful_god"},
        expected_anchor_ids={"q_v30_mainline_review", "q_v30_time_context_boundary"},
        negative_expectations={"no_fixed_useful_god_verdict", "no_timing_prediction_without_time"},
    )
    result = run_synthetic_case(case)
    assert result.passed
    assert result.failures == []
    assert result.observed["mainline_quality_gate"] == "needs_time_context"


def test_synthetic_case_reports_missing_expectation() -> None:
    case = SyntheticBaziCase(
        case_id="synthetic-missing",
        case_type="negative_counter",
        domain="core_spine",
        chart_input={"day_master": "甲"},
        expected_domains={"nonexistent_domain"},
    )
    result = run_synthetic_case(case)
    assert not result.passed
    assert result.failures == ["missing_domains:nonexistent_domain"]


def test_synthetic_smoke_suite_passes() -> None:
    result = run_synthetic_suite()
    assert result.suite_id == "v30.synthetic.smoke"
    assert result.case_count == len(SYNTHETIC_SMOKE_CASES)
    assert result.passed
    assert result.failed_count == 0


def test_synthetic_bazi_llm_acceptance_tier_passes() -> None:
    result = run_synthetic_tier("bazi_llm_acceptance")
    assert result.suite_id == "v30.synthetic.bazi_llm_acceptance"
    assert result.case_count == len(SYNTHETIC_BAZI_LLM_ACCEPTANCE_CASES)
    assert result.passed
    assert result.failed_count == 0
    observed = result.results[0].observed["bazi_llm_output_acceptance_quality"]
    assert observed["accepted_count"] >= 2
    assert observed["rejected_count"] >= 3
    assert observed["live_llm_required"] is False
    assert observed["chart_fact_mutation_allowed"] is False


def test_synthetic_real_bazi_diagnosis_tier_passes() -> None:
    result = run_synthetic_tier("real_bazi_diagnosis")
    assert result.suite_id == "v30.synthetic.real_bazi_diagnosis"
    assert result.case_count == len(SYNTHETIC_REAL_BAZI_DIAGNOSIS_CASES)
    assert result.passed
    assert result.failed_count == 0
    for row in result.results:
        quality = row.observed["real_bazi_diagnosis_quality"]
        assert quality["version"] == "v30.real_bazi_diagnosis.synthetic_quality.v1"
        assert quality["status"] == "ready"
        assert quality["rule_match_count"] >= 20
        assert quality["path_count"] >= 5
        assert quality["portrait_count"] >= 12
        assert quality["claim_count"] >= 25
        assert quality["untraceable_claim_count"] == 0
        assert quality["llm_generated_claim_count"] == 0
        assert quality["chart_fact_mutation_claim_count"] == 0
        assert quality["fixed_event_prediction_claim_count"] == 0
        assert quality["customer_internal_leak_count"] == 0
        assert quality["customer_has_diagnosis_overview"] is True
        assert quality["admin_diagnostics_visible"] is True
        assert quality["storage_authoritative_facts_stored_here"] is False
        assert quality["readiness_518k_sample"]["ready_for_sample_replay"] is True


def test_synthetic_hidden_factor_case_requires_dialogue_probe() -> None:
    case = next(row for row in SYNTHETIC_SMOKE_CASES if row.domain == "hidden_factor")
    result = run_synthetic_case(case)
    assert result.passed
    assert result.observed["hidden_factor_probe_count"] == 1
    assert "hidden_factor" in result.observed["recommended_topics"]


def test_synthetic_krp_case_requires_bound_signals() -> None:
    case = next(row for row in SYNTHETIC_SMOKE_CASES if row.domain == "knowledge_rule_portrait")
    result = run_synthetic_case(case)
    assert result.passed
    assert set(result.observed["knowledge_rule_portrait_signal_types"]) >= {"knowledge", "rule", "portrait"}
    assert result.observed["structure_path_scores"]["knowledge_signal_count"] == 1.0
    assert result.observed["structure_path_scores"]["mechanism_path_count"] >= 3.0
    assert "mechanism.useful_god_candidate_gate" in result.observed["mechanism_ids"]
    assert any(row.startswith("rule_signal:") for row in result.observed["supporting_mainlines"])
    completion = result.observed["m3_completion_summary"]
    assert completion["version"] == "v30.m3_completion_summary.v1"
    assert completion["status"] == "ready"
    assert completion["completion_coverage"] == 1.0
    assert completion["m4_model_signal_support"] is True
    assert completion["m5_ranked_decision_support_count"] >= 2
    assert completion["m6_practical_reading_support_count"] >= 5
    assert completion["acts_as_conclusion_engine"] is False
    assert completion["chart_fact_mutation_allowed"] is False
    assert completion["boundary"] == "m3_completion_summary_validates_evidence_spine_supports_m4_m5_m6_not_final_verdicts"


def test_synthetic_gradient_suite_passes_policy_and_path_thresholds() -> None:
    result = run_synthetic_tier("gradient")
    assert result.suite_id == "v30.synthetic.gradient"
    assert result.case_count == len(SYNTHETIC_GRADIENT_CASES)
    assert result.passed


def test_synthetic_interaction_loop_tier_passes_customer_followup_contracts() -> None:
    result = run_synthetic_tier("interaction_loop")
    assert result.suite_id == "v30.synthetic.interaction_loop"
    assert result.case_count == len(SYNTHETIC_INTERACTION_LOOP_CASES)
    assert result.passed
    direct_click = next(
        row for row in result.results
        if row.case_id.endswith("direct_question_click_001")
    )
    state = direct_click.observed["interaction_state"]
    surface = direct_click.observed["customer_reading_surface"]
    assert state["visible_next_question_id"] == "q_v30_user_timing_pressure"
    assert state["internal_next_question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert surface["visible_next_question_id"] == "q_v30_user_timing_pressure"
    assert "internal_next_question_id" not in surface


def test_synthetic_interaction_brain_structured_constraints_tier_passes() -> None:
    result = run_synthetic_tier("interaction_brain_structured_constraints")
    assert result.suite_id == "v30.synthetic.interaction_brain_structured_constraints"
    assert result.case_count == len(SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES)
    assert result.passed
    rejected = next(
        row for row in result.results
        if row.case_id.endswith("rejected_pollution_001")
    )
    state = rejected.observed["interaction_state"]
    brain = rejected.observed["interaction_brain_result"]
    assert state["invalid_retry_question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert brain["allowed_to_update_hidden_factor"] is False
    assert brain["chart_fact_mutation_allowed"] is False

    signals = extract_training_signals(result)
    signal = next(
        row for row in signals
        if row.signal_id == "v30.training_signal.interaction_brain_structured_constraints"
    )
    assert signal.payload["accepted_count"] >= 2
    assert signal.payload["rejected_count"] >= 1
    assert signal.payload["invalid_retry_count"] >= 1
    assert signal.payload["chart_fact_mutation_allowed_count"] == 0


def test_synthetic_central_brain_tier_passes() -> None:
    result = run_synthetic_tier("central_brain")

    assert result.suite_id == "v30.synthetic.central_brain"
    assert result.case_count == len(SYNTHETIC_CENTRAL_BRAIN_CASES)
    assert result.case_count >= 5
    assert result.passed
    summaries = [row.observed["central_brain_synthetic_summary"] for row in result.results]
    assert all(row["version"] == "v30.central_brain.v1" for row in summaries)
    assert all(row["expression_surface"] == "clean" for row in summaries)
    assert all(
        {"question_intelligence", "expression"} <= set(row["training_route_domains"])
        for row in summaries
    )
    assert all(
        {"question_intelligence", "expression", "hidden_factor"} <= set(row["training_route_domains"])
        for row in summaries
        if row["hidden_factor_focus"] != "amplifier_candidate"
    )
    assert all(not row["guest_diagnostics_visible"] for row in summaries)
    assert all(row["practitioner_diagnostics_visible"] for row in summaries)
    assert all(row["admin_diagnostics_visible"] for row in summaries)
    assert any(row["hidden_factor_focus"] == "amplifier_candidate" for row in summaries)


def test_synthetic_training_pipeline_tier_passes_training_contracts() -> None:
    result = run_synthetic_tier("training_pipeline")

    assert result.suite_id == "v30.synthetic.training_pipeline"
    assert result.case_count == len(SYNTHETIC_TRAINING_PIPELINE_CASES)
    assert result.case_count >= 80
    assert result.passed
    signals = extract_training_signals(result)
    signal_ids = {signal.signal_id for signal in signals}
    required_signal_ids = {
        "v30.training_signal.krp_unit_coverage",
        "v30.training_signal.m3_core_spine_coverage",
        "v30.training_signal.per_unit_parameter_tuning",
        "v30.training_signal.m1_m2_base_fact_contract",
        "v30.training_signal.ten_god_energy_fusion",
        "v30.training_signal.ranked_decision_fusion",
        "v30.training_signal.m5_weight_replay",
        "v30.training_signal.practical_reading_quality",
        "v30.training_signal.real_case_calibration_pack",
        "v30.training_signal.api_projection_contract",
        "v30.training_signal.question_dialogue_outcome",
        "v30.training_signal.interaction_state_machine",
        "v30.training_signal.interaction_loop_quality",
        "v30.training_signal.interaction_brain_structured_constraints",
        "v30.training_signal.central_brain_route_coverage",
        "v30.training_signal.expression_quality",
        "v30.training_signal.llm_output_contract_quality",
        "v30.training_signal.structure_dynamic_competition",
        "v30.training_signal.hidden_factor_event_alignment",
    }
    assert required_signal_ids <= signal_ids
    assert len(signals) >= 25
    assert all(signal.source_case_ids for signal in signals if signal.signal_id in required_signal_ids)
    signal_by_id = {signal.signal_id: signal for signal in signals}
    assert signal_by_id["v30.training_signal.real_case_calibration_pack"].payload["case_count"] >= 30
    assert signal_by_id["v30.training_signal.central_brain_route_coverage"].strength == 1.0
    assert signal_by_id["v30.training_signal.interaction_loop_quality"].payload["internal_next_question_surface_leak_count"] == 0
    assert signal_by_id["v30.training_signal.api_projection_contract"].payload["user_leak_pass_count"] >= 30
    assert signal_by_id["v30.training_signal.hidden_factor_event_alignment"].payload["denial_count"] >= 1
    assert signal_by_id["v30.training_signal.per_unit_parameter_tuning"].payload["boundary"] == "per_unit_weights_tune_runtime_candidates_not_chart_facts"
    assert signal_by_id["v30.training_signal.ranked_decision_fusion"].payload["boundary"] == "ranked_decision_fusion_trains_candidate_scoring_not_fixed_verdicts"
    assert signal_by_id["v30.training_signal.m5_weight_replay"].payload["boundary"] == "m5_weight_replay_trains_candidate_weights_not_chart_facts"
    assert signal_by_id["v30.training_signal.real_case_calibration_pack"].payload["boundary"] == "real_case_calibration_pack_trains_validation_policy_not_chart_facts"


def test_synthetic_core_bazi_calculation_tier_projects_first_screen_result() -> None:
    result = run_synthetic_tier("core_bazi_calculation")
    assert result.suite_id == "v30.synthetic.core_bazi_calculation"
    assert result.case_count == len(SYNTHETIC_CORE_CALCULATION_CASES)
    assert result.passed
    ready_rows = [
        row for row in result.results
        if row.observed.get("chart_build", {}).get("status") == "ready"
    ]
    assert ready_rows
    for row in ready_rows:
        core = row.observed["core_bazi_reading"]
        assert core["surface_type"] == "core_bazi_calculation"
        assert core["fact_integrity"]["deterministic"] is True
        assert core["fact_integrity"]["llm_generated"] is False
        assert core["base_fact_summary"]["version"] == "v30.base_bazi_fact_summary.v1"
        assert core["base_fact_explanations"]["version"] == "v30.base_bazi_fact_explanations.v1"
        assert len(core["four_pillars"]) == 4
        assert set(core["ranked_decisions"]) >= {"strength", "structure_pattern", "useful_god"}


def test_synthetic_m1_m2_bazi_calculation_tier_seals_base_fact_contract() -> None:
    result = run_synthetic_tier("m1_m2_bazi_calculation")
    assert result.suite_id == "v30.synthetic.m1_m2_bazi_calculation"
    assert result.case_count == len(SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES)
    assert result.passed
    ready_contracts = [
        row.observed["m1_m2_base_fact_contract"]
        for row in result.results
        if row.observed.get("m1_m2_base_fact_contract", {}).get("status") == "ready"
    ]
    assert len(ready_contracts) >= 10
    assert {row["calendar_type"] for row in ready_contracts} >= {"solar", "lunar"}
    assert any(row["lunar_is_leap_month"] for row in ready_contracts)
    assert any(row["use_true_solar_time"] for row in ready_contracts)
    assert any(row["gender_status"] == "unknown" for row in ready_contracts)
    for contract in ready_contracts:
        assert contract["deterministic"] is True
        assert contract["non_deterministic_source_count"] == 0
        assert contract["pillar_count"] == 4
        assert contract["visible_ten_god_count"] >= 3
        assert contract["hidden_ten_god_count"] > 0
        assert {
            "visible_ten_god_counts",
            "hidden_ten_god_counts",
            "hidden_stem_summary",
            "relation_type_counts",
            "relation_families",
            "root_fact_summary",
            "element_distribution",
        } <= set(contract["summary_keys"])
        assert contract["root_fact_summary"]["boundary"] == "root_vault_summary_records_presence_without_strength_or_useful_god_verdict"
        assert contract["completion_summary_version"] == "v30.m1_m2_completion_summary.v1"
        assert contract["completion_status"] == "ready"
        assert contract["completion_required_key_coverage"] == 1.0
        assert contract["completion_explanation_coverage"] == 1.0
        assert contract["completion_downstream_consumption_ready"] is True
        assert contract["completion_m5_uses_root_fact_summary_count"] >= 3
        assert contract["completion_m6_uses_m1_m2_fact_count"] >= 5
        assert contract["completion_chart_fact_mutation_allowed"] is False
        assert contract["completion_boundary"] == "m1_m2_completion_summary_validates_fact_layer_and_downstream_consumption_not_judgment"


def test_synthetic_m4_ten_god_real_case_replay_tier_passes() -> None:
    result = run_synthetic_tier("m4_ten_god_real_case_replay")
    assert result.suite_id == "v30.synthetic.m4_ten_god_real_case_replay"
    assert result.case_count == len(SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES)
    assert result.passed


def test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage() -> None:
    result = run_synthetic_tier("real_case_calibration_pack")
    assert result.suite_id == "v30.synthetic.real_case_calibration_pack"
    assert result.case_count == len(SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES)
    assert result.case_count >= 30
    assert result.passed
    fixtures = [row.observed["real_case_fixture"] for row in result.results]
    metadata_rows = [row.observed["production_replay_metadata"] for row in result.results]
    assert {row["calendar_type"] for row in fixtures} >= {"solar", "lunar"}
    assert any(row["lunar_is_leap_month"] for row in fixtures)
    assert any(row["use_true_solar_time"] for row in fixtures)
    assert any(row["unknown_hour"] and not row["has_pillars"] for row in fixtures)
    assert any(row["gender_status"] == "unknown" for row in fixtures)
    drift_summaries = [row["calibration_drift_summary"] for row in fixtures]
    assert len(drift_summaries) == len(fixtures)
    assert all(row["version"] == "v30.real_case_calibration_drift_summary.v1" for row in drift_summaries)
    assert all(row["calibration_status"] == "stable" for row in drift_summaries)
    assert all(row["drift_flags"] == [] for row in drift_summaries)
    assert all(row["module_adjustment_targets"] == [] for row in drift_summaries)
    assert all(row["module_readiness"]["M7_real_case_calibration"] is True for row in drift_summaries)
    assert all(row["boundary"] == "real_case_calibration_drift_routes_to_module_adjustments_not_chart_fact_mutation" for row in drift_summaries)
    assert len(metadata_rows) == len(fixtures)
    assert all(row["version"] == "v30.production_replay_metadata.v1" for row in metadata_rows)
    assert {row["calendar_type"] for row in metadata_rows} >= {"solar", "lunar"}
    assert any(row["lunar_is_leap_month"] for row in metadata_rows)
    assert any(row["use_true_solar_time"] for row in metadata_rows)
    assert any(row["unknown_hour"] for row in metadata_rows)
    assert any(row["unknown_gender"] for row in metadata_rows)
    assert {"ready", "pending", "blocked"} <= {row["chart_status"] for row in metadata_rows}
    assert all(row["privacy_guard"]["metadata_only"] is True for row in metadata_rows)
    assert all(row["privacy_guard"]["no_private_user_content"] is True for row in metadata_rows)
    assert all(row["privacy_guard"]["forbidden_key_scan_passed"] is True for row in metadata_rows)
    assert all(row["boundary"] == "production_replay_metadata_tags_do_not_import_private_content_or_mutate_chart_facts" for row in metadata_rows)
    forbidden_metadata_keys = {"birth_date", "birth_time", "answer", "name", "raw_payload", "user_text"}
    assert all(forbidden_metadata_keys.isdisjoint(row) for row in metadata_rows)
    assert sum(1 for row in metadata_rows if row["m4_model_signal_ready"]) >= 20
    assert sum(1 for row in metadata_rows if row["m5_ranked_decision_ready"]) >= 20
    assert sum(1 for row in metadata_rows if row["m6_practical_contract_ready"]) >= 20
    assert all(row["projection_leak_scan_passed"] for row in metadata_rows)
    primaries = [row["ranked_primary_candidates"] for row in fixtures if row.get("ranked_primary_candidates")]
    strength_primaries = {row.get("strength") for row in primaries}
    useful_primaries = {row.get("useful_god") for row in primaries}
    assert {"weak", "slightly_weak", "balanced", "strong"} <= strength_primaries
    assert {
        "resource_or_self_support_review",
        "balance_review",
        "output_or_wealth_release_review",
    } <= useful_primaries
    assert all(row.get("ranked_score_key_count", {}).get("strength", 0) >= 5 for row in fixtures if row["has_pillars"])
    structure_scores = [
        row.get("ranked_candidate_scores", {}).get("structure_pattern", {})
        for row in fixtures
        if row.get("ranked_candidate_scores")
    ]
    useful_scores = [
        row.get("ranked_candidate_scores", {}).get("useful_god", {})
        for row in fixtures
        if row.get("ranked_candidate_scores")
    ]
    assert any(row.get("regulation_climate_boundary_review", 0.0) >= 0.45 for row in structure_scores)
    assert any(row.get("special_structure_boundary_review", 0.0) >= 0.35 for row in structure_scores)
    assert any(row.get("follow_structure_boundary_review", 0.0) >= 0.55 for row in structure_scores)
    assert any(row.get("disputed_structure_review", 0.0) >= 0.52 for row in structure_scores)
    assert any(row.get("climate_regulation_review", 0.0) >= 0.40 for row in useful_scores)
    structure_signals = [
        row.get("ranked_scoring_basis_signals", {}).get("structure_pattern", {})
        for row in fixtures
        if row.get("ranked_scoring_basis_signals")
    ]
    assert any(row.get("follow_structure_boundary_signal") for row in structure_signals)
    assert any(row.get("disputed_structure_signal") for row in structure_signals)
    assert any(row.get("non_unique_candidate_signal") for row in structure_signals)
    practical_contracts = [
        contract
        for fixture in fixtures
        for contract in fixture.get("practical_domain_contracts", {}).values()
        if isinstance(fixture.get("practical_domain_contracts", {}), dict)
    ]
    assert practical_contracts
    assert all(contract["version"] == "v30.practical_domain_reading.v2" for contract in practical_contracts)
    assert all(contract["calculation_basis_version"] == "v30.practical_domain_calculation_basis.v1" for contract in practical_contracts)
    assert all(contract["model_signal_context_version"] == "v30.practical_model_signal_context.v1" for contract in practical_contracts)
    assert all(contract["ranked_decision_link_count"] >= 3 for contract in practical_contracts)
    assert all(contract["explanation_unit_count"] >= 3 for contract in practical_contracts)
    assert all(not contract["raw_score_leak"] for contract in practical_contracts)


def test_synthetic_m5_ranked_decision_contract_tier_passes() -> None:
    result = run_synthetic_tier("m5_ranked_decision_contract")
    assert result.suite_id == "v30.synthetic.m5_ranked_decision_contract"
    assert result.case_count == len(SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES)
    assert result.case_count >= 30
    assert result.passed
    ready_rows = [
        row for row in result.results
        if row.observed.get("ranked_decisions")
    ]
    assert ready_rows
    for row in ready_rows:
        for domain, decision in row.observed["ranked_decisions"].items():
            basis = decision["scoring_basis"]
            assert basis["model_signal_interface_version"] == "v30.model_signal_interface_contract.v1"
            assert basis["model_signal_calibration_profile_version"] == "v30.model_signal_calibration_profile.v1"
            assert basis["model_signal_calibration_flags"]
            assert basis["model_signal_ranked_adjustment_version"] == "v30.model_signal_ranked_decision_adjustments.v1"
            assert basis["model_signal_ranked_adjustment_flags"]
            assert isinstance(basis["model_signal_score_bias"], dict)
            assert basis["root_fact_summary_version"] == "v30.root_vault_fact_summary.v1"
            assert decision["status"] == "ranked_candidate"
            assert decision["boundary"].endswith(("verdict", "geju"))
            assert "raw_weight" not in str(decision["model_signal_summary"])
            assert domain in {"strength", "structure_pattern", "useful_god"}


def test_synthetic_m6_practical_reading_contract_tier_passes() -> None:
    result = run_synthetic_tier("m6_practical_reading_contract")
    assert result.suite_id == "v30.synthetic.m6_practical_reading_contract"
    assert result.case_count == len(SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES)
    assert result.case_count >= 30
    assert result.passed
    ready_rows = [
        row for row in result.results
        if row.observed.get("practical_reading_context", {}).get("domain_readings")
    ]
    assert ready_rows
    for row in ready_rows:
        readings = row.observed["practical_reading_context"]["domain_readings"]
        assert set(readings) >= {"career", "wealth", "relationship", "health", "timing"}
        for domain, payload in readings.items():
            assert payload["version"] == "v30.practical_domain_reading.v2"
            assert payload["calculation_basis"]["version"] == "v30.practical_domain_calculation_basis.v1"
            assert payload["model_signal_context"]["version"] == "v30.practical_model_signal_context.v1"
            assert set(payload["ranked_decision_links"]) >= {"strength", "structure_pattern", "useful_god"}
            assert len(payload["domain_insights"]) == 3
            assert {row["insight_type"] for row in payload["domain_insights"]} == {
                "opportunity_path",
                "pressure_or_risk_path",
                "calibration_path",
            }
            assert len(payload["action_steps"]) >= 3
            assert len(payload["calibration_prompts"]) >= 2
            assert payload["module_trace"]["version"] == "v30.m6_practical_module_trace.v1"
            assert payload["module_trace"]["uses_m1_m2_facts"] is True
            assert payload["module_trace"]["uses_m3_structure_evidence"] is True
            assert payload["module_trace"]["uses_m4_model_signal"] is True
            assert payload["module_trace"]["uses_m5_ranked_decisions"] is True
            assert payload["module_trace"]["raw_model_score_visible"] is False
            assert payload["module_trace"]["chart_fact_mutation_allowed"] is False
            assert payload["evidence_ids"]
            assert len(payload["explanation_units"]) >= 3
            assert "must_not_mutate_birth_chart_or_luck_flow_facts" in payload["boundary_conditions"]
            assert payload["blocked_claims"]
            for band in payload["model_signal_context"]["top_energy_bands"]:
                assert "raw_weight" not in band
                assert "raw_score" not in band
                assert "energy" not in band
                assert "stability" not in band
                assert "volatility" not in band
                assert "energy_band" in band
            assert domain in {"career", "wealth", "relationship", "health", "timing"}


def test_synthetic_m8_api_projection_contract_tier_passes() -> None:
    result = run_synthetic_tier("m8_api_projection_contract")
    assert result.suite_id == "v30.synthetic.m8_api_projection_contract"
    assert result.case_count == len(SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES)
    assert result.case_count >= 30
    assert result.passed
    ready_rows = [
        row for row in result.results
        if row.observed.get("api_projection_contract")
    ]
    assert ready_rows
    for row in ready_rows:
        contract = row.observed["api_projection_contract"]
        admin_contract = row.observed["admin_api_projection_contract"]
        assert contract["version"] == "v30.api_projection_contract.v1"
        assert contract["customer_surface_order"][:2] == ["core_bazi_reading", "domain_cards"]
        assert contract["core_first_projection"]["calculation_before_questions"] is True
        assert contract["core_first_projection"]["required_surface_prefix"] == ["core_bazi_reading", "domain_cards"]
        assert contract["customer_surface_contract"]["surface_prefix_ready"] is True
        assert {"reading_surface", "core_bazi_reading", "domain_cards", "questions", "answer_panel", "diagnostics"} <= set(
            contract["additive_api_policy"]["must_preserve"]
        )
        assert {"internal_next_question_id", "actor_context", "llm_runtime_status"} <= set(
            contract["additive_api_policy"]["must_preserve"]
        )
        assert {"raw_score", "raw_weight", "training_signal", "policy_effect"} <= set(
            contract["customer_forbidden_fields"]["fields"]
        )
        assert contract["leak_scan"]["passed"] is True
        assert contract["leak_scan"]["forbidden_token_hits"] == []
        assert contract["leak_scan"]["diagnostics_hidden"] is True
        assert admin_contract["diagnostics_visible"] is True


def test_synthetic_question_policy_override_can_promote_hidden_factor_topic() -> None:
    case = next(row for row in SYNTHETIC_GRADIENT_CASES if row.case_id.endswith("hidden_factor_weight_001"))
    result = run_synthetic_case(case)
    assert result.passed
    assert result.observed["top_topic"] == "hidden_factor"
    assert result.observed["policy_weights_by_topic"]["hidden_factor"] == 1.25
