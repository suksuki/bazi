from __future__ import annotations

from v30.brain import optimize_central_brain_policy
from tests.unit.test_brain_training_examples_phase2 import _decision_trace
from v30.training import build_brain_training_example


def test_phase2_policy_optimizer_promotes_good_examples_with_clipped_deltas() -> None:
    examples = [
        build_brain_training_example(
            reading_id="phase2-reading",
            source="runtime_feedback",
            decision=_decision_trace(),
            question_outcome={"confirmed": True, "selected_option": f"good-{index}", "followup_useful": True},
            labels={
                "claim_correctness": 0.86,
                "question_information_gain": 0.78,
                "advice_actionability": 0.82,
                "template_risk": 0.08,
                "overclaim_risk": 0.1,
                "user_cost": 0.18,
            },
            example_id=f"phase2-good-{index}",
        )
        for index in range(5)
    ]

    result = optimize_central_brain_policy(examples, min_examples=3, max_delta=0.06)

    assert result["version"] == "v30.central_brain_policy_optimizer.v1"
    assert result["promotion_signal"] == "eligible"
    assert result["weights"]["final_synthesis.advice_actionability"] > 1.0
    assert result["weights"]["next_action.information_gain"] > 1.0
    assert max(abs(value) for value in result["weight_deltas"].values()) <= 0.06
    assert result["chart_fact_mutation_allowed"] is False
    assert "chart_facts" in result["blocked_targets"]


def test_phase2_policy_optimizer_blocks_high_risk_examples() -> None:
    examples = [
        build_brain_training_example(
            reading_id="phase2-reading",
            source="runtime_feedback",
            decision=_decision_trace(),
            question_outcome={"contradiction_found": True, "selected_option": f"bad-{index}"},
            labels={
                "claim_correctness": 0.2,
                "question_information_gain": 0.3,
                "advice_actionability": 0.25,
                "template_risk": 0.7,
                "overclaim_risk": 0.75,
                "user_cost": 0.6,
            },
            example_id=f"phase2-bad-{index}",
        )
        for index in range(4)
    ]

    result = optimize_central_brain_policy(examples, min_examples=3)

    assert result["promotion_signal"] == "blocked"
    assert "template_risk_too_high" in result["blocked_reasons"]
    assert "overclaim_risk_too_high" in result["blocked_reasons"]
    assert result["weights"]["final_synthesis.template_risk_penalty"] > 1.0
    assert result["weights"]["final_synthesis.overclaim_risk_penalty"] > 1.0


def test_phase2_policy_optimizer_requires_enough_safe_examples() -> None:
    result = optimize_central_brain_policy([], min_examples=3)

    assert result["status"] == "insufficient_data"
    assert result["promotion_signal"] == "blocked"
    assert result["blocked_reason"] == "not_enough_safe_brain_training_examples"
