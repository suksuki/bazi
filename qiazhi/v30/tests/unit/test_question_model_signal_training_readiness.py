from __future__ import annotations

from v30.validation import extract_training_signals, run_synthetic_tier
from v30.validation.question_model_signal_training_readiness import (
    QUESTION_MODEL_SIGNAL_TRAINING_READINESS_VERSION,
    run_question_model_signal_training_readiness,
)


def test_question_model_signal_personalization_training_signal_extracts_from_interaction_loop() -> None:
    result = run_synthetic_tier("interaction_loop")
    signals = extract_training_signals(result)
    signal = next(
        signal for signal in signals
        if signal.signal_id == "v30.training_signal.question_model_signal_personalization"
    )

    assert signal.domain == "question_intelligence"
    assert signal.signal_type == "model_signal_question_policy_candidate_source"
    assert signal.strength >= 0.8
    assert signal.payload["model_signal_focused_count"] >= 5
    assert len(signal.payload["model_signal_focus_topics"]) >= 4
    assert len(signal.payload["model_signal_focus_pairs"]) >= 6
    assert signal.payload["can_tune_question_strategy"] is True
    assert signal.payload["can_tune_chart_facts"] is False
    assert signal.payload["chart_fact_mutation_allowed_count"] == 0
    assert signal.payload["boundary"] == (
        "question_model_signal_personalization_trains_question_strategy_not_chart_facts"
    )


def test_iq2_question_model_signal_training_readiness_ready() -> None:
    result = run_question_model_signal_training_readiness(reading_id="pytest-iq2")

    assert result["version"] == QUESTION_MODEL_SIGNAL_TRAINING_READINESS_VERSION
    assert result["decision"]["training_readiness_ready"] is True
    assert result["decision"]["decision_status"] == "iq2_question_model_signal_training_ready"
    assert result["decision"]["passed_check_count"] == 5
    assert result["training_summary"]["personalization_signal_id"] == (
        "v30.training_signal.question_model_signal_personalization"
    )
    assert result["training_summary"]["can_tune_question_strategy"] is True
    assert result["training_summary"]["chart_fact_tuning_blocked"] is True
    assert result["next_mainline_selection"]["task_id"] == "IQ-S1"


def test_iq2_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/question-model-signal-training-readiness"
    )
    payload = route.endpoint(reading_id="pytest-iq2-admin")

    assert payload["version"] == QUESTION_MODEL_SIGNAL_TRAINING_READINESS_VERSION
    assert payload["decision"]["training_readiness_ready"] is True
    assert payload["decision"]["policy_pointer_write_allowed"] is False
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
