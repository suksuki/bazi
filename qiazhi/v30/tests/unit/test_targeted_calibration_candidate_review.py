from __future__ import annotations

from v30.validation.frozen_core_calibration_review import DEFAULT_REQUIRED_SIGNAL_IDS
from v30.validation.targeted_calibration_candidate_review import build_targeted_calibration_candidate_review


def _ready_f1_review() -> dict[str, object]:
    return {
        "version": "v30.frozen_core_calibration_review.v1",
        "decision": {
            "calibration_baseline_ready": True,
            "decision_status": "ready_for_targeted_calibration_iteration",
        },
        "synthetic_tier_summary": {
            "m1_m2_bazi_calculation": {"passed": True},
            "m3_core_spine": {"passed": True},
        },
        "training_signal_summary": {
            "signal_count": len(DEFAULT_REQUIRED_SIGNAL_IDS),
        },
    }


def _signals() -> list[dict[str, object]]:
    base = [
        {
            "signal_id": signal_id,
            "domain": "frozen_core",
            "signal_type": "coverage",
            "strength": 1.0,
            "source_case_ids": ["case"],
            "payload": {"boundary": "test_signal_trains_candidates_not_chart_facts"},
        }
        for signal_id in DEFAULT_REQUIRED_SIGNAL_IDS
    ]
    base.extend(
        [
            {
                "signal_id": "v30.training_signal.expression_quality",
                "domain": "expression",
                "signal_type": "quality",
                "strength": 0.8,
                "source_case_ids": ["case"],
                "payload": {"boundary": "expression_trains_wording_not_chart_facts"},
            },
            {
                "signal_id": "v30.training_signal.llm_output_contract_quality",
                "domain": "expression",
                "signal_type": "contract",
                "strength": 0.5,
                "source_case_ids": ["case"],
                "payload": {"boundary": "llm_output_contract_observes_expression_not_chart_facts"},
            },
            {
                "signal_id": "v30.training_signal.question_dialogue_outcome",
                "domain": "question",
                "signal_type": "candidate",
                "strength": 0.7,
                "source_case_ids": ["case"],
                "payload": {"topics": ["hidden_factor", "useful_god"]},
            },
            {
                "signal_id": "v30.training_signal.question_model_signal_personalization",
                "domain": "question_intelligence",
                "signal_type": "model_signal_question_policy_candidate_source",
                "strength": 0.9,
                "source_case_ids": ["case"],
                "payload": {
                    "model_signal_focused_count": 5,
                    "model_signal_focus_reason_count": 16,
                    "model_signal_focus_pairs": ["wealth->wealth", "authority->career"],
                    "model_signal_focus_topics": ["wealth", "career"],
                    "coverage": 1.0,
                    "top_question_coverage": 0.8,
                    "can_tune_question_strategy": True,
                    "can_tune_chart_facts": False,
                    "chart_fact_mutation_allowed_count": 0,
                    "boundary": "question_model_signal_personalization_trains_question_strategy_not_chart_facts",
                },
            },
        ]
    )
    return base


def test_targeted_calibration_candidate_review_ready() -> None:
    review = build_targeted_calibration_candidate_review(
        frozen_core_calibration_review=_ready_f1_review(),
        training_signals=_signals(),
        review_id="unit-f2",
    )

    assert review["version"] == "v30.targeted_calibration_candidate_review.v1"
    assert review["decision"]["targeted_calibration_review_ready"] is True
    assert review["decision"]["policy_pointer_promotion_allowed"] is False
    assert review["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert review["candidate_summary"]["candidate_count"] == 4
    assert set(review["candidate_summary"]["allowed_candidate_tracks"]) == {
        "model_signal_weights",
        "rule_weights",
        "question_strategy",
        "expression_policy",
    }
    assert review["candidate_summary"]["forbidden_payload_key_hits"] == {}
    question_candidate = next(row for row in review["candidates"] if row["family"] == "question_policy")
    assert question_candidate["weight_summary"]["has_model_signal_question_policy"] is True
    assert review["next_mainline_selection"]["task_id"] == "F3"


def test_targeted_calibration_candidate_review_blocks_when_f1_not_ready() -> None:
    review = build_targeted_calibration_candidate_review(
        frozen_core_calibration_review={
            "version": "v30.frozen_core_calibration_review.v1",
            "decision": {"calibration_baseline_ready": False},
        },
        training_signals=[],
        families=("structure_policy",),
        review_id="unit-f2-blocked",
    )

    assert review["decision"]["targeted_calibration_review_ready"] is False
    assert "f1_calibration_baseline_not_ready" in review["decision"]["blockers"]
    assert "targeted_candidate_count_low" in review["decision"]["blockers"]
    assert review["next_mainline_selection"]["task_id"] == "F2"
