from __future__ import annotations

from copy import deepcopy

from v30.validation.real_business_steady_state import (
    REAL_BUSINESS_STEADY_STATE_VERSION,
    build_real_business_steady_state,
)


def _b6_ready() -> dict[str, object]:
    return {
        "version": "v30.real_business_acceptance_closeout.v1",
        "status": "completed",
        "decision": {
            "business_acceptance_closeout_ready": True,
            "decision_status": "b6_business_acceptance_closed",
            "business_track_paused": True,
            "major_validation_requires_explicit_request": True,
            "external_release_ready": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "accepted_business_gate": {
            "version": "v30.business_reading_acceptance_gate.v1",
            "gate_status": "frozen_default_gate",
            "required_tasks": ["B1", "B2", "B3", "B4", "B5"],
            "default_validation_command": "python3 scripts/run_real_business_api_contract_freeze.py",
            "major_validation_requires_explicit_request": True,
            "full_pytest_default": False,
            "full_518k_default": False,
            "external_release_default": False,
            "policy_pointer_promotion_default": False,
            "chart_fact_mutation_allowed": False,
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "pointer_write_allowed": False,
            "business_track_auto_continue_allowed": False,
        },
    }


def test_s1_enters_business_acceptance_steady_state_after_b6_closeout() -> None:
    result = build_real_business_steady_state(b6_acceptance_closeout=_b6_ready())

    assert result["version"] == REAL_BUSINESS_STEADY_STATE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "s1_business_acceptance_steady_state_ready"
    assert result["decision"]["passed_steady_state_check_count"] == 5
    assert result["decision"]["business_track_paused"] is True
    assert result["decision"]["waiting_for_new_business_evidence"] is True
    assert result["routine_business_gate"]["default_gate"] == "B1-B5"
    assert result["routine_business_gate"]["business_track_auto_continue_allowed"] is False
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "S1-WAIT"
    assert result["boundary"] == "s1_business_acceptance_steady_state_after_b6_closeout"


def test_s1_blocks_if_b6_reopens_business_track_or_requests_heavy_validation() -> None:
    b6 = deepcopy(_b6_ready())
    b6["decision"]["business_track_paused"] = False  # type: ignore[index]
    b6["decision"]["full_518k_required"] = True  # type: ignore[index]
    b6["accepted_business_gate"]["full_518k_default"] = True  # type: ignore[index]
    b6["policy_boundary"]["business_track_auto_continue_allowed"] = True  # type: ignore[index]

    result = build_real_business_steady_state(b6_acceptance_closeout=b6)

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "s1_business_acceptance_steady_state_blocked"
    assert "business_track_not_paused" in result["decision"]["blockers"]
    assert "unexpected_heavy_validation_request" in result["decision"]["blockers"]
    assert "business_steady_state_checks_failed" in result["decision"]["blockers"]
    assert set(result["decision"]["failed_steady_state_check_ids"]) == {
        "b6_closeout_ready",
        "major_validation_explicit_only",
        "business_track_no_auto_continue",
    }
    assert result["next_mainline_selection"]["task_id"] == "S1-FR"


def test_s1_blocks_release_pointer_or_chart_fact_mutation_pressure() -> None:
    b6 = deepcopy(_b6_ready())
    b6["decision"]["external_release_ready"] = True  # type: ignore[index]
    b6["decision"]["policy_pointer_promotion_allowed"] = True  # type: ignore[index]
    b6["accepted_business_gate"]["chart_fact_mutation_allowed"] = True  # type: ignore[index]

    result = build_real_business_steady_state(b6_acceptance_closeout=b6)

    assert result["status"] == "blocked"
    assert "unexpected_external_release_pressure" in result["decision"]["blockers"]
    assert "unexpected_pointer_pressure" in result["decision"]["blockers"]
    assert "unexpected_chart_fact_mutation_pressure" in result["decision"]["blockers"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False
