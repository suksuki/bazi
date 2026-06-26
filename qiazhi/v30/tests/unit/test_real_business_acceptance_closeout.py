from __future__ import annotations

from copy import deepcopy

from v30.validation.real_business_acceptance_closeout import (
    REAL_BUSINESS_ACCEPTANCE_CLOSEOUT_VERSION,
    build_real_business_acceptance_closeout,
)


def _b5_ready() -> dict[str, object]:
    return {
        "version": "v30.real_business_api_contract_freeze.v1",
        "status": "completed",
        "decision": {
            "api_contract_freeze_ready": True,
            "decision_status": "b5_business_api_contract_frozen",
            "external_release_ready": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "freeze_summary": {
            "gate_count": 4,
            "passed_gate_count": 4,
            "failed_gate_count": 0,
            "minimum_business_acceptance": ["B1", "B2", "B3", "B4"],
        },
        "api_contract": {
            "version": "v30.business_reading_api_contract.v1",
            "contract_status": "frozen_for_current_business_acceptance_scope",
            "additive_api_policy": {
                "field_removal_allowed": False,
                "new_fields_allowed": True,
            },
            "forbidden_behaviors": [
                "fabricate_pillars_for_pending_or_blocked_birth_input",
                "promote_m4_m5_m6_ready_state_without_ready_chart",
                "mutate_chart_facts_from_answer_feedback",
                "expose_policy_effect_raw_score_or_training_signal_to_customer",
                "run_full_pytest_or_full_518k_by_default",
                "promote_policy_pointer_from_business_contract_freeze",
            ],
        },
        "policy_boundary": {
            "external_release_allowed": False,
        },
    }


def test_b6_closes_business_acceptance_after_b5_contract_freeze() -> None:
    result = build_real_business_acceptance_closeout(b5_api_contract_freeze=_b5_ready())

    assert result["version"] == REAL_BUSINESS_ACCEPTANCE_CLOSEOUT_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "b6_business_acceptance_closed"
    assert result["decision"]["business_track_paused"] is True
    assert result["decision"]["major_validation_requires_explicit_request"] is True
    assert all(row["passed"] for row in result["closeout_checks"])
    assert result["accepted_business_gate"]["gate_status"] == "frozen_default_gate"
    assert result["accepted_business_gate"]["full_pytest_default"] is False
    assert result["policy_boundary"]["business_track_auto_continue_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "S1"


def test_b6_blocks_if_b5_allows_field_removal_or_heavy_validation() -> None:
    b5 = deepcopy(_b5_ready())
    b5["api_contract"]["additive_api_policy"]["field_removal_allowed"] = True  # type: ignore[index]
    b5["decision"]["full_pytest_required"] = True  # type: ignore[index]

    result = build_real_business_acceptance_closeout(b5_api_contract_freeze=b5)

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "b6_business_acceptance_closeout_blocked"
    assert "business_acceptance_closeout_checks_failed" in result["decision"]["blockers"]
    assert set(result["decision"]["failed_check_ids"]) == {
        "api_contract_frozen_additive",
        "no_release_heavy_pointer_or_fact_mutation",
    }
    assert result["decision"]["chart_fact_mutation_allowed"] is False
