from __future__ import annotations

from v30.validation import extract_training_signals, run_bazi_llm_training_synthetic_readiness, run_synthetic_tier


def test_bazi_llm_acceptance_synthetic_tier_emits_training_signal() -> None:
    result = run_synthetic_tier("bazi_llm_acceptance")
    signals = extract_training_signals(result)
    signal = next(
        row for row in signals
        if row.signal_id == "v30.training_signal.bazi_llm_output_acceptance_quality"
    )

    assert result.passed
    assert signal.strength == 1.0
    assert signal.payload["accepted_count"] >= 2
    assert signal.payload["rejected_count"] >= 3
    assert signal.payload["can_tune_expression"] is True
    assert signal.payload["can_tune_question_strategy"] is True
    assert signal.payload["can_tune_chart_facts"] is False
    assert signal.payload["boundary"] == "bazi_llm_output_acceptance_signal_trains_expression_and_question_strategy_not_chart_facts"


def test_bazi_llm_training_synthetic_readiness_accepts_bl6() -> None:
    result = run_bazi_llm_training_synthetic_readiness()

    assert result["version"] == "v30.bazi_llm_training_synthetic_readiness.v1"
    assert result["decision"]["decision_status"] == "bl6_bazi_llm_training_synthetic_ready"
    assert result["decision"]["readiness_ready"] is True
    assert result["decision"]["live_llm_required"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "BL7"
