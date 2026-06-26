from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_iq_intelligent_question_support_review,
    run_iq_intelligent_question_support_review,
)


def _m8(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.m8_projection_api_contract_closeout.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "m8_projection_api_contract_closed" if ready else "m8_projection_api_contract_closeout_blocked",
            "m8_projection_api_contract_closed": ready,
            "projection_case_count": 30,
            "projection_contract_count": 25,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def _iq(
    *,
    blocked: bool = False,
    role_leak: bool = False,
    training_can_mutate: bool = False,
    llm_mutates: bool = False,
) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.intelligent_question_closeout.v1",
        "decision": {
            "decision_status": "iq5_intelligent_question_closeout_ready" if ready else "iq5_intelligent_question_closeout_blocked",
            "intelligent_question_closeout_ready": ready,
            "check_count": 6,
            "passed_count": 6 if ready else 5,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "live_llm_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
        },
        "module_completion": {
            "question_dialogue_graph": 98 if ready else 97,
            "question_policy_training": 92 if ready else 90,
            "llm_question_context": 92 if ready else 90,
        },
        "closeout_summary": {
            "layer_contract": {
                "recommendation_count": 5,
                "user_question_count": 3,
                "visible_next_question_id": "q_visible",
                "internal_next_question_id": "q_internal",
                "user_diagnostic_key_count": 1 if role_leak else 0,
                "admin_has_interaction_state": True,
                "admin_has_question_dialogue_graph": True,
            },
            "training_candidate": {
                "has_model_signal_question_policy": True,
                "model_signal_policy_can_tune_chart_facts": training_can_mutate,
                "has_interaction_followup_policy": True,
                "has_adaptive_question_policy": True,
            },
            "llm_and_role": {
                "answer_task_type": "domain_followup",
                "answer_context_pack": "BaziDomainContext",
                "domain_chart_fact_mutation_allowed": llm_mutates,
                "user_internal_next_visible": role_leak,
            },
            "core_boundary": {
                "core_fingerprint_unchanged": True,
                "model_signal_version": "v30.model_signal_summary.v1",
                "ranked_decision_domains": ["strength", "structure_pattern", "useful_god"],
                "business_topics_present": ["career", "wealth", "timing"],
            },
            "steady_state": {
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
                "live_llm_required": False,
                "policy_pointer_write_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
        },
    }


def _interaction(*, missing_signal: bool = False) -> dict[str, object]:
    signals = [
        "v30.training_signal.question_dialogue_outcome",
        "v30.training_signal.interaction_state_machine",
        "v30.training_signal.interaction_loop_quality",
        "v30.training_signal.question_model_signal_personalization",
    ]
    if missing_signal:
        signals = signals[:2]
    return {
        "suite_id": "v30.synthetic.interaction_loop",
        "passed": not missing_signal,
        "case_count": 5,
        "passed_count": 5 if not missing_signal else 4,
        "training_signals": [{"signal_id": signal_id} for signal_id in signals],
    }


def test_iq_intelligent_question_support_review_ready(tmp_path: Path) -> None:
    result = build_iq_intelligent_question_support_review(
        m8_closeout=_m8(),
        iq_closeout=_iq(),
        interaction_loop=_interaction(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.iq_intelligent_question_support_review.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "iq_intelligent_question_support_ready"
    assert result["next_mainline_selection"]["next_task"] == "LLM Bazi Expression Support Review"
    assert Path(str(result["artifact_uri"])).exists()


def test_iq_support_review_blocks_missing_m8_closeout() -> None:
    result = build_iq_intelligent_question_support_review(
        m8_closeout=_m8(blocked=True),
        iq_closeout=_iq(),
        interaction_loop=_interaction(),
    )

    assert result["status"] == "blocked"
    assert "m8_projection_surface_ready_before_iq_review" in result["decision"]["failed_closeout_check_ids"]


def test_iq_support_review_blocks_iq5_or_interaction_gap() -> None:
    iq_result = build_iq_intelligent_question_support_review(
        m8_closeout=_m8(),
        iq_closeout=_iq(blocked=True),
        interaction_loop=_interaction(),
    )
    interaction_result = build_iq_intelligent_question_support_review(
        m8_closeout=_m8(),
        iq_closeout=_iq(),
        interaction_loop=_interaction(missing_signal=True),
    )

    assert "iq5_closeout_remains_ready" in iq_result["decision"]["failed_closeout_check_ids"]
    assert "interaction_loop_trainable_and_passing" in interaction_result["decision"]["failed_closeout_check_ids"]


def test_iq_support_review_blocks_role_training_or_llm_boundary_gap() -> None:
    role_result = build_iq_intelligent_question_support_review(
        m8_closeout=_m8(),
        iq_closeout=_iq(role_leak=True),
        interaction_loop=_interaction(),
    )
    training_result = build_iq_intelligent_question_support_review(
        m8_closeout=_m8(),
        iq_closeout=_iq(training_can_mutate=True),
        interaction_loop=_interaction(),
    )
    llm_result = build_iq_intelligent_question_support_review(
        m8_closeout=_m8(),
        iq_closeout=_iq(llm_mutates=True),
        interaction_loop=_interaction(),
    )

    assert "question_flow_is_personalized_and_role_safe" in role_result["decision"]["failed_closeout_check_ids"]
    assert "question_training_and_llm_boundaries_locked" in training_result["decision"]["failed_closeout_check_ids"]
    assert "question_training_and_llm_boundaries_locked" in llm_result["decision"]["failed_closeout_check_ids"]


def test_iq_intelligent_question_support_review_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_iq_intelligent_question_support_review(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "iq_intelligent_question_support_ready"
    assert result["decision"]["interaction_loop_case_count"] >= 5
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
