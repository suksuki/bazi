from __future__ import annotations

from v30.runtime import create_smoke_runtime


def test_runtime_composes_rule_bound_answer_context() -> None:
    runtime = create_smoke_runtime("v30-answer-composer-test")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    assert runtime.answer_context.role_answer_contract["llm_role"] == "explain_bound_context_only"
    assert runtime.answer_result.boundary == "rule_bound_answer_no_llm_fact_mutation"
    first_user_question = next(
        row for row in runtime.question_plan.recommended_questions
        if row["interaction_type"] == "user_question"
    )
    assert runtime.answer_result.question_id == first_user_question["question_id"]


def test_runtime_answer_context_prefers_user_question_over_calibration_probe() -> None:
    runtime = create_smoke_runtime(
        "v30-answer-composer-hidden-priority-test",
        policy_payload_overrides={
            "question_policy": {
                "weights": {
                    "topic_weights": {"hidden_factor": 1.35},
                    "intent_weights": {"discover_hidden_factor_amplifier": 1.2},
                }
            }
        },
    )

    assert runtime.question_plan.recommended_questions[0]["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert runtime.question_plan.recommended_questions[0]["interaction_type"] == "calibration_probe"
    assert runtime.answer_result is not None
    assert runtime.answer_result.question_id != "q_v30_hidden_factor_boundary_discovery"
    assert runtime.answer_result.question_id == next(
        row["question_id"]
        for row in runtime.question_plan.recommended_questions
        if row["interaction_type"] == "user_question"
    )
