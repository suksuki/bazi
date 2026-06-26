from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_llm_bazi_expression_support_review,
    run_llm_bazi_expression_support_review,
)


def _iq(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.iq_intelligent_question_support_review.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "iq_intelligent_question_support_ready" if ready else "iq_intelligent_question_support_blocked",
            "iq_support_review_ready": ready,
            "interaction_loop_case_count": 5,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "live_llm_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
        },
    }


def _llm(*, blocked: bool = False, live_required: bool = False, mutate: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.bazi_llm_closeout.v1",
        "decision": {
            "decision_status": "bl8_bazi_llm_steady_state_ready" if ready else "bl8_bazi_llm_closeout_blocked",
            "closeout_ready": ready,
            "bazi_llm_steady_state": ready,
            "optional_live_smoke_allowed": True,
            "live_llm_required": live_required,
            "chart_fact_mutation_allowed": mutate,
            "policy_pointer_write_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "completion_summary": {
            "bazi_llm_context_compiler_completion": 90 if ready else 80,
            "bazi_llm_prompt_registry_completion": 88 if ready else 80,
            "bazi_llm_answer_generator_completion": 88 if ready else 80,
            "bazi_llm_output_acceptance_completion": 88 if ready else 80,
            "bazi_llm_training_synthetic_completion": 86 if ready else 80,
            "bazi_llm_role_locale_completion": 86 if ready else 80,
            "bazi_llm_mainline_completion": 88 if ready else 80,
        },
        "accepted_evidence": {
            key: {"ready": ready}
            for key in ("bl1_bl3", "bl4", "bl5", "bl6", "bl7")
        },
        "steady_state": {
            "boundary": "bazi_llm_steady_state_keeps_llm_as_expression_layer_not_calculation_engine",
        },
    }


def _acceptance(*, blocked: bool = False, bad_training: bool = False) -> dict[str, object]:
    ready = not blocked
    quality = {
        "readiness_ready": ready,
        "accepted_count": 2,
        "rejected_count": 3,
        "schema_rejected_count": 1,
        "role_failure_count": 1,
        "drift_rejected_count": 1,
        "chart_fact_mutation_allowed": False,
        "live_llm_required": False,
    }
    return {
        "suite_id": "v30.synthetic.bazi_llm_acceptance",
        "passed": ready,
        "case_count": 5,
        "passed_count": 5 if ready else 4,
        "results": [
            {
                "case_id": f"case_{idx}",
                "observed": {"bazi_llm_output_acceptance_quality": quality},
            }
            for idx in range(5)
        ],
        "training_signals": [
            {
                "signal_id": "v30.training_signal.bazi_llm_output_acceptance_quality",
                "domain": "llm",
                "signal_type": "bazi_llm_output_acceptance_quality",
                "strength": 1.0,
                "payload": {
                    "accepted_count": 2,
                    "rejected_count": 3,
                    "schema_rejected_count": 1,
                    "role_failure_count": 1,
                    "drift_rejected_count": 1,
                    "can_tune_expression": True,
                    "can_tune_question_strategy": True,
                    "can_tune_chart_facts": bad_training,
                    "chart_fact_mutation_allowed_count": 1 if bad_training else 0,
                },
            }
        ],
    }


def test_llm_bazi_expression_support_review_ready(tmp_path: Path) -> None:
    result = build_llm_bazi_expression_support_review(
        iq_support=_iq(),
        llm_closeout=_llm(),
        bazi_llm_acceptance=_acceptance(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.llm_bazi_expression_support_review.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "llm_bazi_expression_support_ready"
    assert result["next_mainline_selection"]["next_task"] == "Training/Synthetic Support Review"
    assert Path(str(result["artifact_uri"])).exists()


def test_llm_support_review_blocks_missing_iq_or_bl8() -> None:
    iq_result = build_llm_bazi_expression_support_review(
        iq_support=_iq(blocked=True),
        llm_closeout=_llm(),
        bazi_llm_acceptance=_acceptance(),
    )
    bl8_result = build_llm_bazi_expression_support_review(
        iq_support=_iq(),
        llm_closeout=_llm(blocked=True),
        bazi_llm_acceptance=_acceptance(),
    )

    assert "iq_support_ready_before_llm_review" in iq_result["decision"]["failed_closeout_check_ids"]
    assert "bl8_bazi_llm_closeout_ready" in bl8_result["decision"]["failed_closeout_check_ids"]


def test_llm_support_review_blocks_acceptance_or_training_gap() -> None:
    acceptance_result = build_llm_bazi_expression_support_review(
        iq_support=_iq(),
        llm_closeout=_llm(),
        bazi_llm_acceptance=_acceptance(blocked=True),
    )
    training_result = build_llm_bazi_expression_support_review(
        iq_support=_iq(),
        llm_closeout=_llm(),
        bazi_llm_acceptance=_acceptance(bad_training=True),
    )

    assert "bazi_llm_acceptance_synthetic_ready" in acceptance_result["decision"]["failed_closeout_check_ids"]
    assert "llm_training_boundary_locked" in training_result["decision"]["failed_closeout_check_ids"]


def test_llm_support_review_blocks_live_or_mutation_boundary_gap() -> None:
    result = build_llm_bazi_expression_support_review(
        iq_support=_iq(),
        llm_closeout=_llm(live_required=True, mutate=True),
        bazi_llm_acceptance=_acceptance(),
    )

    assert result["status"] == "blocked"
    assert "live_heavy_and_fact_generation_boundaries_locked" in result["decision"]["failed_closeout_check_ids"]


def test_llm_bazi_expression_support_review_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_llm_bazi_expression_support_review(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "llm_bazi_expression_support_ready"
    assert result["decision"]["bazi_llm_acceptance_case_count"] >= 5
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
