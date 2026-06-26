from __future__ import annotations

from v30.validation.core_mainline_selection_after_release_hold import (
    CORE_MAINLINE_SELECTION_AFTER_RELEASE_HOLD_VERSION,
    build_core_mainline_selection_after_release_hold,
    run_core_mainline_selection_after_release_hold,
)


def _rel_s4(*, complete: bool = True, external_release_allowed: bool = False) -> dict[str, object]:
    return {
        "version": "v30.stage_a_evidence_review.v1",
        "status": "completed" if complete else "blocked",
        "decision": {
            "stage_a_evidence_review_complete": complete,
            "decision_status": "rel_s4_stage_a_evidence_review_complete_external_release_held" if complete else "blocked",
            "controlled_trial_readiness_confirmed": complete,
            "external_release_allowed": external_release_allowed,
            "return_to_core_module_mainline": complete,
            "additional_heavy_live_gate_authorization_recommended": False,
            "full_pytest_authorized": False,
            "live_llm_smoke_authorized": False,
            "real_env_smoke_authorized": False,
            "full_518k_authorized": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def _module_review(*, ready: bool = True) -> dict[str, object]:
    return {
        "version": "v30.main_module_completion_review.v1",
        "decision": {
            "decision_status": "mcr1_main_module_review_ready" if ready else "blocked",
            "main_module_completion_review_ready": ready,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "policy_pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "module_completion_matrix": [
            {"module_id": "M1/M2"},
            {"module_id": "M3"},
            {"module_id": "M4"},
            {"module_id": "M5"},
            {"module_id": "M6"},
            {"module_id": "M7"},
            {"module_id": "M8"},
        ],
    }


def test_mcr3_selects_synthetic_archetype_core_calibration() -> None:
    result = build_core_mainline_selection_after_release_hold(
        stage_a_evidence_review=_rel_s4(),
        main_module_completion_review=_module_review(),
    )

    assert result["version"] == CORE_MAINLINE_SELECTION_AFTER_RELEASE_HOLD_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "mcr3_core_mainline_selected"
    assert result["decision"]["selected_task_id"] == "SYN-CAL1"
    assert result["decision"]["external_release_allowed"] is False
    assert result["decision"]["real_person_truth_label_allowed"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL1"
    assert result["next_mainline_selection"]["full_pytest_run_now"] is False


def test_mcr3_blocks_if_release_hold_is_not_closed() -> None:
    result = build_core_mainline_selection_after_release_hold(
        stage_a_evidence_review=_rel_s4(complete=False),
        main_module_completion_review=_module_review(),
    )

    assert result["status"] == "blocked"
    assert "rel_s4_evidence_not_complete" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "MCR3-FR"


def test_mcr3_blocks_if_external_release_is_unexpectedly_allowed() -> None:
    result = build_core_mainline_selection_after_release_hold(
        stage_a_evidence_review=_rel_s4(external_release_allowed=True),
        main_module_completion_review=_module_review(),
    )

    assert result["status"] == "blocked"
    assert "external_release_unexpectedly_allowed" in result["decision"]["blockers"]
    assert result["decision"]["external_release_allowed"] is False


def test_mcr3_runner_uses_recorded_rel_s4_baseline_without_stage_a_rerun() -> None:
    result = run_core_mainline_selection_after_release_hold(reading_id="pytest-mcr3")

    assert result["decision"]["decision_status"] == "mcr3_core_mainline_selected"
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL1"
    assert result["release_hold_summary"]["decision_status"] == "rel_s4_stage_a_evidence_review_complete_external_release_held"
