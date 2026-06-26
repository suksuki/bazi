from __future__ import annotations

from v30.validation import (
    LATENT_DIVERGENCE_CASES,
    extract_training_signals,
    run_latent_bazi_divergence_synthetic_suite,
    run_synthetic_tier,
)


def test_latent_bazi_divergence_synthetic_suite_passes() -> None:
    result = run_latent_bazi_divergence_synthetic_suite()

    assert result.suite_id == "v30.synthetic.latent_bazi_divergence"
    assert result.case_count == len(LATENT_DIVERGENCE_CASES)
    assert result.passed
    assert result.failed_count == 0
    for row in result.results:
        observed = row.observed
        assert observed["version"] == "v30.synthetic.latent_bazi_divergence.v1"
        assert observed["chart_facts_stable"] is True
        assert observed["base_model_stable"] is True
        assert observed["latent_attributes_diverged"] is True
        assert observed["individualized_projection_diverged"] is True
        assert observed["blocked_training_routes"] == ["chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"]
        assert observed["boundary"] == "same_bazi_latent_divergence_validates_personalization_without_chart_fact_mutation"
        assert observed["left"]["status"] == "inferred"
        assert observed["right"]["status"] == "inferred"
        assert observed["left"]["individualization_ready"] is True
        assert observed["right"]["individualization_ready"] is True
        assert observed["left"]["chart_fact_mutation_allowed"] is False
        assert observed["right"]["chart_fact_mutation_allowed"] is False


def test_latent_bazi_divergence_registered_as_synthetic_tier() -> None:
    result = run_synthetic_tier("latent_bazi_divergence")

    assert result.suite_id == "v30.synthetic.latent_bazi_divergence"
    assert result.passed


def test_latent_bazi_divergence_extracts_training_signal() -> None:
    result = run_synthetic_tier("latent_bazi_divergence")
    signals = extract_training_signals(result)
    signal = next(
        row for row in signals
        if row.signal_id == "v30.training_signal.latent_bazi_attribute_alignment"
    )

    assert signal.domain == "hidden_factor"
    assert signal.signal_type == "same_bazi_latent_attribute_and_projection_alignment"
    assert signal.strength == 1.0
    assert signal.source_case_ids == [row.case_id for row in result.results]
    assert signal.payload["case_count"] == len(LATENT_DIVERGENCE_CASES)
    assert signal.payload["variant_count"] == len(LATENT_DIVERGENCE_CASES) * 2
    assert signal.payload["chart_facts_stable_count"] == len(LATENT_DIVERGENCE_CASES)
    assert signal.payload["base_model_stable_count"] == len(LATENT_DIVERGENCE_CASES)
    assert signal.payload["latent_attribute_divergence_count"] == len(LATENT_DIVERGENCE_CASES)
    assert signal.payload["individualized_projection_divergence_count"] == len(LATENT_DIVERGENCE_CASES)
    assert signal.payload["chart_fact_mutation_allowed_count"] == 0
    assert {"career_pressure", "wealth_fluctuation", "relationship_repetition"} <= set(signal.payload["state_tags"])
    assert {"resource_index", "risk_index", "stability_index"} <= set(signal.payload["active_global_attributes"])
    assert {"authority", "resource", "wealth"} <= set(signal.payload["active_ten_god_modifiers"])
    assert {"career_bias", "wealth_bias", "relationship_bias"} <= set(signal.payload["active_domain_biases"])
    assert signal.payload["blocked_training_routes"] == ["calendar_conversion", "chart_facts", "flow_timing", "luck_cycle"]
    assert signal.payload["can_tune_latent_inference"] is True
    assert signal.payload["can_tune_question_strategy"] is True
    assert signal.payload["can_tune_individualized_projection"] is True
    assert signal.payload["can_tune_chart_facts"] is False
    assert signal.payload["boundary"] == "latent_bazi_attribute_alignment_trains_personalization_not_chart_facts"
