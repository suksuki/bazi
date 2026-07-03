from __future__ import annotations

from copy import deepcopy

from v30.validation.central_reading_synthetic_validation import (
    CENTRAL_READING_SYNTHETIC_VALIDATION_VERSION,
    build_central_reading_synthetic_validation,
    run_central_reading_synthetic_validation,
)


def test_cbre5_central_reading_synthetic_validation_ready() -> None:
    result = run_central_reading_synthetic_validation("pytest-cbre5-ready")

    assert result["version"] == CENTRAL_READING_SYNTHETIC_VALIDATION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["central_reading_synthetic_ready"] is True
    assert result["decision"]["decision_status"] == "cbre5_central_reading_synthetic_ready"
    assert result["decision"]["passed_check_count"] == 9
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["synthetic_all_required"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    check_ids = {row["check_id"] for row in result["checks"]}
    assert {
        "central_reading_claim_selection",
        "stage_question_policy",
        "semantic_ontology_mapping",
        "dialogue_training_trace",
        "feedback_weight_update",
        "same_bazi_divergent_feedback",
        "final_synthesis_quality",
        "final_synthesis_blueprint_quality",
        "central_brain_v2_decision_loop",
    } == check_ids
    assert "feedback_alignment_weight" in result["training_targets"]
    assert "claim_selection_for_final_synthesis" in result["training_targets"]
    assert "value_of_information_policy" in result["training_targets"]
    assert "final_synthesis_quality_weight" in result["training_targets"]
    assert "synthesis_blueprint_quality" in result["training_targets"]
    assert "template_risk_penalty" in result["training_targets"]
    assert result["boundary"] == (
        "central_reading_synthetic_validation_checks_dialogue_feedback_and_synthesis_without_mutating_chart_facts"
    )


def test_cbre5_blocks_when_final_synthesis_loses_conclusion_first_contract() -> None:
    ready_payload = _builder_payload("pytest-cbre5-block")
    career_runtime = deepcopy(ready_payload["career_runtime"])
    state = career_runtime["question_plan"]["policy_effect"]["central_reading_state"]
    state["final_synthesis"]["conclusion"] = "当前最值得优先判断的是事业"
    ready_payload["career_runtime"] = career_runtime

    result = build_central_reading_synthetic_validation(**ready_payload)

    assert result["status"] == "blocked"
    assert result["decision"]["central_reading_synthetic_ready"] is False
    assert "final_synthesis_quality" in result["decision"]["failed_check_ids"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False


def _builder_payload(reading_id: str) -> dict[str, object]:
    from v30.runtime import attach_question_outcome, create_smoke_runtime

    baseline = create_smoke_runtime(reading_id)
    career = attach_question_outcome(
        baseline,
        "q_v30_user_career_direction",
        {
            "event_id": f"{reading_id}:career_feedback",
            "answer": "事业压力明显。",
            "selected_option": "career:pressure",
            "confidence": 0.86,
            "feedback_tags": ["career"],
        },
    )
    relationship = attach_question_outcome(
        baseline,
        "q_v30_user_relationship_pattern",
        {
            "event_id": f"{reading_id}:relationship_feedback",
            "answer": "关系反复明显。",
            "selected_option": "relationship:pattern",
            "confidence": 0.84,
            "feedback_tags": ["relationship"],
        },
    )
    return {
        "baseline_runtime": baseline.model_dump(mode="json"),
        "career_runtime": career.model_dump(mode="json"),
        "relationship_runtime": relationship.model_dump(mode="json"),
    }
